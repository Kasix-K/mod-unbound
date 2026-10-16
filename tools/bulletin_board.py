"""
Generate the Bulletin Board's quests (src/unbound_bulletin_board.cpp):

  data/sql/db-world/unbound_bulletin_board.sql

Two boards (gameobject 920000), in Stormwind's Trade District and Orgrimmar's Valley of Strength; both
factions can use either (the server is cross-faction). Level 60 only. Rewards are gold only (no
infusion progress: that stays behind killing).

Daily quests (rotated by the core's quest pools at the daily reset):
  - 2 kill bounties a day, from KILL_QUESTS (level 55-60 creatures across the classic zones)
  - for each gathering profession, 1 quest a day from its list in GATHER_QUESTS
  - for each crafting profession, 1 quest a day from its list in CRAFT_QUESTS
  A profession quest is only offered to players with that profession at the required skill
  (quest_template_addon.RequiredSkillID / RequiredSkillPoints), so everyone sees the ones for their own
  professions. The items are handed in (gathered or crafted by the player).

Weekly quests: one per tier, kill the final boss of this week's dungeon / raid (the whole group gets
credit). Every tier has a quest per dungeon (raid); src/unbound_bulletin_board.cpp picks the week's
dungeon (raid) for each tier, never the same one for two tiers, and stores it in a world state; each
quest is only available while its world state says so (conditions, CONDITION_WORLD_STATE). Tiers:
Normal, Heroic, Mythic for dungeons and raids. Only the tiers that exist get quests (Normal and Heroic
dungeons, Normal raids); the others are picked already, so adding their quests later is all it takes.

Weekly elite bounty: one of ELITE_QUESTS (elite camps in the open world, level 55-62) each week, never
the same as the week before (world state WS_ELITE).

IDs: gameobject 920000 (spawn guids 9920000-9920009), quests 920001-920999, pools 920000-920099, world
states 920001-920009 (keep WS_* and the counts in sync with src/unbound_bulletin_board.cpp).

Run after changing the lists:  python tools/bulletin_board.py
"""
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
OUT = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_bulletin_board.sql')

BOARD = 920000
BOARD_DISPLAY = 202   # "Wanted Board" (the standing board in Goldshire)
BOARD_SPAWNS = [      # guid, map, x, y, z, orientation (next to a mailbox; move with .gobject move)
    (9920000, 0, -8812.40, 651.60, 94.90, 4.88),    # Stormwind, Trade District (by the auction house)
    (9920001, 1, 1609.80, -4376.90, 9.77, 3.29),    # Orgrimmar, Valley of Strength
]

LEVEL = 60
GOLD = 10000          # copper per gold
QUEST_FLAGS_DAILY = 0x1000
QUEST_FLAGS_WEEKLY = 0x8000
QUEST_INFO_DUNGEON, QUEST_INFO_RAID = 81, 62

# World states (src/unbound_bulletin_board.cpp): index of this week's dungeon / raid per tier
WS_DUNGEON = {'Normal': 920001, 'Heroic': 920002, 'Mythic': 920003}
WS_RAID = {'Normal': 920004, 'Heroic': 920005, 'Mythic': 920006}

