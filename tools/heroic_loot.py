"""
Heroic loot for the classic heroic dungeons (tools/classic_heroics.py).

Each heroic boss gets its own loot table (lootid = its heroic entry) instead of sharing the normal
boss's level 15-25 loot. Everything is defined here once and generated into:

  server: data/sql/db-world/unbound_heroic_loot.sql   (item_template rows + heroic creature_loot_template rows)
          data/sql/db-world/unbound_classic_heroics.sql (heroic bosses' lootid and gold, via lootid_sql())
          data/sql/db-world/unbound_custom_dbc.sql     (item_dbc and itemset_dbc rows, via tools/custom_dbc.py)
  client: patch-Z.MPQ                                   (Item.dbc and ItemSet.dbc rows, via tools/custom_dbc.py)

Run after changing this file:

  python tools/heroic_loot.py
  python tools/classic_heroics.py
  python tools/custom_dbc.py

Reserved IDs: items 910100-910999, item sets 950-999.

Reversibility: the generated SQL deletes and re-inserts exactly the items, sets and loot rows defined
here, so switching loot designs is a change to this file plus a regenerate. Never remove an item from
HEROIC_ITEMS once it has dropped on a server: take it out of LOOT instead (players may still own it,
and an item with no definition disappears from their bags). Set 'retired': True to say so.
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)

HEROIC_ENTRY_OFFSET = 1000000  # must match tools/classic_heroics.py

# item_template stat types
AGI, STR, INT, SPI, STA = 3, 4, 5, 6, 7
DEFENSE, DODGE, HIT, CRIT, AP, MP5, SPELL_POWER, BLOCK_VALUE = 12, 13, 31, 32, 38, 43, 45, 48

# Item.dbc columns
CLS_WEAPON, CLS_ARMOR = 2, 4
# weapon subclasses
MACE_1H, MACE_2H, POLEARM, SWORD_1H, STAFF, DAGGER, WAND = 4, 5, 6, 7, 10, 15, 19
# armor subclasses
MISC, CLOTH, LEATHER, MAIL, PLATE, SHIELD = 0, 1, 2, 3, 4, 6
# inventory types
SHOULDERS, CHEST, WAIST, LEGS, HANDS, FINGER, ONE_HAND, SHIELD_SLOT, BACK, TWO_HAND, RANGED_RIGHT = \
    3, 5, 6, 7, 10, 11, 13, 14, 16, 17, 26

# ---------------------------------------------------------------- item sets
ITEM_SETS = [
    {
        'ID': 950,
        'name': 'Blackened Defias Garb',
        'items': [910112, 910115, 910118, 910119],
        'bonuses': [(2, 9102),   # (2) +12 Agility          ("Increased Agility 12")
                    (4, 9336)],  # (4) +30 Attack Power     ("Attack Power 30")
    },
]

# ---------------------------------------------------------------- items
# base = an existing item copied for everything not set here (sounds, durability, flags it doesn't clear).
# Weapons: 'dps' + 'delay' (ms) -> damage range. Armor: 'armor'. Stats are (type, value) pairs.
# Look columns (cls, sub, inv, mat, sheath, display) also feed Item.dbc for the client.
HEROIC_ITEMS = [
    # --- Deadmines (heroic) --------------------------------------------------------------------
    # Rhahk'Zor
    dict(id=910100, base=13142, name="Foreman's Plate Girdle", ilvl=61, cls=CLS_ARMOR, sub=PLATE, inv=WAIST,
         mat=6, sheath=0, display=23628, armor=358, stats=[(STR, 12), (STA, 18), (DEFENSE, 10)]),
    dict(id=910101, base=12589, name="Mine Overseer's Cord", ilvl=61, cls=CLS_ARMOR, sub=CLOTH, inv=WAIST,
         mat=7, sheath=0, display=21796, armor=48, stats=[(INT, 13), (SPI, 8), (STA, 9), (SPELL_POWER, 18)]),
    dict(id=910102, base=5187, name="Rhahk'Zor's Hammer", ilvl=61, cls=CLS_WEAPON, sub=MACE_2H, inv=TWO_HAND,
         mat=2, sheath=1, display=8600, dps=52.5, delay=3200, stats=[(STR, 24), (STA, 16), (CRIT, 14)]),
    # Sneed's Shredder (Sneed himself only appears when the Shredder dies and has no heroic copy)
    dict(id=910103, base=15648, name="Shredder Plating Shield", ilvl=61, cls=CLS_ARMOR, sub=SHIELD,
         inv=SHIELD_SLOT, mat=1, sheath=4, display=27179, armor=2090, block=38,
         stats=[(STA, 16), (DEFENSE, 9), (BLOCK_VALUE, 14)]),
    dict(id=910104, base=5195, name="Gold-flecked Gloves", ilvl=61, cls=CLS_ARMOR, sub=CLOTH, inv=HANDS,
         mat=7, sheath=0, display=16966, armor=54, stats=[(INT, 12), (STA, 8), (SPELL_POWER, 18), (MP5, 4)]),
    dict(id=910105, base=2169, name="Buzzer Blade", ilvl=61, cls=CLS_WEAPON, sub=DAGGER, inv=ONE_HAND,
         mat=1, sheath=3, display=20347, dps=40.4, delay=1500, stats=[(AGI, 9), (STA, 8), (CRIT, 14)]),
    # Gilnid
    dict(id=910106, base=5199, name="Smelting Pants", ilvl=62, cls=CLS_ARMOR, sub=LEATHER, inv=LEGS,
         mat=8, sheath=0, display=1978, armor=152, stats=[(STA, 22), (AGI, 15), (DODGE, 12)]),
    dict(id=910107, base=1156, name="Lavishly Jeweled Ring", ilvl=62, cls=CLS_ARMOR, sub=MISC, inv=FINGER,
         mat=1, sheath=0, display=9839, stats=[(INT, 9), (STA, 6), (SPELL_POWER, 15), (HIT, 8)]),
    dict(id=910108, base=10797, name="Molten Edge", ilvl=62, cls=CLS_WEAPON, sub=SWORD_1H, inv=ONE_HAND,
         mat=1, sheath=3, display=20030, dps=40.9, delay=2400, stats=[(STR, 10), (STA, 9), (CRIT, 14)]),
    # Mr. Smite
    dict(id=910109, base=13166, name="Smite's Bulwark", ilvl=62, cls=CLS_ARMOR, sub=PLATE, inv=SHOULDERS,
         mat=6, sheath=0, display=23704, armor=490, stats=[(STR, 12), (STA, 20), (DEFENSE, 12)]),
    dict(id=910110, base=5202, name="Captain's Vestments", ilvl=62, cls=CLS_ARMOR, sub=CLOTH, inv=CHEST,
         mat=7, sheath=0, display=12803, armor=88, stats=[(INT, 18), (SPI, 14), (STA, 13), (SPELL_POWER, 24)]),
    dict(id=910111, base=7230, name="Smite's Mighty Hammer", ilvl=62, cls=CLS_WEAPON, sub=MACE_2H, inv=TWO_HAND,
         mat=2, sheath=1, display=19610, dps=53.2, delay=3500, stats=[(STR, 26), (AGI, 9), (STA, 14)]),
    # Captain Greenskin
    dict(id=910112, base=10403, name="Blackened Defias Belt", ilvl=62, cls=CLS_ARMOR, sub=LEATHER, inv=WAIST,
         mat=8, sheath=0, display=14389, armor=99, set=950, stats=[(AGI, 14), (STA, 11), (AP, 20)]),
    dict(id=910113, base=5201, name="Emberstone Staff", ilvl=62, cls=CLS_WEAPON, sub=STAFF, inv=TWO_HAND,
         mat=2, sheath=2, display=20340, dps=52.6, delay=3000,
         stats=[(INT, 20), (SPI, 12), (STA, 14), (SPELL_POWER, 30)]),
    dict(id=910114, base=5200, name="Impaling Harpoon", ilvl=62, cls=CLS_WEAPON, sub=POLEARM, inv=TWO_HAND,
         mat=1, sheath=2, display=5949, dps=52.0, delay=2400, stats=[(AGI, 22), (STA, 14), (HIT, 10)]),
    # Cookie
    dict(id=910115, base=10401, name="Blackened Defias Gloves", ilvl=62, cls=CLS_ARMOR, sub=LEATHER, inv=HANDS,
         mat=8, sheath=0, display=27946, armor=110, set=950, stats=[(AGI, 13), (STA, 10), (CRIT, 14)]),
    dict(id=910116, base=5198, name="Cookie's Stirring Rod", ilvl=62, cls=CLS_WEAPON, sub=WAND,
         inv=RANGED_RIGHT, mat=2, sheath=0, display=21011, dps=62.0, delay=1300,
         stats=[(INT, 6), (STA, 4), (SPELL_POWER, 12)]),
    dict(id=910117, base=5197, name="Cookie's Tenderizer", ilvl=62, cls=CLS_WEAPON, sub=MACE_1H, inv=ONE_HAND,
         mat=2, sheath=7, display=20953, dps=40.6, delay=2800, stats=[(STR, 10), (STA, 9), (CRIT, 14)]),
    # Edwin VanCleef
    dict(id=910118, base=10399, name="Blackened Defias Armor", ilvl=63, cls=CLS_ARMOR, sub=LEATHER, inv=CHEST,
         mat=8, sheath=0, display=9123, armor=176, set=950, stats=[(AGI, 20), (STA, 18), (CRIT, 14)]),
    dict(id=910119, base=10400, name="Blackened Defias Leggings", ilvl=63, cls=CLS_ARMOR, sub=LEATHER, inv=LEGS,
         mat=8, sheath=0, display=27947, armor=154, set=950, stats=[(AGI, 19), (STA, 16), (HIT, 10)]),
    dict(id=910120, base=5193, name="Cape of the Brotherhood", ilvl=63, cls=CLS_ARMOR, sub=CLOTH, inv=BACK,
         mat=7, sheath=0, display=22998, armor=45, stats=[(AGI, 10), (STA, 9), (AP, 16)]),
    dict(id=910121, base=5191, name="Cruel Barb", ilvl=63, cls=CLS_WEAPON, sub=SWORD_1H, inv=ONE_HAND,
         mat=1, sheath=3, display=7311, dps=41.5, delay=2800, stats=[(STR, 12), (STA, 9), (CRIT, 14)]),
]

# ---------------------------------------------------------------- loot
# Keyed by map id, then by the NORMAL boss entry (its heroic copy is entry + HEROIC_ENTRY_OFFSET).
#   groups: each list is one loot group with equal chances; exactly one item from each group drops.
#   extra:  (item, chance %) rolled independently.
#   gold:   (min, max) in copper.
LOOT = {
    36: {  # Deadmines
        644:  dict(name="Rhahk'Zor", groups=[[910100, 910101, 910102]], gold=(2000, 4000)),
        642:  dict(name="Sneed's Shredder", groups=[[910103, 910104, 910105]], gold=(2000, 4000)),
        1763: dict(name='Gilnid', groups=[[910106, 910107, 910108]], gold=(2000, 4000)),
        646:  dict(name='Mr. Smite', groups=[[910109, 910110, 910111]], gold=(2000, 4000)),
        647:  dict(name='Captain Greenskin', groups=[[910112, 910113, 910114]],
                   extra=[(8494, 1)],  # Parrot Cage (Hyacinth Macaw) companion
                   gold=(2000, 4000)),
        645:  dict(name='Cookie', groups=[[910115, 910116, 910117]], gold=(2000, 4000)),
        639:  dict(name='Edwin VanCleef', groups=[[910118, 910119], [910120, 910121]], gold=(5000, 10000)),
    },
}


def heroic_entry(entry):
    return entry + HEROIC_ENTRY_OFFSET


def sql_str(s):
    return "'" + s.replace('\\', '\\\\').replace("'", "''") + "'"


def lootid_sql(map_id):
    """SQL for tools/classic_heroics.py: point this map's heroic bosses at their own loot tables."""
    bosses = LOOT.get(map_id, {})
    lines = []
    for entry, boss in bosses.items():
        gmin, gmax = boss.get('gold', (0, 0))
        lines.append(f"UPDATE `creature_template` SET `lootid` = {heroic_entry(entry)}, `mingold` = {gmin}, "
                     f"`maxgold` = {gmax} WHERE `entry` = {heroic_entry(entry)};  -- {boss['name']} (Heroic)")
    if lines:
        lines.insert(0, '-- heroic bosses use their own loot tables (tools/heroic_loot.py)')
    return '\n'.join(lines)


