"""
Bounty Wayfinder: an NPC beside every Bulletin Board that teleports players close to the Bulletin Board's
open-world quests (the daily kill bounties and the weekly elite bounties), never into a hostile creature's
aggro range.

The gossip menu and the teleports are C++ (src/unbound_bounty_teleporter.cpp), which reads the destinations
from the world table `unbound_bounty_teleports` that this tool generates:

  python tools/bounty_teleporter.py          writes data/sql/db-world/unbound_bounty_teleporter.sql
  python tools/bounty_teleporter.py --find   recomputes the landing spots from the live world database and
                                             prints them; paste the result into SPOTS below

How --find picks a landing spot for a quest: the centre of the densest group of the quest's targets, then the
nearest point on the ground (a gameobject spawn such as a herb, ore or chest, a friendly or neutral creature's
spawn, or a graveyard) within 60-250 yards of it (then 400, 600, 1500) that is at least SAFE_DISTANCE yards
(plus its wander radius) from every creature hostile to Alliance or Horde players, and from every point of
their patrol paths (GUARD_DISTANCE from a town's guards). Then the drop point: from the camp's centre out
towards that ground spot, the first point at least as safe, DROP_HEIGHT yards above the highest ground nearby.
Players arrive there with Wayfinder's Descent (spell 200204, a slow fall that lasts until they land), see the
camp from above and glide in; caves and tunnels (GROUND_ONLY) teleport to the ground spot instead.
The aggro range of a level 62 creature against a level 60 player is about 22 yards.

Reserved IDs: NPC 190211, spawn guids 9190211-9190212. Re-running deletes and re-inserts exactly these rows.
"""
import math
import os
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from bulletin_board import BOARD_SPAWNS, KILL_QUESTS, ELITE_QUESTS, ELITE_QUEST_BASE  # noqa: E402
from heroic_loot import sql_str  # noqa: E402

OUT = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_bounty_teleporter.sql')
NPC = 190211
NPC_NAME = 'Bounty Wayfinder'
NPC_SUBNAME = 'Bulletin Board Teleports'
NPC_DISPLAY = 2968        # Archmage Malin's display (a robed human mage)
NPC_OFFSET = (2.5, 2.5)   # yards from the board (move with .npc move)
GREETING = ('Bounties go stale while you walk, $N. Tell me which one you are after and I will send you there: '
            'close to your quarry, but not into its jaws.')

SAFE_DISTANCE = 35.0      # yards from any hostile creature (aggro range is about 20-25 at level 60)
MIN_FROM_CAMP = 60.0
SEARCH_STEPS = (250.0, 400.0, 600.0)   # yards: the nearest safe spot within the first step that has one
FALLBACK = (28.0, 1500.0)              # if none: at least 28 yards from hostiles (still past aggro), within 1500
GUARD_DISTANCE = 80.0                  # yards from creatures hostile to one faction only (towns' guards)
DROP_HEIGHT = 90.0                     # yards above the highest known ground near the drop point
DROP_MIN_FROM_CAMP = 40.0              # the drop point never comes closer to the camp's centre than this
# Camps in caves or tunnels: a drop from the sky would land on the rock above them, so these teleport to the
# ground spot instead.
GROUND_ONLY = {920008, 920909}         # Hive'Regal (tunnels), Mazthoril (cave)

# Destinations, one per Bulletin Board open-world quest: (quest id, name, zone, target entries)
DESTINATIONS = [(920000 + i, title.replace('Bounty: ', ''), zone, [t[0] for t in targets])
                for i, (title, zone, targets) in enumerate(KILL_QUESTS, start=1)]
DESTINATIONS += [(ELITE_QUEST_BASE + i, place, zone, [t[0] for t in targets])
                 for i, (place, zone, targets) in enumerate(ELITE_QUESTS, start=1)]