# ---------------------------------------------------------------- daily kill bounties (2 a day)
# (title, zone, [(creature entry, name, count), ...])
KILL_QUESTS = [
    ('Bounty: The Plaguewood', 'Eastern Plaguelands',
     [(8602, 'Monstrous Plaguebat', 10), (8598, 'Frenzied Plaguehound', 10)]),
    ('Bounty: Abominations of the Plague', 'Eastern Plaguelands',
     [(8543, 'Stitched Horror', 8), (8542, 'Death Singer', 8), (8541, 'Hate Shrieker', 8)]),
    ('Bounty: Mossflayer Trolls', 'Eastern Plaguelands',
     [(8561, 'Mossflayer Shadowhunter', 10), (8562, 'Mossflayer Cannibal', 8)]),
    ('Bounty: The Scarlet Crusade', 'Western Plaguelands',
     [(1834, 'Scarlet Paladin', 8), (1827, 'Scarlet Sentinel', 8), (1883, 'Scarlet Worker', 8)]),
    ('Bounty: The Restless Dead', 'Western Plaguelands',
     [(1795, 'Searing Ghoul', 10), (1789, 'Skeletal Acolyte', 10)]),
    ('Bounty: Wailing Spirits', 'Western Plaguelands',
     [(1804, 'Wailing Death', 8), (1802, 'Hungering Wraith', 8), (4472, 'Haunting Vision', 8)]),
    ("Bounty: Hive'Zora", 'Silithus',
     [(11727, "Hive'Zora Wasp", 12), (11728, "Hive'Zora Reaver", 8)]),
    ("Bounty: Hive'Regal", 'Silithus',
     [(11733, "Hive'Regal Slavemaker", 8), (11732, "Hive'Regal Spitfire", 8), (11734, "Hive'Regal Hive Lord", 6)]),
    ("Bounty: The Twilight's Hammer", 'Silithus',
     [(11880, 'Twilight Avenger', 8), (11881, 'Twilight Geolord', 8), (11882, 'Twilight Stonecaller', 6)]),
    ('Bounty: Stonelash Scorpids', 'Silithus',
     [(11736, 'Stonelash Pincer', 12), (11737, 'Stonelash Flayer', 12)]),
    ('Bounty: Dust and Stone', 'Silithus',
     [(11744, 'Dust Stormer', 10), (11746, 'Desert Rumbler', 8)]),
    ('Bounty: Frostsaber Rock', 'Winterspring',
     [(7432, 'Frostsaber Stalker', 10), (7433, 'Frostsaber Huntress', 8)]),
    ('Bounty: The Shardtooth Packs', 'Winterspring',
     [(7445, 'Elder Shardtooth', 10), (7446, 'Rabid Shardtooth', 8), (7443, 'Shardtooth Mauler', 10)]),
    ('Bounty: Owlbeasts and Chimaera', 'Winterspring',
     [(7453, 'Moontouched Owlbeast', 10), (7449, 'Chillwind Ravager', 10)]),
    ('Bounty: Ice Thistle Yetis', 'Winterspring',
     [(7458, 'Ice Thistle Yeti', 10), (7460, 'Ice Thistle Patriarch', 8)]),
    ('Bounty: The Blackrock Clan', 'Burning Steppes',
     [(7027, 'Blackrock Slayer', 10), (7028, 'Blackrock Warlock', 8)]),
]
KILL_REWARD = 15 * GOLD
KILL_PER_DAY = 2

