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
         mat=6, sheath=0, display=23628, armor=369, stats=[(STR, 8), (STA, 12), (DEFENSE, 6)]),
    dict(id=910101, base=12589, name="Mine Overseer's Cord", ilvl=61, cls=CLS_ARMOR, sub=CLOTH, inv=WAIST,
         mat=7, sheath=0, display=21796, armor=55, stats=[(INT, 7), (SPI, 4), (STA, 5), (SPELL_POWER, 10)]),
    dict(id=910102, base=5187, name="Rhahk'Zor's Hammer", ilvl=61, cls=CLS_WEAPON, sub=MACE_2H, inv=TWO_HAND,
         mat=2, sheath=1, display=8600, dps=53.9, delay=3200, stats=[(STR, 15), (STA, 10), (CRIT, 9)]),
    # Sneed's Shredder (Sneed, who jumps out when the Shredder dies, keeps his normal loot)
    dict(id=910103, base=15648, name="Shredder Plating Shield", ilvl=61, cls=CLS_ARMOR, sub=SHIELD,
         inv=SHIELD_SLOT, mat=1, sheath=4, display=27179, armor=2153, block=40,
         stats=[(STA, 8), (DEFENSE, 5), (BLOCK_VALUE, 7)]),
    dict(id=910104, base=5195, name="Gold-flecked Gloves", ilvl=61, cls=CLS_ARMOR, sub=CLOTH, inv=HANDS,
         mat=7, sheath=0, display=16966, armor=80, stats=[(INT, 7), (STA, 5), (SPELL_POWER, 11), (MP5, 2)]),
    dict(id=910105, base=2169, name="Buzzer Blade", ilvl=61, cls=CLS_WEAPON, sub=DAGGER, inv=ONE_HAND,
         mat=1, sheath=3, display=20347, dps=41.5, delay=1500, stats=[(AGI, 5), (STA, 5), (CRIT, 8)]),
    # Gilnid
    dict(id=910106, base=5199, name="Smelting Pants", ilvl=62, cls=CLS_ARMOR, sub=LEATHER, inv=LEGS,
         mat=8, sheath=0, display=1978, armor=215, stats=[(STA, 18), (AGI, 12), (DODGE, 10)]),
    dict(id=910107, base=1156, name="Lavishly Jeweled Ring", ilvl=62, cls=CLS_ARMOR, sub=MISC, inv=FINGER,
         mat=1, sheath=0, display=9839, stats=[(INT, 4), (STA, 3), (SPELL_POWER, 7), (HIT, 4)]),
    dict(id=910108, base=10797, name="Molten Edge", ilvl=62, cls=CLS_WEAPON, sub=SWORD_1H, inv=ONE_HAND,
         mat=1, sheath=3, display=20030, dps=41.5, delay=2400, stats=[(STR, 5), (STA, 5), (CRIT, 8)]),
    # Mr. Smite
    dict(id=910109, base=13166, name="Smite's Bulwark", ilvl=62, cls=CLS_ARMOR, sub=PLATE, inv=SHOULDERS,
         mat=6, sheath=0, display=23704, armor=552, stats=[(STR, 8), (STA, 14), (DEFENSE, 8)]),
    dict(id=910110, base=5202, name="Captain's Vestments", ilvl=62, cls=CLS_ARMOR, sub=CLOTH, inv=CHEST,
         mat=7, sheath=0, display=12803, armor=96, stats=[(INT, 11), (SPI, 9), (STA, 8), (SPELL_POWER, 15)]),
    dict(id=910111, base=7230, name="Smite's Mighty Hammer", ilvl=62, cls=CLS_WEAPON, sub=MACE_2H, inv=TWO_HAND,
         mat=2, sheath=1, display=19610, dps=53.9, delay=3500, stats=[(STR, 18), (AGI, 6), (STA, 10)]),
    # Captain Greenskin
    dict(id=910112, base=10403, name="Blackened Defias Belt", ilvl=62, cls=CLS_ARMOR, sub=LEATHER, inv=WAIST,
         mat=8, sheath=0, display=14389, armor=134, set=950, stats=[(AGI, 8), (STA, 6), (AP, 12)]),
    dict(id=910113, base=5201, name="Emberstone Staff", ilvl=62, cls=CLS_WEAPON, sub=STAFF, inv=TWO_HAND,
         mat=2, sheath=2, display=20340, dps=53.9, delay=3000,
         stats=[(INT, 9), (SPI, 5), (STA, 6), (SPELL_POWER, 13)]),
    dict(id=910114, base=5200, name="Impaling Harpoon", ilvl=62, cls=CLS_WEAPON, sub=POLEARM, inv=TWO_HAND,
         mat=1, sheath=2, display=5949, dps=53.9, delay=2400, stats=[(AGI, 16), (STA, 10), (HIT, 7)]),
    # Cookie
    dict(id=910115, base=10401, name="Blackened Defias Gloves", ilvl=62, cls=CLS_ARMOR, sub=LEATHER, inv=HANDS,
         mat=8, sheath=0, display=27946, armor=122, set=950, stats=[(AGI, 9), (STA, 7), (CRIT, 9)]),
    dict(id=910116, base=5198, name="Cookie's Stirring Rod", ilvl=62, cls=CLS_WEAPON, sub=WAND,
         inv=RANGED_RIGHT, mat=2, sheath=0, display=21011, dps=63.8, delay=1300,
         stats=[(INT, 2), (STA, 1), (SPELL_POWER, 4)]),
    dict(id=910117, base=5197, name="Cookie's Tenderizer", ilvl=62, cls=CLS_WEAPON, sub=MACE_1H, inv=ONE_HAND,
         mat=2, sheath=7, display=20953, dps=41.5, delay=2800, stats=[(STR, 5), (STA, 5), (CRIT, 8)]),
    # Edwin VanCleef
    dict(id=910118, base=10399, name="Blackened Defias Armor", ilvl=63, cls=CLS_ARMOR, sub=LEATHER, inv=CHEST,
         mat=8, sheath=0, display=9123, armor=181, set=950, stats=[(AGI, 16), (STA, 15), (CRIT, 11)]),
    dict(id=910119, base=10400, name="Blackened Defias Leggings", ilvl=63, cls=CLS_ARMOR, sub=LEATHER, inv=LEGS,
         mat=8, sheath=0, display=27947, armor=215, set=950, stats=[(AGI, 17), (STA, 14), (HIT, 9)]),
    dict(id=910120, base=5193, name="Cape of the Brotherhood", ilvl=63, cls=CLS_ARMOR, sub=CLOTH, inv=BACK,
         mat=7, sheath=0, display=22998, armor=45, stats=[(AGI, 5), (STA, 5), (AP, 9)]),
    dict(id=910121, base=5191, name="Cruel Barb", ilvl=63, cls=CLS_WEAPON, sub=SWORD_1H, inv=ONE_HAND,
         mat=1, sheath=3, display=7311, dps=41.5, delay=2800, stats=[(STR, 6), (STA, 5), (CRIT, 7)]),
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
    # --- Razorfen Kraul (heroic) ------------------------------------------------------------------------
    # Roogug
    dict(id=910181, base=6383, name="Forest Buckler", ilvl=61, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=18483, armor=2153, block=40,
         stats=[(INT, 13), (STA, 7)]),
    dict(id=910182, base=2034, name="Scholarly Robes", ilvl=61, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=12699, armor=96,
         stats=[(INT, 8), (SPI, 34)]),
    dict(id=910183, base=4438, name="Pugilist Bracers", ilvl=61, cls=CLS_ARMOR, sub=3, inv=9, mat=5, sheath=0,
         display=6977, armor=162,
         stats=[(STR, 17), (STA, 7)]),
    # Aggem Thorncurse
    dict(id=910184, base=6681, name="Thornspike", ilvl=61, cls=CLS_WEAPON, sub=15, inv=13, mat=1, sheath=3,
         display=20593, dps=41.5, delay=1700,
         stats=[(AGI, 18)]),
    # Death Speaker Jargba
    dict(id=910185, base=6682, name="Death Speaker Robes", ilvl=62, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=12858, armor=96,
         stats=[(STA, 4), (INT, 12), (SPI, 9), (CRIT, 17)]),
    dict(id=910186, base=6685, name="Death Speaker Mantle", ilvl=62, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=11473, armor=75,
         stats=[(INT, 22), (SPI, 9)]),
    dict(id=910187, base=2816, name="Death Speaker Scepter", ilvl=62, cls=CLS_WEAPON, sub=4, inv=21, mat=2, sheath=3,
         display=19669, dps=41.5, delay=2800,
         stats=[(SPI, 8)]),
    # Overlord Ramtusk
    dict(id=910188, base=6686, name="Tusken Helm", ilvl=62, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=15492, armor=337,
         stats=[(STR, 20), (AGI, 20)]),
    dict(id=910189, base=6687, name="Corpsemaker", ilvl=62, cls=CLS_WEAPON, sub=1, inv=17, mat=1, sheath=1,
         display=22217, dps=53.9, delay=3800,
         stats=[(STR, 22), (STA, 12)]),
    # Agathelos the Raging
    dict(id=910190, base=6691, name="Swinetusk Shank", ilvl=62, cls=CLS_WEAPON, sub=15, inv=13, mat=1, sheath=3,
         display=12880, dps=41.5, delay=1500,
         stats=[(STA, 11), (SPI, 7)]),
    dict(id=910191, base=6690, name="Ferine Leggings", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=17142, armor=215,
         stats=[(STR, 19), (AGI, 21)]),
    # Charlga Razorflank
    dict(id=910192, base=6694, name="Heart of Agamaggan", ilvl=63, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=18454, armor=2153, block=40,
         stats=[(SPI, 11), (STA, 9)]),
    dict(id=910193, base=6693, name="Agamaggan's Clutch", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=1,
         display=6486,
         stats=[(SPI, 12), (STA, 6)]),
    dict(id=910194, base=6692, name="Pronged Reaver", ilvl=63, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=25597, dps=41.5, delay=2400,
         stats=[(SPI, 8), (STR, 10)]),
    # --- Scarlet Monastery: Graveyard (heroic) ----------------------------------------------------------
    # Interrogator Vishas
    dict(id=910195, base=7683, name="Bloody Brass Knuckles", ilvl=62, cls=CLS_WEAPON, sub=13, inv=13, mat=1,
         sheath=7, display=15720, dps=41.5, delay=1600,
         stats=[(STR, 18)]),
    # Bloodmage Thalnos
    dict(id=910196, base=7684, name="Bloodmage Mantle", ilvl=63, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=15800, armor=75,
         stats=[(INT, 11), (SPI, 6), (CRIT, 14)]),
    # --- Scarlet Monastery: Library (heroic) ------------------------------------------------------------
    # Houndmaster Loksey
    dict(id=910197, base=7756, name="Dog Training Gloves", ilvl=62, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=15894, armor=122,
         stats=[(STR, 12), (AGI, 12)]),
    # Arcanist Doan
    dict(id=910198, base=7711, name="Robe of Doan", ilvl=63, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=12673, armor=96,
         stats=[(STA, 10), (SPI, 32)]),
    dict(id=910199, base=34227, name="Deadman's Hand", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=1, sheath=0,
         display=43407,
         stats=[(STA, 18)]),
    dict(id=910200, base=7712, name="Mantle of Doan", ilvl=63, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=4488, armor=75,
         stats=[(INT, 11), (SPI, 9), (HIT, 11)]),
    dict(id=910201, base=7713, name="Illusionary Rod", ilvl=63, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=15806, dps=53.9, delay=3400,
         stats=[(INT, 16), (STA, 7), (CRIT, 11)]),
    dict(id=910202, base=7714, name="Hypnotic Blade", ilvl=63, cls=CLS_WEAPON, sub=15, inv=21, mat=1, sheath=3,
         display=20318, dps=41.5, delay=1400,
         stats=[(INT, 6), (SPI, 2)]),
    # --- Scarlet Monastery: Armory (heroic) -------------------------------------------------------------
    # Herod
    dict(id=910203, base=7718, name="Herod's Shoulder", ilvl=63, cls=CLS_ARMOR, sub=3, inv=3, mat=5, sheath=0,
         display=15809, armor=311,
         stats=[(STR, 9), (STA, 22)]),
    dict(id=910204, base=7719, name="Raging Berserker's Helm", ilvl=63, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=15811, armor=337,
         stats=[(STA, 15), (STR, 24)]),
    dict(id=910205, base=10330, name="Scarlet Leggings", ilvl=63, cls=CLS_ARMOR, sub=3, inv=7, mat=5, sheath=0,
         display=3519, armor=348,
         stats=[(STR, 27), (STA, 13)]),
    # --- Scarlet Monastery: Cathedral (heroic) ----------------------------------------------------------
    # High Inquisitor Fairbanks
    dict(id=910206, base=19507, name="Inquisitor's Shawl", ilvl=61, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=32034, armor=75,
         stats=[(INT, 14), (SPELL_POWER, 17)]),
    dict(id=910207, base=19508, name="Branded Leather Bracers", ilvl=61, cls=CLS_ARMOR, sub=2, inv=9, mat=8,
         sheath=0, display=32036, armor=77,
         stats=[(STA, 6), (AP, 18)]),
    dict(id=910208, base=19509, name="Dusty Mail Boots", ilvl=61, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=32038, armor=266,
         stats=[(STA, 33)]),
    # Scarlet Commander Mograine
    dict(id=910209, base=7726, name="Aegis of the Scarlet Commander", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1,
         sheath=4, display=18751, armor=2153, block=40,
         stats=[(DEFENSE, 6), (STA, 7), (STR, 6)]),
    dict(id=910210, base=7723, name="Mograine's Might", ilvl=62, cls=CLS_WEAPON, sub=5, inv=17, mat=2, sheath=1,
         display=21252, dps=53.9, delay=2800,
         stats=[(HIT, 16), (STA, 18)]),
    dict(id=910211, base=7724, name="Gauntlets of Divinity", ilvl=62, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=16223, armor=242,
         stats=[(STA, 25)]),
    # High Inquisitor Whitemane
    dict(id=910212, base=7721, name="Hand of Righteousness", ilvl=63, cls=CLS_WEAPON, sub=4, inv=21, mat=2, sheath=3,
         display=19735, dps=41.5, delay=2700,
         stats=[(SPI, 8)]),
    dict(id=910213, base=7720, name="Whitemane's Chapeau", ilvl=63, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=16224, armor=81,
         stats=[(SPI, 15), (INT, 15), (STA, 9)]),
    dict(id=910214, base=7722, name="Triune Amulet", ilvl=63, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=6522,
         stats=[(INT, 8), (SPI, 8), (STA, 8)]),
    # --- Razorfen Downs (heroic) ------------------------------------------------------------------------
    # Tuten'kash
    dict(id=910215, base=10776, name="Silky Spider Cape", ilvl=61, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=22994, armor=45,
         stats=[(STA, 13), (SPI, 6)]),
    dict(id=910216, base=10775, name="Carapace of Tuten'kash", ilvl=61, cls=CLS_ARMOR, sub=4, inv=5, mat=6, sheath=0,
         display=28694, armor=706,
         stats=[(STA, 19), (STR, 13), (AGI, 10)]),
    # Mordresh Fire Eye
    dict(id=910217, base=10771, name="Deathmage Sash", ilvl=62, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=19910, armor=55,
         stats=[(INT, 16), (STA, 10)]),
    dict(id=910218, base=10769, name="Glowing Eye of Mordresh", ilvl=62, cls=CLS_ARMOR, sub=0, inv=2, mat=3,
         sheath=0, display=19785,
         stats=[(CRIT, 23)]),
    dict(id=910219, base=10770, name="Mordresh's Lifeless Skull", ilvl=62, cls=CLS_ARMOR, sub=0, inv=23, mat=-1,
         sheath=7, display=19786,
         stats=[(STA, 8)]),
    # Glutton
    dict(id=910220, base=10774, name="Fleshhide Shoulders", ilvl=62, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=28744, armor=196,
         stats=[(STR, 6), (STA, 18), (AGI, 7)]),
    # Plaguemaw the Rotting
    dict(id=910221, base=10760, name="Swine Fists", ilvl=62, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=28683, armor=122,
         stats=[(STR, 13), (AGI, 12)]),
    # Amnennar the Coldbringer
    dict(id=910222, base=10762, name="Robes of the Lich", ilvl=63, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=19953, armor=96,
         stats=[(INT, 11), (STA, 15), (CRIT, 16)]),
    dict(id=910223, base=10763, name="Icemetal Barbute", ilvl=63, cls=CLS_ARMOR, sub=4, inv=1, mat=6, sheath=0,
         display=28783, armor=584,
         stats=[(STR, 18), (AGI, 9), (STA, 12)]),
    dict(id=910224, base=10764, name="Deathchill Armor", ilvl=63, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=28710, armor=398,
         stats=[(STA, 10), (INT, 32)]),
    dict(id=910225, base=10765, name="Bonefingers", ilvl=63, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=28688, armor=122,
         stats=[(STA, 12), (INT, 12)]),
    dict(id=910226, base=10570, name="Manslayer", ilvl=63, cls=CLS_WEAPON, sub=1, inv=17, mat=1, sheath=1,
         display=28796, dps=53.9, delay=3200,
         stats=[(STA, 34)]),
    dict(id=910227, base=10573, name="Boneslasher", ilvl=63, cls=CLS_WEAPON, sub=8, inv=17, mat=1, sheath=1,
         display=20149, dps=53.9, delay=2700,
         stats=[(STA, 8), (STR, 19), (AGI, 6)]),
    # --- Uldaman (heroic) -------------------------------------------------------------------------------
    # Revelosh: no gear drops of its own (heroic: gold only)
    # Baelog
    dict(id=910228, base=9400, name="Baelog's Shortbow", ilvl=61, cls=CLS_WEAPON, sub=2, inv=15, mat=2, sheath=0,
         display=20553, dps=41.4, delay=2300,
         stats=[(HIT, 14)]),
    dict(id=910229, base=9401, name="Nordic Longshank", ilvl=61, cls=CLS_WEAPON, sub=7, inv=13, mat=1, sheath=3,
         display=7485, dps=41.5, delay=2200,
         stats=[(AGI, 11), (STA, 7)]),
    # Eric "The Swift"
    dict(id=910230, base=9398, name="Worn Running Boots", ilvl=61, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=18361, armor=166,
         stats=[(AGI, 18), (STA, 15)]),
    dict(id=910231, base=9394, name="Horned Viking Helmet", ilvl=61, cls=CLS_ARMOR, sub=4, inv=1, mat=6, sheath=0,
         display=21301, armor=584,
         stats=[(AGI, 16), (STA, 23)]),
    # Olaf
    dict(id=910232, base=9403, name="Battered Viking Shield", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=18824, armor=2153, block=40,
         stats=[(STA, 12), (DEFENSE, 8)]),
    dict(id=910233, base=9404, name="Olaf's All Purpose Shield", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1,
         sheath=4, display=18826, armor=2153, block=40,
         stats=[(STA, 20)]),
    # Ironaya
    dict(id=910234, base=9408, name="Ironshod Bludgeon", ilvl=62, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=20274, dps=53.9, delay=2500,
         stats=[(STR, 24), (STA, 10)]),
    dict(id=910235, base=9407, name="Stoneweaver Leggings", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=12345, armor=84,
         stats=[(SPI, 25), (STA, 15)]),
    # Obsidian Sentinel
    dict(id=910236, base=9431, name="Papal Fez", ilvl=62, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=18334, armor=81,
         stats=[(INT, 26), (SPI, 14)]),
    dict(id=910237, base=9384, name="Stonevault Shiv", ilvl=62, cls=CLS_WEAPON, sub=15, inv=13, mat=1, sheath=3,
         display=18264, dps=41.5, delay=1500,
         stats=[(AGI, 13), (STA, 5)]),
    dict(id=910238, base=9393, name="Beacon of Hope", ilvl=62, cls=CLS_ARMOR, sub=0, inv=23, mat=-1, sheath=7,
         display=11410,
         stats=[(SPI, 8)]),
    # Ancient Stone Keeper
    dict(id=910239, base=9411, name="Rockshard Pauldrons", ilvl=62, cls=CLS_ARMOR, sub=3, inv=3, mat=5, sheath=0,
         display=6480, armor=311,
         stats=[(STA, 25), (INT, 6)]),
    dict(id=910240, base=9383, name="Obsidian Cleaver", ilvl=62, cls=CLS_WEAPON, sub=1, inv=17, mat=1, sheath=1,
         display=18328, dps=53.9, delay=3300,
         stats=[(STA, 22), (STR, 7), (AGI, 6)]),
    dict(id=910241, base=9392, name="Annealed Blade", ilvl=62, cls=CLS_WEAPON, sub=7, inv=13, mat=1, sheath=3,
         display=18270, dps=41.5, delay=1800,
         stats=[(STR, 9), (STA, 9)]),
    # Galgann Firehammer
    dict(id=910242, base=11311, name="Emberscale Cape", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=28731, armor=45,
         stats=[(SPI, 8), (STA, 11)]),
    dict(id=910243, base=9419, name="Galgann's Firehammer", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=2, sheath=3,
         display=18312, dps=41.5, delay=2200,
         stats=[(STA, 18)]),
    dict(id=910244, base=11310, name="Flameseer Mantle", ilvl=62, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=5116, armor=75,
         stats=[(SPI, 31)]),
    # Grimlok
    dict(id=910245, base=9415, name="Grimlok's Tribal Vestments", ilvl=62, cls=CLS_ARMOR, sub=1, inv=5, mat=7,
         sheath=0, display=18347, armor=96,
         stats=[(STA, 14), (SPI, 20), (INT, 7)]),
    dict(id=910246, base=9416, name="Grimlok's Charge", ilvl=62, cls=CLS_WEAPON, sub=6, inv=17, mat=1, sheath=2,
         display=22233, dps=53.9, delay=2700,
         stats=[(AGI, 17), (STA, 17)]),
    dict(id=910247, base=9414, name="Oilskin Leggings", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=18434, armor=215,
         stats=[(AGI, 21), (STA, 19)]),
    # Archaedas
    dict(id=910248, base=9413, name="The Rockpounder", ilvl=63, cls=CLS_WEAPON, sub=5, inv=17, mat=2, sheath=1,
         display=19620, dps=53.9, delay=3700,
         stats=[(STR, 34)]),
    # --- Zul'Farrak (heroic) ----------------------------------------------------------------------------
    # Antu'sul
    dict(id=910249, base=9484, name="Spellshock Leggings", ilvl=61, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=22426, armor=84,
         stats=[(INT, 21), (STA, 19)]),
    dict(id=910250, base=9641, name="Lifeblood Amulet", ilvl=61, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=9854,
         stats=[(STA, 23)]),
    # Theka the Martyr
    dict(id=910251, base=2040, name="Troll Protector", ilvl=61, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=18399, armor=2153, block=40,
         stats=[(STA, 20)]),
    dict(id=910252, base=8106, name="Hibernal Armor", ilvl=61, cls=CLS_ARMOR, sub=1, inv=5, mat=7, sheath=0,
         display=16631, armor=96,
         stats=[(STA, 7), (SPI, 35)]),
    dict(id=910253, base=9480, name="Eyegouger", ilvl=61, cls=CLS_WEAPON, sub=6, inv=17, mat=1, sheath=2,
         display=22235, dps=53.9, delay=3000,
         stats=[(AGI, 24), (STR, 10)]),
    # Witch Doctor Zum'rah
    dict(id=910254, base=18083, name="Jumanza Grips", ilvl=61, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=30474, armor=80,
         stats=[(INT, 9), (SPI, 8), (STA, 8)]),
    dict(id=910255, base=18082, name="Zum'rah's Vexing Cane", ilvl=61, cls=CLS_WEAPON, sub=10, inv=17, mat=2,
         sheath=2, display=30472, dps=53.9, delay=2700,
         stats=[(INT, 17), (STA, 17)]),
    # Nekrum Gutchewer
    dict(id=910256, base=8134, name="Myrmidon's Defender", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=26120, armor=2153, block=40,
         stats=[(STA, 3), (AGI, 3), (SPI, 15)]),
    # Shadowpriest Sezz'ziz
    dict(id=910257, base=9470, name="Bad Mojo Mask", ilvl=62, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=18689, armor=81,
         stats=[(INT, 39)]),
    dict(id=910258, base=9473, name="Jinxed Hoodoo Skin", ilvl=62, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=18386, armor=181,
         stats=[(SPELL_POWER, 24), (INT, 8), (STA, 10)]),
    dict(id=910259, base=9474, name="Jinxed Hoodoo Kilt", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=18387, armor=215,
         stats=[(INT, 27), (SPELL_POWER, 13)]),
    # Sergeant Bly
    dict(id=910260, base=14825, name="Symbolic Crest", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=25134, armor=2153, block=40,
         stats=[(STA, 9), (STR, 5), (SPI, 5)]),
    dict(id=910261, base=2624, name="Thinking Cap", ilvl=62, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=15547, armor=81,
         stats=[(INT, 39)]),
    dict(id=910262, base=1624, name="Skullsplitter Helm", ilvl=62, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=15340, armor=337,
         stats=[(STA, 20), (AGI, 19)]),
    # Hydromancer Velratha
    dict(id=910263, base=9481, name="The Minotaur", ilvl=62, cls=CLS_WEAPON, sub=1, inv=17, mat=1, sheath=1,
         display=19309, dps=53.9, delay=3200,
         stats=[(STA, 22), (SPI, 5), (STR, 7)]),
    dict(id=910264, base=8119, name="Heraldic Breastplate", ilvl=62, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=28737, armor=181,
         stats=[(STR, 7), (STA, 35)]),
    # Gahz'rilla
    dict(id=910265, base=9469, name="Gahz'rilla Scale Armor", ilvl=62, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=18382, armor=398,
         stats=[(STA, 42)]),
    # Chief Ukorz Sandscalp
    dict(id=910266, base=9476, name="Big Bad Pauldrons", ilvl=63, cls=CLS_ARMOR, sub=4, inv=3, mat=6, sheath=0,
         display=18389, armor=552,
         stats=[(STR, 12), (STA, 12), (CRIT, 8)]),
    dict(id=910267, base=9479, name="Embrace of the Lycan", ilvl=63, cls=CLS_ARMOR, sub=2, inv=1, mat=8, sheath=0,
         display=18392, armor=162,
         stats=[(STA, 22), (CRIT, 7), (STR, 11)]),
    # --- Maraudon (heroic) ------------------------------------------------------------------------------
    # Noxxion
    dict(id=910268, base=17745, name="Noxious Shooter", ilvl=61, cls=CLS_WEAPON, sub=19, inv=26, mat=2, sheath=0,
         display=29924, dps=63.8, delay=1600,
         stats=[(STA, 5), (CRIT, 3)]),
    dict(id=910269, base=17746, name="Noxxion's Shackles", ilvl=61, cls=CLS_ARMOR, sub=4, inv=9, mat=6, sheath=0,
         display=29925, armor=287,
         stats=[(STA, 6), (STR, 18)]),
    # Razorlash
    dict(id=910270, base=17748, name="Vinerot Sandals", ilvl=61, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=29927, armor=64,
         stats=[(INT, 16), (SPI, 16)]),
    dict(id=910271, base=17749, name="Phytoskin Spaulders", ilvl=61, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=29928, armor=196,
         stats=[(AGI, 14), (STA, 9), (STR, 9)]),
    dict(id=910272, base=17751, name="Brusslehide Leggings", ilvl=61, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=29930, armor=215,
         stats=[(INT, 23), (STA, 17)]),
    # Lord Vyletongue
    dict(id=910273, base=17754, name="Infernal Trickster Leggings", ilvl=62, cls=CLS_ARMOR, sub=3, inv=7, mat=5,
         sheath=0, display=29934, armor=348,
         stats=[(AGI, 21), (INT, 9), (HIT, 9)]),
    dict(id=910274, base=17755, name="Satyrmane Sash", ilvl=62, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=14456, armor=55,
         stats=[(INT, 16), (STA, 10)]),
    # Celebras the Cursed
    dict(id=910275, base=17739, name="Grovekeeper's Drape", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=29916, armor=45,
         stats=[(STA, 10), (AGI, 9)]),
    dict(id=910276, base=17740, name="Soothsayer's Headdress", ilvl=62, cls=CLS_ARMOR, sub=2, inv=1, mat=8, sheath=0,
         display=29941, armor=162,
         stats=[(STA, 18), (INT, 21)]),
    # Landslide
    dict(id=910277, base=17736, name="Rockgrip Gauntlets", ilvl=62, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=29912, armor=242,
         stats=[(INT, 12), (STA, 12)]),
    dict(id=910278, base=17734, name="Helm of the Mountain", ilvl=62, cls=CLS_ARMOR, sub=4, inv=1, mat=6, sheath=0,
         display=29911, armor=584,
         stats=[(STA, 39)]),
    dict(id=910279, base=17737, name="Cloud Stone", ilvl=62, cls=CLS_ARMOR, sub=0, inv=23, mat=3, sheath=7,
         display=29914,
         stats=[(INT, 4), (SPI, 4)]),
    # Tinkerer Gizlock
    dict(id=910280, base=17718, name="Gizlock's Hypertech Buckler", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1,
         sheath=4, display=29896, armor=2153, block=40,
         stats=[(INT, 13), (STA, 7)]),
    dict(id=910281, base=17717, name="Megashot Rifle", ilvl=62, cls=CLS_WEAPON, sub=3, inv=26, mat=1, sheath=0,
         display=4427, dps=41.4, delay=1700,
         stats=[(HIT, 8)]),
    # Rotgrip
    dict(id=910282, base=17732, name="Rotgrip Mantle", ilvl=62, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=29908, armor=75,
         stats=[(INT, 19), (SPI, 12)]),
    dict(id=910283, base=17728, name="Albino Crocscale Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=30172, armor=166,
         stats=[(AGI, 22), (STA, 6), (HIT, 6)]),
    # Princess Theradras
    dict(id=910284, base=17714, name="Bracers of the Stone Princess", ilvl=63, cls=CLS_ARMOR, sub=3, inv=9, mat=5,
         sheath=0, display=29890, armor=162,
         stats=[(STA, 13), (INT, 11)]),
    dict(id=910285, base=17713, name="Blackstone Ring", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=23629,
         stats=[(STA, 18)]),
    dict(id=910286, base=17707, name="Gemshard Heart", ilvl=63, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=29842,
         stats=[(INT, 9), (STA, 9), (SPI, 5)]),
    dict(id=910287, base=17710, name="Charstone Dirk", ilvl=63, cls=CLS_WEAPON, sub=15, inv=13, mat=1, sheath=3,
         display=29872, dps=41.5, delay=1600,
         stats=[(INT, 18)]),
    dict(id=910288, base=17711, name="Elemental Rockridge Leggings", ilvl=63, cls=CLS_ARMOR, sub=4, inv=7, mat=6,
         sheath=0, display=29880, armor=618,
         stats=[(STA, 15), (STR, 17), (CRIT, 8)]),
    dict(id=910289, base=17715, name="Eye of Theradras", ilvl=63, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=29894, armor=81,
         stats=[(INT, 18), (STA, 12), (SPI, 10)]),
    # --- Sunken Temple (heroic) -------------------------------------------------------------------------
    # Atal'alarion
    dict(id=910290, base=10799, name="Headspike", ilvl=61, cls=CLS_WEAPON, sub=6, inv=17, mat=1, sheath=2,
         display=22242, dps=53.9, delay=3000,
         stats=[(STA, 19), (STR, 15)]),
    dict(id=910291, base=10798, name="Atal'alarion's Tusk Ring", ilvl=61, cls=CLS_ARMOR, sub=4, inv=6, mat=5,
         sheath=0, display=28640, armor=369,
         stats=[(STR, 18), (STA, 8)]),
    # Dreamscythe
    dict(id=910292, base=12465, name="Nightfall Drape", ilvl=61, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=22989, armor=45,
         stats=[(STA, 12), (DODGE, 7)]),
    dict(id=910293, base=12464, name="Bloodfire Talons", ilvl=61, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=28680, armor=122,
         stats=[(SPI, 9), (INT, 5), (STA, 10)]),
    dict(id=910294, base=12243, name="Smoldering Claw", ilvl=61, cls=CLS_WEAPON, sub=6, inv=17, mat=1, sheath=2,
         display=5290, dps=53.9, delay=2900,
         stats=[(STR, 34)]),
    # Weaver: shares the items above (910292, 910293, 910294)
    # Avatar of Hakkar
    dict(id=910295, base=10845, name="Warrior's Embrace", ilvl=62, cls=CLS_ARMOR, sub=4, inv=5, mat=6, sheath=0,
         display=19893, armor=706,
         stats=[(STA, 12), (AGI, 4), (DEFENSE, 26)]),
    dict(id=910296, base=10844, name="Spire of Hakkar", ilvl=62, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=20258, dps=53.9, delay=3400,
         stats=[(SPI, 17), (STA, 17)]),
    dict(id=910297, base=10838, name="Might of Hakkar", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=2, sheath=3,
         display=19869, dps=41.5, delay=2400,
         stats=[(STR, 12), (STA, 6)]),
    # Jammal'an the Prophet
    dict(id=910298, base=10806, name="Vestments of the Atal'ai Prophet", ilvl=62, cls=CLS_ARMOR, sub=1, inv=5, mat=7,
         sheath=0, display=19810, armor=96,
         stats=[(INT, 10), (SPI, 16), (CRIT, 16)]),
    dict(id=910299, base=10807, name="Kilt of the Atal'ai Prophet", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7,
         sheath=0, display=19812, armor=84,
         stats=[(SPI, 23), (INT, 5), (STA, 12)]),
    dict(id=910300, base=10808, name="Gloves of the Atal'ai Prophet", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7,
         sheath=0, display=19813, armor=80,
         stats=[(SPI, 11), (STA, 14)]),
    # Ogom the Wretched
    dict(id=910301, base=10804, name="Fist of the Damned", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=2, sheath=3,
         display=19892, dps=41.5, delay=1900,
         stats=[(STR, 18)]),
    dict(id=910302, base=10805, name="Eater of the Dead", ilvl=62, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=19127, dps=41.5, delay=2200,
         stats=[(STA, 18)]),
    # Morphaz: shares the items above (910292, 910293, 910294)
    # Hazzas: shares the items above (910292, 910293, 910294)
    # Shade of Eranikus
    dict(id=910303, base=10835, name="Crest of Supremacy", ilvl=63, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=19840, armor=2153, block=40,
         stats=[(STA, 10), (INT, 10)]),
    dict(id=910304, base=10829, name="The Dragon's Eye", ilvl=63, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=6494,
         stats=[(STA, 9), (SPI, 14)]),
    dict(id=910305, base=10837, name="Tooth of Eranikus", ilvl=63, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=19841, dps=41.5, delay=2400,
         stats=[(STR, 7), (HIT, 11)]),
    dict(id=910306, base=10833, name="Horns of Eranikus", ilvl=63, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=19838, armor=337,
         stats=[(STA, 24), (INT, 15)]),
    dict(id=910307, base=10836, name="Rod of Corrosion", ilvl=63, cls=CLS_WEAPON, sub=19, inv=26, mat=2, sheath=0,
         display=20788, dps=63.8, delay=1300,
         stats=[(CRIT, 8)]),
    # --- Blackrock Depths (heroic) ----------------------------------------------------------------------
    # Lord Roccor
    dict(id=910308, base=11631, name="Stoneshell Guard", ilvl=61, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=21613, armor=2153, block=40,
         stats=[(STR, 8), (STA, 12)]),
    dict(id=910309, base=22234, name="Mantle of Lost Hope", ilvl=61, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=34579, armor=75,
         stats=[(INT, 21), (STA, 10)]),
    dict(id=910310, base=11632, name="Earthslag Shoulders", ilvl=61, cls=CLS_ARMOR, sub=4, inv=3, mat=6, sheath=0,
         display=28725, armor=552,
         stats=[(STR, 12), (CRIT, 12), (STA, 7)]),
    # High Interrogator Gerstahn
    dict(id=910311, base=11624, name="Kentic Amice", ilvl=61, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=28788, armor=75,
         stats=[(INT, 17), (SPI, 8), (STA, 6)]),
    dict(id=910312, base=11625, name="Enthralled Sphere", ilvl=61, cls=CLS_ARMOR, sub=0, inv=23, mat=3, sheath=7,
         display=21595,
         stats=[(INT, 5), (STA, 3)]),
    dict(id=910313, base=11626, name="Blackveil Cape", ilvl=61, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=26278, armor=45,
         stats=[(STR, 6), (AGI, 13)]),
    # Houndmaster Grebmar
    dict(id=910314, base=11623, name="Spritecaster Cape", ilvl=61, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=26137, armor=45,
         stats=[(STA, 6), (INT, 6), (SPI, 7)]),
    dict(id=910315, base=11628, name="Houndmaster's Bow", ilvl=61, cls=CLS_WEAPON, sub=2, inv=15, mat=2, sheath=0,
         display=28780, dps=41.4, delay=1800,
         stats=[(AGI, 14)]),
    dict(id=910316, base=11627, name="Fleetfoot Greaves", ilvl=61, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=28658, armor=266,
         stats=[(AGI, 21), (INT, 6), (STA, 7)]),
    # Gorosh the Dervish
    dict(id=910317, base=22257, name="Bloodclot Band", ilvl=61, cls=CLS_ARMOR, sub=0, inv=11, mat=4, sheath=0,
         display=31655,
         stats=[(INT, 6), (STA, 6), (SPI, 5)]),
    dict(id=910318, base=11726, name="Savage Gladiator Chain", ilvl=61, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=28724, armor=398,
         stats=[(STA, 20), (AGI, 22)]),
    dict(id=910319, base=22271, name="Leggings of Frenzied Magic", ilvl=61, cls=CLS_ARMOR, sub=2, inv=7, mat=8,
         sheath=0, display=34710, armor=215,
         stats=[(INT, 20), (STA, 20)]),
    # Grizzle
    dict(id=910320, base=11703, name="Stonewall Girdle", ilvl=61, cls=CLS_ARMOR, sub=4, inv=6, mat=6, sheath=0,
         display=28686, armor=369,
         stats=[(STA, 18), (DEFENSE, 8)]),
    dict(id=910321, base=11722, name="Dregmetal Spaulders", ilvl=61, cls=CLS_ARMOR, sub=3, inv=3, mat=5, sheath=0,
         display=28721, armor=311,
         stats=[(STA, 9), (INT, 22)]),
    dict(id=910322, base=11702, name="Grizzle's Skinner", ilvl=61, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=28765, dps=41.5, delay=2400,
         stats=[(STR, 8), (STA, 5), (AGI, 6)]),
    # Eviscerator
    dict(id=910323, base=11730, name="Savage Gladiator Grips", ilvl=61, cls=CLS_ARMOR, sub=3, inv=10, mat=5,
         sheath=0, display=28723, armor=242,
         stats=[(AGI, 6), (INT, 9), (STA, 10)]),
    dict(id=910324, base=11679, name="Rubicund Armguards", ilvl=61, cls=CLS_ARMOR, sub=3, inv=9, mat=5, sheath=0,
         display=28820, armor=162,
         stats=[(AGI, 15), (STA, 9)]),
    dict(id=910325, base=11685, name="Splinthide Shoulders", ilvl=61, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=28704, armor=196,
         stats=[(STR, 9), (STA, 8), (AGI, 8), (HIT, 6)]),
    # Ok'thor the Breaker
    dict(id=910326, base=11662, name="Ban'thok Sash", ilvl=61, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=28642, armor=55,
         stats=[(STA, 12), (INT, 14)]),
    dict(id=910327, base=11728, name="Savage Gladiator Leggings", ilvl=61, cls=CLS_ARMOR, sub=3, inv=7, mat=5,
         sheath=0, display=21694, armor=348,
         stats=[(STA, 21), (AGI, 19)]),
    dict(id=910328, base=11665, name="Ogreseer Fists", ilvl=61, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=17263, armor=122,
         stats=[(STA, 9), (INT, 9), (SPI, 7)]),
    # Anub'shiah
    dict(id=910329, base=11677, name="Graverot Cape", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=28381, armor=45,
         stats=[(STA, 19)]),
    dict(id=910330, base=11675, name="Shadefiend Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=18979, armor=166,
         stats=[(STR, 10), (STA, 13), (AGI, 11)]),
    dict(id=910331, base=11678, name="Carapace of Anub'shiah", ilvl=62, cls=CLS_ARMOR, sub=4, inv=5, mat=6, sheath=0,
         display=26654, armor=706,
         stats=[(STA, 21), (STR, 10), (AGI, 10)]),
    # Hedrum the Creeper
    dict(id=910332, base=11634, name="Silkweb Gloves", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=28741, armor=80,
         stats=[(STA, 13), (INT, 12)]),
    dict(id=910333, base=11633, name="Spiderfang Carapace", ilvl=62, cls=CLS_ARMOR, sub=4, inv=5, mat=6, sheath=0,
         display=21898, armor=706,
         stats=[(STR, 17), (STA, 13), (HIT, 12)]),
    dict(id=910334, base=11729, name="Savage Gladiator Helm", ilvl=62, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=28826, armor=337,
         stats=[(STA, 12), (AGI, 27)]),
    # Lord Incendius: no fixed-stat gear drops of its own (heroic: gold only)
    # Fineous Darkvire
    dict(id=910335, base=11839, name="Chief Architect's Monocle", ilvl=62, cls=CLS_ARMOR, sub=1, inv=1, mat=7,
         sheath=0, display=21839, armor=81,
         stats=[(INT, 13), (STA, 8), (CRIT, 18)]),
    dict(id=910336, base=22223, name="Foreman's Head Protector", ilvl=62, cls=CLS_ARMOR, sub=4, inv=1, mat=6,
         sheath=0, display=34564, armor=584,
         stats=[(STR, 13), (STA, 12), (AGI, 14)]),
    dict(id=910337, base=11841, name="Senior Designer's Pantaloons", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7,
         sheath=0, display=28720, armor=84,
         stats=[(SPI, 22), (STA, 10), (INT, 8)]),
    # Bael'Gar
    dict(id=910338, base=11807, name="Sash of the Burning Heart", ilvl=62, cls=CLS_ARMOR, sub=1, inv=6, mat=7,
         sheath=0, display=28825, armor=55,
         stats=[(INT, 9), (STA, 9), (CRIT, 9)]),
    dict(id=910339, base=11802, name="Lavacrest Leggings", ilvl=62, cls=CLS_ARMOR, sub=4, inv=7, mat=6, sheath=0,
         display=19843, armor=618,
         stats=[(STR, 28), (STA, 12)]),
    dict(id=910340, base=11803, name="Force of Magma", ilvl=62, cls=CLS_WEAPON, sub=5, inv=17, mat=2, sheath=1,
         display=21793, dps=53.9, delay=3200,
         stats=[(STR, 34)]),
    # General Angerforge
    dict(id=910341, base=11816, name="Angerforge's Battle Axe", ilvl=62, cls=CLS_WEAPON, sub=1, inv=17, mat=1,
         sheath=1, display=22212, dps=53.9, delay=2600,
         stats=[(STR, 24), (STA, 10)]),
    dict(id=910342, base=11820, name="Royal Decorated Armor", ilvl=62, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=28819, armor=398,
         stats=[(STR, 7), (STA, 24), (AGI, 11)]),
    dict(id=910343, base=11821, name="Warstrife Leggings", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=28623, armor=215,
         stats=[(STR, 8), (STA, 11), (AGI, 21)]),
    # Golem Lord Argelmach
    dict(id=910344, base=11822, name="Omnicast Boots", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=28660, armor=64,
         stats=[(INT, 20), (STA, 13)]),
    dict(id=910345, base=11669, name="Naglering", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=9837, armor=50,
         stats=[(STA, 18)]),
    dict(id=910346, base=11823, name="Luminary Kilt", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=28728, armor=215,
         stats=[(INT, 22), (SPI, 9), (STA, 9)]),
    # Hurley Blackbreath
    dict(id=910347, base=22275, name="Firemoss Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=6762, armor=166,
         stats=[(INT, 23), (STA, 10)]),
    dict(id=910348, base=18043, name="Coal Miner Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=2373, armor=166,
         stats=[(STA, 8), (STR, 9), (AGI, 16)]),
    dict(id=910349, base=18044, name="Hurley's Tankard", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=2, sheath=7,
         display=30436, dps=41.5, delay=2700,
         stats=[(STA, 13), (AGI, 5)]),
    # Phalanx
    dict(id=910350, base=11745, name="Fists of Phalanx", ilvl=62, cls=CLS_ARMOR, sub=4, inv=10, mat=6, sheath=0,
         display=28740, armor=429,
         stats=[(STR, 17), (STA, 8)]),
    dict(id=910351, base=22212, name="Golem Fitted Pauldrons", ilvl=62, cls=CLS_ARMOR, sub=3, inv=3, mat=5, sheath=0,
         display=34558, armor=311,
         stats=[(AGI, 13), (STA, 18)]),
    dict(id=910352, base=11743, name="Rockfist", ilvl=62, cls=CLS_WEAPON, sub=13, inv=13, mat=1, sheath=7,
         display=21714, dps=41.5, delay=1400,
         stats=[(CRIT, 18)]),
    # Ribbly Screwspigot: no fixed-stat gear drops of its own (heroic: gold only)
    # Plugger Spazzring
    dict(id=910353, base=12793, name="Mixologist's Tunic", ilvl=62, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=23266, armor=181,
         stats=[(STR, 16), (STA, 16), (AGI, 10)]),
    # Ambassador Flamelash
    dict(id=910354, base=11812, name="Cape of the Fire Salamander", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7,
         sheath=0, display=22997, armor=45,
         stats=[(STA, 19)]),
    dict(id=910355, base=11814, name="Molten Fists", ilvl=62, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=21805, armor=242,
         stats=[(INT, 9), (STA, 9), (AGI, 8)]),
    dict(id=910356, base=11808, name="Circle of Flame", ilvl=62, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=28268, armor=81,
         stats=[(STA, 39)]),
    # Magmus
    dict(id=910357, base=11935, name="Magmus Stone", ilvl=62, cls=CLS_ARMOR, sub=0, inv=23, mat=3, sheath=7,
         display=28795,
         stats=[(SPI, 3), (STA, 5)]),
    dict(id=910358, base=11746, name="Golem Skull Helm", ilvl=62, cls=CLS_ARMOR, sub=4, inv=1, mat=6, sheath=0,
         display=21717, armor=584,
         stats=[(STA, 20), (STR, 20)]),
    dict(id=910359, base=22208, name="Lavastone Hammer", ilvl=62, cls=CLS_WEAPON, sub=5, inv=17, mat=1, sheath=1,
         display=34556, dps=53.9, delay=3400,
         stats=[(STA, 10), (CRIT, 12), (STR, 12)]),
    # Princess Moira Bronzebeard
    dict(id=910360, base=12554, name="Hands of the Exalted Herald", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7,
         sheath=0, display=28771, armor=80,
         stats=[(INT, 13), (SPI, 12)]),
    dict(id=910361, base=12553, name="Swiftwalker Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=28670, armor=166,
         stats=[(AGI, 22), (STA, 7), (STR, 4)]),
    dict(id=910362, base=12556, name="High Priestess Boots", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=22779, armor=64,
         stats=[(STA, 24), (SPI, 9)]),
    # Emperor Dagran Thaurissan
    dict(id=910363, base=11924, name="Robes of the Royal Crown", ilvl=63, cls=CLS_ARMOR, sub=1, inv=20, mat=7,
         sheath=0, display=28814, armor=96,
         stats=[(SPI, 10), (INT, 12), (STA, 19)]),
    dict(id=910364, base=11933, name="Imperial Jewel", ilvl=63, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=28784,
         stats=[(STA, 23)]),
    dict(id=910365, base=11928, name="Thaurissan's Royal Scepter", ilvl=63, cls=CLS_ARMOR, sub=0, inv=23, mat=3,
         sheath=3, display=21962,
         stats=[(SPI, 4), (INT, 2), (STA, 2)]),
    dict(id=910366, base=11930, name="The Emperor's New Cape", ilvl=63, cls=CLS_ARMOR, sub=1, inv=16, mat=7,
         sheath=0, display=21965, armor=45,
         stats=[(STA, 13), (AGI, 6)]),
    dict(id=910367, base=11932, name="Guiding Stave of Wisdom", ilvl=63, cls=CLS_WEAPON, sub=10, inv=17, mat=2,
         sheath=2, display=21968, dps=53.9, delay=3300,
         stats=[(SPI, 16), (STA, 18)]),
    dict(id=910368, base=22204, name="Wristguards of Renown", ilvl=63, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=34549, armor=77,
         stats=[(STR, 7), (STA, 8), (AGI, 8)]),
    # --- Blackrock Spire: Lower (heroic) ----------------------------------------------------------------
    # Highlord Omokk
    dict(id=910369, base=13168, name="Plate of the Shaman King", ilvl=61, cls=CLS_ARMOR, sub=4, inv=5, mat=6,
         sheath=0, display=23559, armor=706,
         stats=[(STA, 15), (STR, 12), (INT, 15)]),
    dict(id=910370, base=13166, name="Slamshot Shoulders", ilvl=61, cls=CLS_ARMOR, sub=4, inv=3, mat=6, sheath=0,
         display=23704, armor=552,
         stats=[(STA, 31)]),
    dict(id=910371, base=13167, name="Fist of Omokk", ilvl=61, cls=CLS_WEAPON, sub=5, inv=17, mat=2, sheath=1,
         display=25180, dps=53.9, delay=3300,
         stats=[(STR, 24), (STA, 10)]),
    # Shadow Hunter Vosh'gajin
    dict(id=910372, base=12626, name="Funeral Cuffs", ilvl=61, cls=CLS_ARMOR, sub=1, inv=9, mat=7, sheath=0,
         display=14618, armor=39,
         stats=[(INT, 18), (SPI, 6)]),
    dict(id=910373, base=13255, name="Trueaim Gauntlets", ilvl=61, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=23849, armor=242,
         stats=[(CRIT, 17), (HIT, 8)]),
    dict(id=910374, base=13257, name="Demonic Runed Spaulders", ilvl=61, cls=CLS_ARMOR, sub=2, inv=3, mat=8,
         sheath=0, display=23852, armor=196,
         stats=[(HIT, 11), (STA, 10), (AGI, 10)]),
    # War Master Voone
    dict(id=910375, base=13179, name="Brazecore Armguards", ilvl=61, cls=CLS_ARMOR, sub=3, inv=9, mat=5, sheath=0,
         display=23730, armor=162,
         stats=[(INT, 13), (STA, 11)]),
    dict(id=910376, base=28972, name="Flightblade Throwing Axe", ilvl=61, cls=CLS_WEAPON, sub=16, inv=25, mat=1,
         sheath=0, display=23723, dps=41.4, delay=2200,
         stats=[(AGI, 10), (STA, 8)]),
    dict(id=910377, base=13177, name="Talisman of Evasion", ilvl=61, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=6494,
         stats=[(AGI, 23)]),
    # Mother Smolderweb
    dict(id=910378, base=13244, name="Gilded Gauntlets", ilvl=62, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=23827, armor=242,
         stats=[(STA, 12), (INT, 13)]),
    dict(id=910379, base=16715, name="Wildheart Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=29981, armor=166,
         stats=[(SPI, 16), (STA, 9), (INT, 8)]),
    # Urok Doomhowl
    dict(id=910380, base=13259, name="Ribsteel Footguards", ilvl=62, cls=CLS_ARMOR, sub=4, inv=8, mat=6, sheath=0,
         display=23856, armor=472,
         stats=[(STR, 9), (STA, 15), (AGI, 9)]),
    dict(id=910381, base=22232, name="Marksman's Girdle", ilvl=62, cls=CLS_ARMOR, sub=3, inv=6, mat=5, sheath=0,
         display=34577, armor=208,
         stats=[(AGI, 26)]),
    # Quartermaster Zigris
    dict(id=910382, base=13253, name="Hands of Power", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=23846, armor=80,
         stats=[(SPI, 12), (INT, 12)]),
    dict(id=910383, base=13252, name="Cloudrunner Girdle", ilvl=62, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=23844, armor=134,
         stats=[(AGI, 13), (STR, 13)]),
    # Halycon
    dict(id=910384, base=13211, name="Slashclaw Bracers", ilvl=62, cls=CLS_ARMOR, sub=3, inv=9, mat=5, sheath=0,
         display=23769, armor=162,
         stats=[(SPI, 7), (AGI, 8), (STA, 8)]),
    dict(id=910385, base=13212, name="Halycon's Spiked Collar", ilvl=62, cls=CLS_ARMOR, sub=0, inv=2, mat=3,
         sheath=0, display=23766,
         stats=[(STA, 23)]),
    dict(id=910386, base=22313, name="Ironweave Bracers", ilvl=62, cls=CLS_ARMOR, sub=1, inv=9, mat=7, sheath=0,
         display=34793, armor=39,
         stats=[(STA, 15), (INT, 9)]),
    # Gizrul the Slavener
    dict(id=910387, base=13205, name="Rhombeard Protector", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=23750, armor=2153, block=40,
         stats=[(SPI, 8), (INT, 12)]),
    dict(id=910388, base=13206, name="Wolfshear Leggings", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=23753, armor=84,
         stats=[(SPI, 33), (STA, 7)]),
    dict(id=910389, base=13208, name="Bleak Howler Armguards", ilvl=62, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=23760, armor=77,
         stats=[(SPI, 15), (INT, 9)]),
    # Overlord Wyrmthalak
    dict(id=910390, base=13161, name="Trindlehaven Staff", ilvl=63, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=23673, dps=53.9, delay=2100,
         stats=[(INT, 23), (STA, 11)]),
    dict(id=910391, base=13162, name="Reiver Claws", ilvl=63, cls=CLS_ARMOR, sub=4, inv=10, mat=6, sheath=0,
         display=23675, armor=429,
         stats=[(STA, 16), (STR, 9)]),
    dict(id=910392, base=13163, name="Relentless Scythe", ilvl=63, cls=CLS_WEAPON, sub=8, inv=17, mat=1, sheath=1,
         display=23683, dps=53.9, delay=3300,
         stats=[(AGI, 8), (STR, 19), (STA, 8)]),
    dict(id=910393, base=16679, name="Beaststalker's Mantle", ilvl=63, cls=CLS_ARMOR, sub=3, inv=3, mat=5, sheath=0,
         display=31409, armor=311,
         stats=[(STA, 15), (AGI, 7), (INT, 6), (SPI, 3)]),
    # --- Blackrock Spire: Upper (heroic) ----------------------------------------------------------------
    # Pyroguard Emberseer
    dict(id=910394, base=16672, name="Gauntlets of Elements", ilvl=61, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=31414, armor=242,
         stats=[(SPI, 10), (INT, 6), (STR, 6), (STA, 3)]),
    dict(id=910395, base=12929, name="Emberfury Talisman", ilvl=61, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=9658,
         stats=[(STA, 9), (STR, 6), (HIT, 8)]),
    # Solakar Flamewreath
    dict(id=910396, base=12589, name="Dustfeather Sash", ilvl=61, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=21796, armor=55,
         stats=[(INT, 14), (STA, 12)]),
    dict(id=910397, base=12603, name="Nightbrace Tunic", ilvl=61, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=8725, armor=181,
         stats=[(AGI, 21), (STA, 14), (HIT, 7)]),
    dict(id=910398, base=12606, name="Crystallized Girdle", ilvl=61, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=22837, armor=134,
         stats=[(STA, 5), (INT, 16), (SPI, 5)]),
    # Goraluk Anvilcrack
    dict(id=910399, base=18048, name="Mastersmith's Hammer", ilvl=61, cls=CLS_WEAPON, sub=4, inv=21, mat=2, sheath=3,
         display=30440, dps=41.5, delay=2400,
         stats=[(INT, 8)]),
    dict(id=910400, base=13498, name="Handcrafted Mastersmith Leggings", ilvl=61, cls=CLS_ARMOR, sub=4, inv=7, mat=6,
         sheath=0, display=24162, armor=618,
         stats=[(STR, 28), (STA, 12)]),
    dict(id=910401, base=13502, name="Handcrafted Mastersmith Girdle", ilvl=61, cls=CLS_ARMOR, sub=4, inv=6, mat=6,
         sheath=0, display=24164, armor=369,
         stats=[(STR, 9), (STA, 8), (AGI, 8)]),
    # Gyth
    dict(id=910402, base=16669, name="Pauldrons of Elements", ilvl=62, cls=CLS_ARMOR, sub=3, inv=3, mat=5, sheath=0,
         display=30925, armor=311,
         stats=[(INT, 11), (STA, 11), (SPI, 5), (STR, 5)]),
    # Warchief Rend Blackhand
    dict(id=910403, base=18102, name="Dragonrider Boots", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=14617, armor=64,
         stats=[(INT, 25), (STA, 8)]),
    dict(id=910404, base=12940, name="Dal'Rend's Sacred Charge", ilvl=62, cls=CLS_WEAPON, sub=7, inv=21, mat=1,
         sheath=3, display=25648, dps=41.5, delay=2800,
         stats=[(STR, 8)]),
    dict(id=910405, base=12587, name="Eye of Rend", ilvl=62, cls=CLS_ARMOR, sub=2, inv=1, mat=8, sheath=0,
         display=22794, armor=162,
         stats=[(STA, 14), (STR, 25)]),
    # The Beast
    dict(id=910406, base=12967, name="Bloodmoon Cloak", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=23553, armor=45,
         stats=[(STA, 5), (INT, 3), (CRIT, 11)]),
    dict(id=910407, base=12964, name="Tristam Legguards", ilvl=62, cls=CLS_ARMOR, sub=3, inv=7, mat=5, sheath=0,
         display=23548, armor=348,
         stats=[(STA, 14), (AGI, 26)]),
    dict(id=910408, base=12963, name="Blademaster Leggings", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=23547, armor=215,
         stats=[(AGI, 33), (STA, 7)]),
    # Mor Grayhoof
    dict(id=910409, base=22306, name="Ironweave Belt", ilvl=62, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=34790, armor=55,
         stats=[(STA, 16), (INT, 10)]),
    dict(id=910410, base=22325, name="Belt of the Trickster", ilvl=62, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=14389, armor=134,
         stats=[(AGI, 18), (STA, 8)]),
    dict(id=910411, base=22319, name="Tome of Divine Right", ilvl=62, cls=CLS_ARMOR, sub=0, inv=23, mat=8, sheath=7,
         display=34802,
         stats=[(INT, 4), (STA, 4)]),
    # Lord Valthalak
    dict(id=910412, base=22336, name="Draconian Aegis of the Legion", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1,
         sheath=4, display=18790, armor=2153, block=40,
         stats=[(STA, 20)]),
    dict(id=910413, base=22302, name="Ironweave Cowl", ilvl=62, cls=CLS_ARMOR, sub=1, inv=1, mat=7, sheath=0,
         display=34781, armor=81,
         stats=[(STA, 24), (INT, 15)]),
    dict(id=910414, base=22339, name="Rune Band of Wizardry", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=31616,
         stats=[(STA, 18)]),
    # General Drakkisath
    dict(id=910415, base=12602, name="Draconian Deflector", ilvl=63, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=23419, armor=2153, block=40,
         stats=[(STA, 20)]),
    dict(id=910416, base=16666, name="Vest of Elements", ilvl=63, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=31416, armor=398,
         stats=[(INT, 16), (SPI, 16), (STA, 10)]),
    dict(id=910417, base=16721, name="Shadowcraft Tunic", ilvl=63, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=28160, armor=181,
         stats=[(AGI, 21), (STA, 11), (HIT, 10)]),
    dict(id=910418, base=16674, name="Beaststalker's Tunic", ilvl=63, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=31402, armor=398,
         stats=[(AGI, 11), (STA, 12), (INT, 10), (SPI, 5), (STR, 4)]),
    dict(id=910419, base=16688, name="Magister's Robes", ilvl=63, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=29591, armor=96,
         stats=[(INT, 27), (SPI, 7), (STA, 8)]),
    dict(id=910420, base=16690, name="Devout Robe", ilvl=63, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=30422, armor=96,
         stats=[(INT, 19), (SPI, 12), (STA, 10)]),
    # --- Dire Maul: East (heroic) -----------------------------------------------------------------------
    # Pusillin: no fixed-stat gear drops of its own (heroic: gold only)
    # Lethtendris
    dict(id=910421, base=18311, name="Quel'dorei Channeling Rod", ilvl=61, cls=CLS_WEAPON, sub=10, inv=17, mat=2,
         sheath=2, display=28511, dps=53.9, delay=2800,
         stats=[(INT, 18), (STA, 8), (SPI, 8)]),
    dict(id=910422, base=18302, name="Band of Vigor", ilvl=61, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=30661,
         stats=[(STR, 7), (STA, 6), (AGI, 6)]),
    dict(id=910423, base=18325, name="Felhide Cap", ilvl=61, cls=CLS_ARMOR, sub=2, inv=1, mat=8, sheath=0,
         display=30685, armor=162,
         stats=[(AGI, 23), (STA, 16)]),
    # Hydrospawn
    dict(id=910424, base=18317, name="Tempest Talisman", ilvl=62, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=9853,
         stats=[(INT, 12), (SPI, 11)]),
    dict(id=910425, base=18305, name="Breakwater Legguards", ilvl=62, cls=CLS_ARMOR, sub=4, inv=7, mat=6, sheath=0,
         display=30671, armor=618,
         stats=[(STR, 40)]),
    dict(id=910426, base=18322, name="Waterspout Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=6779, armor=166,
         stats=[(INT, 16), (SPI, 16)]),
    # Zevrim Thornhoof
    dict(id=910427, base=18306, name="Gloves of Shadowy Mist", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7,
         sheath=0, display=30669, armor=80,
         stats=[(STA, 25)]),
    dict(id=910428, base=18313, name="Helm of Awareness", ilvl=62, cls=CLS_ARMOR, sub=4, inv=1, mat=6, sheath=0,
         display=41372, armor=584,
         stats=[(STA, 39)]),
    dict(id=910429, base=18323, name="Satyr's Bow", ilvl=62, cls=CLS_WEAPON, sub=2, inv=15, mat=2, sheath=0,
         display=30683, dps=41.4, delay=2400,
         stats=[(AGI, 14)]),
    # Isalien
    dict(id=910430, base=22304, name="Ironweave Gloves", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=34789, armor=80,
         stats=[(STA, 15), (INT, 10)]),
    dict(id=910431, base=22314, name="Huntsman's Harpoon", ilvl=62, cls=CLS_WEAPON, sub=6, inv=17, mat=1, sheath=1,
         display=34794, dps=53.9, delay=3600,
         stats=[(AGI, 34)]),
    dict(id=910432, base=22315, name="Hammer of Revitalization", ilvl=62, cls=CLS_WEAPON, sub=4, inv=21, mat=2,
         sheath=3, display=6798, dps=41.5, delay=2700,
         stats=[(STA, 8)]),
    # Alzzin the Wildshaper
    dict(id=910433, base=18309, name="Gloves of Restoration", ilvl=63, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=30672, armor=122,
         stats=[(STA, 13), (INT, 12)]),
    dict(id=910434, base=18310, name="Fiendish Machete", ilvl=63, cls=CLS_WEAPON, sub=7, inv=13, mat=1, sheath=3,
         display=30673, dps=41.5, delay=2400,
         stats=[(AGI, 18)]),
    dict(id=910435, base=18312, name="Energized Chestplate", ilvl=63, cls=CLS_ARMOR, sub=4, inv=5, mat=6, sheath=0,
         display=30675, armor=706,
         stats=[(STR, 12), (STA, 19), (INT, 11)]),
    dict(id=910436, base=18314, name="Ring of Demonic Guile", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=24646,
         stats=[(INT, 18)]),
    dict(id=910437, base=18315, name="Ring of Demonic Potency", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=5,
         sheath=0, display=28812,
         stats=[(STA, 18)]),
    dict(id=910438, base=18318, name="Merciful Greaves", ilvl=63, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=30679, armor=266,
         stats=[(INT, 16), (STA, 16)]),
    # --- Dire Maul: West (heroic) -----------------------------------------------------------------------
    # Tendris Warpwood
    dict(id=910439, base=18353, name="Stoneflower Staff", ilvl=61, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=30711, dps=53.9, delay=3000,
         stats=[(INT, 34)]),
    dict(id=910440, base=18390, name="Tanglemoss Leggings", ilvl=61, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=18935, armor=215,
         stats=[(INT, 18), (SPI, 12), (STA, 11)]),
    dict(id=910441, base=18393, name="Warpwood Binding", ilvl=61, cls=CLS_ARMOR, sub=3, inv=6, mat=2, sheath=0,
         display=30751, armor=208,
         stats=[(AGI, 13), (INT, 8), (STA, 5)]),
    # Illyanna Ravenoak
    dict(id=910442, base=18386, name="Padre's Trousers", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=21964, armor=84,
         stats=[(INT, 40)]),
    dict(id=910443, base=18347, name="Well Balanced Axe", ilvl=62, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=30699, dps=41.5, delay=1900,
         stats=[(AGI, 18)]),
    dict(id=910444, base=18349, name="Gauntlets of Accuracy", ilvl=62, cls=CLS_ARMOR, sub=3, inv=10, mat=5, sheath=0,
         display=30702, armor=242,
         stats=[(AGI, 25)]),
    # Magister Kalendris
    dict(id=910445, base=18397, name="Elder Magus Pendant", ilvl=62, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=9859,
         stats=[(INT, 10), (SPI, 7), (STA, 6)]),
    dict(id=910446, base=18374, name="Flamescarred Shoulders", ilvl=62, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=18971, armor=196,
         stats=[(AGI, 11), (STR, 11), (STA, 10)]),
    # Immol'thar
    dict(id=910447, base=18379, name="Odious Greaves", ilvl=62, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=30736, armor=266,
         stats=[(STA, 22), (INT, 11)]),
    dict(id=910448, base=18372, name="Blade of the New Moon", ilvl=62, cls=CLS_WEAPON, sub=15, inv=13, mat=1,
         sheath=3, display=30724, dps=41.5, delay=1400,
         stats=[(STA, 18)]),
    dict(id=910449, base=18377, name="Quickdraw Gloves", ilvl=62, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=30729, armor=122,
         stats=[(AGI, 9), (STR, 8), (STA, 8)]),
    # Prince Tortheldrin
    dict(id=910450, base=18373, name="Chestplate of Tranquility", ilvl=63, cls=CLS_ARMOR, sub=2, inv=5, mat=8,
         sheath=0, display=17099, armor=181,
         stats=[(INT, 23), (SPI, 7), (STA, 12)]),
    dict(id=910451, base=18375, name="Bracers of the Eclipse", ilvl=63, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=30727, armor=77,
         stats=[(AGI, 13), (STA, 11)]),
    dict(id=910452, base=18376, name="Timeworn Mace", ilvl=63, cls=CLS_WEAPON, sub=4, inv=13, mat=1, sheath=3,
         display=30728, dps=41.5, delay=2200,
         stats=[(STR, 7), (STA, 11)]),
    dict(id=910453, base=18378, name="Silvermoon Leggings", ilvl=63, cls=CLS_ARMOR, sub=3, inv=7, mat=5, sheath=0,
         display=30730, armor=348,
         stats=[(INT, 13), (SPI, 8), (STA, 13), (AGI, 5)]),
    dict(id=910454, base=18380, name="Eldritch Reinforced Legplates", ilvl=63, cls=CLS_ARMOR, sub=4, inv=7, mat=6,
         sheath=0, display=30737, armor=618,
         stats=[(STR, 14), (STA, 18), (AGI, 8)]),
    dict(id=910455, base=18388, name="Stoneshatter", ilvl=63, cls=CLS_WEAPON, sub=18, inv=26, mat=2, sheath=0,
         display=30747, dps=41.4, delay=2900,
         stats=[(CRIT, 8)]),
    # --- Dire Maul: North (heroic) ----------------------------------------------------------------------
    # Guard Mol'dar
    dict(id=910456, base=18450, name="Robe of Combustion", ilvl=61, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=30802, armor=96,
         stats=[(INT, 42)]),
    dict(id=910457, base=18451, name="Hyena Hide Belt", ilvl=61, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=30803, armor=134,
         stats=[(STA, 26)]),
    dict(id=910458, base=18458, name="Modest Armguards", ilvl=61, cls=CLS_ARMOR, sub=3, inv=9, mat=5, sheath=0,
         display=26103, armor=162,
         stats=[(INT, 24)]),
    # Stomper Kreeg
    dict(id=910459, base=18425, name="Kreeg's Mug", ilvl=61, cls=CLS_ARMOR, sub=0, inv=23, mat=3, sheath=7,
         display=30796,
         stats=[(STA, 4), (SPI, 4), (INT, -10)]),
    # Guard Fengus: shares the items above (910456, 910457, 910458)
    # Guard Slip'kik: shares the items above (910456, 910457, 910458)
    # Captain Kromcrush
    dict(id=910460, base=18507, name="Boots of the Full Moon", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=19921, armor=64,
         stats=[(INT, 12), (SPI, 9), (STA, 12)]),
    dict(id=910461, base=18502, name="Monstrous Glaive", ilvl=62, cls=CLS_WEAPON, sub=6, inv=17, mat=6, sheath=1,
         display=30836, dps=53.9, delay=2900,
         stats=[(STA, 34)]),
    dict(id=910462, base=18503, name="Kromcrush's Chestplate", ilvl=62, cls=CLS_ARMOR, sub=4, inv=5, mat=6, sheath=0,
         display=30837, armor=706,
         stats=[(STR, 21), (STA, 21)]),
    # Cho'Rush the Observer
    dict(id=910463, base=18485, name="Observer's Shield", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=6, sheath=4,
         display=20900, armor=2153, block=40,
         stats=[(INT, 10), (SPI, 4), (STA, 6)]),
    dict(id=910464, base=18490, name="Insightful Hood", ilvl=62, cls=CLS_ARMOR, sub=2, inv=1, mat=8, sheath=0,
         display=33293, armor=162,
         stats=[(INT, 16), (SPI, 10), (STA, 13)]),
    # King Gordok
    dict(id=910465, base=18524, name="Leggings of Destruction", ilvl=63, cls=CLS_ARMOR, sub=3, inv=7, mat=5,
         sheath=0, display=30857, armor=348,
         stats=[(AGI, 12), (INT, 11), (STA, 17)]),
    dict(id=910466, base=18521, name="Grimy Metal Boots", ilvl=63, cls=CLS_ARMOR, sub=4, inv=8, mat=6, sheath=0,
         display=30854, armor=472,
         stats=[(STR, 33)]),
    dict(id=910467, base=18522, name="Band of the Ogre King", ilvl=63, cls=CLS_ARMOR, sub=0, inv=11, mat=3, sheath=0,
         display=23897,
         stats=[(STR, 9), (STA, 9)]),
    dict(id=910468, base=18523, name="Brightly Glowing Stone", ilvl=63, cls=CLS_ARMOR, sub=0, inv=23, mat=3,
         sheath=7, display=30855,
         stats=[(STA, 8)]),
    dict(id=910469, base=18525, name="Bracers of Prosperity", ilvl=63, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=30859, armor=77,
         stats=[(INT, 10), (STA, 8), (SPI, 5)]),
    dict(id=910470, base=18526, name="Crown of the Ogre King", ilvl=63, cls=CLS_ARMOR, sub=1, inv=1, mat=3, sheath=0,
         display=30860, armor=81,
         stats=[(INT, 16), (SPI, 10), (STA, 14)]),
    # --- Scholomance (heroic) ---------------------------------------------------------------------------
    # Kirtonos the Herald
    dict(id=910471, base=13960, name="Heart of the Fiend", ilvl=61, cls=CLS_ARMOR, sub=0, inv=2, mat=5, sheath=0,
         display=19785,
         stats=[(SPI, 14), (INT, 5), (STA, 5)]),
    dict(id=910472, base=13957, name="Gargoyle Slashers", ilvl=61, cls=CLS_ARMOR, sub=2, inv=10, mat=8, sheath=0,
         display=24768, armor=122,
         stats=[(AGI, 5), (STR, 9), (STA, 11)]),
    dict(id=910473, base=13969, name="Loomguard Armbraces", ilvl=61, cls=CLS_ARMOR, sub=3, inv=9, mat=5, sheath=0,
         display=24793, armor=162,
         stats=[(INT, 13), (STA, 11)]),
    # Jandice Barov
    dict(id=910474, base=15943, name="Imbued Shield", ilvl=61, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=27588, armor=2153, block=40,
         stats=[(STR, 4), (STA, 16)]),
    dict(id=910475, base=14545, name="Ghostloom Leggings", ilvl=61, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=25169, armor=215,
         stats=[(INT, 17), (SPELL_POWER, 14), (STA, 9)]),
    dict(id=910476, base=18690, name="Wraithplate Leggings", ilvl=61, cls=CLS_ARMOR, sub=4, inv=7, mat=6, sheath=0,
         display=25226, armor=618,
         stats=[(STA, 40)]),
    # Rattlegore
    dict(id=910477, base=14528, name="Rattlecage Buckler", ilvl=61, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=25138, armor=2153, block=40,
         stats=[(SPI, 5), (INT, 9), (STA, 5)]),
    dict(id=910478, base=14538, name="Deadwalker Mantle", ilvl=61, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=28705, armor=75,
         stats=[(STA, 21), (INT, 10)]),
    dict(id=910479, base=14537, name="Corpselight Greaves", ilvl=61, cls=CLS_ARMOR, sub=4, inv=8, mat=6, sheath=0,
         display=25160, armor=472,
         stats=[(STA, 33)]),
    # Marduk Blackpool
    dict(id=910480, base=18692, name="Death Knight Sabatons", ilvl=61, cls=CLS_ARMOR, sub=4, inv=8, mat=6, sheath=0,
         display=31133, armor=472,
         stats=[(STR, 9), (STA, 9), (INT, 9), (SPI, 7)]),
    # Vectus
    dict(id=910481, base=14577, name="Skullsmoke Pants", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=28715, armor=84,
         stats=[(INT, 20), (STA, 20)]),
    dict(id=910482, base=18691, name="Dark Advisor's Pendant", ilvl=62, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=15420,
         stats=[(STA, 12), (INT, 11)]),
    # Ras Frostwhisper
    dict(id=910483, base=18696, name="Intricately Runed Shield", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=6,
         sheath=4, display=18790, armor=2153, block=40,
         stats=[(STA, 20)]),
    dict(id=910484, base=13314, name="Alanna's Embrace", ilvl=62, cls=CLS_ARMOR, sub=1, inv=20, mat=7, sheath=0,
         display=24760, armor=96,
         stats=[(INT, 14), (SPI, 14), (STA, 14)]),
    dict(id=910485, base=14502, name="Frostbite Girdle", ilvl=62, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=28757, armor=134,
         stats=[(STR, 4), (AGI, 11), (STA, 11)]),
    # Instructor Malicia
    dict(id=910486, base=14611, name="Bloodmail Hauberk", ilvl=62, cls=CLS_ARMOR, sub=3, inv=5, mat=5, sheath=0,
         display=25222, armor=398,
         stats=[(STA, 13), (INT, 13), (STR, 8), (SPI, 8)]),
    dict(id=910487, base=16710, name="Shadowcraft Bracers", ilvl=62, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=24190, armor=77,
         stats=[(AGI, 16), (STA, 8)]),
    dict(id=910488, base=14612, name="Bloodmail Legguards", ilvl=62, cls=CLS_ARMOR, sub=3, inv=7, mat=5, sheath=0,
         display=25223, armor=348,
         stats=[(INT, 10), (STA, 11), (STR, 10), (AGI, 8)]),
    # Doctor Theolen Krastinov
    dict(id=910489, base=16684, name="Magister's Gloves", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=29593, armor=80,
         stats=[(SPI, 9), (INT, 9), (STA, 6)]),
    dict(id=910490, base=14620, name="Deathbone Girdle", ilvl=62, cls=CLS_ARMOR, sub=4, inv=6, mat=6, sheath=0,
         display=25225, armor=369,
         stats=[(STA, 26)]),
    # Lorekeeper Polkelt
    dict(id=910491, base=16705, name="Dreadmist Wraps", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=29800, armor=80,
         stats=[(SPI, 10), (INT, 6), (STA, 9)]),
    # The Ravenian
    dict(id=910492, base=16716, name="Wildheart Belt", ilvl=62, cls=CLS_ARMOR, sub=2, inv=6, mat=8, sheath=0,
         display=29976, armor=134,
         stats=[(INT, 12), (SPI, 7), (STA, 6)]),
    # Lord Alexei Barov
    dict(id=910493, base=18682, name="Ghoul Skin Leggings", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=10006, armor=215,
         stats=[(STA, 22), (INT, 9), (SPI, 9)]),
    dict(id=910494, base=18683, name="Hammer of the Vesper", ilvl=62, cls=CLS_WEAPON, sub=4, inv=13, mat=1, sheath=3,
         display=31126, dps=41.5, delay=2500,
         stats=[(STA, 11), (STR, 7)]),
    dict(id=910495, base=18681, name="Burial Shawl", ilvl=62, cls=CLS_ARMOR, sub=1, inv=3, mat=7, sheath=0,
         display=10177, armor=75,
         stats=[(INT, 31)]),
    # Lady Illucia Barov: shares the items above (910486, 910490, 910488)
    # Kormok
    dict(id=910496, base=22303, name="Ironweave Pants", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=34788, armor=84,
         stats=[(STA, 25), (INT, 15)]),
    dict(id=910497, base=22331, name="Band of the Steadfast Hero", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=3,
         sheath=0, display=24569,
         stats=[(STR, 7), (STA, 11)]),
    dict(id=910498, base=22326, name="Amalgam's Band", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=26001,
         stats=[(INT, 10), (STA, 8)]),
    # Darkmaster Gandling
    dict(id=910499, base=13398, name="Boots of the Shrieker", ilvl=63, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=9653, armor=166,
         stats=[(INT, 11), (SPI, 11), (STA, 11)]),
    dict(id=910500, base=13944, name="Tombstone Breastplate", ilvl=63, cls=CLS_ARMOR, sub=2, inv=5, mat=8, sheath=0,
         display=28632, armor=181,
         stats=[(STR, 21), (STA, 21)]),
    dict(id=910501, base=13938, name="Bonecreeper Stylus", ilvl=63, cls=CLS_WEAPON, sub=19, inv=26, mat=2, sheath=0,
         display=24743, dps=63.8, delay=1900,
         stats=[(INT, 8)]),
    dict(id=910502, base=13951, name="Vigorsteel Vambraces", ilvl=63, cls=CLS_ARMOR, sub=4, inv=9, mat=6, sheath=0,
         display=24749, armor=287,
         stats=[(STA, 17), (AGI, 7)]),
    dict(id=910503, base=13964, name="Witchblade", ilvl=63, cls=CLS_WEAPON, sub=15, inv=21, mat=1, sheath=3,
         display=24775, dps=41.5, delay=1600,
         stats=[(INT, 8)]),
    dict(id=910504, base=16667, name="Coif of Elements", ilvl=63, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=45174, armor=337,
         stats=[(INT, 16), (STA, 9), (SPI, 9), (STR, 5)]),
    # --- Stratholme: Live (heroic) ----------------------------------------------------------------------
    # The Unforgiven
    dict(id=910505, base=13404, name="Mask of the Unforgiven", ilvl=61, cls=CLS_ARMOR, sub=2, inv=1, mat=8, sheath=0,
         display=41843, armor=162,
         stats=[(STA, 10), (HIT, 17), (CRIT, 12)]),
    dict(id=910506, base=13405, name="Wailing Nightbane Pauldrons", ilvl=61, cls=CLS_ARMOR, sub=4, inv=3, mat=6,
         sheath=0, display=24115, armor=552,
         stats=[(STA, 16), (STR, 16)]),
    # Timmy the Cruel
    dict(id=910507, base=13402, name="Timmy's Galoshes", ilvl=61, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=33114, armor=266,
         stats=[(STA, 9), (AGI, 14), (INT, 9)]),
    dict(id=910508, base=13400, name="Vambraces of the Sadist", ilvl=61, cls=CLS_ARMOR, sub=4, inv=9, mat=6,
         sheath=0, display=24110, armor=287,
         stats=[(STA, 13), (STR, 11)]),
    dict(id=910509, base=13403, name="Grimgore Noose", ilvl=61, cls=CLS_ARMOR, sub=1, inv=6, mat=7, sheath=0,
         display=24113, armor=55,
         stats=[(SPI, 7), (STA, 6), (INT, 12)]),
    # Malor the Zealous
    dict(id=910510, base=15943, name="Imbued Shield", ilvl=61, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=27588, armor=2153, block=40,
         stats=[(STR, 4), (STA, 16)]),
    dict(id=910511, base=18745, name="Sacred Cloth Leggings", ilvl=61, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=2311, armor=84,
         stats=[(INT, 18), (SPI, 11), (STA, 11)]),
    dict(id=910512, base=18742, name="Stratholme Militia Shoulderguard", ilvl=61, cls=CLS_ARMOR, sub=3, inv=3, mat=5,
         sheath=0, display=31194, armor=311,
         stats=[(AGI, 22), (STA, 9)]),
    # Cannon Master Willey
    dict(id=910513, base=18721, name="Barrage Girdle", ilvl=62, cls=CLS_ARMOR, sub=3, inv=6, mat=8, sheath=0,
         display=31171, armor=208,
         stats=[(INT, 9), (SPI, 9), (STA, 9)]),
    dict(id=910514, base=13380, name="Willey's Portable Howitzer", ilvl=62, cls=CLS_WEAPON, sub=3, inv=26, mat=1,
         sheath=0, display=18298, dps=41.4, delay=2900,
         stats=[(STA, 8)]),
    dict(id=910515, base=13381, name="Master Cannoneer Boots", ilvl=62, cls=CLS_ARMOR, sub=4, inv=8, mat=6, sheath=0,
         display=24068, armor=472,
         stats=[(STR, 11), (STA, 22)]),
    # Archivist Galford
    dict(id=910516, base=16692, name="Devout Gloves", ilvl=62, cls=CLS_ARMOR, sub=1, inv=10, mat=7, sheath=0,
         display=30427, armor=80,
         stats=[(SPI, 12), (INT, 7), (STA, 6)]),
    dict(id=910517, base=18716, name="Ash Covered Boots", ilvl=62, cls=CLS_ARMOR, sub=2, inv=8, mat=8, sheath=0,
         display=31166, armor=166,
         stats=[(AGI, 16), (STA, 16)]),
    dict(id=910518, base=13385, name="Tome of Knowledge", ilvl=62, cls=CLS_ARMOR, sub=0, inv=23, mat=3, sheath=7,
         display=24072,
         stats=[(AGI, 2), (STR, 2), (INT, 2), (SPI, 2), (STA, 2)]),
    # Crimson Hammersmith
    dict(id=910519, base=8283, name="Arcane Armor", ilvl=62, cls=CLS_ARMOR, sub=1, inv=5, mat=7, sheath=0,
         display=17251, armor=96,
         stats=[(STA, 10), (INT, 32)]),
    dict(id=910520, base=8300, name="Traveler's Leggings", ilvl=62, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=17313, armor=215,
         stats=[(STR, 20), (AGI, 20)]),
    # Fras Siabi: no fixed-stat gear drops of its own (heroic: gold only)
    # Postmaster Malown
    dict(id=910521, base=13388, name="The Postmaster's Tunic", ilvl=62, cls=CLS_ARMOR, sub=1, inv=5, mat=7, sheath=0,
         display=25049, armor=96,
         stats=[(SPI, 10), (STA, 13), (INT, 20)]),
    dict(id=910522, base=13389, name="The Postmaster's Trousers", ilvl=62, cls=CLS_ARMOR, sub=1, inv=7, mat=7,
         sheath=0, display=25050, armor=84,
         stats=[(STA, 9), (SPI, 15), (INT, 15)]),
    dict(id=910523, base=13391, name="The Postmaster's Treads", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7,
         sheath=0, display=25051, armor=64,
         stats=[(INT, 14), (SPI, 6), (STA, 13)]),
    # Jarien: no fixed-stat gear drops of its own (heroic: gold only)
    # Sothos: no fixed-stat gear drops of its own (heroic: gold only)
    # Balnazzar
    dict(id=910524, base=13353, name="Book of the Dead", ilvl=63, cls=CLS_ARMOR, sub=0, inv=23, mat=3, sheath=7,
         display=24039,
         stats=[(SPI, 2), (INT, 4), (STA, 2)]),
    dict(id=910525, base=13358, name="Wyrmtongue Shoulders", ilvl=63, cls=CLS_ARMOR, sub=2, inv=3, mat=8, sheath=0,
         display=18971, armor=196,
         stats=[(AGI, 22), (STA, 9)]),
    dict(id=910526, base=12103, name="Star of Mystaria", ilvl=63, cls=CLS_ARMOR, sub=0, inv=2, mat=5, sheath=0,
         display=23717,
         stats=[(SPI, 5), (INT, 6), (STA, 6), (HIT, 5)]),
    dict(id=910527, base=13359, name="Crown of Tyranny", ilvl=63, cls=CLS_ARMOR, sub=3, inv=1, mat=5, sheath=0,
         display=24045, armor=337,
         stats=[(STA, 39), (SPI, -10)]),
    dict(id=910528, base=13360, name="Gift of the Elven Magi", ilvl=63, cls=CLS_WEAPON, sub=15, inv=13, mat=1,
         sheath=3, display=24046, dps=41.5, delay=1500,
         stats=[(SPI, 5), (INT, 9), (STA, 4)]),
    dict(id=910529, base=13369, name="Fire Striders", ilvl=63, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=24054, armor=64,
         stats=[(SPI, 33)]),
    # --- Stratholme: Undead (heroic) --------------------------------------------------------------------
    # Magistrate Barthilas
    dict(id=910530, base=13376, name="Royal Tribunal Cloak", ilvl=61, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=24065, armor=45,
         stats=[(INT, 13), (STA, 6)]),
    dict(id=910531, base=18722, name="Death Grips", ilvl=61, cls=CLS_ARMOR, sub=4, inv=10, mat=6, sheath=0,
         display=31173, armor=429,
         stats=[(STR, 25)]),
    dict(id=910532, base=18726, name="Magistrate's Cuffs", ilvl=61, cls=CLS_ARMOR, sub=2, inv=9, mat=8, sheath=0,
         display=31175, armor=77,
         stats=[(STA, 24)]),
    # Baroness Anastari
    dict(id=910533, base=16704, name="Dreadmist Sandals", ilvl=61, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=29799, armor=64,
         stats=[(STA, 16), (SPI, 9), (INT, 8)]),
    dict(id=910534, base=18728, name="Anastari Heirloom", ilvl=61, cls=CLS_ARMOR, sub=0, inv=2, mat=3, sheath=0,
         display=9657,
         stats=[(STA, 23)]),
    dict(id=910535, base=18729, name="Screeching Bow", ilvl=61, cls=CLS_WEAPON, sub=2, inv=15, mat=2, sheath=0,
         display=31240, dps=41.4, delay=2300,
         stats=[(STA, 14)]),
    # Nerub'enkan
    dict(id=910536, base=13529, name="Husk of Nerub'enkan", ilvl=62, cls=CLS_ARMOR, sub=6, inv=14, mat=1, sheath=4,
         display=4107, armor=2153, block=40,
         stats=[(STA, 20)]),
    dict(id=910537, base=18739, name="Chitinous Plate Legguards", ilvl=62, cls=CLS_ARMOR, sub=4, inv=7, mat=6,
         sheath=0, display=31191, armor=618,
         stats=[(INT, 20), (STA, 20)]),
    dict(id=910538, base=16675, name="Beaststalker's Boots", ilvl=62, cls=CLS_ARMOR, sub=3, inv=8, mat=5, sheath=0,
         display=31408, armor=266,
         stats=[(AGI, 20), (STA, 13)]),
    # Maleki the Pallid
    dict(id=910539, base=16691, name="Devout Sandals", ilvl=62, cls=CLS_ARMOR, sub=1, inv=8, mat=7, sheath=0,
         display=30430, armor=64,
         stats=[(SPI, 16), (INT, 9), (STA, 8)]),
    dict(id=910540, base=18737, name="Bone Slicing Hatchet", ilvl=62, cls=CLS_WEAPON, sub=0, inv=13, mat=1, sheath=3,
         display=31189, dps=41.5, delay=1700,
         stats=[(AGI, 13), (STA, 5)]),
    dict(id=910541, base=18734, name="Pale Moon Cloak", ilvl=62, cls=CLS_ARMOR, sub=1, inv=16, mat=7, sheath=0,
         display=31351, armor=45,
         stats=[(STR, 8), (STA, 11)]),
    # Ramstein the Gorger
    dict(id=910542, base=13372, name="Slavedriver's Cane", ilvl=62, cls=CLS_WEAPON, sub=10, inv=17, mat=2, sheath=2,
         display=24063, dps=53.9, delay=3900,
         stats=[(STR, 24), (STA, 10)]),
    dict(id=910543, base=13373, name="Band of Flesh", ilvl=62, cls=CLS_ARMOR, sub=0, inv=11, mat=5, sheath=0,
         display=1225,
         stats=[(STA, 12), (STR, 4), (AGI, 2)]),
    # Baron Rivendare
    dict(id=910544, base=16668, name="Kilt of Elements", ilvl=63, cls=CLS_ARMOR, sub=3, inv=7, mat=5, sheath=0,
         display=31415, armor=348,
         stats=[(SPI, 13), (INT, 10), (STR, 8), (STA, 5), (AGI, 4)]),
    dict(id=910545, base=16709, name="Shadowcraft Pants", ilvl=63, cls=CLS_ARMOR, sub=2, inv=7, mat=8, sheath=0,
         display=28161, armor=215,
         stats=[(AGI, 20), (STA, 10), (STR, 10)]),
    dict(id=910546, base=16678, name="Beaststalker's Pants", ilvl=63, cls=CLS_ARMOR, sub=3, inv=7, mat=5, sheath=0,
         display=31403, armor=348,
         stats=[(AGI, 17), (SPI, 11), (STA, 6), (STR, 6)]),
    dict(id=910547, base=16687, name="Magister's Leggings", ilvl=63, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=29273, armor=84,
         stats=[(SPI, 16), (INT, 15), (STA, 9)]),
    dict(id=910548, base=16694, name="Devout Skirt", ilvl=63, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=30424, armor=84,
         stats=[(SPI, 18), (INT, 12), (STA, 10)]),
    dict(id=910549, base=16699, name="Dreadmist Leggings", ilvl=63, cls=CLS_ARMOR, sub=1, inv=7, mat=7, sheath=0,
         display=29797, armor=84,
         stats=[(SPI, 17), (STA, 12), (INT, 11)]),
]

