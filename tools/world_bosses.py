"""
World bosses: open-world bosses with their own spawn, fight script, zone yells and loot.

The server-wide announcements (10 and 5 minutes before it spawns, when it spawns, when it dies) and the
despawn of a boss nobody killed within a day are C++: src/unbound_world_bosses.cpp. A boss added here
must also be added to WORLD_BOSSES there (entry, spawn guid, name, location).

Everything is defined here once and generated into:

  server: data/sql/db-world/unbound_world_bosses.sql  (creatures, spawn, SmartAI, yells, items, loot)
          data/sql/db-world/unbound_custom_dbc.sql     (item_dbc rows, via tools/custom_dbc.py)
  client: patch-Z.MPQ                                   (Item.dbc rows, via tools/custom_dbc.py)

Run after changing this file:

  python tools/world_bosses.py
  python tools/custom_dbc.py

Reserved IDs: creatures 190110-190199, spawn guids 9190110-9190199, items 911000-911999.

The fights are SmartAI only (no C++), so a change here needs a worldserver restart, not a rebuild.

Reversibility: the generated SQL deletes and re-inserts exactly the rows defined here. To remove a boss,
delete it from WORLD_BOSSES and regenerate: its creature, spawn, script, texts and loot table go away.
As with heroic loot, never remove an item from WORLD_BOSS_ITEMS once it has dropped (players may own
it); take it out of the boss's loot instead.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from heroic_loot import (  # noqa: E402
    sql_str, item_sql, AGI, STR, INT, SPI, STA, DEFENSE, HIT, CRIT, AP, SPELL_POWER,
    CLS_WEAPON, CLS_ARMOR, MACE_2H, STAFF, CLOTH, LEATHER, MAIL, PLATE, SHOULDERS, CHEST, LEGS, TWO_HAND)

# creature_text Type / TextRange
YELL, BOSS_EMOTE = 14, 41
RANGE_NORMAL, RANGE_ZONE = 0, 2  # world-wide messages come from src/unbound_world_bosses.cpp

# SmartAI ids used below (src/server/game/AI/SmartScripts/SmartScriptMgr.h)
EV_UPDATE_IC, EV_HEALTH_PCT, EV_AGGRO, EV_DEATH, EV_RESPAWN, EV_JUST_SUMMONED = 0, 2, 4, 6, 11, 54
ACT_TALK, ACT_CAST, ACT_SUMMON, ACT_ZONE_COMBAT = 1, 11, 12, 38
TGT_SELF, TGT_VICTIM, TGT_RANDOM, TGT_CREATURE_RANGE = 1, 2, 5, 9
NOT_REPEATABLE = 1
TIMED_DESPAWN_OUT_OF_COMBAT = 4  # TempSummonType

# ---------------------------------------------------------------- items
# Same format as heroic_loot.HEROIC_ITEMS (base = existing item copied for everything not set here).
WORLD_BOSS_ITEMS = [
    # --- Hrimthar the Frostbound ---------------------------------------------------------------
    dict(id=911000, base=2915, name="Hrimthar's Glacial Maul", ilvl=68, cls=CLS_WEAPON, sub=MACE_2H,
         inv=TWO_HAND, mat=2, sheath=1, display=19664, dps=64.5, delay=3600,
         stats=[(STR, 32), (STA, 20), (CRIT, 14)], sell=90000),
    dict(id=911001, base=17113, name='Spire of the Frozen Lake', ilvl=68, cls=CLS_WEAPON, sub=STAFF,
         inv=TWO_HAND, mat=2, sheath=2, display=30870, dps=50.0, delay=3200,
         stats=[(INT, 26), (STA, 18), (SPI, 12), (SPELL_POWER, 40)], sell=90000),
    dict(id=911002, base=22699, name='Frostbound Legplates', ilvl=66, cls=CLS_ARMOR, sub=PLATE, inv=LEGS,
         mat=6, sheath=0, display=35278, armor=748, stats=[(STA, 28), (STR, 14), (DEFENSE, 12)], sell=60000),
    dict(id=911003, base=18699, name='Rimefrost Spaulders', ilvl=66, cls=CLS_ARMOR, sub=LEATHER,
         inv=SHOULDERS, mat=8, sheath=0, display=31142, armor=171, stats=[(AGI, 24), (STA, 14), (HIT, 10)],
         sell=60000),
    dict(id=911004, base=22968, name='Mantle of the Shattered Ice', ilvl=66, cls=CLS_ARMOR, sub=CLOTH,
         inv=SHOULDERS, mat=7, sheath=0, display=35369, armor=87,
         stats=[(INT, 17), (STA, 12), (SPI, 8), (SPELL_POWER, 21)], sell=60000),
    dict(id=911005, base=22664, name='Icebound Scale Hauberk', ilvl=67, cls=CLS_ARMOR, sub=MAIL, inv=CHEST,
         mat=5, sheath=0, display=36436, armor=490, stats=[(AGI, 24), (STA, 20), (INT, 12), (AP, 28)],
         sell=60000),
]
for _i in WORLD_BOSS_ITEMS:
    _i.update(quality=4, desc='', label='world boss')

# ---------------------------------------------------------------- bosses
# Health = 3331 (level 63 warrior base) x health_mod; Azuregos uses 275 (about 916k) for 40 players.
# damage_mod scales melee only; Azuregos uses 20.45. Spells do their own (fixed) damage.
WORLD_BOSSES = [
    dict(
        entry=190110, guid=9190110, name='Hrimthar the Frostbound', subname=None,
        display=24531, scale=1.0,             # Frost Giant Stormherald model
        level=63, faction=7,                   # 7 = neutral like Azuregos: only fights those who attack him
        creature_type=5, type_flags=44,        # giant; boss flags as on Azuregos
        immunities=169,                        # Azuregos's immunity set (no stuns, fears, etc.)
        health_mod=85, damage_mod=10.0, armor_mod=1.0,
        gold=(50000, 80000),                   # 5-8 gold (Azuregos: about 8-10)
        respawn=3 * 24 * 3600,                 # 3 days
        # Lake Kel'Theril, Winterspring: open ice between the Ruins of Kel'Theril and Everlook.
        map=1, x=6530.0, y=-4065.0, z=658.6, o=3.14,
        texts=[
            # group, type, range, text
            (0, YELL, RANGE_ZONE, 'The ice of Kel\'Theril cracks... Hrimthar the Frostbound walks again!'),
            (1, YELL, RANGE_ZONE, 'Who dares wake me upon the frozen lake? Your bones will join the ice!'),
            (2, YELL, RANGE_NORMAL, 'Rise, shards of the lake! Bury them!'),
            (3, BOSS_EMOTE, RANGE_NORMAL, '%s becomes enraged as the ice around him shatters!'),
            (4, YELL, RANGE_ZONE, 'The lake... grows... still...'),
        ],
        # (event, params(6), flags, action, action params(6), target, target params(4), comment)
        script=[
            (EV_RESPAWN, (0, 0, 0, 0, 0, 0), 0, ACT_TALK, (0, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0), 'On respawn - announce'),
            (EV_AGGRO, (0, 0, 0, 0, 0, 0), 0, ACT_TALK, (1, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0), 'On aggro - yell'),
            (EV_UPDATE_IC, (8000, 12000, 14000, 18000, 0, 0), 0, ACT_CAST, (8398, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0),
             'In combat - Frostbolt Volley (all within 20 yd, slows)'),
            (EV_UPDATE_IC, (15000, 18000, 18000, 24000, 0, 0), 0, ACT_CAST, (21099, 0, 0, 0, 0, 0), TGT_VICTIM, (0, 0, 0, 0),
             'In combat - Frost Breath (frontal cone)'),
            (EV_UPDATE_IC, (20000, 25000, 22000, 28000, 0, 0), 0, ACT_CAST, (22645, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0),
             'In combat - Frost Nova (roots everyone within 10 yd)'),
            (EV_HEALTH_PCT, (0, 50, 0, 0, 0, 0), NOT_REPEATABLE, ACT_TALK, (2, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0),
             'At 50% - yell'),
        ] + [
            (EV_HEALTH_PCT, (0, 50, 0, 0, 0, 0), NOT_REPEATABLE, ACT_SUMMON,
             (190111, TIMED_DESPAWN_OUT_OF_COMBAT, 10000, 0, 0, 0), TGT_SELF, (0, 0, 0, 0),
             f'At 50% - summon Frostbound Shard {n}', (dx, dy))
            for n, (dx, dy) in enumerate([(8, 0), (-8, 0), (0, 8), (0, -8)], 1)
        ] + [
            (EV_HEALTH_PCT, (0, 20, 0, 0, 0, 0), NOT_REPEATABLE, ACT_TALK, (3, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0),
             'At 20% - enrage emote'),
            (EV_HEALTH_PCT, (0, 20, 0, 0, 0, 0), 0, ACT_CAST, (8599, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0),
             'Below 20% - Enrage (recast every 2 minutes)', None, (120000, 120000)),
            (EV_DEATH, (0, 0, 0, 0, 0, 0), 0, ACT_TALK, (4, 0, 0, 0, 0, 0), TGT_SELF, (0, 0, 0, 0), 'On death - announce'),
        ],
        # one guaranteed item from the pool, plus extra independent rolls (item, chance %)
        loot_groups=[[911000, 911001, 911002, 911003, 911004, 911005]],
        loot_extra=[(13086, 3)],  # Reins of the Winterspring Frostsaber
        adds=[
            dict(entry=190111, name='Frostbound Shard', display=21910, scale=0.8, level=60, faction=14,
                 creature_type=4, health_mod=3.0, damage_mod=2.0,
                 script=[
                     # Outside dungeons this action engages every player within target_param3 yards; it needs a
                     # target that reads that range (the boss, by entry), since unused params on SELF are rejected.
                     (EV_JUST_SUMMONED, (0, 0, 0, 0, 0, 0), 0, ACT_ZONE_COMBAT, (0, 0, 0, 0, 0, 0),
                      TGT_CREATURE_RANGE, (190110, 0, 60, 0), 'On summon - attack every player within 60 yd'),
                     (EV_UPDATE_IC, (3000, 6000, 8000, 12000, 0, 0), 0, ACT_CAST, (15499, 0, 0, 0, 0, 0), TGT_VICTIM,
                      (0, 0, 0, 0), 'In combat - Frost Shock'),
                 ]),
        ],
    ),
]

TEMPLATE_COLS = ['entry', 'name', 'subname', 'minlevel', 'maxlevel', 'exp', 'faction', 'npcflag', 'speed_walk',
                 'speed_run', 'detection_range', 'rank', 'dmgschool', 'DamageModifier', 'BaseAttackTime',
                 'RangeAttackTime', 'unit_class', 'unit_flags', 'unit_flags2', 'type', 'type_flags', 'lootid',
                 'mingold', 'maxgold', 'AIName', 'MovementType', 'HealthModifier', 'ManaModifier',
                 'ArmorModifier', 'ExperienceModifier', 'RegenHealth', 'CreatureImmunitiesId', 'flags_extra',
                 'ScriptName']


def lit(v):
    if v is None:
        return 'NULL'
    if isinstance(v, str):
        return sql_str(v)
    return str(v)


def template_row(c, boss):
    return [c['entry'], c['name'], c.get('subname'), c['level'], c['level'], 0, c['faction'], 0, 1, 1.14286,
            20, 3 if boss else 1, 0, c['damage_mod'], 2000, 2000, 1, 0, 2048, c['creature_type'],
            c.get('type_flags', 0), c['entry'] if boss else 0, *(c['gold'] if boss else (0, 0)), 'SmartAI', 0,
            c['health_mod'], 1, c.get('armor_mod', 1), 1, 1, c.get('immunities', 0), 0, '']


def script_rows(entry, script):
    rows = []
    for n, s in enumerate(script):
        ev, ep, flags, act, ap, tgt, tp, comment = s[:8]
        offset = s[8] if len(s) > 8 and s[8] else (0, 0)
        repeat = s[9] if len(s) > 9 else None
        ep = list(ep)
        if repeat:  # health events: repeat min/max (ms) while inside the range
            ep[2], ep[3] = repeat
        rows.append([entry, 0, n, 0, ev, 0, 100, flags, *ep, act, *ap, tgt, *tp,
                     float(offset[0]), float(offset[1]), 0.0, 0.0, comment])
    return rows


def values(rows):
    return ',\n'.join('(' + ', '.join(lit(v) for v in r) + ')' for r in rows) + ';'


def boss_sql(b):
    creatures = [b] + b['adds']
    ids = ', '.join(str(c['entry']) for c in creatures)
    out = [f"-- {b['name']} (map {b['map']}: {b['x']}, {b['y']}, {b['z']})",
           f'DELETE FROM `creature_template` WHERE `entry` IN ({ids});',
           'INSERT INTO `creature_template` (' + ', '.join(f'`{c}`' for c in TEMPLATE_COLS) + ') VALUES',
           values([template_row(b, True)] + [template_row(a, False) for a in b['adds']]),
           f'DELETE FROM `creature_template_model` WHERE `CreatureID` IN ({ids});',
           'INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, '
           '`Probability`, `VerifiedBuild`) VALUES',
           values([[c['entry'], 0, c['display'], c.get('scale', 1.0), 1, 0] for c in creatures]),
           '',
           f"DELETE FROM `creature` WHERE `guid` = {b['guid']} OR `id` IN ({ids});",
           'INSERT INTO `creature` (`guid`, `id`, `map`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, '
           '`position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `MovementType`, `Comment`) VALUES',
           values([[b['guid'], b['entry'], b['map'], 1, 1, b['x'], b['y'], b['z'], b['o'], b['respawn'], 0, 0,
                    'mod-unbound world boss']]),
           '',
           f'DELETE FROM `creature_text` WHERE `CreatureID` IN ({ids});',
           'INSERT INTO `creature_text` (`CreatureID`, `GroupID`, `ID`, `Text`, `Type`, `Language`, `Probability`, '
           '`Emote`, `Duration`, `Sound`, `BroadcastTextId`, `TextRange`, `comment`) VALUES',
           values([[b['entry'], g, 0, text, typ, 0, 100, 0, 0, 0, 0, rng, b['name']]
                   for g, typ, rng, text in b['texts']]),
           '',
           f'DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN ({ids});',
           'INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, '
           '`event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, '
           '`event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, '
           '`action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, '
           '`target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, '
           '`comment`) VALUES',
           values(script_rows(b['entry'], b['script']) +
                  [r for a in b['adds'] for r in script_rows(a['entry'], a['script'])]),
           '',
           f"DELETE FROM `creature_loot_template` WHERE `Entry` = {b['entry']};",
           'INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, '
           '`LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES',
           values([[b['entry'], item, 0, 0, 0, 1, g, 1, 1, b['name']]
                   for g, group in enumerate(b['loot_groups'], 1) for item in group] +
                  [[b['entry'], item, 0, chance, 0, 1, 0, 1, 1, b['name'] + ' (rare)']
                   for item, chance in b['loot_extra']]),
           '']
    return '\n'.join(out)


def item_dbc_rows():
    """Item.dbc / item_dbc rows (see heroic_loot.item_dbc_rows)."""
    return [(i['id'], i['cls'], i['sub'], -1, i['mat'], i['display'], i['inv'], i['sheath']) for i in WORLD_BOSS_ITEMS]


def check():
    ids = [i['id'] for i in WORLD_BOSS_ITEMS]
    assert len(ids) == len(set(ids)) and all(911000 <= i <= 911999 for i in ids), 'items use 911000-911999'
    for b in WORLD_BOSSES:
        for c in [b] + b['adds']:
            assert 190110 <= c['entry'] <= 190199, 'world boss creatures use 190110-190199'
        assert 9190110 <= b['guid'] <= 9190199
        for group in b['loot_groups']:
            for item in group:
                assert item in ids, f'{item} is not in WORLD_BOSS_ITEMS'
        talk_groups = {s[4][0] for s in b['script'] if s[3] == ACT_TALK}
        assert talk_groups <= {t[0] for t in b['texts']}, 'script talks a text group that is not defined'


def main():
    check()
    item_ids = ', '.join(str(i['id']) for i in WORLD_BOSS_ITEMS)
    parts = ['-- Generated by tools/world_bosses.py - edit the tables there, not this file.',
             '-- Re-running deletes and re-inserts exactly these rows (see the reversibility note there).',
             '',
             f'DELETE FROM `item_template` WHERE `entry` IN ({item_ids});',
             '']
    parts += [item_sql(i).replace('unbound_hl_tmp', 'unbound_wb_tmp') + '\n' for i in WORLD_BOSS_ITEMS]
    parts += ['DROP TEMPORARY TABLE IF EXISTS `unbound_wb_tmp`;', '']
    parts += [boss_sql(b) for b in WORLD_BOSSES]
    path = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_world_bosses.sql')
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(parts) + '\n')
    print('wrote', path, f'({len(WORLD_BOSSES)} world bosses, {len(WORLD_BOSS_ITEMS)} items)')


if __name__ == '__main__':
    main()
