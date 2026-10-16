-- mod-unbound: the Heroic Quartermaster (ROADMAP.md "Heroic currency and vendor"; src/unbound_heroic_quartermaster.cpp).
-- 190104 is the NPC players talk to: a menu of category pages, each opening the vendor list of one never-spawned page
-- creature (190105-190109; their npc_vendor rows, priced in Heroic Sigils, come from tools/heroic_loot.py). A 3.3.5
-- vendor window holds at most 150 items and there are 450 heroic items, hence the pages.
-- Place one in each capital with `.npc add 190104` (friendly to both factions). Looks like Arcanist Ivrenne, the
-- Emblem of Heroism Quartermaster (display 27556).
SET @QM := 190104;

DELETE FROM `creature_template` WHERE `entry` BETWEEN @QM AND @QM + 5;
INSERT INTO `creature_template` (`entry`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`,
    `faction`, `npcflag`, `rank`, `dmgschool`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`,
    `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `AIName`, `MovementType`, `HoverHeight`, `RacialLeader`,
    `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`) VALUES
-- npcflag 129 = gossip (1) + vendor (128); the vendor flag lets it open its pages' lists
(@QM, 'Heroic Quartermaster', 'Heroic Sigils', NULL, 0, 80, 80, 2, 35, 129, 0, 0, 2000, 0, 1, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2,
    'npc_unbound_heroic_quartermaster'),
-- the pages: vendor-only templates that are never spawned (npc_vendor needs a vendor creature entry)
(@QM + 1, 'Heroic Quartermaster', 'Accessories', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 1, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@QM + 2, 'Heroic Quartermaster', 'Head, shoulders and chest', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 1, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@QM + 3, 'Heroic Quartermaster', 'Hands, legs and feet', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 1, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@QM + 4, 'Heroic Quartermaster', 'Weapons', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 1, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, ''),
(@QM + 5, 'Heroic Quartermaster', 'Final boss treasures', NULL, 0, 80, 80, 2, 35, 128, 0, 0, 2000, 0, 1, 2, 7, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, '');

DELETE FROM `creature_template_model` WHERE `CreatureID` BETWEEN @QM AND @QM + 5;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(@QM, 0, 27556, 1, 1, 0),
(@QM + 1, 0, 27556, 1, 1, 0),
(@QM + 2, 0, 27556, 1, 1, 0),
(@QM + 3, 0, 27556, 1, 1, 0),
(@QM + 4, 0, 27556, 1, 1, 0),
(@QM + 5, 0, 27556, 1, 1, 0);

-- Greeting
DELETE FROM `npc_text` WHERE `ID` = @QM;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`) VALUES
(@QM, 'Heroic Sigils, earned from the bosses of the Heroic dungeons, are honored here.$B$BEvery Heroic boss drops its gear; I let you choose the piece you are still missing. Rings and the like are cheapest, armor and weapons cost more, and the final bosses\' treasures the most.$B$BYour Sigils are shared by all your characters.', '', 0, 0, 1);
