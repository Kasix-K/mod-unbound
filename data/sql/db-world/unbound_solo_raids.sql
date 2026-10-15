-- mod-unbound: soloable raid mechanics (src/unbound_solo_raids.cpp).
-- These spells fail when the listed boss casts them in a raid with at most one player in it; the C++
-- list (BLOCKED_SPELLS) says which caster each one is blocked for. Existing scripts on these spells
-- (e.g. spell_vael_burning_adrenaline) are kept: a spell can have several scripts.
DELETE FROM `spell_script_names` WHERE `ScriptName` = 'spell_unbound_solo_raid_block';
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(14515, 'spell_unbound_solo_raid_block'),  -- Dominate Mind (Grethok the Controller, Blackwing Lair)
(18173, 'spell_unbound_solo_raid_block'),  -- Burning Adrenaline (Vaelastrasz the Corrupt)
(23340, 'spell_unbound_solo_raid_block'),  -- Shadow of Ebonroc (Ebonroc)
(23310, 'spell_unbound_solo_raid_block'),  -- Time Lapse (Chromaggus)
(23174, 'spell_unbound_solo_raid_block'),  -- Chromatic Mutation (Chromaggus)
(22667, 'spell_unbound_solo_raid_block');  -- Shadow Command (Lord Victor Nefarius)

-- Black Dragon Egg in Razorgore's room: solo players break eggs by walking over or clicking them.
-- (It had no script before; groups get the game's normal handling.)
UPDATE `gameobject_template` SET `ScriptName` = 'go_unbound_solo_razorgore_egg' WHERE `entry` = 177807;
