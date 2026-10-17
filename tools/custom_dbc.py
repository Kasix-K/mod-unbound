"""
Generate mod-unbound's custom DBC rows for both sides from one definition:

  server: data/sql/db-world/unbound_custom_dbc.sql   (spell_dbc, spell_script_names, item_dbc, itemset_dbc, mapdifficulty_dbc,
                                                      questsort_dbc, itemdisplayinfo_dbc, currencytypes_dbc,
                                                      itemextendedcost_dbc)
  client: <client>/Data/patch-Z.MPQ                  (DBFilesClient\\Spell.dbc, Item.dbc, ItemSet.dbc, SkillLineAbility.dbc,
                                                      MapDifficulty.dbc, QuestSort.dbc, ItemDisplayInfo.dbc,
                                                      CurrencyTypes.dbc, CurrencyCategory.dbc, ItemExtendedCost.dbc)

The client DBCs are built from the server's extracted DBCs, which are identical to the 3.3.5a
(12340) client's. Run after changing the tables below, then restart the worldserver and the client:

  python tools/custom_dbc.py [--dbc DIR] [--client DIR]
"""
import argparse
import os
import re
import struct
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from classic_heroics import HEROIC_DUNGEONS, HEROIC_LEVEL, HEROIC_MAX_PLAYERS, map_difficulty_id  # noqa: E402
import heroic_loot  # noqa: E402
from bulletin_board import QUEST_SORTS  # noqa: E402
import world_bosses  # noqa: E402
import fetch_assets  # noqa: E402
import shadowflame_ward  # noqa: E402
MODULE = os.path.dirname(HERE)
ACORE = os.path.dirname(os.path.dirname(MODULE))
ROOT = os.path.dirname(ACORE)

# Name masks/flags the client expects on localized string columns.
LANG_MASK = 16712190

# Spell attributes (see SharedDefines.h)
SPELL_ATTR0_IS_ABILITY = 0x00000010
SPELL_ATTR0_ALLOW_WHILE_MOUNTED = 0x01000000
SPELL_ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL = 0x10000000
SPELL_ATTR0_NO_AURA_CANCEL = 0x80000000

SPELL_EFFECT_DUMMY = 3
SPELL_EFFECT_APPLY_AURA = 6
SPELL_AURA_DUMMY = 4
TARGET_UNIT_CASTER = 1
SKILL_COMPANIONS = 778

