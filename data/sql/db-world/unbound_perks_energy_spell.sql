-- mod-unbound perks: server-only passive spell for the Focused Mind utility perk (src/unbound_perks.cpp,
-- SPELL_PERK_ENERGY). Passive auras are never sent to the client, so it needs no client patch; the amount is set
-- by the server from the perk's rank (mod_unbound.conf).
--   200217 Perk energy   energy regeneration % (110, SPELL_AURA_MOD_POWER_REGEN_PERCENT, misc 3 = energy; like the
--                        Vitality talent)
-- Attributes 192 = PASSIVE | DO_NOT_DISPLAY; duration 21 = infinite; range 1 = self; target 1 = caster.
DELETE FROM `spell_dbc` WHERE `ID` = 200217;
INSERT INTO `spell_dbc` (`ID`, `Attributes`, `CastingTimeIndex`, `DurationIndex`, `RangeIndex`, `EquippedItemClass`, `SchoolMask`,
    `Effect_1`, `ImplicitTargetA_1`, `EffectAura_1`, `EffectMiscValue_1`, `Name_Lang_enUS`) VALUES
(200217, 192, 1, 21, 1, -1, 1,   6, 1, 110, 3,   'Unbound Perk: Focused Mind');
