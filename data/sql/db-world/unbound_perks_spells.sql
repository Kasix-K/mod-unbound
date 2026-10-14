-- mod-unbound perks: spell scripts for class perks (src/unbound_perks.cpp).
-- Retribution (Paladin): Divine Storm and the three Judgements.
DELETE FROM `spell_script_names` WHERE `ScriptName` IN ('spell_unbound_ret_divine_storm', 'spell_unbound_ret_judgement');
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(53385, 'spell_unbound_ret_divine_storm'),
(20271, 'spell_unbound_ret_judgement'),
(53407, 'spell_unbound_ret_judgement'),
(53408, 'spell_unbound_ret_judgement');