# Every custom spell: column name -> value. Unlisted columns are 0 / '' unless '_base' names an
# existing spell to copy (its localized strings are cleared; set the enUS ones you want). '_or' ORs flags into
# the copied values (e.g. {'Attributes': SPELL_ATTR0_NO_AURA_CANCEL}).
SPELLS = [
    {
        'ID': 200200,  # Transmogrify, keep in sync with src/unbound_transmog_spell.cpp
        '_script': 'spell_unbound_transmogrify',
        'Attributes': SPELL_ATTR0_IS_ABILITY | SPELL_ATTR0_ALLOW_WHILE_MOUNTED | SPELL_ATTR0_NOT_IN_COMBAT_ONLY_PEACEFUL,
        'CastingTimeIndex': 1,      # instant
        'RecoveryTime': 5000,       # 5 s cooldown
        'ProcChance': 101,
        'RangeIndex': 1,            # self
        'EquippedItemClass': -1,
        'Effect_1': SPELL_EFFECT_DUMMY,
        'ImplicitTargetA_1': TARGET_UNIT_CASTER,
        'EffectChainAmplitude_1': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'SpellIconID': 1,           # Trade_Engineering
        'Name_Lang_enUS': 'Transmogrify',
        'Description_Lang_enUS': 'Opens the transmogrification window.',
        'SchoolMask': 1,
    },
    {
        'ID': 200201,  # Loot Goblin companion, keep in sync with src/unbound_loot_goblin.cpp
        '_base': 4055,              # Mechanical Squirrel's summon spell
        'EffectMiscValue_1': 190100,
        'SpellIconID': 4244,        # inv_misc_bag_10_green
        'Name_Lang_enUS': 'Loot Goblin',
        'Description_Lang_enUS': 'Summons a Loot Goblin. While it is out, looting a corpse also loots '
                                 'every corpse nearby.',
    },
    {
        'ID': 200202,  # Arcane Loot Scanner companion, keep in sync with src/unbound_loot_goblin.cpp
        '_base': 4055,              # Mechanical Squirrel's summon spell
        'EffectMiscValue_1': 190102,
        'SpellIconID': 2303,        # INV_Gizmo_KhoriumPowerCore
        'Name_Lang_enUS': 'Arcane Loot Scanner',
        'Description_Lang_enUS': 'Summons an Arcane Loot Scanner. While it is out, looting a corpse also '
                                 'loots every corpse nearby.',
    },
    {
        'ID': 200203,  # Scavenger Imp companion, keep in sync with src/unbound_loot_goblin.cpp
        '_base': 4055,              # Mechanical Squirrel's summon spell
        'EffectMiscValue_1': 190210,
        'SpellIconID': 215,         # Spell_Shadow_SummonImp
        'Name_Lang_enUS': 'Scavenger Imp',
        'Description_Lang_enUS': 'Summons a Scavenger Imp. While it is out, looting a corpse also loots '
                                 'up to 4 corpses around it.',
    },
    {
        'ID': 200204,  # Wayfinder's Descent, keep in sync with src/unbound_bounty_teleporter.cpp
        '_base': 130,               # Slow Fall: the feather fall aura
        '_or': {'Attributes': SPELL_ATTR0_NO_AURA_CANCEL},
        'DurationIndex': 4,         # 2 minutes at most; removed as soon as the player lands
        'SpellClassSet': 0, 'SpellClassMask_1': 0, 'SpellClassMask_2': 0, 'SpellClassMask_3': 0,   # not a mage spell
        'Name_Lang_enUS': "Wayfinder's Descent",
        'Description_Lang_enUS': 'Falls slowly and safely to the ground.',
        'AuraDescription_Lang_enUS': 'Falling slowly. No falling damage.',
    },
    # Crusader's Oath (the Paladin Retribution class perk), keep in sync with src/unbound_perks.cpp. The
    # perk teaches the three abilities while it is on; the numbers here are the level 60 ones (the server
    # scales them by Holy Power, rank and oath).
    {
        'ID': 200220,  # Holy Power: a visible buff, one stack per Holy Power (the addon draws it as a bar)
        'Attributes': SPELL_ATTR0_NO_AURA_CANCEL,
        'CastingTimeIndex': 1,      # instant
        'DurationIndex': 18,        # 20 s, refreshed by every Holy Power gained
        'ProcChance': 101,
        'RangeIndex': 1,            # self
        'EquippedItemClass': -1,
        'CumulativeAura': 3,        # up to 3 stacks
        'Effect_1': SPELL_EFFECT_APPLY_AURA,
        'EffectAura_1': SPELL_AURA_DUMMY,
        'ImplicitTargetA_1': TARGET_UNIT_CASTER,
        'EffectChainAmplitude_1': 1.0,
        'EffectBonusMultiplier_1': 1.0,
        'SpellIconID': 1795,        # Spell_Holy_Power
        'Name_Lang_enUS': 'Holy Power',
        'Description_Lang_enUS': 'Spent by Templar\'s Verdict and Inquisition.',
        'AuraDescription_Lang_enUS': 'Holy Power, spent by Templar\'s Verdict and Inquisition.',
        'SchoolMask': 2,
    },
    {
        'ID': 200221,  # Templar's Verdict: Crusader Strike's strike, Holy, a bigger hit with more Holy Power
        '_base': 35395,             # Crusader Strike
        '_script': 'spell_unbound_oath_templars_verdict',
        'RecoveryTime': 0,
        'ManaCostPct': 0,
        'BaseLevel': 1, 'SpellLevel': 1,
        'DurationIndex': 0,
        'EffectBasePoints_2': 199,  # 200% weapon damage at 3 Holy Power
        'Effect_3': 0, 'EffectAura_3': 0, 'ImplicitTargetA_3': 0, 'EffectChainAmplitude_3': 0.0,
        'SpellClassMask_2': 0,      # not Crusader Strike for talents and glyphs
        'StanceBarOrder': 0,        # Crusader Strike's -1 doesn't fit the server's unsigned column
        'SchoolMask': 2,            # Holy
        'SpellIconID': 3025,        # Ability_Paladin_RighteousVengeance
        'Name_Lang_enUS': "Templar's Verdict",
        'Description_Lang_enUS': 'Spends all your Holy Power on a Holy strike for 60% / 130% / 200% weapon '
                                 'damage at 1 / 2 / 3 Holy Power.',
    },
    {
        'ID': 200222,  # Inquisition: Holy damage done, amount and duration set by the server
        '_base': 31884,             # Avenging Wrath: its damage done aura
        '_script': 'spell_unbound_oath_inquisition',
        'DispelType': 0,
        'ExcludeCasterAuraSpell': 0,
        'RecoveryTime': 0,
        'ManaCostPct': 0,
        'BaseLevel': 1, 'SpellLevel': 1,
        'DurationIndex': 9,         # 30 s at most
        'EffectBasePoints_1': 14,   # +15% at 3 Holy Power
        'EffectMiscValue_1': 2,     # Holy
        'Effect_2': 0, 'EffectAura_2': 0, 'EffectBasePoints_2': 0, 'EffectMiscValue_2': 0,
        'EffectSpellClassMaskC_2': 0, 'ImplicitTargetA_2': 0, 'EffectDieSides_2': 0,
        'Effect_3': 0, 'EffectAura_3': 0, 'EffectBasePoints_3': 0, 'EffectMiscValue_3': 0,
        'ImplicitTargetA_3': 0, 'EffectDieSides_3': 0,
        'SpellVisualID_1': 0,       # no Avenging Wrath wings
        'SpellClassMask_2': 0,
        'SpellIconID': 3029,        # Ability_Paladin_SanctifiedWrath
        'Name_Lang_enUS': 'Inquisition',
        'Description_Lang_enUS': 'Spends all your Holy Power: your Holy damage is increased by 5% / 10% / 15% '
                                 'for 10 / 20 / 30 sec at 1 / 2 / 3 Holy Power.',
        'AuraDescription_Lang_enUS': 'Holy damage increased.',
    },
    {
        'ID': 200223,  # Ashbringer's Call: summons creature 190220 (data/sql/db-world/unbound_crusaders_oath.sql)
        '_base': 34433,             # Shadowfiend: a 15 s guardian that attacks the target
        'EffectMiscValue_1': 190220,
        'Effect_2': 0, 'EffectTriggerSpell_2': 0, 'ImplicitTargetA_2': 0, 'EffectChainAmplitude_2': 0.0,
        'RecoveryTime': 120000,     # 2 min
        'BaseLevel': 60, 'SpellLevel': 60,
        'ShapeshiftMask': 0,
        'SpellVisualID_1': 0,
        'SpellClassSet': 10, 'SpellClassMask_1': 0, 'SpellClassMask_2': 0, 'SpellClassMask_3': 0,  # not Shadowfiend
        'SchoolMask': 2,
        'SpellIconID': 1648,        # INV_Sword_48 (the Ashbringer)
        'Name_Lang_enUS': "Ashbringer's Call",
        'Description_Lang_enUS': 'Summons the Spirit of the Ashbringer to fight your target for 15 sec. Every '
                                 'third hit it lands gives you 1 Holy Power.',
    },
]

