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
(22667, 'spell_unbound_solo_raid_block'),  -- Shadow Command (Lord Victor Nefarius)
(20604, 'spell_unbound_solo_raid_block'),  -- Dominate Mind (Flamewaker Protector, Molten Core)
(19393, 'spell_unbound_solo_raid_block'),  -- Soul Burn, which silences (Firelord, Molten Core)
(24262, 'spell_unbound_solo_raid_block'),  -- Brain Wash Totem (Jin'do the Hexxer, Zul'Gurub)
(24466, 'spell_unbound_solo_raid_block'),  -- Banish (Jin'do the Hexxer)
(24327, 'spell_unbound_solo_raid_block'),  -- Cause Insanity (Hakkar)
(24324, 'spell_unbound_solo_raid_block'),  -- Blood Siphon (Hakkar)
(25725, 'spell_unbound_solo_raid_block'),  -- Paralyze (Ayamiss the Hunter, Ruins of Ahn'Qiraj)
(25721, 'spell_unbound_solo_raid_block'),  -- Feed (Hive'Zara Larva, Ayamiss)
(25195, 'spell_unbound_solo_raid_block'),  -- Curse of Tongues (Ossirian the Unscarred)
(785, 'spell_unbound_solo_raid_block'),    -- True Fulfillment (The Prophet Skeram, Temple of Ahn'Qiraj)
(7393, 'spell_unbound_solo_raid_block'),   -- Heal Brother (Twin Emperors)
(26079, 'spell_unbound_solo_raid_block');  -- Cause Insanity (Qiraji Mindslayer)

-- Black Dragon Egg in Razorgore's room: solo players break eggs by walking over or clicking them.
-- (It had no script before; groups get the game's normal handling.)
UPDATE `gameobject_template` SET `ScriptName` = 'go_unbound_solo_razorgore_egg' WHERE `entry` = 177807;

-- Enveloping Winds (Ossirian the Unscarred): solo, at most every Unbound.SoloRaid.OssirianWindsInterval seconds.
DELETE FROM `spell_script_names` WHERE `ScriptName` = 'spell_unbound_solo_ossirian_winds';
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES (25189, 'spell_unbound_solo_ossirian_winds');