# ---------------------------------------------------------------- loot
# Keyed by map id, then by the NORMAL boss entry (its heroic copy is entry + HEROIC_ENTRY_OFFSET).
#   groups: each list is one loot group with equal chances; exactly one item from each group drops.
#   extra:  (item, chance %) rolled independently.
#   gold:   (min, max) in copper (left as the normal boss's when not given).
#   final:  True for the last boss of a dungeon or wing (the 26 in bulletin_board.DUNGEONS; check() makes sure):
#           it drops SIGILS_FINAL Heroic Sigils instead of SIGILS.
#   normal_loot: True = the heroic boss drops the normal boss's whole loot (the pilot heroics, Stockade and
#           Ragefire Chasm, have no heroic gear), plus its Heroic Sigils.
# Every heroic boss drops Heroic Sigils (the Heroic currency, item 912000: tools/custom_dbc.py and
# data/sql/db-world/unbound_currencies.sql). The item is multi-drop, so every group member loots their own.
HEROIC_SIGIL = 912000
SIGILS = 1         # per heroic boss
SIGILS_FINAL = 2   # from a final boss

# ---------------------------------------------------------------- the Heroic Quartermaster
# Creature 190104 (data/sql/db-world/unbound_heroic_quartermaster.sql, src/unbound_heroic_quartermaster.cpp) shows a
# menu; each page is a never-spawned vendor creature whose npc_vendor list it opens (a 3.3.5 vendor window holds at
# most 150 items, and there are 450 heroic items). Prices are ItemExtendedCost rows (tools/custom_dbc.py builds them
# from SIGIL_EXTENDED_COSTS): Sigils -> ExtendedCost id.
SIGIL_EXTENDED_COSTS = {10: 3000, 15: 3001, 20: 3002, 25: 3003, 30: 3004,
                        5: 3005, 40: 3006, 75: 3007, 90: 3008, 100: 3009, 120: 3010}  # 3005+: the Warden's prices