# Item.dbc rows (client) / item_dbc rows (server). item_template holds the rest of the item.
ITEMS = [
    # ID, Class, SubClass, SoundOverrideSubclass, Material, DisplayInfoID, InventoryType, SheathType
    (910001, 15, 2, -1, 8, 8442, 0, 0),  # Loot Goblin (companion item, loot-bag icon)
    (910002, 15, 2, -1, 8, 41425, 0, 0),  # Arcane Loot Scanner (companion item, Khorium power core icon)
    (910003, 15, 2, -1, 8, 7155, 0, 0),  # Scavenger Imp (companion item, Imp in a Jar icon)
]
ITEMS += heroic_loot.item_dbc_rows()  # heroic dungeon loot (tools/heroic_loot.py)
ITEMS += world_bosses.item_dbc_rows()  # world boss loot (tools/world_bosses.py)
ITEMS += shadowflame_ward.item_dbc_rows()  # Shadowflame Ward quest items and cloak (tools/shadowflame_ward.py)

# ---------------------------------------------------------------- currencies
# Account-wide currencies (ROADMAP.md "Heroic currency and vendor"): items 912000-912099 in the Currency tab
# under an "Unbound" header. The item's full row (soulbound, multi-drop, currency token bag) is in
# data/sql/db-world/unbound_currencies.sql.
HEROIC_SIGIL = 912000
CURRENCY_CATEGORY_UNBOUND = 100
ITEMS += [
    # ID, Class, SubClass, SoundOverrideSubclass, Material, DisplayInfoID, InventoryType, SheathType
    (HEROIC_SIGIL, 10, 0, -1, 4, 70000, 0, 0),  # Heroic Sigil (class 10 = currency, like Emblem of Heroism)
]

# ItemDisplayInfo.dbc rows (client) / itemdisplayinfo_dbc rows (server): currency icons. Modelled on Emblem of
# Heroism's display (54562): only the inventory icon and the pickup sound group.
ITEM_DISPLAY_COLUMNS = ['ID', 'ModelName_1', 'ModelName_2', 'ModelTexture_1', 'ModelTexture_2', 'InventoryIcon_1',
                        'InventoryIcon_2', 'GeosetGroup_1', 'GeosetGroup_2', 'GeosetGroup_3', 'Flags',
                        'SpellVisualID', 'GroupSoundIndex', 'HelmetGeosetVis_1', 'HelmetGeosetVis_2'] + \
                       [f'Texture_{k}' for k in range(1, 9)] + ['ItemVisual', 'ParticleColorID']


def item_display_row(display_id, icon):
    values = {'ID': display_id, 'InventoryIcon_1': icon, 'GroupSoundIndex': 7}
    return [values.get(c, '' if c.startswith(('Model', 'Inventory', 'Texture')) else 0) for c in ITEM_DISPLAY_COLUMNS]


ITEM_DISPLAYS = [
    item_display_row(70000, 'Spell_Holy_SealOfRighteousness'),  # Heroic Sigil: a gold lion's head on green
]

