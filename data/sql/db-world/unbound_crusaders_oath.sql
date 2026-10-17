-- mod-unbound: Crusader's Oath, the Paladin Retribution class perk (src/unbound_perks.cpp).
--   Spirit of the Ashbringer: creature 190220, summoned for 15 seconds by Ashbringer's Call (spell 200223,
--   tools/custom_dbc.py). A guardian like the priest's Shadowfiend (19668): it attacks the Paladin's target.
--   Its hits are set by the server (75% of the Paladin's weapon hit, Holy) and every third one gives Holy Power.
--   The look is Spirit of Mograine's (16775): a ghostly Highlord Mograine with the Ashbringer.
DELETE FROM `creature_template` WHERE `entry` = 190220;
INSERT INTO `creature_template` (`entry`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `rank`, `dmgschool`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `AIName`, `MovementType`, `HoverHeight`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`) VALUES
(190220, 'Spirit of the Ashbringer', NULL, NULL, 0, 60, 60, 0, 14, 0, 0, 1, 2000, 0, 1, 0, 10, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 0, '');

DELETE FROM `creature_template_model` WHERE `CreatureID` = 190220;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(190220, 0, 16326, 1, 1, 0);

DELETE FROM `creature_equip_template` WHERE `CreatureID` = 190220;
INSERT INTO `creature_equip_template` (`CreatureID`, `ID`, `ItemID1`, `ItemID2`, `ItemID3`, `VerifiedBuild`) VALUES
(190220, 1, 22709, 0, 0, 0);
