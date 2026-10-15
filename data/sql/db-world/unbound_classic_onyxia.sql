-- mod-unbound: Onyxia's Lair as a classic level 60 raid (src/unbound_classic_onyxia.cpp scales her spells'
-- damage back to classic and removes the 3.2 Onyxian Lair Guards).
-- Numbers from the classic 1.12 data (VMaNGOS/CMaNGOS world databases): Onyxia level 63, 1,099,230
-- health, 4,691 armor, 1648-2184 melee every 2 s. AzerothCore: health = level stats x HealthModifier,
-- melee = (base damage + attack power / 14) x attack time x DamageModifier (creature_classlevelstats).
-- The 25-player difficulty (Onyxia 36538) keeps its level 80 entry requirement, so it can't be entered.
-- Scale of Onyxia and the Onyxia Scale Cloak recipe stay unobtainable (no skinning).

-- Entry from level 60 (10-player difficulty)
UPDATE `dungeon_access_template` SET `min_level` = 60 WHERE `map_id` = 249 AND `difficulty` = 0;

-- Onyxia: level 63 (3331 x 330 = 1,099,230 health; armor 4641 x 1.01; melee 109.8-145.6 x 15), classic gold,
-- not skinnable
UPDATE `creature_template` SET `minlevel` = 63, `maxlevel` = 63, `exp` = 0, `HealthModifier` = 330,
  `ArmorModifier` = 1.01, `DamageModifier` = 15, `BaseAttackTime` = 2000, `mingold` = 910000, `maxgold` = 1070000,
  `skinloot` = 0 WHERE `entry` = 10184;
UPDATE `creature_template` SET `skinloot` = 0 WHERE `entry` = 36538;
DELETE FROM `skinning_loot_template` WHERE `Entry` = 10184 AND `Item` = 15410;

-- Onyxian Whelp: level 56-57, 2699-2784 health, melee 355-480
UPDATE `creature_template` SET `minlevel` = 56, `maxlevel` = 57, `exp` = 0, `HealthModifier` = 1, `ArmorModifier` = 1,
  `DamageModifier` = 3.7 WHERE `entry` = 11262;

-- Onyxian Warder (elite): level 60-63, 76,300-83,275 health, melee 1039-1456
UPDATE `creature_template` SET `minlevel` = 60, `maxlevel` = 63, `exp` = 0, `HealthModifier` = 25, `ArmorModifier` = 1,
  `DamageModifier` = 10 WHERE `entry` = 12129;

-- Onyxian Lair Guard (added in 3.2): despawns as soon as it appears
UPDATE `creature_template` SET `ScriptName` = 'npc_unbound_onyxia_no_lair_guard' WHERE `entry` = 36561;