# CurrencyTypes.dbc rows (client) / currencytypes_dbc rows (server): ID, ItemID, CategoryID, BitIndex. BitIndex is
# the item's bit in the character's known-currencies mask (64 bits; 29 is the highest the game uses).
CURRENCY_TYPES = [
    (400, HEROIC_SIGIL, CURRENCY_CATEGORY_UNBOUND, 30),
]

# CurrencyCategory.dbc rows, client only (the server doesn't load it): the Currency tab's headers.
CURRENCY_CATEGORY_COLUMNS = ['ID', 'Flags'] + [f'Name_Lang_{loc}' for loc in (
    'enUS', 'enGB', 'koKR', 'frFR', 'deDE', 'enCN', 'zhCN', 'enTW', 'zhTW', 'esES', 'esMX', 'ruRU', 'ptPT', 'ptBR',
    'itIT', 'Unk')] + ['Name_Lang_Mask']
CURRENCY_CATEGORIES = [
    [CURRENCY_CATEGORY_UNBOUND, 0, 'Unbound'] + [''] * 15 + [LANG_MASK],
]

# ItemExtendedCost.dbc rows (client) / itemextendedcost_dbc rows (server): vendor prices in Heroic Sigils, one row per
# price (an npc_vendor row's ExtendedCost points at one). The gear prices from the roadmap; more come with the vendor.
ITEM_EXTENDED_COST_COLUMNS = ['ID', 'HonorPoints', 'ArenaPoints', 'ArenaBracket'] + \
                             [f'ItemID_{k}' for k in range(1, 6)] + [f'ItemCount_{k}' for k in range(1, 6)] + \
                             ['RequiredArenaRating', 'ItemPurchaseGroup']
SIGIL_PRICES = {cost_id: sigils for sigils, cost_id in heroic_loot.SIGIL_EXTENDED_COSTS.items()}  # ExtendedCost id: sigils
ITEM_EXTENDED_COSTS = [
    (cost_id, 0, 0, 0, HEROIC_SIGIL, 0, 0, 0, 0, sigils, 0, 0, 0, 0, 0, 0)
    for cost_id, sigils in SIGIL_PRICES.items()
]

# ItemSet.dbc rows (client) / itemset_dbc rows (server): heroic dungeon sets (tools/heroic_loot.py)
ITEM_SETS = heroic_loot.item_set_rows()
ITEM_SET_COLUMNS = (['ID'] + [f'Name_Lang_{loc}' for loc in ('enUS', 'enGB', 'koKR', 'frFR', 'deDE', 'enCN',
                                                           'zhCN', 'enTW', 'zhTW', 'esES', 'esMX', 'ruRU',
                                                           'ptPT', 'ptBR', 'itIT', 'Unk')]
                    + ['Name_Lang_Mask'] + [f'ItemID_{k}' for k in range(1, 18)]
                    + [f'SetSpellID_{k}' for k in range(1, 9)] + [f'SetThreshold_{k}' for k in range(1, 9)]
                    + ['RequiredSkill', 'RequiredSkillRank'])

# SkillLineAbility.dbc rows, client only: they put companion spells in the Companions tab.
SKILL_LINE_ABILITIES = [
    # ID, SkillLine, Spell, RaceMask, ClassMask, ExcludeRace, ExcludeClass, MinSkillLineRank,
    # SupercededBySpell, AcquireMethod, TrivialHigh, TrivialLow, CharacterPoints x2
    (900001, SKILL_COMPANIONS, 200201, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0),
    (900002, SKILL_COMPANIONS, 200202, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0),
    (900003, SKILL_COMPANIONS, 200203, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0),
]


# MapDifficulty.dbc rows (client) / mapdifficulty_dbc rows (server): the heroic mode of each classic
# dungeon in tools/classic_heroics.py, modelled on Utgarde Keep's heroic row (5 players, daily reset).
MAP_DIFFICULTIES = [
    {
        'ID': map_difficulty_id(map_id),
        'MapID': map_id,
        'Difficulty': 1,
        'Message_Lang_enUS': f'Heroic Difficulty requires you to be level {HEROIC_LEVEL}.',
        'RaidDuration': 86400,
        'MaxPlayers': HEROIC_MAX_PLAYERS.get(map_id, 5),
        'Difficultystring': 'DUNGEON_DIFFICULTY_5PLAYER_HEROIC',
    }
    for map_id, _ in HEROIC_DUNGEONS
]
MAP_DIFFICULTY_COLUMNS = (['ID', 'MapID', 'Difficulty']
                          + [f'Message_Lang_{loc}' for loc in ('enUS', 'enGB', 'koKR', 'frFR', 'deDE', 'enCN',
                                                               'zhCN', 'enTW', 'zhTW', 'esES', 'esMX', 'ruRU',
                                                               'ptPT', 'ptBR', 'itIT', 'Unk')]
                          + ['Message_Lang_Mask', 'RaidDuration', 'MaxPlayers', 'Difficultystring'])


