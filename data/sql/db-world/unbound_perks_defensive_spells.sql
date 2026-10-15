-- mod-unbound perks: server-only passive spells for the Defensive perks (src/unbound_perks.cpp, SPELL_PERK_*).
-- Passive auras are never sent to the client, so these need no client patch. Amounts are set by the server
-- from the perk's rank (mod_unbound.conf).
--   200214 Perk vitality      maximum health % (133): Vital Reserve; armor % (101, school mask 1): Heavy Frame
--   200215 Perk defense proc  dummy (4) that procs on melee attacks taken (auto attacks 0x8 and melee spells
--                             0x20) that hit, crit or are dodged, parried or blocked (hit mask 0x73); the
--                             AuraScript spell_unbound_perk_defense_proc drives Counterweight, Shield Wall
--                             Training and Thornmail
-- Attributes 192 = PASSIVE | DO_NOT_DISPLAY; duration 21 = infinite; range 1 = self; target 1 = caster.
DELETE FROM `spell_dbc` WHERE `ID` IN (200214, 200215);
INSERT INTO `spell_dbc` (`ID`, `Attributes`, `CastingTimeIndex`, `DurationIndex`, `RangeIndex`, `EquippedItemClass`, `SchoolMask`,
    `ProcTypeMask`, `ProcChance`,
    `Effect_1`, `ImplicitTargetA_1`, `EffectAura_1`, `EffectMiscValue_1`,
    `Effect_2`, `ImplicitTargetA_2`, `EffectAura_2`, `EffectMiscValue_2`,
    `Name_Lang_enUS`) VALUES
(200214, 192, 1, 21, 1, -1, 1,   0, 0,       6, 1, 133, 0,    6, 1, 101, 1,    'Unbound Perk: Vitality'),
(200215, 192, 1, 21, 1, -1, 1,   40, 100,    6, 1, 4, 0,      0, 0, 0, 0,      'Unbound Perk: Defense Proc');

DELETE FROM `spell_proc` WHERE `SpellId` = 200215;
INSERT INTO `spell_proc` (`SpellId`, `ProcFlags`, `HitMask`, `Chance`) VALUES
(200215, 40, 115, 100);

DELETE FROM `spell_script_names` WHERE `ScriptName` = 'spell_unbound_perk_defense_proc';
INSERT INTO `spell_script_names` (`spell_id`, `ScriptName`) VALUES
(200215, 'spell_unbound_perk_defense_proc');
