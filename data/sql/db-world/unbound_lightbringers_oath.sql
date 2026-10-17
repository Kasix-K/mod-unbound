-- mod-unbound: Lightbringer's Oath, the Paladin Holy class perk (src/unbound_perks.cpp).
--   Naaru: creature 190222, summoned for 15 seconds by Naaru's Blessing (spell 200231, tools/custom_dbc.py). A
--   guardian like the Spirit of the Ashbringer (190220), but it never melees and can't be attacked (pacified, not
--   attackable, not selectable): every 2 seconds the server has it cast Smite on the enemy the Paladin is fighting
--   and Flash Heal on the Paladin, and every third spell gives Holy Power.
--   The look is A'dal's (18481), shrunk to a small Naaru.
DELETE FROM `creature_template` WHERE `entry` = 190222;
INSERT INTO `creature_template` (`entry`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `rank`, `dmgschool`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `AIName`, `MovementType`, `HoverHeight`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`) VALUES
(190222, 'Naaru', 'Blessing of the Light', NULL, 0, 60, 60, 0, 14, 0, 0, 1, 2000, 0, 2, 33685506, 10, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 0, '');

DELETE FROM `creature_template_model` WHERE `CreatureID` = 190222;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(190222, 0, 18135, 0.15, 1, 0);

-- Oath of the Dawn: Holy Shock's and Exorcism's critical strikes give Holy Power (every rank).
DELETE FROM `spell_script_names` WHERE `ScriptName` = 'spell_unbound_lightbringer_dawn_crit';
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(-25912, 'spell_unbound_lightbringer_dawn_crit'),
(-879, 'spell_unbound_lightbringer_dawn_crit');
