-- mod-unbound perks: server-only passive spell for the Endless Rage utility perk (src/unbound_perks.cpp,
-- SPELL_PERK_RAGE). Passive auras are never sent to the client, so it needs no client patch; the amount is set
-- by the server from the perk's rank (mod_unbound.conf).
--   200216 Perk rage   rage from damage dealt % (213, SPELL_AURA_MOD_RAGE_FROM_DAMAGE_DEALT, like the Endless Rage
--                      talent); rage from damage taken is added in C++
-- Attributes 192 = PASSIVE | DO_NOT_DISPLAY; duration 21 = infinite; range 1 = self; target 1 = caster.
DELETE FROM `spell_dbc` WHERE `ID` = 200216;
INSERT INTO `spell_dbc` (`ID`, `Attributes`, `CastingTimeIndex`, `DurationIndex`, `RangeIndex`, `EquippedItemClass`, `SchoolMask`,
    `Effect_1`, `ImplicitTargetA_1`, `EffectAura_1`, `EffectMiscValue_1`, `Name_Lang_enUS`) VALUES
(200216, 192, 1, 21, 1, -1, 1,   6, 1, 213, 0,   'Unbound Perk: Endless Rage');