def map_difficulty_row(entry):
    def default(col):
        if col.endswith('_Mask'):
            return LANG_MASK
        return '' if col.startswith('Message') or col == 'Difficultystring' else 0
    return [entry.get(col, default(col)) for col in MAP_DIFFICULTY_COLUMNS]


# QuestSort.dbc rows (client) / questsort_dbc rows (server): the Bulletin Board's quest log headers
# (tools/bulletin_board.py, QUEST_SORTS).
LOCALES = ('enUS', 'enGB', 'koKR', 'frFR', 'deDE', 'enCN', 'zhCN', 'enTW', 'zhTW', 'esES', 'esMX', 'ruRU', 'ptPT',
           'ptBR', 'itIT', 'Unk')
QUEST_SORT_COLUMNS = ['ID'] + [f'SortName_Lang_{loc}' for loc in LOCALES] + ['SortName_Lang_Mask']


def quest_sort_row(sort_id, name):
    return [sort_id, name] + [''] * (len(LOCALES) - 1) + [LANG_MASK]


# ---------------------------------------------------------------- DBC helpers

def read_dbc(path):
    data = open(path, 'rb').read()
    magic, count, nfields, recsize, strsize = struct.unpack_from('<4sIIII', data)
    assert magic == b'WDBC', f'{path} is not a WDBC file'
    records = data[20:20 + count * recsize]
    strings = bytearray(data[20 + count * recsize:20 + count * recsize + strsize])
    return count, nfields, recsize, records, strings


def write_dbc(nfields, recsize, records, count, strings):
    return struct.pack('<4sIIII', b'WDBC', count, nfields, recsize, len(strings)) + bytes(records) + bytes(strings)


def pack_int(v):
    return struct.pack('<i' if v < 0 else '<I', v)


def append_int_rows(base_path, rows):
    """Append rows of plain integers to a DBC (no strings), refusing IDs that already exist."""
    count, nfields, recsize, records, strings = read_dbc(base_path)
    existing = {struct.unpack_from('<I', records, i * recsize)[0] for i in range(count)}
    new = bytearray()
    for row in rows:
        assert len(row) == nfields, f'{os.path.basename(base_path)} rows need {nfields} fields'
        assert row[0] not in existing, f'{row[0]} already exists in {os.path.basename(base_path)}'
        new += b''.join(pack_int(v) for v in row)
    return write_dbc(nfields, recsize, records + new, count + len(rows), strings)


def append_rows_with_strings(base_path, rows):
    """Append rows whose values are ints or strs (strs go into the string block), refusing existing IDs."""
    count, nfields, recsize, records, strings = read_dbc(base_path)
    existing = {struct.unpack_from('<I', records, i * recsize)[0] for i in range(count)}
    new = bytearray()
    for row in rows:
        assert len(row) == nfields, f'{os.path.basename(base_path)} rows need {nfields} fields'
        assert row[0] not in existing, f'{row[0]} already exists in {os.path.basename(base_path)}'
        for v in row:
            if isinstance(v, str):
                off = 0
                if v:
                    off = len(strings)
                    strings += v.encode('utf8') + b'\0'
                new += struct.pack('<I', off)
            else:
                new += pack_int(v)
    return write_dbc(nfields, recsize, records + new, count + len(rows), strings)


# ---------------------------------------------------------------- spells

def spell_dbc_columns():
    """(name, sqltype) for all 234 spell_dbc columns, in Spell.dbc field order."""
    path = os.path.join(ACORE, 'data', 'sql', 'base', 'db_world', 'spell_dbc.sql')
    sql = open(path, encoding='utf8').read()
    body = re.search(r'CREATE TABLE `spell_dbc` \((.*?)\n\)', sql, re.S).group(1)
    return re.findall(r'^\s*`(\w+)`\s+(\w+)', body, re.M)


def is_string(typ):
    return typ in ('varchar', 'text')


def base_spell_values(dbc, spell_id, cols):
    count, nfields, recsize, records, _ = dbc
    for i in range(count):
        if struct.unpack_from('<I', records, i * recsize)[0] != spell_id:
            continue
        raw = records[i * recsize:(i + 1) * recsize]
        values = {}
        for k, (name, typ) in enumerate(cols):
            if is_string(typ):
                values[name] = ''
            elif typ == 'float':
                values[name] = struct.unpack_from('<f', raw, k * 4)[0]
            else:
                values[name] = struct.unpack_from('<i' if typ == 'int' else '<I', raw, k * 4)[0]
        return values
    raise KeyError(f'base spell {spell_id} not found in Spell.dbc')