def item_dbc_rows():
    """Item.dbc / item_dbc rows: ID, Class, SubClass, SoundOverrideSubclass, Material, DisplayInfoID, InventoryType, SheathType."""
    return [(i['id'], i['cls'], i['sub'], -1, i['mat'], i['display'], i['inv'], i['sheath']) for i in HEROIC_ITEMS]


def item_set_rows():
    """ItemSet.dbc / itemset_dbc rows in column order (53 fields)."""
    rows = []
    for s in ITEM_SETS:
        items = (s['items'] + [0] * 17)[:17]
        spells = ([sp for _, sp in s['bonuses']] + [0] * 8)[:8]
        thresholds = ([n for n, _ in s['bonuses']] + [0] * 8)[:8]
        rows.append([s['ID'], s['name']] + [''] * 15 + [16712190] + items + spells + thresholds + [0, 0])
    return rows


def item_sql(item):
    stats = (item['stats'] + [(0, 0)] * 10)[:10]
    sets = [f"`stat_type{k}` = {t}, `stat_value{k}` = {v}" for k, (t, v) in enumerate(stats, 1)]
    spells = ', '.join(f"`spellid_{k}` = 0, `spelltrigger_{k}` = 0, `spellcharges_{k}` = 0, `spellppmRate_{k}` = 0, "
                       f"`spellcooldown_{k}` = -1, `spellcategory_{k}` = 0, `spellcategorycooldown_{k}` = -1"
                       for k in range(1, 6))
    if 'dps' in item:
        avg = item['dps'] * item['delay'] / 1000
        dmin, dmax = round(avg * 0.78), round(avg * 1.22)
        weapon = f"`dmg_min1` = {dmin}, `dmg_max1` = {dmax}, `delay` = {item['delay']}"
        sell = 45000 if item['inv'] == TWO_HAND else 30000
    else:
        weapon = '`dmg_min1` = 0, `dmg_max1` = 0'
        sell = 25000
    sell = item.get('sell', sell)
    return '\n'.join([
        f"-- {item['name']} ({item.get('label', 'heroic')}, item level {item['ilvl']})",
        'DROP TEMPORARY TABLE IF EXISTS `unbound_hl_tmp`;',
        f"CREATE TEMPORARY TABLE `unbound_hl_tmp` SELECT * FROM `item_template` WHERE `entry` = {item['base']};",
        f"UPDATE `unbound_hl_tmp` SET `entry` = {item['id']}, `name` = {sql_str(item['name'])}, "
        f"`description` = {sql_str(item.get('desc', 'Heroic'))}, `class` = {item['cls']}, `subclass` = {item['sub']}, "
        f"`displayid` = {item['display']}, `InventoryType` = {item['inv']}, `Material` = {item['mat']}, "
        f"`sheath` = {item['sheath']},",
        f"    `Quality` = {item.get('quality', 3)}, `ItemLevel` = {item['ilvl']}, `RequiredLevel` = 60, `bonding` = 1, `Flags` = 0, "
        "`FlagsExtra` = 0, `AllowableClass` = -1, `AllowableRace` = -1, `maxcount` = 0, `stackable` = 1,",
        f"    `BuyPrice` = {sell * 4}, `SellPrice` = {sell}, `armor` = {item.get('armor', 0)}, "
        f"`block` = {item.get('block', 0)}, `itemset` = {item.get('set', 0)},",
        f"    {weapon}, `dmg_min2` = 0, `dmg_max2` = 0, `dmg_type2` = 0,",
        '    ' + ', '.join(sets) + ',',
        '    `ScalingStatDistribution` = 0, `ScalingStatValue` = 0, `RandomProperty` = 0, `RandomSuffix` = 0,',
        '    `holy_res` = 0, `fire_res` = 0, `nature_res` = 0, `frost_res` = 0, `shadow_res` = 0, `arcane_res` = 0,',
        '    ' + spells + ',',
        '    `socketColor_1` = 0, `socketContent_1` = 0, `socketColor_2` = 0, `socketContent_2` = 0, '
        '`socketColor_3` = 0, `socketContent_3` = 0, `socketBonus` = 0, `GemProperties` = 0,',
        '    `RequiredDisenchantSkill` = -1, `DisenchantID` = 0, `startquest` = 0, `area` = 0, `Map` = 0, '
        "`ScriptName` = '', `VerifiedBuild` = 0;",
        'INSERT INTO `item_template` SELECT * FROM `unbound_hl_tmp`;',
    ])