QUARTERMASTER_PAGES = [
    # vendor entry, menu text, inventory types (final-boss items all go on the last page), Sigils
    (190105, 'Rings, necks, cloaks, wrists and belts (10 Sigils)', {2, 6, 9, 11, 12, 16}, 10),
    (190106, 'Head, shoulders and chest (15 Sigils)', {1, 3, 5, 20}, 15),
    (190107, 'Hands, legs and feet (15 Sigils)', {7, 8, 10}, 15),
    (190108, 'Weapons, shields and off-hands (20-25 Sigils)', {13, 14, 15, 17, 21, 22, 23, 25, 26, 28}, None),
    (190109, 'Final boss treasures (30 Sigils)', None, 30),
]
TWO_HANDED_OR_RANGED = {15, 17, 25, 26, 28}  # 25 Sigils on the weapons page; one-handers, shields, off-hands 20

# ---------------------------------------------------------------- the Warden of Rare Wonders
# Creature 190200 (data/sql/db-world/unbound_warden_of_rare_wonders.sql, same script as the Quartermaster): cosmetics
# for Heroic Sigils, a menu of four pages (never-spawned vendor creatures 190201-190204). Only items a level 60
# character can use on a classic-only server: no level 70 or Expert Riding mounts, no profession items, and no mounts
# that still drop in reachable content (Deathcharger, the Zul'Gurub mounts, the Black Qiraji crystal). Items checked in
# the world database on 2026-10-16.
WARDEN_PAGES = [
    # vendor entry, menu text, [(item, Sigils), ...]
    (190201, 'Mounts', [
        (23720, 40),    # Riding Turtle (level 1, no riding skill)
        (49283, 75),    # Reins of the Spectral Tiger
        (37719, 90),    # Swift Zhevra
        (54811, 100),   # Celestial Steed (scales with riding)
        (37012, 100),   # The Horseman's Reins (scales with riding)
        (46778, 100),   # Magic Rooster Egg (level 60)
        (49284, 120),   # Reins of the Swift Spectral Tiger
    ]),
    (190202, 'Pets', [
        (910003, 40),   # Scavenger Imp (loot companion: loots up to 4 corpses around the one you open)
        (49362, 15), (44819, 15), (49662, 15), (49663, 15), (25535, 15),   # Onyxian Whelpling, Baby Blizzard Bear,
                                                                            # Gryphon Hatchling, Wind Rider Cub, Netherwhelp
        (20371, 20), (30360, 20), (13583, 20), (13584, 20), (13582, 20),   # Murky, Lurky, Panda Cub, Mini Diablo, Zergling
        (39286, 20), (41133, 20), (35504, 20),                             # Frosty, Mr. Chilly, Phoenix Hatchling
        (49665, 25), (49646, 25), (54847, 25), (56806, 25), (38050, 25),   # Pandaren Monk, Core Hound Pup, Lil' XT,
                                                                            # Mini Thor, Ethereal Soul-Trader
        (49693, 30), (49343, 30),                                          # Lil' K.T., Spectral Tiger Cub
    ]),
    (190203, 'Tabards', [
        (23705, 25), (23709, 25), (38309, 25), (38310, 25),   # Flame, Frost, Nature, the Arcane
        (38314, 25), (38312, 25), (38311, 25), (38313, 25),   # the Defender, Brilliance, the Void, Fury
    ]),
    (190204, 'Fun items', [
        (8529, 5), (38577, 5), (36863, 5),   # Noggenfogger Elixir, Party G.R.E.N.A.D.E., Decahedral Dwarven Dice
        (46780, 10), (34480, 10),            # Ogre Pinata, Romantic Picnic Basket
        (13379, 15),                         # Piccolo of the Flaming Fire (level 53)
        (1973, 20),                          # Orb of Deception (level 54)
    ]),
]
# Each page lists its items by type, then alphabetically: by slot (head to feet, then rings, trinkets, weapons),
# then armor type (cloth, leather, mail, plate) or weapon type (axe, dagger, mace, ...), then name.
QUARTERMASTER_SLOT_ORDER = [1, 2, 3, 16, 5, 20, 9, 10, 6, 7, 8, 11, 12,  # head .. feet, rings, trinkets
                            13, 21, 22, 14, 23, 17, 15, 26, 25, 28]   # one-hand .. two-hand, ranged, relics