def spell_rows(dbc, cols):
    """Full column values for every SPELLS entry, in column order."""
    rows = []
    for spell in SPELLS:
        values = base_spell_values(dbc, spell['_base'], cols) if '_base' in spell else {}
        for name, typ in cols:
            if name not in values:
                if name.endswith('_Lang_Mask'):
                    values[name] = LANG_MASK
                elif is_string(typ):
                    values[name] = ''
                elif typ == 'float':
                    values[name] = 0.0
                else:
                    values[name] = 0
        values.update({k: v for k, v in spell.items() if not k.startswith('_')})
        for name, flags in spell.get('_or', {}).items():   # flag columns are unsigned
            values[name] = (values[name] & 0xffffffff) | flags
        rows.append([values[name] for name, _ in cols])
    return rows


def build_spell_dbc(dbc, cols, rows):
    count, nfields, recsize, records, strings = dbc
    assert nfields == len(cols) and recsize == nfields * 4, 'unexpected Spell.dbc layout'
    existing = {struct.unpack_from('<I', records, i * recsize)[0] for i in range(count)}
    new = bytearray()
    for row in rows:
        assert row[0] not in existing, f'spell {row[0]} already exists in Spell.dbc'
        for (name, typ), v in zip(cols, row):
            if is_string(typ):
                if v:
                    off = len(strings)
                    strings += v.encode('utf8') + b'\0'
                else:
                    off = 0  # offset 0 is the empty string
                new += struct.pack('<I', off)
            elif typ == 'float':
                new += struct.pack('<f', v)
            else:
                new += pack_int(v)
    return write_dbc(nfields, recsize, records + new, count + len(rows), strings)


# ---------------------------------------------------------------- server SQL

def sql_literal(v):
    if isinstance(v, str):
        return "'" + v.replace('\\', '\\\\').replace("'", "''") + "'"
    return repr(v) if isinstance(v, float) else str(v)


def write_sql(cols, rows, path):
    ids = ', '.join(str(s['ID']) for s in SPELLS)
    names = ', '.join('`' + n + '`' for n, _ in cols)
    lines = ['-- Generated by tools/custom_dbc.py - edit the tables there, not this file.',
             f'DELETE FROM `spell_dbc` WHERE `ID` IN ({ids});',
             f'INSERT INTO `spell_dbc` ({names}) VALUES',
             ',\n'.join('(' + ','.join(sql_literal(v) for v in row) + ')' for row in rows) + ';']
    scripted = [s for s in SPELLS if s.get('_script')]
    if scripted:
        lines.append(f"DELETE FROM `spell_script_names` WHERE `spell_id` IN ({', '.join(str(s['ID']) for s in scripted)});")
        lines.append('INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES')
        lines.append(',\n'.join(f"({s['ID']}, '{s['_script']}')" for s in scripted) + ';')
    if ITEMS:
        lines.append(f"DELETE FROM `item_dbc` WHERE `ID` IN ({', '.join(str(i[0]) for i in ITEMS)});")
        lines.append('INSERT INTO `item_dbc` (`ID`, `ClassID`, `SubclassID`, `Sound_Override_Subclassid`, '
                     '`Material`, `DisplayInfoID`, `InventoryType`, `SheatheType`) VALUES')
        lines.append(',\n'.join('(' + ','.join(str(v) for v in i) + ')' for i in ITEMS) + ';')
    if ITEM_SETS:
        lines.append(f"DELETE FROM `itemset_dbc` WHERE `ID` IN ({', '.join(str(r[0]) for r in ITEM_SETS)});")
        lines.append('INSERT INTO `itemset_dbc` (' + ', '.join('`' + c + '`' for c in ITEM_SET_COLUMNS) + ') VALUES')
        lines.append(',\n'.join('(' + ','.join(sql_literal(v) for v in r) + ')' for r in ITEM_SETS) + ';')
    if MAP_DIFFICULTIES:
        ids = ', '.join(str(m['ID']) for m in MAP_DIFFICULTIES)
        lines.append(f'DELETE FROM `mapdifficulty_dbc` WHERE `ID` IN ({ids});')
        lines.append('INSERT INTO `mapdifficulty_dbc` (' + ', '.join('`' + c + '`' for c in MAP_DIFFICULTY_COLUMNS)
                     + ') VALUES')
        lines.append(',\n'.join('(' + ','.join(sql_literal(v) for v in map_difficulty_row(m)) + ')'
                                for m in MAP_DIFFICULTIES) + ';')
    if QUEST_SORTS:
        lines.append(f"DELETE FROM `questsort_dbc` WHERE `ID` IN ({', '.join(str(s) for s, _ in QUEST_SORTS)});")
        lines.append('INSERT INTO `questsort_dbc` (' + ', '.join('`' + c + '`' for c in QUEST_SORT_COLUMNS) + ') VALUES')
        lines.append(',\n'.join('(' + ','.join(sql_literal(v) for v in quest_sort_row(s, n)) + ')'
                                for s, n in QUEST_SORTS) + ';')
    if ITEM_DISPLAYS:
        lines.append(f"DELETE FROM `itemdisplayinfo_dbc` WHERE `ID` IN ({', '.join(str(r[0]) for r in ITEM_DISPLAYS)});")
        lines.append('INSERT INTO `itemdisplayinfo_dbc` (' + ', '.join('`' + c + '`' for c in ITEM_DISPLAY_COLUMNS)
                     + ') VALUES')
        lines.append(',\n'.join('(' + ','.join(sql_literal(v) for v in r) + ')' for r in ITEM_DISPLAYS) + ';')
    if CURRENCY_TYPES:
        lines.append(f"DELETE FROM `currencytypes_dbc` WHERE `ID` IN ({', '.join(str(r[0]) for r in CURRENCY_TYPES)});")
        lines.append('INSERT INTO `currencytypes_dbc` (`ID`, `ItemID`, `CategoryID`, `BitIndex`) VALUES')
        lines.append(',\n'.join('(' + ','.join(str(v) for v in r) + ')' for r in CURRENCY_TYPES) + ';')
    if ITEM_EXTENDED_COSTS:
        lines.append(f"DELETE FROM `itemextendedcost_dbc` WHERE `ID` IN "
                     f"({', '.join(str(r[0]) for r in ITEM_EXTENDED_COSTS)});")
        lines.append('INSERT INTO `itemextendedcost_dbc` (' + ', '.join('`' + c + '`' for c in ITEM_EXTENDED_COST_COLUMNS)
                     + ') VALUES')
        lines.append(',\n'.join('(' + ','.join(str(v) for v in r) + ')' for r in ITEM_EXTENDED_COSTS) + ';')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')