def loot_sql():
    lines = []
    for map_id, bosses in LOOT.items():
        for entry, boss in bosses.items():
            h = heroic_entry(entry)
            lines.append(f"-- {boss['name']} (Heroic), map {map_id}")
            lines.append(f'DELETE FROM `creature_loot_template` WHERE `Entry` = {h};')
            rows = []
            for group_id, group in enumerate(boss.get('groups', []), 1):
                rows += [f"({h}, {item}, 0, 0, 0, 1, {group_id}, 1, 1, {sql_str('Heroic ' + boss['name'])})" for item in group]
            rows += [f"({h}, {item}, 0, {chance}, 0, 1, 0, 1, 1, {sql_str('Heroic ' + boss['name'] + ' (rare)')})"
                     for item, chance in boss.get('extra', [])]
            if rows:
                lines.append('INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, '
                             '`QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES')
                lines.append(',\n'.join(rows) + ';')
    return '\n'.join(lines)


def check():
    ids = [i['id'] for i in HEROIC_ITEMS]
    assert len(ids) == len(set(ids)), 'duplicate item id in HEROIC_ITEMS'
    assert all(910100 <= i <= 910999 for i in ids), 'heroic items use ids 910100-910999'
    known = set(ids)
    for bosses in LOOT.values():
        for boss in bosses.values():
            for group in boss.get('groups', []):
                for item in group:
                    assert item in known, f'{item} in LOOT is not defined in HEROIC_ITEMS'
    for s in ITEM_SETS:
        assert 950 <= s['ID'] <= 999
        for item in s['items']:
            assert item in known, f'set item {item} is not defined in HEROIC_ITEMS'


def main():
    check()
    ids = ', '.join(str(i['id']) for i in HEROIC_ITEMS)
    parts = ['-- Generated by tools/heroic_loot.py - edit the tables there, not this file.',
             '-- Items are deleted and re-inserted by id (never removed): see the reversibility note in heroic_loot.py.',
             f'DELETE FROM `item_template` WHERE `entry` IN ({ids});',
             '']
    parts += [item_sql(i) + '\n' for i in HEROIC_ITEMS]
    parts += ['DROP TEMPORARY TABLE IF EXISTS `unbound_hl_tmp`;', '', loot_sql()]
    path = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_heroic_loot.sql')
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(parts) + '\n')
    print('wrote', path, f'({len(HEROIC_ITEMS)} items, {sum(len(b) for b in LOOT.values())} heroic bosses)')


if __name__ == '__main__':
    main()