# Landing spots from --find (quest id: map, x, y, z, orientation, drop): the ground spot, and the point in the
# air the Wayfinder drops players from (x, y, z; None = teleport to the ground spot), with Wayfinder's Descent
# (spell 200204, a slow fall that lasts until they land) so they can glide in and choose their way.
SPOTS = {
    # The Plaguewood: ground spot 120 yd from the camp (Argent Dawn Infantry), nearest hostile 49 yd; drop 109 yd out
    920001: (0, 2750.24, -4042.46, 96.15, 4.84, (2751.61, -4052.77, 215.27)),
    # Abominations of the Plague: ground spot 165 yd from the camp (Plaguebloom), nearest hostile 41 yd; drop 160 yd out
    920002: (0, 1855.35, -4576.70, 79.52, 0.38, (1860.13, -4574.77, 172.56)),
    # Mossflayer Trolls: ground spot 329 yd from the camp (Mountain Silversage), nearest hostile 73 yd; drop 122 yd out
    920003: (0, 3089.17, -5043.34, 119.61, 0.26, (3290.14, -4990.54, 274.14)),
    # The Scarlet Crusade: ground spot 160 yd from the camp (Rich Thorium Vein), nearest hostile 39 yd; drop 160 yd out
    920004: (0, 2955.94, -1341.01, 151.77, 4.74, (2955.94, -1341.01, 257.16)),
    # The Restless Dead: ground spot 283 yd from the camp (Mithril Deposit), nearest hostile 45 yd; drop 283 yd out
    920005: (0, 1402.24, -1103.01, 72.02, 4.65, (1402.24, -1103.01, 169.84)),
    # Wailing Spirits: ground spot 140 yd from the camp (Small Thorium Vein), nearest hostile 53 yd; drop 135 yd out
    920006: (0, 1593.42, -2215.51, 64.31, 5.50, (1597.09, -2219.16, 153.81)),
    # Hive'Zora: ground spot 627 yd from the camp (Cenarion Outrider), nearest hostile 45 yd;
    #   drop 130 yd out (check: 1 ground points 20+ yd above the camp, a cave?)
    920007: (1, -7773.97, 1185.79, 0.29, 0.80, (-7427.65, 1541.33, 96.13)),
    # Hive'Regal: ground spot 255 yd from the camp (Small Thorium Vein), nearest hostile 67 yd; ground only
    920008: (1, -7561.12, 574.45, -21.49, 3.85, None),
    # The Twilight's Hammer: ground spot 238 yd from the camp (Camp Banner), nearest hostile 43 yd; drop 218 yd out
    920009: (1, -6999.62, 928.20, 8.17, 1.54, (-6999.09, 948.44, 105.13)),
    # Stonelash Scorpids: ground spot 391 yd from the camp (Golden Sansam), nearest hostile 45 yd; drop 391 yd out
    920010: (1, -7493.65, 901.77, 4.00, 1.20, (-7493.65, 901.77, 94.11)),
    # Dust and Stone: ground spot 278 yd from the camp (Mountain Silversage), nearest hostile 64 yd; drop 268 yd out
    920011: (1, -6867.83, 1851.35, 24.27, 6.27, (-6857.73, 1851.18, 117.24)),
    # Frostsaber Rock: ground spot 118 yd from the camp (Scourge Invasion Minion, finder), nearest hostile 53 yd;
    #   drop 118 yd out
    920012: (1, 7930.05, -3865.68, 696.55, 3.29, (7930.05, -3865.68, 853.09)),
    # The Shardtooth Packs: ground spot 74 yd from the camp (Winterspring Screecher), nearest hostile 42 yd;
    #   drop 69 yd out
    920013: (1, 7781.15, -4582.95, 683.45, 0.92, (7784.36, -4578.76, 789.22)),
    # Owlbeasts and Chimaera: ground spot 171 yd from the camp (Winterspring Screecher), nearest hostile 51 yd;
    #   drop 121 yd out
    920014: (1, 7340.50, -4418.61, 650.00, 5.87, (7386.58, -4438.76, 739.5)),
    # Ice Thistle Yetis: ground spot 253 yd from the camp (Winterspring Owl), nearest hostile 67 yd; drop 137 yd out
    920015: (1, 6453.11, -4802.73, 717.26, 4.86, (6469.85, -4918.05, 835.54)),
    # The Blackrock Clan: ground spot 100 yd from the camp (Mountain Silversage), nearest hostile 52 yd; drop 80 yd out
    920016: (0, -7638.90, -1553.96, 166.70, 2.42, (-7653.96, -1540.74, 256.2)),
    # The Tainted Scar: ground spot 273 yd from the camp (Bonfire), nearest hostile 52 yd; drop 147 yd out
    920901: (0, -11758.30, -2830.26, 7.19, 2.38, (-11849.65, -2742.61, 102.55)),
    # The Dragonmaw Gates: ground spot 1463 yd from the camp (Copper Vein), nearest hostile 82 yd; drop 185 yd out
    920902: (0, -4144.73, -2474.29, 185.60, 4.79, (-4042.14, -3748.21, 275.1)),
    # Purgation Isle: ground spot 485 yd from the camp (Briarthorn), nearest hostile 45 yd;
    #   drop 207 yd out (check: 1 ground points 20+ yd above the camp, a cave?)
    920903: (0, -1068.65, 145.38, 66.37, 2.13, (-1215.74, 381.11, 155.87)),
    # Tyr's Hand: ground spot 155 yd from the camp (Mountain Silversage), nearest hostile 55 yd; drop 135 yd out
    920904: (0, 1507.19, -5424.58, 111.44, 5.49, (1521.3, -5438.83, 201.21)),
    # Alcaz Island: ground spot 271 yd from the camp (Alliance Bell), nearest hostile 62 yd; drop 45 yd out
    920905: (1, -2827.14, -4737.72, 5.91, 5.21, (-2719.85, -4936.39, 158.3)),
    # The Isle of Dread: ground spot 1293 yd from the camp (Purple Lotus), nearest hostile 43 yd; drop 586 yd out
    920906: (1, -4774.86, 3676.36, 11.14, 3.36, (-5464.08, 3521.63, 140.66)),
    # Darkwhisper Gorge: ground spot 160 yd from the camp (graveyard), nearest hostile 60 yd; drop 140 yd out
    920907: (1, 4460.24, -4287.70, 918.15, 4.22, (4450.74, -4305.36, 1007.65)),
    # Frostwhisper Gorge: ground spot 68 yd from the camp (Rich Thorium Vein), nearest hostile 54 yd; drop 68 yd out
    920908: (1, 5166.90, -4775.03, 701.53, 5.90, (5166.9, -4775.03, 959.82)),
    # Mazthoril: ground spot 438 yd from the camp (Icecap), nearest hostile 59 yd; ground only
    920909: (1, 6578.92, -4341.99, 692.45, 2.97, None),
    # Seradane: ground spot 103 yd from the camp (Mithril Deposit), nearest hostile 37 yd; drop 103 yd out
    920910: (0, 755.06, -3831.65, 127.91, 4.44, (755.06, -3831.65, 220.5)),
    # Jademir Lake: ground spot 221 yd from the camp (Liferoot), nearest hostile 40 yd; drop 141 yd out
    920911: (1, -2801.66, 2058.35, 29.15, 5.16, (-2767.14, 1985.82, 122.06)),
    # Bough Shadow: ground spot 251 yd from the camp (Mageroyal), nearest hostile 58 yd; drop 60 yd out
    920912: (1, 2939.44, -3543.78, 109.80, 6.11, (3127.12, -3576.47, 219.84)),
}

