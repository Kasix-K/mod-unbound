-- mod-unbound: Bulwark's Oath, the Paladin Protection class perk (src/unbound_perks.cpp).
--   Guardian of the Light: creature 190221, summoned for 15 seconds by Guardian of the Light (spell 200226,
--   tools/custom_dbc.py). A guardian like the Spirit of the Ashbringer (190220): it attacks the Paladin's target.
--   Its hits are set by the server (50% of the Paladin's weapon hit) and every third one gives Holy Power.
--   The look is the Ghost of Uther Lightbringer's (17233, Andorhal): a spectral paladin.
DELETE FROM `creature_template` WHERE `entry` = 190221;
INSERT INTO `creature_template` (`entry`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `rank`, `dmgschool`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `AIName`, `MovementType`, `HoverHeight`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`) VALUES
(190221, 'Guardian of the Light', NULL, NULL, 0, 60, 60, 0, 14, 0, 0, 1, 2000, 0, 1, 0, 10, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 0, '');

DELETE FROM `creature_template_model` WHERE `CreatureID` = 190221;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(190221, 0, 16929, 1, 1, 0);