# ---------------------------------------------------------------- daily profession quests (1 per profession a day)
# skill id: (profession, [(item, name, count, required skill), ...])
GATHER_QUESTS = {
    186: ('Mining', [(10620, 'Thorium Ore', 20, 250), (7911, 'Truesilver Ore', 10, 230),
                     (3858, 'Mithril Ore', 20, 175), (11370, 'Dark Iron Ore', 10, 230)]),
    182: ('Herbalism', [(13463, 'Dreamfoil', 15, 270), (13465, 'Mountain Silversage', 15, 280),
                        (13466, 'Plaguebloom', 15, 285), (13467, 'Icecap', 15, 290), (13464, 'Golden Sansam', 15, 260)]),
    393: ('Skinning', [(8170, 'Rugged Leather', 20, 250), (4304, 'Thick Leather', 20, 200),
                       (15417, 'Devilsaur Leather', 5, 250), (15408, 'Heavy Scorpid Scale', 10, 250)]),
    356: ('Fishing', [(13422, 'Stonescale Eel', 10, 250), (13889, 'Raw Whitescale Salmon', 10, 250),
                      (13759, 'Raw Nightfin Snapper', 10, 250), (13760, 'Raw Sunscale Salmon', 10, 250),
                      (13893, 'Large Raw Mightfish', 5, 250)]),
}
CRAFT_QUESTS = {
    171: ('Alchemy', [(13446, 'Major Healing Potion', 5, 275), (13444, 'Major Mana Potion', 5, 295),
                      (13452, 'Elixir of the Mongoose', 3, 280), (13457, 'Greater Fire Protection Potion', 3, 290)]),
    164: ('Blacksmithing', [(12404, 'Dense Sharpening Stone', 10, 250), (12643, 'Dense Weightstone', 10, 250),
                            (12425, 'Imperial Plate Bracers', 1, 270)]),
    165: ('Leatherworking', [(15564, 'Rugged Armor Kit', 5, 250), (15407, 'Cured Rugged Hide', 5, 250)]),
    197: ('Tailoring', [(14048, 'Bolt of Runecloth', 10, 250), (14046, 'Runecloth Bag', 2, 260),
                        (14342, 'Mooncloth', 2, 250)]),
    202: ('Engineering', [(15994, 'Thorium Widget', 5, 260), (15992, 'Dense Blasting Powder', 10, 250),
                          (15993, 'Thorium Grenade', 10, 260)]),
    333: ('Enchanting', [(20746, 'Lesser Wizard Oil', 3, 200), (20747, 'Lesser Mana Oil', 3, 250),
                         (20750, 'Wizard Oil', 3, 275)]),
    185: ('Cooking', [(12218, 'Monster Omelet', 10, 225), (12216, 'Spiced Chili Crab', 10, 225),
                      (13928, 'Grilled Squid', 10, 240), (13931, 'Nightfin Soup', 10, 250),
                      (13935, 'Baked Salmon', 10, 275)]),
    129: ('First Aid', [(14530, 'Heavy Runecloth Bandage', 20, 290), (14529, 'Runecloth Bandage', 20, 260)]),
}
GATHER_REWARD = 12 * GOLD
CRAFT_REWARD = 15 * GOLD

# ---------------------------------------------------------------- weekly dungeons and raids
HEROIC_ENTRY_OFFSET = 1000000   # tools/classic_heroics.py: a boss's heroic copy
# (dungeon, final boss entry, boss name); the order is the world state value (index + 1): append only
DUNGEONS = [
    ('The Stockade', 1716, 'Bazil Thredd'),
    ('Ragefire Chasm', 11519, 'Bazzalan'),
    ('The Deadmines', 639, 'Edwin VanCleef'),
    ('Wailing Caverns', 3654, 'Mutanus the Devourer'),
    ('Shadowfang Keep', 4275, 'Archmage Arugal'),
    ('Blackfathom Deeps', 4829, "Aku'mai"),
    ('Gnomeregan', 7800, 'Mekgineer Thermaplugg'),
    ('Razorfen Kraul', 4421, 'Charlga Razorflank'),
    ('Scarlet Monastery: Graveyard', 4543, 'Bloodmage Thalnos'),
    ('Scarlet Monastery: Library', 6487, 'Arcanist Doan'),
    ('Scarlet Monastery: Armory', 3975, 'Herod'),
    ('Scarlet Monastery: Cathedral', 3977, 'High Inquisitor Whitemane'),
    ('Razorfen Downs', 7358, 'Amnennar the Coldbringer'),
    ('Uldaman', 2748, 'Archaedas'),
    ("Zul'Farrak", 7267, 'Chief Ukorz Sandscalp'),
    ('Maraudon', 12201, 'Princess Theradras'),
    ('The Temple of Atal\'Hakkar', 5709, 'Shade of Eranikus'),
    ('Blackrock Depths', 9019, 'Emperor Dagran Thaurissan'),
    ('Lower Blackrock Spire', 9568, 'Overlord Wyrmthalak'),
    ('Upper Blackrock Spire', 10363, 'General Drakkisath'),
    ('Dire Maul: East', 11492, 'Alzzin the Wildshaper'),
    ('Dire Maul: West', 11486, 'Prince Tortheldrin'),
    ('Dire Maul: North', 11501, 'King Gordok'),
    ('Scholomance', 1853, 'Darkmaster Gandling'),
    ('Stratholme: Live', 10813, 'Balnazzar'),
    ('Stratholme: Undead', 10440, 'Baron Rivendare'),
]
RAIDS = [
    ('Molten Core', 11502, 'Ragnaros'),
    ("Onyxia's Lair", 10184, 'Onyxia'),
    ('Blackwing Lair', 11583, 'Nefarian'),
    ("Zul'Gurub", 14834, 'Hakkar'),
    ("Ruins of Ahn'Qiraj", 15339, 'Ossirian the Unscarred'),
    ("Temple of Ahn'Qiraj", 15727, "C'Thun"),
    ('Naxxramas', 351019, "Kel'Thuzad"),   # classic Naxxramas (src/naxx40)
]
# tier: (quest id base, reward, boss entry for a dungeon/raid entry, or None while the tier doesn't exist yet).
# Every tier asks for the normal boss entry: the core gives kill credit for a creature's normal entry even when
# its heroic copy (entry + HEROIC_ENTRY_OFFSET) was killed. src/unbound_bulletin_board.cpp checks the mode: a
# Normal quest only counts a kill in Normal, a Heroic quest only one in Heroic (by the quest id's tier).
DUNGEON_TIERS = {
    'Normal': (920100, 50 * GOLD, lambda boss: boss),
    'Heroic': (920200, 100 * GOLD, lambda boss: boss),
    'Mythic': (920300, 150 * GOLD, None),   # Mythic+ isn't built yet
}
RAID_TIERS = {
    'Normal': (920400, 100 * GOLD, lambda boss: boss),
    'Heroic': (920500, 200 * GOLD, None),   # Heroic raids aren't built yet
    'Mythic': (920600, 300 * GOLD, None),
}