# ---------------------------------------------------------------- --find


MYSQL = os.environ.get('UNBOUND_MYSQL', r'E:\WoW Solo Server\deps\mysql-8.4.11-winx64\bin\mysql.exe')
DBC = os.environ.get('UNBOUND_DBC', r'E:\WoW Solo Server\data\dbc')


def query(sql):
    out = subprocess.run([MYSQL, '-uacore', '-pacore', '-h127.0.0.1', 'acore_world', '-B', '-N', '-e', sql],
                         capture_output=True, text=True, check=True).stdout
    return [line.split('\t') for line in out.splitlines() if line]


def hostile_factions():
    """FactionTemplate ids hostile to Alliance or Horde players, and the ones hostile to only one of them."""
    data = open(os.path.join(DBC, 'FactionTemplate.dbc'), 'rb').read()
    _, count, fields, size, _ = struct.unpack_from('<4sIIII', data)
    player_factions = {1, 2, 3, 4, 5, 6, 115, 116, 1610, 1629}   # the playable races' factions
    hostile, one_side = set(), set()
    for i in range(count):
        v = struct.unpack_from(f'<{fields}I', data, 20 + i * size)
        tid, _faction, _flags, group, friend_group, enemy_group = v[:6]
        enemies = v[6:10]
        if enemy_group & 0x7 or any(e in player_factions for e in enemies if e):
            hostile.add(tid)
            if group & 0x6 and not group & 0x8:   # an Alliance or Horde faction (a town's guards)
                one_side.add(tid)
        elif group & 0x8 and not friend_group & 0x7:   # monsters, unless friendly to players
            hostile.add(tid)
    return hostile, one_side