# ---------------------------------------------------------------- MPQ writer (format v0)

def _crypt_table():
    table, seed = [0] * 0x500, 0x00100001
    for i in range(0x100):
        idx = i
        for _ in range(5):
            seed = (seed * 125 + 3) % 0x2AAAAB
            hi = (seed & 0xFFFF) << 16
            seed = (seed * 125 + 3) % 0x2AAAAB
            table[idx] = hi | (seed & 0xFFFF)
            idx += 0x100
    return table


CRYPT = _crypt_table()


def mpq_hash(name, kind):
    s1, s2 = 0x7FED7FED, 0xEEEEEEEE
    for ch in name.upper().replace('/', '\\'):
        c = ord(ch)
        s1 = (CRYPT[(kind << 8) + c] ^ (s1 + s2)) & 0xFFFFFFFF
        s2 = (c + s1 + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return s1


def mpq_encrypt(data, key):
    words = struct.unpack('<%dI' % (len(data) // 4), data)
    s2, out = 0xEEEEEEEE, []
    for w in words:
        s2 = (s2 + CRYPT[0x400 + (key & 0xFF)]) & 0xFFFFFFFF
        out.append((w ^ (key + s2)) & 0xFFFFFFFF)
        key = (((~key << 0x15) + 0x11111111) | (key >> 0x0B)) & 0xFFFFFFFF
        s2 = (w + s2 + (s2 << 5) + 3) & 0xFFFFFFFF
    return struct.pack('<%dI' % len(out), *out)


def write_mpq(path, files):
    """files: {archive name: bytes}. Stores each file zlib-compressed in 4 KiB sectors."""
    sector = 512 << 3
    files = dict(files)
    files['(listfile)'] = '\r\n'.join(files).encode() + b'\r\n'

    body, blocks = bytearray(), []
    for name, data in files.items():
        start = 32 + len(body)
        nsec = (len(data) + sector - 1) // sector
        chunks = []
        for i in range(nsec):
            raw = data[i * sector:(i + 1) * sector]
            packed = b'\x02' + zlib.compress(raw, 9)
            chunks.append(packed if len(packed) < len(raw) else raw)
        offsets, pos = [], (nsec + 1) * 4
        for c in chunks:
            offsets.append(pos)
            pos += len(c)
        offsets.append(pos)
        body += struct.pack('<%dI' % len(offsets), *offsets) + b''.join(chunks)
        blocks.append((start, pos, len(data), 0x80000000 | 0x00000200))  # EXISTS | COMPRESS

    hsize = 16
    while hsize < len(files) * 2:
        hsize *= 2
    htable = [(0xFFFFFFFF, 0xFFFFFFFF, 0xFFFF, 0xFFFF, 0xFFFFFFFF)] * hsize
    for bi, name in enumerate(files):
        i = mpq_hash(name, 0) % hsize
        while htable[i][4] != 0xFFFFFFFF:
            i = (i + 1) % hsize
        htable[i] = (mpq_hash(name, 1), mpq_hash(name, 2), 0, 0, bi)

    hraw = b''.join(struct.pack('<IIHHI', *e) for e in htable)
    braw = b''.join(struct.pack('<IIII', *b) for b in blocks)
    hpos = 32 + len(body)
    bpos = hpos + len(hraw)
    total = bpos + len(braw)
    header = struct.pack('<4sIIHHIIII', b'MPQ\x1a', 32, total, 0, 3, hpos, bpos, hsize, len(blocks))
    # Write next to the target and swap it in, so a locked or failed write never leaves a broken patch.
    tmp = path + '.tmp'
    with open(tmp, 'wb') as f:
        f.write(header + body + mpq_encrypt(hraw, mpq_hash('(hash table)', 3))
                + mpq_encrypt(braw, mpq_hash('(block table)', 3)))
    try:
        os.replace(tmp, path)
    except PermissionError:
        os.remove(tmp)
        raise SystemExit(f'{path} is in use - close the game client and run this again.')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dbc', default=os.path.join(ROOT, 'data', 'dbc'), help='server DBC folder')
    ap.add_argument('--client', default=r'E:\WoW 3.3.5a Unbound', help='client folder')
    ap.add_argument('--assets', default=fetch_assets.DEFAULT_ASSETS,
                    help='local assets folder (icons, textures; see tools/fetch_assets.py)')
    args = ap.parse_args()

    cols = spell_dbc_columns()
    assert len(cols) == 234, f'spell_dbc has {len(cols)} columns, expected 234'
    spell_dbc = read_dbc(os.path.join(args.dbc, 'Spell.dbc'))
    rows = spell_rows(spell_dbc, cols)

    sql_path = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_custom_dbc.sql')
    write_sql(cols, rows, sql_path)
    print('wrote', sql_path)

    files = {'DBFilesClient\\Spell.dbc': build_spell_dbc(spell_dbc, cols, rows)}
    if ITEMS:
        files['DBFilesClient\\Item.dbc'] = append_int_rows(os.path.join(args.dbc, 'Item.dbc'), ITEMS)
    if SKILL_LINE_ABILITIES:
        files['DBFilesClient\\SkillLineAbility.dbc'] = append_int_rows(
            os.path.join(args.dbc, 'SkillLineAbility.dbc'), SKILL_LINE_ABILITIES)
    if ITEM_SETS:
        files['DBFilesClient\\ItemSet.dbc'] = append_rows_with_strings(os.path.join(args.dbc, 'ItemSet.dbc'), ITEM_SETS)
    if MAP_DIFFICULTIES:
        files['DBFilesClient\\MapDifficulty.dbc'] = append_rows_with_strings(
            os.path.join(args.dbc, 'MapDifficulty.dbc'), [map_difficulty_row(m) for m in MAP_DIFFICULTIES])
    if QUEST_SORTS:
        files['DBFilesClient\\QuestSort.dbc'] = append_rows_with_strings(
            os.path.join(args.dbc, 'QuestSort.dbc'), [quest_sort_row(s, n) for s, n in QUEST_SORTS])
    if ITEM_DISPLAYS:
        files['DBFilesClient\\ItemDisplayInfo.dbc'] = append_rows_with_strings(
            os.path.join(args.dbc, 'ItemDisplayInfo.dbc'), ITEM_DISPLAYS)
    if CURRENCY_TYPES:
        files['DBFilesClient\\CurrencyTypes.dbc'] = append_int_rows(os.path.join(args.dbc, 'CurrencyTypes.dbc'),
                                                                    CURRENCY_TYPES)
    if CURRENCY_CATEGORIES:
        files['DBFilesClient\\CurrencyCategory.dbc'] = append_rows_with_strings(
            os.path.join(args.dbc, 'CurrencyCategory.dbc'), CURRENCY_CATEGORIES)
    if ITEM_EXTENDED_COSTS:
        files['DBFilesClient\\ItemExtendedCost.dbc'] = append_int_rows(os.path.join(args.dbc, 'ItemExtendedCost.dbc'),
                                                                       ITEM_EXTENDED_COSTS)
    # icons and textures from the local assets folder (data/client_assets.txt; never in git)
    assets, missing = fetch_assets.load(args.assets)
    files.update(assets)
    for name in missing:
        print('WARNING: asset not in', args.assets, '-', name, '(run tools/fetch_assets.py)')
    mpq_path = os.path.join(args.client, 'Data', 'patch-Z.MPQ')
    write_mpq(mpq_path, files)
    if assets or missing:
        print(f'packed {len(assets)} of {len(assets) + len(missing)} listed assets')
    print('wrote', mpq_path, f'({len(SPELLS)} spells, {len(ITEMS)} items, {len(ITEM_SETS)} item sets, '
                             f'{len(SKILL_LINE_ABILITIES)} skill line abilities, '
                             f'{len(MAP_DIFFICULTIES)} map difficulties, {len(QUEST_SORTS)} quest sorts, '
                             f'{len(ITEM_DISPLAYS)} item displays, {len(CURRENCY_TYPES)} currencies, '
                             f'{len(CURRENCY_CATEGORIES)} currency categories, {len(ITEM_EXTENDED_COSTS)} prices)')


if __name__ == '__main__':
    main()
