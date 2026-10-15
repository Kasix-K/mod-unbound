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
    # --- Wailing Caverns (heroic) -----------------------------------------------------------------------
    # Lady Anacondra
    dict(id=910122, base=5404, name="Serpent's Shoulders", ilvl=61, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=6729, armor=196,
         stats=[(AGI, 31)]),
    dict(id=910123, base=10412, name="Belt of the Fang", ilvl=61, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=28384, armor=134,
         stats=[(STA, 14), (AGI, 12)]),
    # Lord Cobrahn
    dict(id=910124, base=6465, name="Robe of the Moccasin", ilvl=61, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=12693, armor=96,
         stats=[(SPI, 21), (STA, 21)]),
    dict(id=910125, base=6460, name="Cobrahn's Grasp", ilvl=61, cls=CLS_ARMOR, sub=3, inv=6, mat=5, sheath=0,
         display=11945, armor=208,
         stats=[(STR, 19), (AGI, 7)]),
    dict(id=910126, base=10410, name="Leggings of the Fang", ilvl=61, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=28385, armor=215,
         stats=[(STR, 11), (STA, 9), (AGI, 20)]),
    # Kresh: no gear drops of its own (heroic: gold only)
    # Lord Pythas
    dict(id=910127, base=6473, name="Armor of the Fang", ilvl=62, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=17091, armor=181,
         stats=[(STR, 21), (STA, 21)]),
    # Skum
    dict(id=910128, base=6449, name="Glowing Lizardscale Cloak", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7,
         sheath=0, display=23001, armor=45,
         stats=[(AGI, 14), (STA, 5)]),
    dict(id=910129, base=6448, name="Tail Spike", ilvl=62, cls=CLS_WEAPON, sub=15, inv=13, mat=1, sheath=3,
         display=20349, dps=41.5, delay=1800,
         stats=[(AGI, 8), (STR, 10)]),
    # Lord Serpentis
    dict(id=910130, base=5970, name="Serpent Gloves", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=19128, armor=80,
         stats=[(INT, 25)]),
    dict(id=910131, base=6459, name="Savage Trodders", ilvl=62, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=11935, armor=266,
         stats=[(STA, 33)]),
    dict(id=910132, base=10411, name="Footpads of the Fang", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=27949, armor=166,
         stats=[(STA, 16), (AGI, 16)]),
    # Verdan the Everliving
    dict(id=910133, base=6630, name="Seedcloud Buckler", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=6274, armor=2153, block=40,
         stats=[(SPI, 7), (INT, 13)]),
    dict(id=910134, base=6631, name="Living Root", ilvl=62, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=20336, dps=53.9, delay=2900,
         stats=[(SPI, 29), (STA, 5)]),
    dict(id=910135, base=6629, name="Sporid Cape", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=23141, armor=45,
         stats=[(STA, 11), (SPI, 8)]),
    # Mutanus the Devourer
    dict(id=910136, base=6463, name="Deep Fathom Ring", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=9846,
         stats=[(SPI, 9), (STA, 4), (INT, 4)]),
    dict(id=910137, base=6627, name="Mutant Scale Breastplate", ilvl=63, cls=CLS_ARMOR, sub=3, inv=5, mat=5,
         sheath=0, display=12595, armor=398,
         stats=[(STR, 30), (STA, 12)]),
    # --- Shadowfang Keep (heroic) -----------------------------------------------------------------------
    # Rethilgore
    dict(id=910138, base=5254, name="Rugged Spaulders", ilvl=61, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=10179, armor=196,
         stats=[(AGI, 31)]),
    # Razorclaw the Butcher
    dict(id=910139, base=6226, name="Bloody Apron", ilvl=61, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=12652, armor=96,
         stats=[(STA, 42)]),
    dict(id=910140, base=6633, name="Butcher's Slicer", ilvl=61, cls=CLS_WEAPON, sub=7, inv=13, mat=1, sheath=3,
         display=12610, dps=41.5, delay=2900,
         stats=[(STR, 10), (STA, 8)]),
    dict(id=910141, base=1292, name="Butcher's Cleaver", ilvl=61, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=8466, dps=41.5, delay=1700,
         stats=[(STR, 13), (AGI, 5)]),
    # Baron Silverlaine
    dict(id=910142, base=6323, name="Baron's Scepter", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=2, sheath=3,
         display=21051, dps=41.5, delay=2400,
         stats=[(STR, 18)]),
    dict(id=910143, base=6321, name="Silverlaine's Family Seal", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=5,
         sheath=0, display=14433,
         stats=[(STR, 13), (STA, 5)]),
    # Commander Springvale
    dict(id=910144, base=6320, name="Commander's Crest", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=18700, armor=2153, block=40,
         stats=[(DODGE, 5), (STA, 5), (STR, 10)]),
    dict(id=910145, base=3191, name="Arced War Axe", ilvl=62, cls=CLS_WEAPON, sub=1, inv=17, mat=1, sheath=1,
         display=11165, dps=53.9, delay=3300,
         stats=[(STR, 18), (STA, 16)]),
    # Odo the Blindwatcher
    dict(id=910146, base=6319, name="Girdle of the Blindwatcher", ilvl=62, cls=CLS_ARMOR, sub=2, inv=6, mat=8,
         sheath=0, display=11253, armor=134,
         stats=[(STA, 12), (INT, 14)]),
    dict(id=910147, base=6318, name="Odo's Ley Staff", ilvl=62, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=20335, dps=53.9, delay=2900,
         stats=[(SPI, 24), (STA, 10)]),
    # Fenrus the Devourer
    dict(id=910148, base=6340, name="Fenrus' Hide", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=23027, armor=45,
         stats=[(AGI, 10), (STA, 9)]),
    dict(id=910149, base=3230, name="Black Wolf Bracers", ilvl=62, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=17166, armor=77,
         stats=[(STA, 24)]),
    # Wolf Master Nandos
    dict(id=910150, base=6314, name="Wolfmaster Cape", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=23082, armor=45,
         stats=[(DODGE, 10), (AGI, 9)]),
    dict(id=910151, base=3748, name="Feline Mantle", ilvl=62, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=10169, armor=75,
         stats=[(INT, 20), (SPI, 11)]),
    # Archmage Arugal
    dict(id=910152, base=6324, name="Robes of Arugal", ilvl=63, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=12696, armor=96,
         stats=[(SPI, 7), (INT, 22), (STA, 12)]),
    dict(id=910153, base=6392, name="Belt of Arugal", ilvl=63, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=11533, armor=55,
         stats=[(INT, 20), (SPI, 6)]),
    # --- Blackfathom Deeps (heroic) ---------------------------------------------------------------------
    # Ghamoo-ra
    dict(id=910154, base=6908, name="Ghamoo-ra's Bind", ilvl=61, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=16723, armor=55,
         stats=[(STA, 13), (INT, 13)]),
    dict(id=910155, base=6907, name="Tortoise Armor", ilvl=61, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=16903, armor=398,
         stats=[(STA, 42)]),
    # Lady Sarevess
    dict(id=910156, base=888, name="Naga Battle Gloves", ilvl=61, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=17182, armor=122,
         stats=[(AGI, 12), (STA, 7), (STR, 7)]),
    dict(id=910157, base=11121, name="Darkwater Talwar", ilvl=61, cls=CLS_WEAPON, sub=7, inv=13, mat=1, sheath=3,
         display=20094, dps=41.5, delay=2200,
         stats=[(STR, 18)]),
    dict(id=910158, base=3078, name="Naga Heartpiercer", ilvl=61, cls=CLS_WEAPON, sub=2, inv=15, mat=2, sheath=0,
         display=20669, dps=41.4, delay=1800,
         stats=[(AGI, 14)]),
    # Gelihast
    dict(id=910159, base=6905, name="Reef Axe", ilvl=62, cls=CLS_WEAPON, sub=1, inv=17, mat=1, sheath=1,
         display=22222, dps=53.9, delay=3300,
         stats=[(STA, 34)]),
    dict(id=910160, base=6906, name="Algae Fists", ilvl=62, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=13361, armor=242,
         stats=[(STR, 18), (STA, 7)]),
    # Baron Aquanis
    dict(id=910161, base=3416, name="Martyr's Chain", ilvl=62, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=12971, armor=398,
         stats=[(14, 10), (STA, 16), (STR, 16)]),
    dict(id=910162, base=1491, name="Ring of Precision", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=1, sheath=1,
         display=9836,
         stats=[(AGI, 12), (SPI, 6)]),
    dict(id=910163, base=1454, name="Axe of the Enforcer", ilvl=62, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=8457, dps=41.5, delay=2600,
         stats=[(STR, 10), (STA, 8)]),
    # Twilight Lord Kelris
    dict(id=910164, base=1155, name="Rod of the Sleepwalker", ilvl=62, cls=CLS_WEAPON, sub=10, inv=17, mat=2,
         sheath=2, display=20327, dps=53.9, delay=2800,
         stats=[(INT, 18), (SPI, 16)]),
    dict(id=910165, base=6903, name="Gaze Dreamer Pants", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=13357, armor=84,
         stats=[(INT, 22), (SPI, 18)]),
    # Old Serra'kis
    dict(id=910166, base=6901, name="Glowing Thresher Cape", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=23002, armor=45,
         stats=[(SPI, 14), (INT, 5)]),
    dict(id=910167, base=6902, name="Bands of Serra'kis", ilvl=62, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=17001, armor=77,
         stats=[(STR, 8), (STA, 4), (AGI, 12)]),
    # Aku'mai
    dict(id=910168, base=6910, name="Leech Pants", ilvl=63, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=13365, armor=84,
         stats=[(INT, 10), (SPI, 29), (STA, 2)]),
    dict(id=910169, base=6911, name="Moss Cinch", ilvl=63, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=16931, armor=134,
         stats=[(INT, 18), (STA, 8)]),
    # --- Gnomeregan (heroic) ----------------------------------------------------------------------------
    # Grubbis
    dict(id=910170, base=9445, name="Grubbis Paws", ilvl=61, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=18364, armor=242,
         stats=[(AGI, 6), (STR, 8), (STA, 11)]),
    # Viscous Fallout
    dict(id=910171, base=9454, name="Acidic Walkers", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=14749, armor=64,
         stats=[(INT, 22), (SPI, 11)]),
    dict(id=910172, base=9488, name="Oscillating Power Hammer", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=2,
         sheath=3, display=18406, dps=41.5, delay=2000,
         stats=[(STR, 15), (STA, 3)]),
    dict(id=910173, base=9490, name="Gizmotron Megachopper", ilvl=62, cls=CLS_WEAPON, sub=8, inv=17, mat=1, sheath=1,
         display=18409, dps=53.9, delay=3200,
         stats=[(STR, 25), (AGI, 9)]),
    # Electrocutioner 6000
    dict(id=910174, base=9447, name="Electrocutioner Lagnut", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=1,
         display=18365,
         stats=[(SPI, 12), (STA, 6)]),
    dict(id=910175, base=9448, name="Spidertank Oilrag", ilvl=62, cls=CLS_ARMOR, sub=1, inv=9, mat=7, sheath=0,
         display=18366, armor=39,
         stats=[(STA, 24)]),
    # Crowd Pummeler 9-60
    dict(id=910176, base=9450, name="Gnomebot Operating Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8,
         sheath=0, display=18367, armor=166,
         stats=[(STA, 24), (INT, 9)]),
    dict(id=910177, base=9449, name="Manual Crowd Pummeler", ilvl=62, cls=CLS_WEAPON, sub=5, inv=17, mat=2, sheath=1,
         display=19645, dps=53.9, delay=2000,
         stats=[(STR, 26), (AGI, 8)]),
    # Mekgineer Thermaplugg
    dict(id=910178, base=9458, name="Thermaplugg's Central Core", ilvl=63, cls=CLS_ARMOR, sub=6, inv=14, mat=1,
         sheath=4, display=18374, armor=2153, block=40,
         stats=[(SPI, 20)]),
    dict(id=910179, base=9492, name="Electromagnetic Gigaflux Reactivator", ilvl=63, cls=CLS_ARMOR, sub=1, inv=1,
         mat=7, sheath=0, display=18415, armor=81,
         stats=[(SPI, 17), (INT, 22)]),
    dict(id=910180, base=9459, name="Thermaplugg's Left Arm", ilvl=63, cls=CLS_WEAPON, sub=1, inv=17, mat=1,
         sheath=1, display=19298, dps=53.9, delay=2700,
         stats=[(STR, 24), (STA, 10)]),
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
    43: {  # Wailing Caverns
        3671: dict(name="Lady Anacondra", groups=[[910122, 910123]], gold=(2000, 4000)),
        3669: dict(name="Lord Cobrahn", groups=[[910124, 910125, 910126]], gold=(2000, 4000)),
        3653: dict(name="Kresh", groups=[], gold=(2000, 4000)),
        3670: dict(name="Lord Pythas", groups=[[910127]], gold=(2000, 4000)),
        3674: dict(name="Skum", groups=[[910128, 910129]], gold=(2000, 4000)),
        3673: dict(name="Lord Serpentis", groups=[[910130, 910131, 910132]], gold=(2000, 4000)),
        5775: dict(name="Verdan the Everliving", groups=[[910133, 910134, 910135]], gold=(2000, 4000)),
        3654: dict(name="Mutanus the Devourer", groups=[[910136], [910137]], gold=(5000, 10000)),
    },
    33: {  # Shadowfang Keep
        3914: dict(name="Rethilgore", groups=[[910138]], gold=(2000, 4000)),
        3886: dict(name="Razorclaw the Butcher", groups=[[910139, 910140, 910141]], gold=(2000, 4000)),
        3887: dict(name="Baron Silverlaine", groups=[[910142, 910143]], gold=(2000, 4000)),
        4278: dict(name="Commander Springvale", groups=[[910144, 910145]], gold=(2000, 4000)),
        4279: dict(name="Odo the Blindwatcher", groups=[[910146, 910147]], gold=(2000, 4000)),
        4274: dict(name="Fenrus the Devourer", groups=[[910148, 910149]], gold=(2000, 4000)),
        3927: dict(name="Wolf Master Nandos", groups=[[910150, 910151]], gold=(2000, 4000)),
        4275: dict(name="Archmage Arugal", groups=[[910152], [910153]], gold=(5000, 10000)),
    },
    48: {  # Blackfathom Deeps
        4887: dict(name="Ghamoo-ra", groups=[[910154, 910155]], gold=(2000, 4000)),
        4831: dict(name="Lady Sarevess", groups=[[910156, 910157, 910158]], gold=(2000, 4000)),
        6243: dict(name="Gelihast", groups=[[910159, 910160]], gold=(2000, 4000)),
        12876: dict(name="Baron Aquanis", groups=[[910161, 910162, 910163]], gold=(2000, 4000)),
        4832: dict(name="Twilight Lord Kelris", groups=[[910164, 910165]], gold=(2000, 4000)),
        4830: dict(name="Old Serra'kis", groups=[[910166, 910167]], gold=(2000, 4000)),
        4829: dict(name="Aku'mai", groups=[[910168], [910169]], gold=(5000, 10000)),
    },
    90: {  # Gnomeregan
        7361: dict(name="Grubbis", groups=[[910170]], gold=(2000, 4000)),
        7079: dict(name="Viscous Fallout", groups=[[910171, 910172, 910173]], gold=(2000, 4000)),
        6235: dict(name="Electrocutioner 6000", groups=[[910174, 910175]], gold=(2000, 4000)),
        6229: dict(name="Crowd Pummeler 9-60", groups=[[910176, 910177]], gold=(2000, 4000)),
        7800: dict(name="Mekgineer Thermaplugg", groups=[[910178, 910179], [910180]], gold=(5000, 10000)),
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
