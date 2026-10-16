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
spawn, or a graveyard) within 60-250 yards of it (400, then 600, if there is none) that is at least SAFE_DISTANCE yards (plus its wander radius)
from every creature hostile to Alliance or Horde players, and from every point of their patrol paths.
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

# Destinations, one per Bulletin Board open-world quest: (quest id, name, zone, target entries)
DESTINATIONS = [(920000 + i, title.replace('Bounty: ', ''), zone, [t[0] for t in targets])
                for i, (title, zone, targets) in enumerate(KILL_QUESTS, start=1)]
DESTINATIONS += [(ELITE_QUEST_BASE + i, place, zone, [t[0] for t in targets])
                 for i, (place, zone, targets) in enumerate(ELITE_QUESTS, start=1)]

# Landing spots from --find (quest id: map, x, y, z, orientation)
SPOTS = {
    920001: (0, 2750.24, -4042.46, 96.15, 4.84),  # The Plaguewood: 120 yd from the camp, nearest hostile 49 yd, at: Argent Dawn Infantry
    920002: (0, 1855.35, -4576.70, 79.52, 0.38),  # Abominations of the Plague: 165 yd from the camp, nearest hostile 41 yd, at: Plaguebloom
    920003: (0, 3089.17, -5043.34, 119.61, 0.26),  # Mossflayer Trolls: 329 yd from the camp, nearest hostile 73 yd, at: Mountain Silversage
    920004: (0, 2955.94, -1341.01, 151.77, 4.74),  # The Scarlet Crusade: 160 yd from the camp, nearest hostile 39 yd, at: Rich Thorium Vein
    920005: (0, 1402.24, -1103.01, 72.02, 4.65),  # The Restless Dead: 283 yd from the camp, nearest hostile 45 yd, at: Mithril Deposit
    920006: (0, 1593.42, -2215.51, 64.31, 5.50),  # Wailing Spirits: 140 yd from the camp, nearest hostile 53 yd, at: Small Thorium Vein
    920007: (1, -7773.97, 1185.79, 0.29, 0.80),  # Hive'Zora: 627 yd from the camp, nearest hostile 45 yd, at: Cenarion Outrider
    920008: (1, -7561.12, 574.45, -21.49, 3.85),  # Hive'Regal: 255 yd from the camp, nearest hostile 67 yd, at: Small Thorium Vein
    920009: (1, -6999.62, 928.20, 8.17, 1.54),  # The Twilight's Hammer: 238 yd from the camp, nearest hostile 43 yd, at: Camp Banner
    920010: (1, -7493.65, 901.77, 4.00, 1.20),  # Stonelash Scorpids: 391 yd from the camp, nearest hostile 45 yd, at: Golden Sansam
    920011: (1, -6867.83, 1851.35, 24.27, 6.27),  # Dust and Stone: 278 yd from the camp, nearest hostile 64 yd, at: Mountain Silversage
    920012: (1, 7930.05, -3865.68, 696.55, 3.29),  # Frostsaber Rock: 118 yd from the camp, nearest hostile 53 yd, at: Scourge Invasion Minion, finder
    920013: (1, 7781.15, -4582.95, 683.45, 0.92),  # The Shardtooth Packs: 74 yd from the camp, nearest hostile 42 yd, at: Winterspring Screecher
    920014: (1, 7340.50, -4418.61, 650.00, 5.87),  # Owlbeasts and Chimaera: 171 yd from the camp, nearest hostile 51 yd, at: Winterspring Screecher
    920015: (1, 6453.11, -4802.73, 717.26, 4.86),  # Ice Thistle Yetis: 253 yd from the camp, nearest hostile 67 yd, at: Winterspring Owl
    920016: (0, -7638.90, -1553.96, 166.70, 2.42),  # The Blackrock Clan: 100 yd from the camp, nearest hostile 52 yd, at: Mountain Silversage
    920901: (0, -11758.30, -2830.26, 7.19, 2.38),  # The Tainted Scar: 273 yd from the camp, nearest hostile 52 yd, at: Bonfire
    920902: (0, -4144.73, -2474.29, 185.60, 4.79),  # The Dragonmaw Gates: 1463 yd from the camp, nearest hostile 82 yd, at: Copper Vein
    920903: (0, -1068.65, 145.38, 66.37, 2.13),  # Purgation Isle: 485 yd from the camp, nearest hostile 45 yd, at: Briarthorn
    920904: (0, 1507.19, -5424.58, 111.44, 5.49),  # Tyr's Hand: 155 yd from the camp, nearest hostile 55 yd, at: Mountain Silversage
    920905: (1, -2827.14, -4737.72, 5.91, 5.21),  # Alcaz Island: 271 yd from the camp, nearest hostile 62 yd, at: Alliance Bell
    920906: (1, -4774.86, 3676.36, 11.14, 3.36),  # The Isle of Dread: 1293 yd from the camp, nearest hostile 43 yd, at: Purple Lotus
    920907: (1, 4460.24, -4287.70, 918.15, 4.22),  # Darkwhisper Gorge: 160 yd from the camp, nearest hostile 60 yd, at: graveyard
    920908: (1, 5166.90, -4775.03, 701.53, 5.90),  # Frostwhisper Gorge: 68 yd from the camp, nearest hostile 54 yd, at: Rich Thorium Vein
    920909: (1, 6578.92, -4341.99, 692.45, 2.97),  # Mazthoril: 438 yd from the camp, nearest hostile 59 yd, at: Icecap
    920910: (0, 755.06, -3831.65, 127.91, 4.44),  # Seradane: 103 yd from the camp, nearest hostile 37 yd, at: Mithril Deposit
    920911: (1, -2801.66, 2058.35, 29.15, 5.16),  # Jademir Lake: 221 yd from the camp, nearest hostile 40 yd, at: Liferoot
    920912: (1, 2939.44, -3543.78, 109.80, 6.11),  # Bough Shadow: 251 yd from the camp, nearest hostile 58 yd, at: Mageroyal
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
        spots[qid] = (m, round(gx, 2), round(gy, 2), round(gz + 0.5, 2), round(o, 2))
        print(f'    {qid}: ({m}, {gx:.2f}, {gy:.2f}, {gz + 0.5:.2f}, {o:.2f}),  '
              f'# {name}: {dist:.0f} yd from the camp, nearest hostile {nearest:.0f} yd, at: {what}')
    return spots


# ---------------------------------------------------------------- SQL


def main():
    missing = [d[0] for d in DESTINATIONS if d[0] not in SPOTS]
    assert not missing, f'no landing spot for quests {missing}: run --find'
    guids = [9190211 + n for n in range(len(BOARD_SPAWNS))]
    rows = [f"({qid}, {sql_str(name)}, {sql_str(zone)}, {m}, {x}, {y}, {z}, {o})"
            for qid, name, zone, _ in DESTINATIONS for (m, x, y, z, o) in [SPOTS[qid]]]
    spawns = [f"({g}, {NPC}, {m}, 1, 1, {x + NPC_OFFSET[0]:.2f}, {y + NPC_OFFSET[1]:.2f}, {z:.2f}, {o}, 300, 0, 0, "
              f"'mod-unbound Bounty Wayfinder')" for g, (_, m, x, y, z, o) in zip(guids, BOARD_SPAWNS)]
    sql = [
        '-- Generated by tools/bounty_teleporter.py - edit the tables there, not this file.',
        '-- The Bounty Wayfinder (src/unbound_bounty_teleporter.cpp) beside every Bulletin Board.',
        '',
        'CREATE TABLE IF NOT EXISTS `unbound_bounty_teleports` (',
        '  `quest` INT UNSIGNED NOT NULL,',
        "  `name` VARCHAR(100) NOT NULL DEFAULT '',",
        "  `zone` VARCHAR(100) NOT NULL DEFAULT '',",
        '  `map` SMALLINT UNSIGNED NOT NULL,',
        '  `x` FLOAT NOT NULL, `y` FLOAT NOT NULL, `z` FLOAT NOT NULL, `o` FLOAT NOT NULL,',
        '  PRIMARY KEY (`quest`)',
        ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='mod-unbound: Bounty Wayfinder destinations';",
        'DELETE FROM `unbound_bounty_teleports`;',
        'INSERT INTO `unbound_bounty_teleports` (`quest`, `name`, `zone`, `map`, `x`, `y`, `z`, `o`) VALUES',
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
