"""
Tag every gear item with the expansion it comes from, for gear infusion (src/unbound_attunement.cpp).

An item's expansion is the earliest expansion whose content can give it (0 = classic, 1 = The Burning
Crusade, 2 = Wrath of the Lich King). Infusion only accepts items from released expansions
(Unbound.ExpansionUnlocked), so locked expansions' items never count, however a player got them.

Sources, worked out from the world database and the server's DBC files:
  - creature loot, skinning and pickpocketing (including reference loot, nested): the map the creature is
    spawned on (its expansion in Map.dbc); also each creature's difficulty versions (heroic copies).
    Creatures that are never spawned (summoned by scripts) use their stat expansion
    (creature_template.exp). Classic Naxxramas' creatures and chest are classic although map 533 is Wrath.
  - gameobject loot (chests, fishing holes): the map the gameobject is spawned on
  - containers (item_loot_template): the container item's expansion
  - disenchanting (disenchant_loot_template): the disenchanted item's expansion (e.g. Dream Dust, a
    reagent of classic crafted gear)
  - vendors: the map the vendor is spawned on
  - quest rewards: the maps of the quest's starters and enders (follow-up quests often have no starter)
  - crafting (profession recipes): the latest expansion among its reagents (all of them are needed);
    Jewelcrafting recipes are at least The Burning Crusade and Inscription recipes at least Wrath
  - items made by using another item (e.g. Sulfuras from the Eye of Sulfuras): the later of that item's
    expansion and its reagents'
The minimum over all sources wins, repeated until nothing changes (a crafted item depends on its reagents,
a container on its own sources, and so on). Items with no known source get no row and never count.

Shared world-drop tables mix expansions: on 3.3.5, some classic level 58-62 creatures can drop early Burning
Crusade greens (e.g. the Laughing Skull set, item level 90). So greens and blues are also held to their
expansion's item level range (ITEM_LEVEL_LIMITS): classic greens and blues stop at item level 74 and TBC's
start at 80; TBC's stop at about 119 and Wrath's start at 130. An item above its expansion's limit moves to
the next expansion. Epics need no limit: none from a later expansion requires a level the earlier one has.

Custom items (entries 900000-999999, this module's) are classic.

Writes data/sql/db-world/unbound_item_expansion.sql. Run it again (with the worldserver's database
running) when the world database's loot, vendors or quests change; the result is committed, so others
don't need to run it:

  python tools/item_expansions.py [--mysql <mysql.exe>] [--dbc <server dbc folder>]
"""
import argparse
import os
import struct
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
ACORE = os.path.dirname(os.path.dirname(MODULE))
ROOT = os.path.dirname(ACORE)

UNKNOWN = 99
CUSTOM_ITEMS = range(900000, 1000000)

# Profession skill lines whose recipes can make gear; the minimum expansion of a recipe in that profession.
PROFESSIONS = {164: 0, 165: 0, 197: 0, 202: 0, 171: 0, 333: 0, 186: 0, 185: 0, 129: 0,
               755: 1,   # Jewelcrafting (The Burning Crusade)
               773: 2}   # Inscription (Wrath of the Lich King)

# Highest item level a green or blue (Quality 2/3) of each expansion has; above it, the next expansion.
ITEM_LEVEL_LIMITS = {0: 79, 1: 125}

# Spell.dbc columns (3.3.5a)
SPELL_REAGENTS, SPELL_REAGENT_COUNTS, SPELL_EFFECTS, SPELL_EFFECT_ITEMS = 52, 60, 71, 107
SPELL_EFFECT_CREATE_ITEM = 24
MAP_EXPANSION = 63  # Map.dbc

# Classic Naxxramas (src/naxx40, data/sql/db-world/unbound_naxx40*.sql) is the 40-player difficulty of the Wrath
# map 533: its creatures (entries 351000-351099, own loot tables) and the Four Horsemen chest count as classic.
NAXX40_CREATURES = (351000, 351100)
NAXX40_GAMEOBJECTS = (361000,)