# ---------------------------------------------------------------- weekly elite bounty (one a week)
# Elite camps in the open world, level 55-62. One bounty is offered each week, never last week's
# (src/unbound_bulletin_board.cpp, world state WS_ELITE). Append only: the position is stored.
WS_ELITE = 920007
ELITE_QUEST_BASE = 920900
ELITE_REWARD = 75 * GOLD
ELITE_GROUP = 3
ELITE_QUESTS = [
    ('The Tainted Scar', 'Blasted Lands',
     [(8717, 'Felguard Elite', 15), (8718, 'Manahound', 8), (12396, 'Doomguard Commander', 6), (8716, 'Dreadlord', 3)]),
    ('The Dragonmaw Gates', 'Wetlands',
     [(1050, 'Scalebane Royal Guard', 8), (1049, 'Wyrmkin Firebrand', 6), (1047, 'Red Scalebane', 5),
      (1048, 'Scalebane Lieutenant', 4)]),
    ('Purgation Isle', 'Hillsbrad Foothills',
     [(7071, 'Cursed Paladin', 6), (7075, 'Writhing Mage', 5), (7072, 'Cursed Justicar', 3), (7070, 'Condemned Cleric', 3)]),
    ("Tyr's Hand", 'Eastern Plaguelands',
     [(9448, 'Scarlet Praetorian', 15), (9450, 'Scarlet Curate', 8), (9451, 'Scarlet Archmage', 8)]),
    ('Alcaz Island', 'Dustwallow Marsh',
     [(4374, 'Strashaz Hydra', 8), (4368, 'Strashaz Myrmidon', 5), (4366, 'Strashaz Serpent Guard', 5),
      (4371, 'Strashaz Siren', 4)]),
    ('The Isle of Dread', 'Feralas',
     [(12800, 'Chimaerok', 6), (12801, 'Arcane Chimaerok', 6), (12802, 'Chimaerok Devourer', 6),
      (12803, 'Lord Lakmaeran', 1)]),
    ('Darkwhisper Gorge', 'Winterspring',
     [(7462, 'Hederine Manastalker', 10), (7463, 'Hederine Slayer', 10), (7461, 'Hederine Initiate', 10)]),
    ('Frostwhisper Gorge', 'Winterspring',
     [(7428, 'Frostmaul Giant', 10), (7429, 'Frostmaul Preserver', 10)]),
    ('Mazthoril', 'Winterspring',
     [(7435, 'Cobalt Wyrmkin', 10), (7437, 'Cobalt Mageweaver', 8), (7436, 'Cobalt Scalebane', 5)]),
    ('Seradane', 'The Hinterlands',
     [(12477, 'Verdantine Boughguard', 10), (12478, 'Verdantine Oracle', 8), (12479, 'Verdantine Tree Warder', 5)]),
    ('Jademir Lake', 'Feralas',
     [(5320, 'Jademir Boughguard', 10), (5317, 'Jademir Oracle', 10), (5319, 'Jademir Tree Warder', 10)]),
    ('Bough Shadow', 'Ashenvale',
     [(12474, 'Emeraldon Boughguard', 6), (12476, 'Emeraldon Oracle', 5), (12475, 'Emeraldon Tree Warder', 4)]),
]