-- Classic loot. Every kill: two Tier 2 helms, one of Sapphiron Drape / Ring of Binding / Eskhandar's Collar /
-- Ancient Cornerstone Grimoire, the Head of Onyxia for the looter's faction, the Onyxia Hide Backpack;
-- 24% one of Deathbringer / Vis'kag the Bloodletter / Shard of the Scale. Quest drops as before (Mature Black
-- Dragon Sinew for the hunter quest, Draconic for Dummies). The level 80 loot (gear, Emblems of Triumph,
-- the Onyxian Drake mount, gem sack, bag, level 80 heads) is gone.
SET @T2_HELMS := 9100100;
SET @ONYXIA_EPICS := 9100101;
DELETE FROM `reference_loot_template` WHERE `Entry` IN (@T2_HELMS, @ONYXIA_EPICS);
INSERT INTO `reference_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(@T2_HELMS, 16900, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Stormrage Cover'),
(@T2_HELMS, 16908, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Bloodfang Hood'),
(@T2_HELMS, 16914, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Netherwind Crown'),
(@T2_HELMS, 16921, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Halo of Transcendence'),
(@T2_HELMS, 16929, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Nemesis Skullcap'),
(@T2_HELMS, 16939, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Dragonstalker\'s Helm'),
(@T2_HELMS, 16947, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Helmet of Ten Storms'),
(@T2_HELMS, 16955, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Judgement Crown'),
(@T2_HELMS, 16963, 0, 0, 0, 1, 1, 1, 1, 'Onyxia T2 helms - Helm of Wrath'),
(@ONYXIA_EPICS, 17078, 0, 0, 0, 1, 1, 1, 1, 'Onyxia epics - Sapphiron Drape'),
(@ONYXIA_EPICS, 18813, 0, 0, 0, 1, 1, 1, 1, 'Onyxia epics - Ring of Binding'),
(@ONYXIA_EPICS, 18205, 0, 0, 0, 1, 1, 1, 1, 'Onyxia epics - Eskhandar\'s Collar'),
(@ONYXIA_EPICS, 17067, 0, 0, 0, 1, 1, 1, 1, 'Onyxia epics - Ancient Cornerstone Grimoire');

DELETE FROM `creature_loot_template` WHERE `Entry` = 10184;
INSERT INTO `creature_loot_template` (`Entry`, `Item`, `Reference`, `Chance`, `QuestRequired`, `LootMode`, `GroupId`, `MinCount`, `MaxCount`, `Comment`) VALUES
(10184, @T2_HELMS, @T2_HELMS, 100, 0, 1, 0, 2, 2, 'Onyxia - (ReferenceTable) two Tier 2 helms'),
(10184, @ONYXIA_EPICS, @ONYXIA_EPICS, 100, 0, 1, 0, 1, 1, 'Onyxia - (ReferenceTable) one epic'),
(10184, 17068, 0, 8, 0, 1, 1, 1, 1, 'Onyxia - Deathbringer'),
(10184, 17075, 0, 8, 0, 1, 1, 1, 1, 'Onyxia - Vis\'kag the Bloodletter'),
(10184, 17064, 0, 8, 0, 1, 1, 1, 1, 'Onyxia - Shard of the Scale'),
(10184, 17966, 0, 100, 0, 1, 0, 1, 1, 'Onyxia - Onyxia Hide Backpack'),
(10184, 18422, 0, 100, 0, 1, 0, 1, 1, 'Onyxia - Head of Onyxia (Horde)'),
(10184, 18423, 0, 100, 0, 1, 0, 1, 1, 'Onyxia - Head of Onyxia (Alliance)'),
(10184, 18705, 0, 100, 1, 1, 0, 1, 1, 'Onyxia - Mature Black Dragon Sinew'),
(10184, 21108, 0, 100, 0, 1, 0, 1, 1, 'Onyxia - Draconic for Dummies');

-- Each faction's head drops for that faction (like the level 80 heads did)
DELETE FROM `conditions` WHERE `SourceTypeOrReferenceId` = 1 AND `SourceGroup` = 10184 AND `SourceEntry` IN (18422, 18423, 49643, 49644);
INSERT INTO `conditions` (`SourceTypeOrReferenceId`, `SourceGroup`, `SourceEntry`, `SourceId`, `ElseGroup`, `ConditionTypeOrReference`, `ConditionTarget`, `ConditionValue1`, `ConditionValue2`, `ConditionValue3`, `NegativeCondition`, `ErrorType`, `ErrorTextId`, `ScriptName`, `Comment`) VALUES
(1, 10184, 18422, 0, 0, 6, 0, 67, 0, 0, 0, 0, 0, '', 'Head of Onyxia (Horde) drops for Horde players'),
(1, 10184, 18423, 0, 0, 6, 0, 469, 0, 0, 0, 0, 0, '', 'Head of Onyxia (Alliance) drops for Alliance players');

-- Head of Onyxia quests (classic, their quest givers were removed in 3.2). The head starts the quest.
-- Horde: Victory for the Horde (7490) to Thrall, then For All To See (7491) to Overlord Runthak, who raises
-- the head and casts Rallying Cry of the Dragonslayer on Orgrimmar.
-- Alliance: Victory for the Alliance (7495) to King Varian Wrynn (Highlord Bolvar Fordragon, the classic quest
-- giver, isn't in Stormwind in 3.3.5), then Celebrating Good Times (7496) to Major Mattingly, who does the same
-- in Stormwind. Rewards: Onyxia Blood Talisman, Dragonslayer's Signet or Onyxia Tooth Pendant.
DELETE FROM `creature_queststarter` WHERE `quest` IN (7490, 7491, 7495, 7496);
INSERT INTO `creature_queststarter` (`id`, `quest`) VALUES
(4949, 7491),
(29611, 7496);
DELETE FROM `creature_questender` WHERE `quest` IN (7490, 7491, 7495, 7496);
INSERT INTO `creature_questender` (`id`, `quest`) VALUES
(4949, 7490),
(14392, 7491),
(29611, 7495),
(14394, 7496);
