-- mod-unbound: the Warden of Rare Wonders, the cosmetics vendor for Heroic Sigils (src/unbound_heroic_quartermaster.cpp).
-- 190200 is the NPC players talk to: a menu of four pages (Mounts, Pets, Tabards, Fun items), each opening the vendor
-- list of one never-spawned page creature (190201-190204; their npc_vendor rows come from tools/heroic_loot.py,
-- WARDEN_PAGES). NPCs 190200-190299 (190100-190109 are used and 190110-190199 are the world bosses').
-- Place one in each capital with `.npc add 190200` (friendly to both factions). Looks like Tyrande Whisperwind
-- (display 7274, her Darnassus model).
SET @WARDEN := 190200;

DELETE FROM `creature_template` WHERE `entry` BETWEEN @WARDEN AND @WARDEN + 4;
INSERT INTO `creature_template` (`entry`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `rank`, `dmgschool`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`,
    `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `AIName`, `MovementType`, `HoverHeight`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`) VALUES
-- npcflag 129 = gossip (1) + vendor (128); the vendor flag lets it open its pages' lists
(@WARDEN, 'Warden of Rare Wonders', 'Heroic Sigils', NULL, 0, 80, 80, 2, 35, 129, 0, 0, 2000, 0, 2, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2,
    'npc_unbound_warden_of_rare_wonders'),
-- the pages: vendor-only templates that are never spawned (npc_vendor needs a vendor creature entry)
(@WARDEN + 1, 'Warden of Rare Wonders', 'Mounts', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 2, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@WARDEN + 2, 'Warden of Rare Wonders', 'Pets', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 2, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@WARDEN + 3, 'Warden of Rare Wonders', 'Tabards', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 2, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@WARDEN + 4, 'Warden of Rare Wonders', 'Fun items', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 2, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, '');

DELETE FROM `creature_template_model` WHERE `CreatureID` BETWEEN @WARDEN AND @WARDEN + 4;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(@WARDEN, 0, 7274, 1, 1, 0),
(@WARDEN + 1, 0, 7274, 1, 1, 0),
(@WARDEN + 2, 0, 7274, 1, 1, 0),
(@WARDEN + 3, 0, 7274, 1, 1, 0),
(@WARDEN + 4, 0, 7274, 1, 1, 0);

-- Greeting
DELETE FROM `npc_text` WHERE `ID` = @WARDEN;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`) VALUES
(@WARDEN, 'Elune''s light finds beauty in rare things, $N. Steeds of spirit and flame, little companions, the colors of distant banners, and toys to make a friend laugh.$B$BI trade them for Heroic Sigils, the proof of your victories in the Heroic dungeons.', '', 0, 0, 1);