# Quest log headers: each board quest is sorted under one of these categories (QuestSortID = -id). They are
# new QuestSort.dbc rows (IDs above the game's 376), added to the client patch and the server by
# tools/custom_dbc.py, which reads this list. Append only: the ids are stored in the quests.
SORT_OPEN_WORLD, SORT_NORMAL_DUNGEON, SORT_HEROIC_DUNGEON, SORT_MYTHIC_DUNGEON, SORT_RAIDS, SORT_GATHERING, \
    SORT_CRAFTING = range(920, 927)
QUEST_SORTS = [
    (SORT_OPEN_WORLD, 'Open World'),
    (SORT_NORMAL_DUNGEON, 'Normal Dungeon'),
    (SORT_HEROIC_DUNGEON, 'Heroic Dungeon'),
    (SORT_MYTHIC_DUNGEON, 'Mythic Dungeon'),
    (SORT_RAIDS, 'Raids'),
    (SORT_GATHERING, 'Gathering'),
    (SORT_CRAFTING, 'Crafting'),
]
DUNGEON_SORT = {'Normal': SORT_NORMAL_DUNGEON, 'Heroic': SORT_HEROIC_DUNGEON, 'Mythic': SORT_MYTHIC_DUNGEON}

# pools (pool_template / pool_quest), one quest a day per pool except the kill bounties
POOL_KILL = 920000
POOL_FIRST_PROFESSION = 920001


def esc(text):
    return "'" + text.replace('\\', '\\\\').replace("'", "\\'") + "'"


QUEST_COLUMNS = ['ID', 'QuestType', 'QuestLevel', 'MinLevel', 'QuestSortID', 'QuestInfoID', 'SuggestedGroupNum',
                 'RewardXPDifficulty', 'RewardMoney', 'Flags', 'AllowableRaces', 'LogTitle', 'LogDescription',
                 'QuestDescription', 'AreaDescription', 'QuestCompletionLog',
                 'RequiredNpcOrGo1', 'RequiredNpcOrGo2', 'RequiredNpcOrGo3', 'RequiredNpcOrGo4',
                 'RequiredNpcOrGoCount1', 'RequiredNpcOrGoCount2', 'RequiredNpcOrGoCount3', 'RequiredNpcOrGoCount4',
                 'RequiredItemId1', 'RequiredItemCount1', 'ObjectiveText1', 'ObjectiveText2', 'ObjectiveText3',
                 'ObjectiveText4', 'VerifiedBuild']


