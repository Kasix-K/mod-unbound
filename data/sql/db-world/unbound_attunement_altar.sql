-- mod-unbound: Altar of Tribute (creature 190103), gear attunement stage 3 (src/unbound_attunement.cpp).
-- Talking to it lists the items in your bags that can be offered as tribute; the game's own confirmation box shows
-- the gold price. Place it in the capital cities with `.npc add 190103` (friendly to both factions).
SET @ALTAR := 190103;

DELETE FROM `creature_template` WHERE `entry` = @ALTAR;
INSERT INTO `creature_template` (`entry`, `name`, `subname`, `IconName`, `gossip_menu_id`, `minlevel`, `maxlevel`, `exp`, `faction`, `npcflag`, `rank`, `dmgschool`, `BaseAttackTime`, `RangeAttackTime`, `unit_class`, `unit_flags`, `type`, `type_flags`, `lootid`, `pickpocketloot`, `skinloot`, `AIName`, `MovementType`, `HoverHeight`, `RacialLeader`, `movementId`, `RegenHealth`, `CreatureImmunitiesId`, `flags_extra`, `ScriptName`) VALUES
(@ALTAR, 'Altar of Tribute', 'Attunement', NULL, 0, 80, 80, 2, 35, 1, 0, 0, 2000, 0, 1, 0, 10, 0, 0, 0, 0, '', 0, 1, 0, 0, 1, 0, 2, 'npc_unbound_attunement_altar');

-- The Spirit Healer's model (5233)
DELETE FROM `creature_template_model` WHERE `CreatureID` = @ALTAR;
INSERT INTO `creature_template_model` (`CreatureID`, `Idx`, `CreatureDisplayID`, `DisplayScale`, `Probability`, `VerifiedBuild`) VALUES
(@ALTAR, 0, 5233, 1, 1, 0);

-- Greeting
DELETE FROM `npc_text` WHERE `ID` = @ALTAR;
INSERT INTO `npc_text` (`ID`, `text0_0`, `text0_1`, `BroadcastTextID0`, `lang0`, `Probability0`) VALUES
(@ALTAR, 'Lay an item upon the altar and it is unmade, its strength passing into you for good, as if you had worn it to full attunement.$B$BOnly gear that can be attuned is accepted, each piece once. The altar asks a price in gold, and twice as much for gear you could have attuned by wearing it.$B$BItems must be in your bags.', '', 0, 0, 1);