QUARTERMASTER_SLOT_RANK = {inv: rank for rank, inv in enumerate(QUARTERMASTER_SLOT_ORDER)}
QUARTERMASTER_SLOT_RANK[20] = QUARTERMASTER_SLOT_RANK[5]   # robes with chests
QUARTERMASTER_WEAPON_TYPES = {0: 'Axe', 1: 'Axe', 2: 'Bow', 3: 'Gun', 4: 'Mace', 5: 'Mace', 6: 'Polearm',
                              7: 'Sword', 8: 'Sword', 10: 'Staff', 13: 'Fist Weapon', 15: 'Dagger', 16: 'Thrown',
                              18: 'Crossbow', 19: 'Wand'}


def quartermaster_sort_key(item):
    """Slot, then armor type (cloth, leather, mail, plate; rings and the like first) or weapon type, then name."""
    kind = QUARTERMASTER_WEAPON_TYPES[item['sub']] if item['cls'] == CLS_WEAPON else f"{item['sub']:02d}"
    return QUARTERMASTER_SLOT_RANK.get(item['inv'], len(QUARTERMASTER_SLOT_ORDER)), kind, item['name'].lower()
LOOT = {
    34: {  # Stormwind Stockades (pilot heroic: normal loot plus Sigils)
        1696: dict(name='Targorr the Dread', normal_loot=True),
        1666: dict(name='Kam Deepfury', normal_loot=True),
        1717: dict(name='Hamhock', normal_loot=True),
        1716: dict(name='Bazil Thredd', normal_loot=True, final=True),
        1663: dict(name='Dextren Ward', normal_loot=True),
        1720: dict(name='Bruegal Ironknuckle', normal_loot=True),
    },
    389: {  # Ragefire Chasm (pilot heroic: normal loot plus Sigils)
        11517: dict(name='Oggleflint', normal_loot=True),
        11520: dict(name='Taragaman the Hungerer', normal_loot=True),
        11518: dict(name='Jergosh the Invoker', normal_loot=True),
        11519: dict(name='Bazzalan', normal_loot=True, final=True),
    },
    36: {  # Deadmines
        644:  dict(name="Rhahk'Zor", groups=[[910100, 910101, 910102]], gold=(2000, 4000)),
        642:  dict(name="Sneed's Shredder", groups=[[910103, 910104, 910105]], gold=(2000, 4000)),
        1763: dict(name='Gilnid', groups=[[910106, 910107, 910108]], gold=(2000, 4000)),
        646:  dict(name='Mr. Smite', groups=[[910109, 910110, 910111]], gold=(2000, 4000)),
        647:  dict(name='Captain Greenskin', groups=[[910112, 910113, 910114]],
                   extra=[(8494, 1)],  # Parrot Cage (Hyacinth Macaw) companion
                   gold=(2000, 4000)),
        645:  dict(name='Cookie', groups=[[910115, 910116, 910117]], gold=(2000, 4000)),
        639:  dict(final=True, name='Edwin VanCleef', groups=[[910118, 910119], [910120, 910121]], gold=(5000, 10000)),
    },
    43: {  # Wailing Caverns
        3671: dict(name="Lady Anacondra", groups=[[910122, 910123]], gold=(2000, 4000)),
        3669: dict(name="Lord Cobrahn", groups=[[910124, 910125, 910126]], gold=(2000, 4000)),
        3653: dict(name="Kresh", groups=[], gold=(2000, 4000)),
        3670: dict(name="Lord Pythas", groups=[[910127]], gold=(2000, 4000)),
        3674: dict(name="Skum", groups=[[910128, 910129]], gold=(2000, 4000)),
        3673: dict(name="Lord Serpentis", groups=[[910130, 910131, 910132]], gold=(2000, 4000)),
        5775: dict(name="Verdan the Everliving", groups=[[910133, 910134, 910135]], gold=(2000, 4000)),
        3654: dict(final=True, name="Mutanus the Devourer", groups=[[910136], [910137]], gold=(5000, 10000)),
    },
    33: {  # Shadowfang Keep
        3914: dict(name="Rethilgore", groups=[[910138]], gold=(2000, 4000)),
        3886: dict(name="Razorclaw the Butcher", groups=[[910139, 910140, 910141]], gold=(2000, 4000)),
        3887: dict(name="Baron Silverlaine", groups=[[910142, 910143]], gold=(2000, 4000)),
        4278: dict(name="Commander Springvale", groups=[[910144, 910145]], gold=(2000, 4000)),
        4279: dict(name="Odo the Blindwatcher", groups=[[910146, 910147]], gold=(2000, 4000)),
        4274: dict(name="Fenrus the Devourer", groups=[[910148, 910149]], gold=(2000, 4000)),
        3927: dict(name="Wolf Master Nandos", groups=[[910150, 910151]], gold=(2000, 4000)),
        4275: dict(final=True, name="Archmage Arugal", groups=[[910152], [910153]], gold=(5000, 10000)),
    },
    48: {  # Blackfathom Deeps
        4887: dict(name="Ghamoo-ra", groups=[[910154, 910155]], gold=(2000, 4000)),
        4831: dict(name="Lady Sarevess", groups=[[910156, 910157, 910158]], gold=(2000, 4000)),
        6243: dict(name="Gelihast", groups=[[910159, 910160]], gold=(2000, 4000)),
        12876: dict(name="Baron Aquanis", groups=[[910161, 910162, 910163]], gold=(2000, 4000)),
        4832: dict(name="Twilight Lord Kelris", groups=[[910164, 910165]], gold=(2000, 4000)),
        4830: dict(name="Old Serra'kis", groups=[[910166, 910167]], gold=(2000, 4000)),
        4829: dict(final=True, name="Aku'mai", groups=[[910168], [910169]], gold=(5000, 10000)),
    },
    90: {  # Gnomeregan
        7361: dict(name="Grubbis", groups=[[910170]], gold=(2000, 4000)),
        7079: dict(name="Viscous Fallout", groups=[[910171, 910172, 910173]], gold=(2000, 4000)),
        6235: dict(name="Electrocutioner 6000", groups=[[910174, 910175]], gold=(2000, 4000)),
        6229: dict(name="Crowd Pummeler 9-60", groups=[[910176, 910177]], gold=(2000, 4000)),
        7800: dict(final=True, name="Mekgineer Thermaplugg", groups=[[910178, 910179], [910180]], gold=(5000, 10000)),
    },
    47: {  # Razorfen Kraul
        6168: dict(name="Roogug", groups=[[910181, 910182, 910183]], gold=(2000, 4000)),
        4424: dict(name="Aggem Thorncurse", groups=[[910184]], gold=(2000, 4000)),
        4428: dict(name="Death Speaker Jargba", groups=[[910185, 910186, 910187]], gold=(2000, 4000)),
        4420: dict(name="Overlord Ramtusk", groups=[[910188, 910189]], gold=(2000, 4000)),
        4422: dict(name="Agathelos the Raging", groups=[[910190, 910191]], gold=(2000, 4000)),
        4421: dict(final=True, name="Charlga Razorflank", groups=[[910192, 910193], [910194]], gold=(5000, 10000)),
    },
    189: {  # Scarlet Monastery
        3983: dict(name="Interrogator Vishas", groups=[[910195]], gold=(2000, 4000)),
        4543: dict(final=True, name="Bloodmage Thalnos", groups=[[910196]], gold=(5000, 10000)),
        3974: dict(name="Houndmaster Loksey", groups=[[910197]], gold=(2000, 4000)),
        6487: dict(final=True, name="Arcanist Doan", groups=[[910198, 910199, 910200], [910201, 910202]], gold=(5000, 10000)),
        3975: dict(final=True, name="Herod", groups=[[910203, 910204], [910205]], gold=(5000, 10000)),
        4542: dict(name="High Inquisitor Fairbanks", groups=[[910206, 910207, 910208]], gold=(2000, 4000)),
        3976: dict(name="Scarlet Commander Mograine", groups=[[910209, 910210, 910211]], gold=(2000, 4000)),
        3977: dict(final=True, name="High Inquisitor Whitemane", groups=[[910212, 910213], [910214]], gold=(5000, 10000)),
    },
    129: {  # Razorfen Downs
        7355: dict(name="Tuten'kash", groups=[[910215, 910216]], gold=(2000, 4000)),
        7357: dict(name="Mordresh Fire Eye", groups=[[910217, 910218, 910219]], gold=(2000, 4000)),
        8567: dict(name="Glutton", groups=[[910220]], gold=(2000, 4000)),
        7356: dict(name="Plaguemaw the Rotting", groups=[[910221]], gold=(2000, 4000)),
        7358: dict(final=True, name="Amnennar the Coldbringer", groups=[[910222, 910223, 910224], [910225, 910226, 910227]], gold=(5000, 10000)),
    },
    70: {  # Uldaman
        6910: dict(name="Revelosh", groups=[], gold=(2000, 4000)),
        6906: dict(name="Baelog", groups=[[910228, 910229]], gold=(2000, 4000)),
        6907: dict(name="Eric \"The Swift\"", groups=[[910230, 910231]], gold=(2000, 4000)),
        6908: dict(name="Olaf", groups=[[910232, 910233]], gold=(2000, 4000)),
        7228: dict(name="Ironaya", groups=[[910234, 910235]], gold=(2000, 4000)),
        7023: dict(name="Obsidian Sentinel", groups=[[910236, 910237, 910238]], gold=(2000, 4000)),
        7206: dict(name="Ancient Stone Keeper", groups=[[910239, 910240, 910241]], gold=(2000, 4000)),
        7291: dict(name="Galgann Firehammer", groups=[[910242, 910243, 910244]], gold=(2000, 4000)),
        4854: dict(name="Grimlok", groups=[[910245, 910246, 910247]], gold=(2000, 4000)),
        2748: dict(final=True, name="Archaedas", groups=[[910248]], gold=(5000, 10000)),
    },
    209: {  # Zul'Farrak
        8127: dict(name="Antu'sul", groups=[[910249, 910250]], gold=(2000, 4000)),
        7272: dict(name="Theka the Martyr", groups=[[910251, 910252, 910253]], gold=(2000, 4000)),
        7271: dict(name="Witch Doctor Zum'rah", groups=[[910254, 910255]], gold=(2000, 4000)),
        7796: dict(name="Nekrum Gutchewer", groups=[[910256, 910252, 910253]], gold=(2000, 4000)),
        7275: dict(name="Shadowpriest Sezz'ziz", groups=[[910257, 910258, 910259]], gold=(2000, 4000)),
        7604: dict(name="Sergeant Bly", groups=[[910260, 910261, 910262]], gold=(2000, 4000)),
        7795: dict(name="Hydromancer Velratha", groups=[[910256, 910263, 910264]], gold=(2000, 4000)),
        7273: dict(name="Gahz'rilla", groups=[[910265]], gold=(2000, 4000)),
        7267: dict(final=True, name="Chief Ukorz Sandscalp", groups=[[910249, 910266], [910267]], gold=(5000, 10000)),
    },
    349: {  # Maraudon
        13282: dict(name="Noxxion", groups=[[910268, 910269]], gold=(2000, 4000)),
        12258: dict(name="Razorlash", groups=[[910270, 910271, 910272]], gold=(2000, 4000)),
        12236: dict(name="Lord Vyletongue", groups=[[910273, 910274]], gold=(2000, 4000)),
        12225: dict(name="Celebras the Cursed", groups=[[910275, 910276]], gold=(2000, 4000)),
        12203: dict(name="Landslide", groups=[[910277, 910278, 910279]], gold=(2000, 4000)),
        13601: dict(name="Tinkerer Gizlock", groups=[[910280, 910281]], gold=(2000, 4000)),
        13596: dict(name="Rotgrip", groups=[[910282, 910283]], gold=(2000, 4000)),
        12201: dict(final=True, name="Princess Theradras", groups=[[910284, 910285, 910286], [910287, 910288, 910289]], gold=(5000, 10000)),
    },
    109: {  # Sunken Temple
        8580: dict(name="Atal'alarion", groups=[[910290, 910291]], gold=(2000, 4000)),
        5721: dict(name="Dreamscythe", groups=[[910292, 910293, 910294]], gold=(2000, 4000)),
        5720: dict(name="Weaver", groups=[[910292, 910293, 910294]], gold=(2000, 4000)),
        8443: dict(name="Avatar of Hakkar", groups=[[910295, 910296, 910297]], gold=(2000, 4000)),
        5710: dict(name="Jammal'an the Prophet", groups=[[910298, 910299, 910300]], gold=(2000, 4000)),
        5711: dict(name="Ogom the Wretched", groups=[[910301, 910302]], gold=(2000, 4000)),
        5719: dict(name="Morphaz", groups=[[910292, 910293, 910294]], gold=(2000, 4000)),
        5722: dict(name="Hazzas", groups=[[910292, 910293, 910294]], gold=(2000, 4000)),
        5709: dict(final=True, name="Shade of Eranikus", groups=[[910303, 910304, 910305], [910306, 910307]], gold=(5000, 10000)),
    },
    230: {  # Blackrock Depths
        9025: dict(name="Lord Roccor", groups=[[910308, 910309, 910310]], gold=(2000, 4000)),
        9018: dict(name="High Interrogator Gerstahn", groups=[[910311, 910312, 910313]], gold=(2000, 4000)),
        9319: dict(name="Houndmaster Grebmar", groups=[[910314, 910315, 910316]], gold=(2000, 4000)),
        9027: dict(name="Gorosh the Dervish", groups=[[910317, 910318, 910319]], gold=(2000, 4000)),
        9028: dict(name="Grizzle", groups=[[910320, 910321, 910322]], gold=(2000, 4000)),
        9029: dict(name="Eviscerator", groups=[[910323, 910324, 910325]], gold=(2000, 4000)),
        9030: dict(name="Ok'thor the Breaker", groups=[[910326, 910327, 910328]], gold=(2000, 4000)),
        9031: dict(name="Anub'shiah", groups=[[910329, 910330, 910331]], gold=(2000, 4000)),
        9032: dict(name="Hedrum the Creeper", groups=[[910332, 910333, 910334]], gold=(2000, 4000)),
        9017: dict(name="Lord Incendius", groups=[], gold=(2000, 4000)),
        9056: dict(name="Fineous Darkvire", groups=[[910335, 910336, 910337]], gold=(2000, 4000)),
        9016: dict(name="Bael'Gar", groups=[[910338, 910339, 910340]], gold=(2000, 4000)),
        9033: dict(name="General Angerforge", groups=[[910341, 910342, 910343]], gold=(2000, 4000)),
        8983: dict(name="Golem Lord Argelmach", groups=[[910344, 910345, 910346]], gold=(2000, 4000)),
        9537: dict(name="Hurley Blackbreath", groups=[[910347, 910348, 910349]], gold=(2000, 4000)),
        9502: dict(name="Phalanx", groups=[[910350, 910351, 910352]], gold=(2000, 4000)),
        9543: dict(name="Ribbly Screwspigot", groups=[], gold=(2000, 4000)),
        9499: dict(name="Plugger Spazzring", groups=[[910353]], gold=(2000, 4000)),
        9156: dict(name="Ambassador Flamelash", groups=[[910354, 910355, 910356]], gold=(2000, 4000)),
        9938: dict(name="Magmus", groups=[[910357, 910358, 910359]], gold=(2000, 4000)),
        8929: dict(name="Princess Moira Bronzebeard", groups=[[910360, 910361, 910362]], gold=(2000, 4000)),
        9019: dict(final=True, name="Emperor Dagran Thaurissan", groups=[[910363, 910364, 910365], [910366, 910367, 910368]], gold=(5000, 10000)),
    },
    229: {  # Blackrock Spire
        9196: dict(name="Highlord Omokk", groups=[[910369, 910370, 910371]], gold=(2000, 4000)),
        9236: dict(name="Shadow Hunter Vosh'gajin", groups=[[910372, 910373, 910374]], gold=(2000, 4000)),
        9237: dict(name="War Master Voone", groups=[[910375, 910376, 910377]], gold=(2000, 4000)),
        10596: dict(name="Mother Smolderweb", groups=[[910378, 910379]], gold=(2000, 4000)),
        10584: dict(name="Urok Doomhowl", groups=[[910380, 910381]], gold=(2000, 4000)),
        9736: dict(name="Quartermaster Zigris", groups=[[910382, 910383]], gold=(2000, 4000)),
        10220: dict(name="Halycon", groups=[[910384, 910385, 910386]], gold=(2000, 4000)),
        10268: dict(name="Gizrul the Slavener", groups=[[910387, 910388, 910389]], gold=(2000, 4000)),
        9568: dict(final=True, name="Overlord Wyrmthalak", groups=[[910390, 910391, 910392], [910393]], gold=(5000, 10000)),
        9816: dict(name="Pyroguard Emberseer", groups=[[910394, 910395]], gold=(2000, 4000)),
        10264: dict(name="Solakar Flamewreath", groups=[[910396, 910397, 910398]], gold=(2000, 4000)),
        10899: dict(name="Goraluk Anvilcrack", groups=[[910399, 910400, 910401]], gold=(2000, 4000)),
        10339: dict(name="Gyth", groups=[[910402]], gold=(2000, 4000)),
        10429: dict(name="Warchief Rend Blackhand", groups=[[910403, 910404, 910405]], gold=(2000, 4000)),
        10430: dict(name="The Beast", groups=[[910406, 910407, 910408]], gold=(2000, 4000)),
        16080: dict(name="Mor Grayhoof", groups=[[910409, 910410, 910411]], gold=(2000, 4000)),
        16042: dict(name="Lord Valthalak", groups=[[910412, 910413, 910414]], gold=(2000, 4000)),
        10363: dict(final=True, name="General Drakkisath", groups=[[910415, 910416, 910417], [910418, 910419, 910420]], gold=(5000, 10000)),
    },
    429: {  # Dire Maul
        14354: dict(name="Pusillin", groups=[], gold=(2000, 4000)),
        14327: dict(name="Lethtendris", groups=[[910421, 910422, 910423]], gold=(2000, 4000)),
        13280: dict(name="Hydrospawn", groups=[[910424, 910425, 910426]], gold=(2000, 4000)),
        11490: dict(name="Zevrim Thornhoof", groups=[[910427, 910428, 910429]], gold=(2000, 4000)),
        16097: dict(name="Isalien", groups=[[910430, 910431, 910432]], gold=(2000, 4000)),
        11492: dict(final=True, name="Alzzin the Wildshaper", groups=[[910433, 910434, 910435], [910436, 910437, 910438]], gold=(5000, 10000)),
        11489: dict(name="Tendris Warpwood", groups=[[910439, 910440, 910441]], gold=(2000, 4000)),
        11488: dict(name="Illyanna Ravenoak", groups=[[910442, 910443, 910444]], gold=(2000, 4000)),
        11487: dict(name="Magister Kalendris", groups=[[910445, 910446]], gold=(2000, 4000)),
        11496: dict(name="Immol'thar", groups=[[910447, 910448, 910449]], gold=(2000, 4000)),
        11486: dict(final=True, name="Prince Tortheldrin", groups=[[910450, 910451, 910452], [910453, 910454, 910455]], gold=(5000, 10000)),
        14326: dict(name="Guard Mol'dar", groups=[[910456, 910457, 910458]], gold=(2000, 4000)),
        14322: dict(name="Stomper Kreeg", groups=[[910459]], gold=(2000, 4000)),
        14321: dict(name="Guard Fengus", groups=[[910456, 910457, 910458]], gold=(2000, 4000)),
        14323: dict(name="Guard Slip'kik", groups=[[910456, 910457, 910458]], gold=(2000, 4000)),
        14325: dict(name="Captain Kromcrush", groups=[[910460, 910461, 910462]], gold=(2000, 4000)),
        14324: dict(name="Cho'Rush the Observer", groups=[[910463, 910464]], gold=(2000, 4000)),
        11501: dict(final=True, name="King Gordok", groups=[[910465, 910466, 910467], [910468, 910469, 910470]], gold=(5000, 10000)),
    },
    289: {  # Scholomance
        10506: dict(name="Kirtonos the Herald", groups=[[910471, 910472, 910473]], gold=(2000, 4000)),
        10503: dict(name="Jandice Barov", groups=[[910474, 910475, 910476]], gold=(2000, 4000)),
        11622: dict(name="Rattlegore", groups=[[910477, 910478, 910479]], gold=(2000, 4000)),
        10433: dict(name="Marduk Blackpool", groups=[[910480]], gold=(2000, 4000)),
        10432: dict(name="Vectus", groups=[[910481, 910482]], gold=(2000, 4000)),
        10508: dict(name="Ras Frostwhisper", groups=[[910483, 910484, 910485]], gold=(2000, 4000)),
        10505: dict(name="Instructor Malicia", groups=[[910486, 910487, 910488]], gold=(2000, 4000)),
        11261: dict(name="Doctor Theolen Krastinov", groups=[[910489, 910490, 910486]], gold=(2000, 4000)),
        10901: dict(name="Lorekeeper Polkelt", groups=[[910491, 910490, 910486]], gold=(2000, 4000)),
        10507: dict(name="The Ravenian", groups=[[910492, 910490, 910486]], gold=(2000, 4000)),
        10504: dict(name="Lord Alexei Barov", groups=[[910493, 910494, 910495]], gold=(2000, 4000)),
        10502: dict(name="Lady Illucia Barov", groups=[[910486, 910490, 910488]], gold=(2000, 4000)),
        16118: dict(name="Kormok", groups=[[910496, 910497, 910498]], gold=(2000, 4000)),
        1853: dict(final=True, name="Darkmaster Gandling", groups=[[910499, 910500, 910501], [910502, 910503, 910504]], gold=(5000, 10000)),
    },
    329: {  # Stratholme
        10516: dict(name="The Unforgiven", groups=[[910505, 910506]], gold=(2000, 4000)),
        10808: dict(name="Timmy the Cruel", groups=[[910507, 910508, 910509]], gold=(2000, 4000)),
        11032: dict(name="Malor the Zealous", groups=[[910510, 910511, 910512]], gold=(2000, 4000)),
        10997: dict(name="Cannon Master Willey", groups=[[910513, 910514, 910515]], gold=(2000, 4000)),
        10811: dict(name="Archivist Galford", groups=[[910516, 910517, 910518]], gold=(2000, 4000)),
        11120: dict(name="Crimson Hammersmith", groups=[[910510, 910519, 910520]], gold=(2000, 4000)),
        11058: dict(name="Fras Siabi", groups=[], gold=(2000, 4000)),
        11143: dict(name="Postmaster Malown", groups=[[910521, 910522, 910523]], gold=(2000, 4000)),
        16101: dict(name="Jarien", groups=[], gold=(2000, 4000)),
        16102: dict(name="Sothos", groups=[], gold=(2000, 4000)),
        10813: dict(final=True, name="Balnazzar", groups=[[910524, 910525, 910526], [910527, 910528, 910529]], gold=(5000, 10000)),
        10435: dict(name="Magistrate Barthilas", groups=[[910530, 910531, 910532]], gold=(2000, 4000)),
        10436: dict(name="Baroness Anastari", groups=[[910533, 910534, 910535]], gold=(2000, 4000)),
        10437: dict(name="Nerub'enkan", groups=[[910536, 910537, 910538]], gold=(2000, 4000)),
        10438: dict(name="Maleki the Pallid", groups=[[910539, 910540, 910541]], gold=(2000, 4000)),
        10439: dict(name="Ramstein the Gorger", groups=[[910510, 910542, 910543]], gold=(2000, 4000)),
        10440: dict(final=True, name="Baron Rivendare", groups=[[910544, 910545, 910546], [910547, 910548, 910549]], gold=(5000, 10000)),
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
        gold = ''
        if 'gold' in boss:  # otherwise the heroic copy keeps the normal boss's gold
            gold = f", `mingold` = {boss['gold'][0]}, `maxgold` = {boss['gold'][1]}"
        lines.append(f"UPDATE `creature_template` SET `lootid` = {heroic_entry(entry)}{gold} "
                     f"WHERE `entry` = {heroic_entry(entry)};  -- {boss['name']} (Heroic)")
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
            sigils = SIGILS_FINAL if boss.get('final') else SIGILS  # always drops; multi-drop: one each per player
            rows.append(f"({h}, {HEROIC_SIGIL}, 0, 100, 0, 1, 0, {sigils}, {sigils}, "
                        f"{sql_str('Heroic ' + boss['name'] + ' (Heroic Sigil)')})")
            if rows:
                lines.append('INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, '
                             '`QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES')
                lines.append(',\n'.join(rows) + ';')
            if boss.get('normal_loot'):
                # a pilot heroic without heroic gear: the normal boss's whole loot table, references and groups too
                lines.append('INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, '
                             '`QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`)')
                lines.append(f"SELECT {h}, `l`.`Item`, `l`.`Reference`, `l`.`Chance`, `l`.`QuestRequired`, `l`.`LootMode`, "
                             f"`l`.`GroupId`, `l`.`MinCount`, `l`.`MaxCount`, {sql_str('Heroic ' + boss['name'] + ' (normal loot)')}")
                lines.append('FROM `creature_template` `ct` JOIN `creature_loot_template` `l` ON `l`.`Entry` = `ct`.`lootid` '
                             f'WHERE `ct`.`entry` = {entry};')
                continue
            # the normal boss's quest drops (quest items, items that start a quest, quest-only drops), same chances
            lines.append('INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, '
                         '`QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`)')
            lines.append(f"SELECT {h}, `l`.`Item`, 0, `l`.`Chance`, `l`.`QuestRequired`, `l`.`LootMode`, 0, `l`.`MinCount`, "
                         f"`l`.`MaxCount`, {sql_str('Heroic ' + boss['name'] + ' (quest)')}")
            lines.append('FROM `creature_template` `ct` JOIN `creature_loot_template` `l` ON `l`.`Entry` = `ct`.`lootid` '
                         'JOIN `item_template` `i` ON `i`.`entry` = `l`.`Item`')
            lines.append(f'WHERE `ct`.`entry` = {entry} AND `l`.`Reference` = 0 AND `l`.`GroupId` = 0 '
                         'AND (`i`.`class` = 12 OR `l`.`QuestRequired` = 1 OR `i`.`startquest` > 0);')
    return '\n'.join(lines)


def final_boss_items():
    return {item for bosses in LOOT.values() for boss in bosses.values() if boss.get('final')
            for group in boss.get('groups', []) for item in group}


def quartermaster_pages():
    """{vendor entry: [(item, Sigils), ...]} for the Heroic Quartermaster's pages."""
    finals = final_boss_items()
    pages = {entry: [] for entry, _, _, _ in QUARTERMASTER_PAGES}
    for item in sorted(HEROIC_ITEMS, key=quartermaster_sort_key):
        for entry, _, slots, sigils in QUARTERMASTER_PAGES:
            if slots is None:
                if item['id'] in finals:
                    pages[entry].append((item['id'], sigils))
                    break
            elif item['id'] not in finals and item['inv'] in slots:
                pages[entry].append((item['id'], sigils or (25 if item['inv'] in TWO_HANDED_OR_RANGED else 20)))
                break
        else:
            raise AssertionError(f"heroic item {item['id']} fits no Quartermaster page (inventory type {item['inv']})")
    return pages


def vendor_sql():
    entries = ', '.join(str(entry) for entry, _, _, _ in QUARTERMASTER_PAGES)
    lines = ['-- the Heroic Quartermaster\'s pages (src/unbound_heroic_quartermaster.cpp): prices in Heroic Sigils',
             f'DELETE FROM `npc_vendor` WHERE `entry` IN ({entries});',
             'INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`) VALUES']
    rows = []
    for entry, items in quartermaster_pages().items():
        for slot, (item, sigils) in enumerate(items):
            rows.append(f'({entry}, {slot}, {item}, 0, 0, {SIGIL_EXTENDED_COSTS[sigils]})')
    lines.append(',\n'.join(rows) + ';')
    # the Warden of Rare Wonders' pages (cosmetics)
    entries = ', '.join(str(entry) for entry, _, _ in WARDEN_PAGES)
    lines += ['', '-- the Warden of Rare Wonders\' pages (cosmetics; src/unbound_heroic_quartermaster.cpp): prices in Heroic Sigils',
              f'DELETE FROM `npc_vendor` WHERE `entry` IN ({entries});',
              'INSERT INTO `npc_vendor` (`entry`, `slot`, `item`, `maxcount`, `incrtime`, `ExtendedCost`) VALUES']
    rows = [f'({entry}, {slot}, {item}, 0, 0, {SIGIL_EXTENDED_COSTS[sigils]})'
            for entry, _, items in WARDEN_PAGES for slot, (item, sigils) in enumerate(items)]
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
    # the final bosses (two Sigils) are exactly the Bulletin Board's: the last boss of every dungeon and wing
    import bulletin_board
    finals = {entry for bosses in LOOT.values() for entry, boss in bosses.items() if boss.get('final')}
    expected = {row[1] for row in bulletin_board.DUNGEONS}
    assert finals == expected, f'final=True differs from bulletin_board.DUNGEONS: {sorted(finals ^ expected)}'
    # every Quartermaster page fits in a 3.3.5 vendor window
    for entry, items in quartermaster_pages().items():
        assert len(items) <= 150, f'Quartermaster page {entry} has {len(items)} items (at most 150)'
    for entry, _, items in WARDEN_PAGES:
        assert len(items) <= 150, f'Warden page {entry} has {len(items)} items (at most 150)'
        for item, sigils in items:
            assert sigils in SIGIL_EXTENDED_COSTS, f'no ItemExtendedCost row for {sigils} Sigils (item {item})'


def main():
    check()
    ids = ', '.join(str(i['id']) for i in HEROIC_ITEMS)
    parts = ['-- Generated by tools/heroic_loot.py - edit the tables there, not this file.',
             '-- Items are deleted and re-inserted by id (never removed): see the reversibility note in heroic_loot.py.',
             f'DELETE FROM `item_template` WHERE `entry` IN ({ids});',
             '']
    parts += [item_sql(i) + '\n' for i in HEROIC_ITEMS]
    parts += ['DROP TEMPORARY TABLE IF EXISTS `unbound_hl_tmp`;', '', loot_sql(), '', vendor_sql()]
    path = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_heroic_loot.sql')
    with open(path, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(parts) + '\n')
    print('wrote', path, f'({len(HEROIC_ITEMS)} items, {sum(len(b) for b in LOOT.values())} heroic bosses)')


if __name__ == '__main__':
    main()