def quest_row(qid, title, log, description, flags, reward, kills=(), item=None, info=0, group=0, area='', sort=0):
    kills = list(kills) + [(0, 0)] * (4 - len(kills))
    # QuestType 2: a normal quest (0 would make it auto-complete, skipping its objectives).
    # QuestSortID -sort: the quest log header (QUEST_SORTS).
    row = [qid, 2, LEVEL, LEVEL, -sort, info, group, 0, reward, flags, 0, esc(title), esc(log),
           esc(description), esc(area), esc('Return to a Bulletin Board.')]
    row += [k[0] for k in kills] + [k[1] for k in kills]
    row += [item[0] if item else 0, item[1] if item else 0, "''", "''", "''", "''", 0]
    return '(' + ', '.join(str(v) for v in row) + ')'


def main():
    quests, addons, offers, requests, conditions, pool_templates, pool_quests = [], [], [], [], [], [], []

    def add(qid, title, log, description, flags, reward, kills=(), item=None, info=0, group=0, area='',
            skill=(0, 0), offer='', request='', sort=0):
        quests.append(quest_row(qid, title, log, description, flags, reward, kills, item, info, group, area, sort))
        # SpecialFlags 1: repeatable (the core expects it on daily and weekly quests)
        addons.append(f'({qid}, 0, 0, 0, 0, 0, 0, 0, 0, 0, {skill[0]}, {skill[1]}, 0, 0, 0, 0, 0, 1)')
        offers.append(f'({qid}, 0, 0, 0, 0, 0, 0, 0, 0, {esc(offer)}, 0)')
        if request:
            requests.append(f'({qid}, 0, 0, {esc(request)}, 0)')

    # daily kill bounties
    pool_templates.append(f"({POOL_KILL}, {KILL_PER_DAY}, 'Bulletin Board - daily kill bounties')")
    for i, (title, zone, targets) in enumerate(KILL_QUESTS, start=1):
        qid = 920000 + i
        names = ', '.join(f'{count} {name}' for _, name, count in targets)
        add(qid, title, f'Slay {names} in {zone}.',
            f'By order of the Bulletin Board: the {zone} grow more dangerous by the day. Thin their numbers and '
            f'collect the bounty.$B$BSlay {names}.',
            QUEST_FLAGS_DAILY, KILL_REWARD, kills=[(entry, count) for entry, _, count in targets], area=zone,
            offer='Good hunting. The bounty is yours.', sort=SORT_OPEN_WORLD)
        pool_quests.append(f"({qid}, {POOL_KILL}, {esc(title)})")

    # daily profession quests: one pool per profession
    pool = POOL_FIRST_PROFESSION
    for group, base, reward, verb, sort in ((GATHER_QUESTS, 920700, GATHER_REWARD, 'Gather', SORT_GATHERING),
                                            (CRAFT_QUESTS, 920800, CRAFT_REWARD, 'Craft', SORT_CRAFTING)):
        for p, (skill, (profession, items)) in enumerate(group.items()):
            pool_templates.append(f"({pool}, 1, {esc('Bulletin Board - daily ' + profession)})")
            for i, (item, name, count, points) in enumerate(items, start=1):
                qid = base + p * 10 + i
                title = f'{profession}: {name}'
                add(qid, title, f'{verb} {count} {name} and bring them to a Bulletin Board.',
                    f'A request has been pinned to the board: {count} {name}, wanted by the end of the day. Only '
                    f'someone skilled in {profession} need apply.',
                    QUEST_FLAGS_DAILY, reward, item=(item, count), skill=(skill, points),
                    offer='Just what was asked for. The payment is yours.',
                    request=f'Have you brought the {name}?', sort=sort)
                pool_quests.append(f"({qid}, {pool}, {esc(title)})")
            pool += 1

    # weekly dungeons and raids
    for places, tiers, ws, kind, info in ((DUNGEONS, DUNGEON_TIERS, WS_DUNGEON, 'dungeon', QUEST_INFO_DUNGEON),
                                          (RAIDS, RAID_TIERS, WS_RAID, 'raid', QUEST_INFO_RAID)):
        for tier, (base, reward, boss_of) in tiers.items():
            if boss_of is None:
                continue
            group = 5 if kind == 'dungeon' else 10
            for i, (name, boss, boss_name) in enumerate(places, start=1):
                qid = base + i
                label = f'{name} ({tier})'
                difficulty = '' if tier == 'Normal' else f' on {tier} difficulty'
                add(qid, f'Weekly {kind.title()}: {label}', f'Defeat {boss_name} in {name}{difficulty}.',
                    f'This week the board calls for {name}{difficulty}. Clear it and defeat {boss_name}; '
                    f'your whole group shares the credit.', QUEST_FLAGS_WEEKLY, reward,
                    kills=[(boss_of(boss), 1)], info=info, group=group, area=name,
                    offer=f'{boss_name} is defeated. Well done; the reward is yours.',
                    sort=DUNGEON_SORT[tier] if kind == 'dungeon' else SORT_RAIDS)
                conditions.append(f"(19, 0, {qid}, 0, 0, 11, 0, {ws[tier]}, {i}, 0, 0, 0, 0, '', "
                                  f"{esc(f'Bulletin Board: {label} is this week' + chr(39) + 's ' + tier + ' ' + kind)})")

    # weekly elite bounty: one of ELITE_QUESTS, chosen each week
    for i, (place, zone, targets) in enumerate(ELITE_QUESTS, start=1):
        qid = ELITE_QUEST_BASE + i
        names = ', '.join(f'{count} {name}' for _, name, count in targets)
        add(qid, f'Weekly Elite Bounty: {place}', f'Slay {names} at {place} in {zone}.',
            f'The board has posted a bounty on the elites of {place}, {zone}. They are dangerous: bring '
            f'friends if you need them.$B$BSlay {names}.',
            QUEST_FLAGS_WEEKLY, ELITE_REWARD, kills=[(entry, count) for entry, _, count in targets],
            group=ELITE_GROUP, area=zone, offer=f'{place} will be quieter for a while. The bounty is yours.',
            sort=SORT_OPEN_WORLD)
        conditions.append(f"(19, 0, {qid}, 0, 0, 11, 0, {WS_ELITE}, {i}, 0, 0, 0, 0, '', "
                          f"{esc('Bulletin Board: this week' + chr(39) + 's elite bounty is ' + place)})")

    ids = 'BETWEEN 920001 AND 920999'
    out = [
        '-- Generated by tools/bulletin_board.py - run it again instead of editing this file.',
        '-- mod-unbound Bulletin Board: daily and weekly quests (src/unbound_bulletin_board.cpp).',
        '',
        '-- The board (a quest giver gameobject), in Stormwind and Orgrimmar',
        f'DELETE FROM `gameobject_template` WHERE `entry` = {BOARD};',
        'INSERT INTO `gameobject_template` (`entry`, `type`, `displayId`, `name`, `IconName`, `castBarCaption`, `unk1`, '
        '`size`, `AIName`, `ScriptName`, `VerifiedBuild`) VALUES',
        f"({BOARD}, 2, {BOARD_DISPLAY}, 'Bulletin Board', '', '', '', 1, '', '', 0);",
        f'DELETE FROM `gameobject` WHERE `id` = {BOARD} OR `guid` BETWEEN 9920000 AND 9920009;',
        'INSERT INTO `gameobject` (`guid`, `id`, `map`, `zoneId`, `areaId`, `spawnMask`, `phaseMask`, `position_x`, '
        '`position_y`, `position_z`, `orientation`, `rotation0`, `rotation1`, `rotation2`, `rotation3`, '
        '`spawntimesecs`, `animprogress`, `state`, `ScriptName`, `VerifiedBuild`) VALUES',
        ',\n'.join(f'({g}, {BOARD}, {m}, 0, 0, 1, 1, {x}, {y}, {z}, {o}, 0, 0, '
                   f'{math.sin(o / 2):.6f}, {math.cos(o / 2):.6f}, 300, 0, 1, \'\', 0)'
                   for g, m, x, y, z, o in BOARD_SPAWNS) + ';',
        '',
        '-- Quests',
        f'DELETE FROM `quest_template` WHERE `ID` {ids};',
        'INSERT INTO `quest_template` (' + ', '.join('`' + c + '`' for c in QUEST_COLUMNS) + ') VALUES',
        ',\n'.join(quests) + ';',
        f'DELETE FROM `quest_template_addon` WHERE `ID` {ids};',
        'INSERT INTO `quest_template_addon` (`ID`, `MaxLevel`, `AllowableClasses`, `SourceSpellID`, `PrevQuestID`, '
        '`NextQuestID`, `ExclusiveGroup`, `BreadcrumbForQuestId`, `RewardMailTemplateID`, `RewardMailDelay`, '
        '`RequiredSkillID`, `RequiredSkillPoints`, `RequiredMinRepFaction`, `RequiredMaxRepFaction`, '
        '`RequiredMinRepValue`, `RequiredMaxRepValue`, `ProvidedItemCount`, `SpecialFlags`) VALUES',
        ',\n'.join(addons) + ';',
        f'DELETE FROM `quest_offer_reward` WHERE `ID` {ids};',
        'INSERT INTO `quest_offer_reward` (`ID`, `Emote1`, `Emote2`, `Emote3`, `Emote4`, `EmoteDelay1`, `EmoteDelay2`, '
        '`EmoteDelay3`, `EmoteDelay4`, `RewardText`, `VerifiedBuild`) VALUES',
        ',\n'.join(offers) + ';',
        f'DELETE FROM `quest_request_items` WHERE `ID` {ids};',
        'INSERT INTO `quest_request_items` (`ID`, `EmoteOnComplete`, `EmoteOnIncomplete`, `CompletionText`, '
        '`VerifiedBuild`) VALUES',
        ',\n'.join(requests) + ';',
        '',
        '-- Both boards start and end every quest',
        f'DELETE FROM `gameobject_queststarter` WHERE `id` = {BOARD} OR `quest` {ids};',
        'INSERT INTO `gameobject_queststarter` (`id`, `quest`) VALUES',
        ',\n'.join(f'({BOARD}, {q.split(",")[0][1:]})' for q in quests) + ';',
        f'DELETE FROM `gameobject_questender` WHERE `id` = {BOARD} OR `quest` {ids};',
        'INSERT INTO `gameobject_questender` (`id`, `quest`) VALUES',
        ',\n'.join(f'({BOARD}, {q.split(",")[0][1:]})' for q in quests) + ';',
        '',
        '-- Daily rotation: the core picks max_limit quests of each pool at the daily reset',
        'DELETE FROM `pool_quest` WHERE `pool_entry` BETWEEN 920000 AND 920099;',
        'DELETE FROM `pool_template` WHERE `entry` BETWEEN 920000 AND 920099;',
        'INSERT INTO `pool_template` (`entry`, `max_limit`, `description`) VALUES',
        ',\n'.join(pool_templates) + ';',
        'INSERT INTO `pool_quest` (`entry`, `pool_entry`, `description`) VALUES',
        ',\n'.join(pool_quests) + ';',
        '',
        "-- Weekly: only this week's dungeon / raid of each tier (world states set by src/unbound_bulletin_board.cpp)",
        f'DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 19 AND `SourceEntry` {ids};',
        'INSERT INTO `conditions` (`SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`, '
        '`ConditionTypeOrReference`, `ConditionTarget`, `ConditionValue1`, `ConditionValue2`, `ConditionValue3`, '
        '`NegativeCondition`, `ErrorType`, `ErrorTextId`, `ScriptName`, `Comment`) VALUES',
        ',\n'.join(conditions) + ';',
    ]
    with open(OUT, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(out) + '\n')
    print(f'wrote {OUT}: {len(quests)} quests, {len(pool_templates)} pools, {len(conditions)} weekly conditions')


if __name__ == '__main__':
    main()
