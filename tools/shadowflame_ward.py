"""
The Shadowflame Ward: a quest chain (about as long as the Drakefire Amulet's) for a cloak that protects from
Shadowflame in Blackwing Lair, replacing the Onyxia Scale Cloak (unobtainable here on purpose).

The core only checks for the Onyxia Scale Cloak's aura (spell 22683) when Shadowflame hits
(SpellEffects.cpp, instance_blackwing_lair.cpp), so the Ward simply has that aura on equip: no C++.

The chain (neutral, from Kaelastrasz of the red dragonflight at Thorium Point, Searing Gorge):
  1        Shadows Over Blackrock: the story; opens the five flights at once (do them in any order)
  2, 3     black: scales in the Burning Steppes, then the pristine scale from Vexathrax there
  4, 5     red: scales in Grim Batol (Wetlands), then the pristine scale from Pyraxis there
  6, 7     blue: scales in Mazthoril (Winterspring), then the pristine scale from Azurathys in Azshara
  8        green: scales from the Nightmare dragonspawn at Seradane, Bough Shadow or the Dream Bough
  9        bronze: the scale of Chronalis (Caverns of Time, Tanaris)
  10       The Scales Assembled: needs all five flights done
  11       Scale of the Broodmother: the Scale of Onyxia (now a quest drop from Onyxia) binds the scales
  12       The Shadowflame Ward: the cloak
Vexathrax, Pyraxis and Azurathys are new 10-minute elites using the models of the rares Teremus the Devourer,
Narillasanz and Azurous (copies of their templates and fight scripts, renamed and set to level 60).

Generated into:
  server: data/sql/db-world/unbound_shadowflame_ward.sql (items, NPCs, spawns, quests, scale drops)
          data/sql/db-world/unbound_classic_onyxia.sql holds the Scale of Onyxia drop (Onyxia's loot is
          rebuilt there)
          data/sql/db-world/unbound_custom_dbc.sql and the client's patch-Z.MPQ (Item.dbc rows, via
          tools/custom_dbc.py)

Run after changing this file:
  python tools/shadowflame_ward.py
  python tools/custom_dbc.py --client <client>

Reserved IDs: items 912100-912199, NPCs 190206-190209, spawn guids 9190206-9190209, quests 921001-921099.
Re-running deletes and re-inserts exactly these rows. Never remove an item once players may own it.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from heroic_loot import sql_str, STA  # noqa: E402

OUT = os.path.join(MODULE, 'data', 'sql', 'db-world', 'unbound_shadowflame_ward.sql')
GOLD = 10000
SEARING_GORGE = 51           # QuestSortID: the quest log header is the zone
SPELL_ONYXIA_SCALE_CLOAK = 22683
SCALE_OF_ONYXIA = 15410      # dropped by Onyxia for the quest (unbound_classic_onyxia.sql)
SCALE_CHANCE = 35            # % per kill, for players on the quest
SCALE_COUNT = 8

# ---------------------------------------------------------------- items
WARD = 912100
UNFINISHED_WARD = 912109
SCALES = {  # flight: (item, name, icon display)
    'black': (912101, 'Black Dragonflight Scale', 20914),
    'red': (912102, 'Red Dragonflight Scale', 26374),
    'blue': (912103, 'Blue Dragonflight Scale', 26375),
    'green': (912104, 'Green Dragonflight Scale', 21363),
    'bronze': (912105, 'Bronze Dragonflight Scale', 22838),
}
PRISTINE = {
    'black': (912106, 'Pristine Black Dragonflight Scale', 20914),
    'red': (912107, 'Pristine Red Dragonflight Scale', 26374),
    'blue': (912108, 'Pristine Blue Dragonflight Scale', 26375),
}
QUEST_ITEM_BASE = 13920      # Healthy Dragon Scale: a quest item to copy
CLOAK_BASE = 15138           # Onyxia Scale Cloak

# ---------------------------------------------------------------- creatures
AGENT = dict(entry=190206, guid=9190206, name='Kaelastrasz', subname='The Red Dragonflight', display=24976,
             # Thorium Point, Searing Gorge, beside Hansel Heavyhands (move with .npc move)
             map=0, x=-6517.5, y=-1178.0, z=309.34, o=4.0)
DRAGONS = {  # flight: new elite copied from a rare's template and script
    'black': dict(entry=190207, guid=9190207, name='Vexathrax', base=7846,      # Teremus the Devourer
                  map=0, x=-7758.78, y=-2958.45, z=133.343, o=3.114, zone='the Burning Steppes'),
    'red': dict(entry=190208, guid=9190208, name='Pyraxis', base=2447,          # Narillasanz
                map=0, x=-3480.7, y=-3679.04, z=62.1456, o=2.287, zone='Grim Batol'),
    'blue': dict(entry=190209, guid=9190209, name='Azurathys', base=10202,      # Azurous
                 map=1, x=2756.68, y=-5395.01, z=116.377, o=1.502, zone='Azshara'),
}
DRAGON_LEVEL = 60
DRAGON_HEALTH = 6            # about twice a normal level 60 elite (the camps' elites use 3)
DRAGON_DAMAGE = 3.0
DRAGON_RESPAWN = 600
DRAGON_GOLD = (30000, 60000)

# creatures that drop each flight's scales (loot ids; Scalebane Royal Guard shares 1049)
SCALE_DROPPERS = {
    'black': [7040, 7041, 7042, 7043, 7044, 7045, 7046],        # Burning Steppes dragonkin
    'red': [1045, 1046, 1047, 1048, 1049, 12899],                # Grim Batol dragonkin, Axtroz
    'blue': [7435, 7436, 7437, 10661, 10662, 10663, 10664],     # Mazthoril dragonkin
    'green': [12474, 12475, 12476, 12477, 12478, 12479, 5317, 5319, 5320,   # the three Nightmare camps
              12496, 12497, 12498, 5312, 5314, 5718],
    'bronze': [8197],                                            # Chronalis
}

# ---------------------------------------------------------------- quests
Q = {name: 921000 + n for n, name in enumerate(
    ['intro', 'black', 'black_pristine', 'red', 'red_pristine', 'blue', 'blue_pristine', 'green', 'bronze',
     'assembled', 'broodmother', 'ward'], 1)}
FLIGHTS_DONE = [Q['black_pristine'], Q['red_pristine'], Q['blue_pristine'], Q['green'], Q['bronze']]
ALL_FLIGHTS_GROUP = -Q['assembled']   # each-from-all exclusive group: all five must be done for 'assembled'

QUESTS = [
    # key, title, objective (log), description, completion (request) text, reward text, item (id, count),
    # previous quest, money, reward item
    ('intro', 'Shadows Over Blackrock',
     'Speak with Kaelastrasz at Thorium Point.',
     "Above us, in the spire of Blackrock, Nefarian breathes a fire that is not fire: Shadowflame, the dark "
     "flame of Deathwing's line. It burns flesh and soul alike, and no mortal armor turns it.$B$BOnce, champions "
     "wore cloaks of Onyxia's own scales against it. Her scales are not enough on their own. But a ward woven "
     "from the scales of all five flights, bound with the scale of the Broodmother herself... that, $N, would "
     "hold.$B$BWill you gather them?",
     '', 'Then we begin. Five flights, five scales. Go where you will; I will be here.', None, 0, 0, None),
    ('black', 'Scales of the Black Brood',
     'Bring 8 Black Dragonflight Scales to Kaelastrasz at Thorium Point.',
     "The black brood is the heart of the ward: only a black scale knows Shadowflame for what it is. The "
     "Burning Steppes crawl with Nefarian's dragonkin. Take their scales, $N. Eight should be enough.",
     'Have you brought the black scales?', 'Dark and still warm. Good.',
     (SCALES['black'][0], SCALE_COUNT), 'intro', 3 * GOLD, None),
    ('black_pristine', 'Vexathrax',
     'Bring the Pristine Black Dragonflight Scale from Vexathrax to Kaelastrasz at Thorium Point.',
     "Common scales hold the weave, but the ward needs a heartscale for each flight: one taken from a dragon "
     "of true age and strength. In the Burning Steppes a drake named Vexathrax hunts for its master. Bring me "
     "its pristine scale.",
     'Is Vexathrax dead?', 'A pristine heartscale. Vexathrax will not be missed.',
     (PRISTINE['black'][0], 1), 'black', 4 * GOLD, None),
    ('red', 'Scales of the Red Brood',
     'Bring 8 Red Dragonflight Scales to Kaelastrasz at Thorium Point.',
     "It grieves me to ask it. My own flight's dragonkin still haunt Grim Batol, in the Wetlands, maddened by "
     "what the Dragonmaw did to them there. They will not listen to reason any longer. Bring me eight of "
     "their scales, $N, and be quick about it.",
     'Did you find my kin in Grim Batol?', 'Red as the life they guarded. Thank you, $N.',
     (SCALES['red'][0], SCALE_COUNT), 'intro', 3 * GOLD, None),
    ('red_pristine', 'Pyraxis',
     'Bring the Pristine Red Dragonflight Scale from Pyraxis to Kaelastrasz at Thorium Point.',
     "A drake of my flight called Pyraxis rules Grim Batol's broken gates now, and the madness is deepest in "
     "him. End it, $N, and bring me his heartscale. He would have wanted it to protect someone.",
     'Is it done?', 'Rest now, Pyraxis.',
     (PRISTINE['red'][0], 1), 'red', 4 * GOLD, None),
    ('blue', 'Scales of the Blue Brood',
     "Bring 8 Blue Dragonflight Scales to Kaelastrasz at Thorium Point.",
     "Malygos's children guard their magic jealously in the caves of Mazthoril, in Winterspring. A blue scale "
     "will hold the weave together where fire would tear it apart. Bring me eight.",
     'Have you been to Mazthoril?', 'Cold to the touch, and humming with arcane power. Perfect.',
     (SCALES['blue'][0], SCALE_COUNT), 'intro', 3 * GOLD, None),
    ('blue_pristine', 'Azurathys',
     'Bring the Pristine Blue Dragonflight Scale from Azurathys to Kaelastrasz at Thorium Point.',
     "The blue heartscale must come from Azurathys, who guards the blue dragonkin's camp in Azshara. "
     "Azurathys is old and proud, and will not give it willingly.",
     'Azurathys?', 'It still glows. Azshara will be quieter now.',
     (PRISTINE['blue'][0], 1), 'blue', 4 * GOLD, None),
    ('green', 'Scales of the Dreaming',
     'Bring 8 Green Dragonflight Scales to Kaelastrasz at Thorium Point.',
     "Something has gone wrong in the Emerald Dream. Ysera's dragonkin now guard the great trees at Seradane "
     "in the Hinterlands, Bough Shadow in Ashenvale and the Dream Bough in Feralas, and they attack anyone who "
     "comes near. Their scales will keep the ward from burning. Bring me eight, from any of the three.",
     'Did the Dream let you go?', 'They smell of rain and nightmares. These will do.',
     (SCALES['green'][0], SCALE_COUNT), 'intro', 3 * GOLD, None),
    ('bronze', 'Scales of the Timeless',
     'Bring the Bronze Dragonflight Scale from Chronalis to Kaelastrasz at Thorium Point.',
     "The bronze flight gives nothing freely, least of all to me. At the Caverns of Time in Tanaris, "
     "Chronalis tests all who come near. Pass his test the hard way, $N: one bronze scale will anchor the ward "
     "in time, so it cannot fade.",
     'Did Chronalis yield?', 'It is warm and ticks like a heartbeat. Nozdormu will understand. I hope.',
     (SCALES['bronze'][0], 1), 'intro', 4 * GOLD, None),
    ('assembled', 'The Scales Assembled',
     'Speak with Kaelastrasz at Thorium Point.',
     "Black, red, blue, green and bronze. All five flights, laid out together for the first time in an age. "
     "I can weave them now, $N, but the weave will not hold Shadowflame... not yet.",
     '', 'One scale remains, and it is the one that matters most.', None, 'black_pristine', 0, None),
    ('broodmother', 'Scale of the Broodmother',
     'Bring the Scale of Onyxia to Kaelastrasz at Thorium Point.',
     "Shadowflame is Deathwing's fire, and only his own blood can turn it. Onyxia, his daughter, lairs in "
     "Dustwallow Marsh. Slay her and take a scale from her hide: with it I can bind the five flights' scales "
     "into one ward.",
     'Is the Broodmother dead?',
     "Her scale... At last. Here, take the weave while I prepare the binding. Do not let it out of your sight.",
     (SCALE_OF_ONYXIA, 1), 'assembled', 10 * GOLD, (UNFINISHED_WARD, 1)),
    ('ward', 'The Shadowflame Ward',
     'Give the Unfinished Shadowflame Ward to Kaelastrasz at Thorium Point.',
     "Everything is ready, $N. Give me the weave and I will bind it with the fire of my flight. When it is "
     "done, no Shadowflame will touch you.",
     'The weave, $N.',
     "It is done. Wear it into Blackwing Lair, and let Nefarian's fire break against the scales of every "
     "flight he has wronged.",
     (UNFINISHED_WARD, 1), 'broodmother', 0, (WARD, 1)),
]

# Item.dbc fields for tools/custom_dbc.py: ID, Class, SubClass, SoundOverride, Material, Display, InventoryType, Sheath
QUEST_ITEMS = [(item, name, icon, SCALE_COUNT) for item, name, icon in SCALES.values()]
QUEST_ITEMS[-1] = QUEST_ITEMS[-1][:3] + (1,)  # one bronze scale
QUEST_ITEMS += [(item, name, icon, 1) for item, name, icon in PRISTINE.values()]
QUEST_ITEMS += [(UNFINISHED_WARD, 'Unfinished Shadowflame Ward', 25921, 1)]


def item_dbc_rows():
    rows = [(item, 12, 0, -1, 4, icon, 0, 0) for item, _, icon, _ in QUEST_ITEMS]
    rows.append((WARD, 4, 1, -1, 7, 25921, 16, 0))
    return rows


def values(rows):
    def lit(v):
        if v is None:
            return 'NULL'
        return sql_str(v) if isinstance(v, str) else str(v)
    return ',\n'.join('(' + ', '.join(lit(v) for v in r) + ')' for r in rows) + ';'


def items_sql():
    ids = [i[0] for i in QUEST_ITEMS] + [WARD]
    out = ['-- items', f"DELETE FROM `item_template` WHERE `entry` IN ({', '.join(map(str, ids))});"]
    for item, name, icon, count in QUEST_ITEMS:
        quality = 2 if item in [p[0] for p in PRISTINE.values()] or item == UNFINISHED_WARD else 1
        out += [
            'DROP TEMPORARY TABLE IF EXISTS `unbound_sw_tmp`;',
            f'CREATE TEMPORARY TABLE `unbound_sw_tmp` SELECT * FROM `item_template` WHERE `entry` = {QUEST_ITEM_BASE};',
            f"UPDATE `unbound_sw_tmp` SET `entry` = {item}, `name` = {sql_str(name)}, `description` = '', "
            f"`class` = 12, `subclass` = 0, `Material` = 4, `displayid` = {icon}, `Quality` = {quality}, `bonding` = 4, "
            f"`Flags` = 2048, `stackable` = {count}, `maxcount` = {count}, `BuyPrice` = 0, `SellPrice` = 0, "
            "`startquest` = 0, `VerifiedBuild` = 0;",
            'INSERT INTO `item_template` SELECT * FROM `unbound_sw_tmp`;']
    # The Shadowflame Ward: epic, item level 66; the Onyxia Scale Cloak's aura gives the Shadowflame protection
    out += [
        'DROP TEMPORARY TABLE IF EXISTS `unbound_sw_tmp`;',
        f'CREATE TEMPORARY TABLE `unbound_sw_tmp` SELECT * FROM `item_template` WHERE `entry` = {CLOAK_BASE};',
        f"UPDATE `unbound_sw_tmp` SET `entry` = {WARD}, `name` = 'Shadowflame Ward', "
        "`description` = 'Woven from the scales of all five dragonflights.', `Quality` = 4, `ItemLevel` = 66, "
        "`RequiredLevel` = 60, `bonding` = 1, `maxcount` = 1, `armor` = 60, "
        f"`stat_type1` = {STA}, `stat_value1` = 12, `fire_res` = 10, `shadow_res` = 10, "
        f"`spellid_1` = {SPELL_ONYXIA_SCALE_CLOAK}, `spelltrigger_1` = 1, "
        "`BuyPrice` = 0, `SellPrice` = 30000, `RequiredSkill` = 0, `RequiredSkillRank` = 0, `VerifiedBuild` = 0;",
        'INSERT INTO `item_template` SELECT * FROM `unbound_sw_tmp`;',
        'DROP TEMPORARY TABLE IF EXISTS `unbound_sw_tmp`;', '']
    return out


def creatures_sql():
    entries = [AGENT['entry']] + [d['entry'] for d in DRAGONS.values()]
    ids = ', '.join(map(str, entries))
    guids = ', '.join(str(g) for g in [AGENT['guid']] + [d['guid'] for d in DRAGONS.values()])
    out = ['-- NPCs', f'DELETE FROM `creature_template` WHERE `entry` IN ({ids});',
           # the quest giver: friendly to both factions (35), questgiver (2)
           'INSERT INTO `creature_template` (`entry`, `name`, `subname`, `minlevel`, `maxlevel`, `exp`, `faction`, '
           '`npcflag`, `rank`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`, '
           '`HealthModifier`, `RegenHealth`, `flags_extra`, `ScriptName`) VALUES',
           values([[AGENT['entry'], AGENT['name'], AGENT['subname'], 63, 63, 0, 35, 2, 0, 2000, 2000, 8, 0, 7, 10,
                    1, 2, '']])]
    for d in DRAGONS.values():
        out += [
            f"-- {d['name']}: a copy of creature {d['base']} (model, spells, script), level {DRAGON_LEVEL}, own loot",
            'DROP TEMPORARY TABLE IF EXISTS `unbound_sw_tmp`;',
            f"CREATE TEMPORARY TABLE `unbound_sw_tmp` SELECT * FROM `creature_template` WHERE `entry` = {d['base']};",
            f"UPDATE `unbound_sw_tmp` SET `entry` = {d['entry']}, `name` = {sql_str(d['name'])}, `subname` = NULL, "
            f"`minlevel` = {DRAGON_LEVEL}, `maxlevel` = {DRAGON_LEVEL}, `rank` = 1, "
            f"`HealthModifier` = {DRAGON_HEALTH}, `DamageModifier` = {DRAGON_DAMAGE}, `lootid` = {d['entry']}, "
            f"`skinloot` = 0, `pickpocketloot` = 0, `mingold` = {DRAGON_GOLD[0]}, `maxgold` = {DRAGON_GOLD[1]}, "
            "`ScriptName` = '', `VerifiedBuild` = 0;",
            'INSERT INTO `creature_template` SELECT * FROM `unbound_sw_tmp`;']
    out += ['DROP TEMPORARY TABLE IF EXISTS `unbound_sw_tmp`;',
            f'DELETE FROM `creature_template_model` WHERE `CreatureID` IN ({ids});',
            'INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, '
            '`Probability`, `VerifiedBuild`) VALUES',
            values([[AGENT['entry'], 0, AGENT['display'], 1, 1, 0]])]
    for d in DRAGONS.values():
        out.append('INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, '
                   f"`Probability`, `VerifiedBuild`) SELECT {d['entry']}, `Idx`, `CreatureDisplayID`, `DisplayScale`, "
                   f"`Probability`, 0 FROM `creature_template_model` WHERE `CreatureID` = {d['base']};")
    out += [f'DELETE FROM `smart_scripts` WHERE `source_type` = 0 AND `entryorguid` IN ({ids});']
    for d in DRAGONS.values():
        out.append(
            'INSERT INTO `smart_scripts` (`entryorguid`, `source_type`, `id`, `link`, `event_type`, '
            '`event_phase_mask`, `event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, '
            '`event_param4`, `event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, '
            '`action_param3`, `action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, '
            '`target_param2`, `target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, '
            f"`comment`) SELECT {d['entry']}, `source_type`, `id`, `link`, `event_type`, `event_phase_mask`, "
            '`event_chance`, `event_flags`, `event_param1`, `event_param2`, `event_param3`, `event_param4`, '
            '`event_param5`, `event_param6`, `action_type`, `action_param1`, `action_param2`, `action_param3`, '
            '`action_param4`, `action_param5`, `action_param6`, `target_type`, `target_param1`, `target_param2`, '
            '`target_param3`, `target_param4`, `target_x`, `target_y`, `target_z`, `target_o`, '
            f"CONCAT({sql_str(d['name'] + ' (copy): ')}, `comment`) FROM `smart_scripts` "
            f"WHERE `source_type` = 0 AND `entryorguid` = {d['base']};")
    spawns = [[AGENT['guid'], AGENT['entry'], AGENT['map'], 1, 1, AGENT['x'], AGENT['y'], AGENT['z'], AGENT['o'],
               300, 0, 0, 'mod-unbound Shadowflame Ward quest giver']]
    spawns += [[d['guid'], d['entry'], d['map'], 1, 1, d['x'], d['y'], d['z'], d['o'], DRAGON_RESPAWN, 0, 0,
                'mod-unbound Shadowflame Ward elite'] for d in DRAGONS.values()]
    out += ['', f'DELETE FROM `creature` WHERE `guid` IN ({guids}) OR `id` IN ({ids});',
            'INSERT INTO `creature` (`guid`, `id`, `map`, `spawnMask`, `phaseMask`, `position_x`, `position_y`, '
            '`position_z`, `orientation`, `spawntimesecs`, `wander_distance`, `MovementType`, `Comment`) VALUES',
            values(spawns), '']
    return out


def loot_sql():
    scale_ids = [i[0] for i in QUEST_ITEMS if i[0] != UNFINISHED_WARD]
    dragon_ids = [d['entry'] for d in DRAGONS.values()]
    rows = []
    for flight, droppers in SCALE_DROPPERS.items():
        item, name, _ = SCALES[flight]
        chance = 100 if flight == 'bronze' else SCALE_CHANCE
        rows += [[loot, item, 0, chance, 1, 1, 0, 1, 1, f'{name} (Shadowflame Ward quest)']
                 for loot in sorted(set(droppers))]
    for flight, d in DRAGONS.items():
        item, name, _ = PRISTINE[flight]
        rows.append([d['entry'], item, 0, 100, 1, 1, 0, 1, 1, f"{d['name']} - {name} (Shadowflame Ward quest)"])
        scale, scale_name, _ = SCALES[flight]
        rows.append([d['entry'], scale, 0, 100, 1, 1, 0, 1, 1, f"{d['name']} - {scale_name} (Shadowflame Ward quest)"])
    return ['-- scale drops (only for players on the quest)',
            f"DELETE FROM `creature_loot_template` WHERE `Item` IN ({', '.join(map(str, scale_ids))}) "
            f"OR `Entry` IN ({', '.join(map(str, dragon_ids))});",
            'INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, '
            '`LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES',
            values(rows), '']


def quests_sql():
    ids = ', '.join(str(Q[q[0]]) for q in QUESTS)
    qrows, addons, offers, requests, starters = [], [], [], [], []
    for key, title, log, desc, request, reward, item, prev, money, reward_item in QUESTS:
        qid = Q[key]
        qrows.append([qid, 2, 60, 58, SEARING_GORGE, 0, 0, 0, money, 0, 0, title, log, desc, '',
                      'Return to Kaelastrasz at Thorium Point in the Searing Gorge.',
                      item[0] if item else 0, item[1] if item else 0,
                      reward_item[0] if reward_item else 0, reward_item[1] if reward_item else 0, 0])
        group = ALL_FLIGHTS_GROUP if qid in FLIGHTS_DONE else 0
        addons.append([qid, 0, 0, 0, Q[prev] if prev else 0, 0, group, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
        offers.append([qid, 0, 0, 0, 0, 0, 0, 0, 0, reward, 0])
        if request:
            requests.append([qid, 0, 0, request, 0])
        starters.append([AGENT['entry'], qid])
    return ['-- quests',
            f'DELETE FROM `quest_template` WHERE `ID` IN ({ids});',
            'INSERT INTO `quest_template` (`ID`, `QuestType`, `QuestLevel`, `MinLevel`, `QuestSortID`, `QuestInfoID`, '
            '`SuggestedGroupNum`, `RewardXPDifficulty`, `RewardMoney`, `Flags`, `AllowableRaces`, `LogTitle`, '
            '`LogDescription`, `QuestDescription`, `AreaDescription`, `QuestCompletionLog`, `RequiredItemId1`, '
            '`RequiredItemCount1`, `RewardItem1`, `RewardAmount1`, `VerifiedBuild`) VALUES',
            values(qrows),
            f'DELETE FROM `quest_template_addon` WHERE `ID` IN ({ids});',
            'INSERT INTO `quest_template_addon` (`ID`, `MaxLevel`, `AllowableClasses`, `SourceSpellID`, `PrevQuestID`, '
            '`NextQuestID`, `ExclusiveGroup`, `BreadcrumbForQuestId`, `RewardMailTemplateID`, `RewardMailDelay`, '
            '`RequiredSkillID`, `RequiredSkillPoints`, `RequiredMinRepFaction`, `RequiredMaxRepFaction`, '
            '`RequiredMinRepValue`, `RequiredMaxRepValue`, `ProvidedItemCount`, `SpecialFlags`) VALUES',
            values(addons),
            f'DELETE FROM `quest_offer_reward` WHERE `ID` IN ({ids});',
            'INSERT INTO `quest_offer_reward` (`ID`, `Emote1`, `Emote2`, `Emote3`, `Emote4`, `EmoteDelay1`, '
            '`EmoteDelay2`, `EmoteDelay3`, `EmoteDelay4`, `RewardText`, `VerifiedBuild`) VALUES',
            values(offers),
            f'DELETE FROM `quest_request_items` WHERE `ID` IN ({ids});',
            'INSERT INTO `quest_request_items` (`ID`, `EmoteOnComplete`, `EmoteOnIncomplete`, `CompletionText`, '
            '`VerifiedBuild`) VALUES',
            values(requests),
            f'DELETE FROM `creature_queststarter` WHERE `quest` IN ({ids});',
            'INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES', values(starters),
            f'DELETE FROM `creature_questender` WHERE `quest` IN ({ids});',
            'INSERT INTO `creature_questender` (`id`, `quest`) VALUES', values(starters), '']


def check():
    items = [i[0] for i in QUEST_ITEMS] + [WARD]
    assert len(set(items)) == len(items) and all(912100 <= i <= 912199 for i in items), 'items use 912100-912199'
    assert all(921001 <= q <= 921099 for q in Q.values())
    assert set(SCALE_DROPPERS) == set(SCALES) and set(DRAGONS) == set(PRISTINE)
    for d in [AGENT] + list(DRAGONS.values()):
        assert 190206 <= d['entry'] <= 190209 and d['guid'] == d['entry'] + 9000000


def main():
    check()
    parts = ['-- Generated by tools/shadowflame_ward.py - edit the tables there, not this file.',
             '-- The Shadowflame Ward quest chain (Kaelastrasz, Thorium Point): see the tool for the design.', '']
    parts += items_sql() + creatures_sql() + loot_sql() + quests_sql()
    with open(OUT, 'w', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(parts) + '\n')
    print('wrote', OUT, f'({len(QUESTS)} quests, {len(QUEST_ITEMS) + 1} items, {1 + len(DRAGONS)} NPCs)')


if __name__ == '__main__':
    main()