def find():
    hostile, one_side = hostile_factions()
    # creature spawns in the open world: guid, id, map, x, y, z, wander, movement, faction, path, type, flags_extra,
    # rank, name
    rows = query("SELECT c.guid, c.id, c.map, c.position_x, c.position_y, c.position_z, c.wander_distance, "
                 "c.MovementType, t.faction, COALESCE(NULLIF(a.path_id, 0), ta.path_id, 0), t.type, t.flags_extra, "
                 "t.`rank`, t.name "
                 "FROM creature c JOIN creature_template t ON t.entry = c.id "
                 "LEFT JOIN creature_addon a ON a.guid = c.guid "
                 "LEFT JOIN creature_template_addon ta ON ta.entry = c.id WHERE c.map IN (0, 1)")
    creatures = [dict(guid=int(r[0]), id=int(r[1]), map=int(r[2]), x=float(r[3]), y=float(r[4]), z=float(r[5]),
                      wander=float(r[6]), move=int(r[7]), faction=int(r[8]), path=int(r[9]), type=int(r[10]),
                      civilian=int(r[11]) & 2, rank=int(r[12]), name=r[13]) for r in rows]
    paths = {}
    for pid, x, y, z in query('SELECT id, position_x, position_y, position_z FROM waypoint_data'):
        paths.setdefault(int(pid), []).append((float(x), float(y), float(z)))
    smart_paths = {}
    for entry, x, y, z in query('SELECT entry, position_x, position_y, position_z FROM waypoints'):
        smart_paths.setdefault(int(entry), []).append((float(x), float(y), float(z)))

    danger = {0: [], 1: []}   # map -> (x, y, radius)
    ground = {0: [], 1: []}   # map -> (x, y, z): places a player can stand
    for c in creatures:
        is_hostile = c['faction'] in hostile and c['type'] != 8 and not c['civilian']
        if is_hostile:
            radius = GUARD_DISTANCE if c['faction'] in one_side else SAFE_DISTANCE
            danger[c['map']].append((c['x'], c['y'], radius + c['wander']))
            for x, y, _ in paths.get(c['path'], []) + (smart_paths.get(c['id'], []) if c['move'] == 2 else []):
                danger[c['map']].append((x, y, SAFE_DISTANCE))
        elif c['type'] != 8 and c['rank'] == 0 and c['id'] < 190000:   # not on a boss or a named creature
            ground[c['map']].append((c['x'], c['y'], c['z'], c['name']))
    for m, x, y, z, name in query('SELECT g.map, g.position_x, g.position_y, g.position_z, t.name FROM gameobject g '
                                  'JOIN gameobject_template t ON t.entry = g.id '
                                  'WHERE g.map IN (0, 1) AND t.type NOT IN (11, 15, 25, 29)'):
        ground[int(m)].append((float(x), float(y), float(z), name))
    for m, x, y, z in query('SELECT Map, x, y, z FROM game_graveyard WHERE Map IN (0, 1)'):
        ground[int(m)].append((float(x), float(y), float(z), 'graveyard'))

    spots = {}
    for qid, name, zone, targets in DESTINATIONS:
        pts = [c for c in creatures if c['id'] in targets]
        maps = [p['map'] for p in pts]
        m = max(set(maps), key=maps.count)
        pts = [p for p in pts if p['map'] == m]
        best = max(pts, key=lambda p: sum(math.dist((p['x'], p['y']), (q['x'], q['y'])) < 120 for q in pts))
        group = [q for q in pts if math.dist((best['x'], best['y']), (q['x'], q['y'])) < 120]
        cx, cy = sum(q['x'] for q in group) / len(group), sum(q['y'] for q in group) / len(group)
        cz = sum(q['z'] for q in group) / len(group)
        choice = None
        for safety, limit in [(None, step) for step in SEARCH_STEPS] + [FALLBACK]:
            near_danger = [d for d in danger[m] if math.dist((cx, cy), d[:2]) < limit + 100]
            for gx, gy, gz, what in sorted(ground[m], key=lambda g: math.dist((cx, cy), g[:2])):
                dist = math.dist((cx, cy), (gx, gy))
                if dist < MIN_FROM_CAMP or abs(gz - cz) > 60:
                    continue
                if dist > limit:
                    break
                need = (lambda d: d[2]) if safety is None else (lambda d: min(d[2], d[2] - SAFE_DISTANCE + safety))
                if all(math.dist((gx, gy), d[:2]) >= need(d) for d in near_danger):
                    choice = (gx, gy, gz, dist, what)
                    break
            if choice:
                break
        if not choice:
            print(f'# {qid} {name}: NO SAFE SPOT within {FALLBACK[1]:.0f} yards', file=sys.stderr)
            continue
        gx, gy, gz, dist, what = choice
        nearest = min((math.dist((gx, gy), d[:2]) for d in near_danger), default=999)
        o = math.atan2(cy - gy, cx - gx) % (2 * math.pi)
        # the drop point: from the camp's centre out towards the ground spot, the first point (at least
        # DROP_MIN_FROM_CAMP out) that is as far from hostiles as a ground spot must be
        drop, note = None, 'ground only'
        if qid not in GROUND_ONLY:
            steps = max(1, int(dist // 5))
            for k in range(steps + 1):
                t = k / steps
                px, py = cx + (gx - cx) * t, cy + (gy - cy) * t
                if math.dist((cx, cy), (px, py)) < DROP_MIN_FROM_CAMP:
                    continue
                if all(math.dist((px, py), d[:2]) >= d[2] for d in near_danger):
                    top = max([gz, cz] + [g[2] for g in ground[m] if math.dist((px, py), g[:2]) < 150])
                    drop = (round(px, 2), round(py, 2), round(top + DROP_HEIGHT, 2))
                    note = f'drop {math.dist((cx, cy), (px, py)):.0f} yd out'
                    break
        overhead = sum(1 for g in ground[m] if math.dist((cx, cy), g[:2]) < 60 and g[2] > cz + 20)
        if overhead and qid not in GROUND_ONLY:
            note += f' (check: {overhead} ground points above the camp, a cave?)'
        spots[qid] = (m, round(gx, 2), round(gy, 2), round(gz + 0.5, 2), round(o, 2), drop)
        print(f'    # {name}: ground spot {dist:.0f} yd from the camp ({what}), nearest hostile {nearest:.0f} yd; '
              f'{note}')
        print(f'    {qid}: ({m}, {gx:.2f}, {gy:.2f}, {gz + 0.5:.2f}, {o:.2f}, {drop}),')
    return spots


# ---------------------------------------------------------------- SQL


def main():
    missing = [d[0] for d in DESTINATIONS if d[0] not in SPOTS]
    assert not missing, f'no landing spot for quests {missing}: run --find'
    guids = [9190211 + n for n in range(len(BOARD_SPAWNS))]
    rows = [f"({qid}, {sql_str(name)}, {sql_str(zone)}, {m}, {x}, {y}, {z}, {o}, "
            f"{', '.join(map(str, drop or (0, 0, 0)))}, {1 if drop else 0})"
            for qid, name, zone, _ in DESTINATIONS for (m, x, y, z, o, drop) in [SPOTS[qid]]]
    spawns = [f"({g}, {NPC}, {m}, 1, 1, {x + NPC_OFFSET[0]:.2f}, {y + NPC_OFFSET[1]:.2f}, {z:.2f}, {o}, 300, 0, 0, "
              f"'mod-unbound Bounty Wayfinder')" for g, (_, m, x, y, z, o) in zip(guids, BOARD_SPAWNS)]
    sql = [
        '-- Generated by tools/bounty_teleporter.py - edit the tables there, not this file.',
        '-- The Bounty Wayfinder (src/unbound_bounty_teleporter.cpp) beside every Bulletin Board.',
        '',
        'DROP TABLE IF EXISTS `unbound_bounty_teleports`;',
        'CREATE TABLE `unbound_bounty_teleports` (',
        '  `quest` INT UNSIGNED NOT NULL,',
        "  `name` VARCHAR(100) NOT NULL DEFAULT '',",
        "  `zone` VARCHAR(100) NOT NULL DEFAULT '',",
        '  `map` SMALLINT UNSIGNED NOT NULL,',
        '  `x` FLOAT NOT NULL, `y` FLOAT NOT NULL, `z` FLOAT NOT NULL, `o` FLOAT NOT NULL,',
        '  `drop_x` FLOAT NOT NULL DEFAULT 0, `drop_y` FLOAT NOT NULL DEFAULT 0, `drop_z` FLOAT NOT NULL DEFAULT 0,',
        "  `drop` TINYINT UNSIGNED NOT NULL DEFAULT 0 COMMENT '1: drop from drop_x/y/z with a slow fall',",
        '  PRIMARY KEY (`quest`)',
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='mod-unbound: Bounty Wayfinder destinations';",
        'INSERT INTO `unbound_bounty_teleports` (`quest`, `name`, `zone`, `map`, `x`, `y`, `z`, `o`, `drop_x`, '
        '`drop_y`, `drop_z`, `drop`) VALUES',
        ',\n'.join(rows) + ';',
        '',
        f'DELETE FROM `creature_template` WHERE `entry` = {NPC};',
        'INSERT INTO `creature_template` (`entry`, `name`, `subname`, `minlevel`, `maxlevel`, `exp`, `faction`, '
        '`npcflag`, `rank`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`, '
        '`HealthModifier`, `RegenHealth`, `flags_extra`, `ScriptName`) VALUES',
        f"({NPC}, {sql_str(NPC_NAME)}, {sql_str(NPC_SUBNAME)}, 60, 60, 0, 35, 1, 0, 2000, 2000, 8, 0, 7, 10, 1, 2, "
        "'npc_unbound_bounty_wayfinder');",
        f'DELETE FROM `creature_template_model` WHERE `CreatureID` = {NPC};',
        'INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, '
        '`Probability`, `VerifiedBuild`) VALUES',
        f'({NPC}, 0, {NPC_DISPLAY}, 1, 1, 0);',
        f'DELETE FROM `npc_text` WHERE `ID` = {NPC};',
        'INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`) VALUES',
        f"({NPC}, {sql_str(GREETING)}, '', 0, 0, 1);",
        f"DELETE FROM `creature` WHERE `guid` IN ({', '.join(map(str, guids))}) OR `id` = {NPC};",
        'INSERT INTO `creature` (`guid`, `id`, `map`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, '
        '`position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `MovementType`, `Comment`) VALUES',
        ',\n'.join(spawns) + ';',
    ]
    with open(OUT, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(sql) + '\n')
    print('wrote', OUT, f'({len(rows)} destinations, {len(spawns)} Wayfinders)')


if __name__ == '__main__':
    if '--find' in sys.argv:
        find()
    else:
        main()