# Gear: weapons and armour (including rings, necks, trinkets, shields), not shirts, tabards, bags, ammo.
GEAR_SQL = ("SELECT entry, Quality, ItemLevel FROM item_template WHERE class IN (2, 4) AND Quality >= 2 "
            "AND InventoryType NOT IN (0, 4, 18, 19, 24, 27)")


def load_dbc(path):
    data = open(path, 'rb').read()
    _, count, fields, size, _ = struct.unpack('<4s4I', data[:20])
    rows = {}
    for i in range(count):
        row = data[20 + i * size:20 + (i + 1) * size]
        rows[struct.unpack_from('<I', row, 0)[0]] = row
    return rows


def col(row, index):
    return struct.unpack_from('<I', row, index * 4)[0]


class Database:
    def __init__(self, mysql, user, password, host, port, name):
        self.args = [mysql, f'--user={user}', f'--password={password}', f'--host={host}', f'--port={port}',
                     '--batch', '--skip-column-names', name]

    def query(self, sql, attempts=3):
        # Every row must be the same number of whole numbers; a garbled read (seen rarely) is retried.
        for attempt in range(attempts):
            out = subprocess.run(self.args + ['-e', sql], capture_output=True, text=True, check=True).stdout
            try:
                rows = [tuple(int(v) for v in line.split('\t')) for line in out.splitlines() if line]
            except ValueError:
                continue
            if len({len(r) for r in rows}) <= 1:
                return rows
        raise RuntimeError(f'could not read a clean result after {attempts} attempts: {sql}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--mysql', default=os.path.join(ROOT, 'deps', 'mysql-8.4.11-winx64', 'bin', 'mysql.exe'))
    ap.add_argument('--dbc', default=os.path.join(ROOT, 'data', 'dbc'), help='server DBC folder')
    ap.add_argument('--user', default='acore')
    ap.add_argument('--password', default='acore')
    ap.add_argument('--host', default='127.0.0.1')
    ap.add_argument('--port', default='3306')
    ap.add_argument('--database', default='acore_world')
    ap.add_argument('--check', type=int, nargs='+', metavar='ITEM',
                    help='only print these items\' expansions (any item, e.g. a reagent), write nothing')
    args = ap.parse_args()
    db = Database(args.mysql, args.user, args.password, args.host, args.port, args.database)

    map_exp = {m: col(r, MAP_EXPANSION) for m, r in load_dbc(os.path.join(args.dbc, 'Map.dbc')).items()}

    def lower(table, key, value):
        if value < table.get(key, UNKNOWN):
            table[key] = value
            return True
        return False

    # creatures: spawn maps, else stat expansion; difficulty versions inherit
    creature_exp = {}
    for cid, m in db.query('SELECT id, map FROM creature'):
        lower(creature_exp, cid, map_exp.get(m, UNKNOWN))
    # Classic Naxxramas (src/naxx40) shares the Wrath map 533; its level 60 creatures are classic
    for cid in range(*NAXX40_CREATURES):
        if cid in creature_exp:
            creature_exp[cid] = 0
    templates = db.query('SELECT entry, lootid, skinloot, pickpocketloot, exp, difficulty_entry_1, difficulty_entry_2, '
                         'difficulty_entry_3 FROM creature_template')
    for entry, _, _, _, exp, *_ in templates:
        if entry not in creature_exp:
            creature_exp[entry] = exp
    for entry, _, _, _, _, *diffs in templates:
        for d in diffs:
            if d:
                lower(creature_exp, d, creature_exp.get(entry, UNKNOWN))
    creature_loot_exp, skinning_exp, pickpocket_exp = {}, {}, {}
    for entry, lootid, skinloot, pickpocketloot, *_ in templates:
        for table, key in ((creature_loot_exp, lootid), (skinning_exp, skinloot), (pickpocket_exp, pickpocketloot)):
            if key:
                lower(table, key, creature_exp.get(entry, UNKNOWN))

    # gameobjects: spawn maps; chests (type 3) and fishing holes (type 25) loot from Data1
    go_exp = {}
    for gid, m in db.query('SELECT id, map FROM gameobject'):
        lower(go_exp, gid, map_exp.get(m, UNKNOWN))
    for gid in NAXX40_GAMEOBJECTS:  # summoned by script, so never spawned
        go_exp[gid] = 0
    go_loot_exp = {}
    for entry, lootid in db.query('SELECT entry, Data1 FROM gameobject_template WHERE type IN (3, 25) AND Data1 > 0'):
        lower(go_loot_exp, lootid, go_exp.get(entry, UNKNOWN))

    loot = {name: db.query(f'SELECT Entry, Item, Reference FROM {name}') for name in
            ('creature_loot_template', 'gameobject_loot_template', 'item_loot_template', 'reference_loot_template',
             'disenchant_loot_template', 'skinning_loot_template', 'pickpocketing_loot_template')}
    # disenchant loot is keyed by the items' DisenchantID: one disenchant table serves many items
    disenchant_users = {}
    for item, de in db.query('SELECT entry, DisenchantID FROM item_template WHERE DisenchantID > 0'):
        disenchant_users.setdefault(de, []).append(item)
    disenchant_exp = {}
    vendors = db.query('SELECT entry, item FROM npc_vendor WHERE item > 0')
    quest_exp = {}
    for table, owner_exp in (('creature_queststarter', creature_exp), ('gameobject_queststarter', go_exp),
                             ('creature_questender', creature_exp), ('gameobject_questender', go_exp)):
        for owner, quest in db.query(f'SELECT id, quest FROM {table}'):
            lower(quest_exp, quest, owner_exp.get(owner, UNKNOWN))
    quest_items = db.query('SELECT ID, RewardItem1, RewardItem2, RewardItem3, RewardItem4, RewardChoiceItemID1, '
                           'RewardChoiceItemID2, RewardChoiceItemID3, RewardChoiceItemID4, RewardChoiceItemID5, '
                           'RewardChoiceItemID6 FROM quest_template')

    # crafting recipes: (minimum expansion, created item, reagents); an item used to cast the spell counts
    # as a reagent
    spells = load_dbc(os.path.join(args.dbc, 'Spell.dbc'))
    recipes = []

    def add_recipe(floor, spell_id, extra_reagents=()):
        spell = spells.get(spell_id)
        if not spell:
            return
        reagents = [col(spell, SPELL_REAGENTS + i) for i in range(8) if col(spell, SPELL_REAGENTS + i)]
        reagents += list(extra_reagents)
        for e in range(3):
            if col(spell, SPELL_EFFECTS + e) == SPELL_EFFECT_CREATE_ITEM and col(spell, SPELL_EFFECT_ITEMS + e):
                recipes.append((floor, col(spell, SPELL_EFFECT_ITEMS + e), reagents))

    for row in load_dbc(os.path.join(args.dbc, 'SkillLineAbility.dbc')).values():
        if col(row, 1) in PROFESSIONS:
            add_recipe(PROFESSIONS[col(row, 1)], col(row, 2))
    for item, *spell_pairs in db.query('SELECT entry, spellid_1, spelltrigger_1, spellid_2, spelltrigger_2, spellid_3, '
                                       'spelltrigger_3, spellid_4, spelltrigger_4, spellid_5, spelltrigger_5 '
                                       'FROM item_template WHERE spellid_1 > 0 OR spellid_2 > 0'):
        for spell_id, trigger in zip(spell_pairs[0::2], spell_pairs[1::2]):
            if spell_id > 0 and trigger == 0:  # on use
                add_recipe(0, spell_id, (item,))

    # fixpoint: an item's expansion is the minimum over all its sources
    item_exp = {i: 0 for i in (r[0] for r in db.query('SELECT entry FROM item_template WHERE entry BETWEEN 900000 AND 999999'))}
    ref_exp = {}
    for v, item in vendors:
        lower(item_exp, item, creature_exp.get(v, UNKNOWN))
    for q, *items in quest_items:
        for item in items:
            if item:
                lower(item_exp, item, quest_exp.get(q, UNKNOWN))
    changed = True
    rounds = 0
    while changed:
        changed = False
        rounds += 1
        for de, users in disenchant_users.items():
            for item in users:
                if item in item_exp:
                    changed |= lower(disenchant_exp, de, item_exp[item])
        for name, owner_exp in (('creature_loot_template', creature_loot_exp), ('gameobject_loot_template', go_loot_exp),
                                ('item_loot_template', item_exp), ('reference_loot_template', ref_exp),
                                ('disenchant_loot_template', disenchant_exp), ('skinning_loot_template', skinning_exp),
                                ('pickpocketing_loot_template', pickpocket_exp)):
            for entry, item, reference in loot[name]:
                exp = owner_exp.get(entry, UNKNOWN)
                if exp == UNKNOWN:
                    continue
                if reference:
                    changed |= lower(ref_exp, reference, exp)
                elif item:
                    changed |= lower(item_exp, item, exp)
        for floor, item, reagents in recipes:
            exp = max([floor] + [item_exp.get(r, UNKNOWN) for r in reagents])
            if exp != UNKNOWN:
                changed |= lower(item_exp, item, exp)

    if args.check:
        names = {'0': 'classic', '1': 'The Burning Crusade', '2': 'Wrath of the Lich King'}
        for item in args.check:
            exp = item_exp.get(item, UNKNOWN)
            print(item, names.get(str(exp), 'no known source'))
        return

    gear = {}
    for item, quality, item_level in db.query(GEAR_SQL):
        exp = item_exp.get(item, UNKNOWN)
        if exp != UNKNOWN and quality in (2, 3) and item not in CUSTOM_ITEMS:
            while exp in ITEM_LEVEL_LIMITS and item_level > ITEM_LEVEL_LIMITS[exp]:
                exp += 1
        gear[item] = exp
    tagged = sorted((i, e) for i, e in gear.items() if e != UNKNOWN)
    counts = {e: sum(1 for _, x in tagged if x == e) for e in (0, 1, 2)}

    path = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_item_expansion.sql')
    lines = ['-- Generated by tools/item_expansions.py - run it again instead of editing this file.',
             '-- The expansion each gear item comes from (0 classic, 1 The Burning Crusade, 2 Wrath of the Lich King),',
             '-- for gear infusion: only items of released expansions (Unbound.ExpansionUnlocked) count.',
             'CREATE TABLE IF NOT EXISTS `unbound_item_expansion` (',
             "  `item` INT UNSIGNED NOT NULL COMMENT 'item_template.entry',",
             "  `expansion` TINYINT UNSIGNED NOT NULL COMMENT '0 classic, 1 TBC, 2 WotLK',",
             '  PRIMARY KEY (`item`)',
             ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='mod-unbound: gear item expansions';",
             'DELETE FROM `unbound_item_expansion`;']
    for start in range(0, len(tagged), 1000):
        chunk = tagged[start:start + 1000]
        lines.append('INSERT INTO `unbound_item_expansion` (`item`, `expansion`) VALUES')
        lines.append(',\n'.join(f'({i},{e})' for i, e in chunk) + ';')
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('wrote', path, f'({len(tagged)} of {len(gear)} gear items tagged: {counts[0]} classic, {counts[1]} TBC, '
          f'{counts[2]} WotLK; {len(gear) - len(tagged)} with no known source; {rounds} rounds)')


if __name__ == '__main__':
    main()
