-- mod-unbound perks: server-only passive spells for the Utility perks (src/unbound_perks.cpp, SPELL_PERK_*).
-- Passive auras are never sent to the client, so these need no client patch. Every amount is 0 here; the
-- server sets it from the perk's rank (mod_unbound.conf).
--   200210 Longer Legs        run speed % (129), mounted speed % (130), swim speed % (58)
--   200211 Relentless Pursuit run speed % (129), timed from the code
--   200212 Perk threat        threat %, all schools (10): Silent Killer, Unbreakable Presence, Pets Roar
--   200213 Steady Hands       pushback reduction % (149), interrupt duration % (232, mechanic 26),
--                             silence duration % (232, mechanic 9)
-- Attributes 192 = PASSIVE | DO_NOT_DISPLAY; duration 21 = infinite; range 1 = self; target 1 = caster.
DELETE FROM `spell_dbc` WHERE `ID` BETWEEN 200210 AND 200213;
INSERT INTO `spell_dbc` (`ID`, `Attributes`, `CastingTimeIndex`, `DurationIndex`, `RangeIndex`, `EquippedItemClass`, `SchoolMask`,
    `Effect_1`, `ImplicitTargetA_1`, `EffectAura_1`, `EffectMiscValue_1`,
    `Effect_2`, `ImplicitTargetA_2`, `EffectAura_2`, `EffectMiscValue_2`,
    `Effect_3`, `ImplicitTargetA_3`, `EffectAura_3`, `EffectMiscValue_3`,
    `Name_Lang_enUS`) VALUES
(200210, 192, 1, 21, 1, -1, 1,   6, 1, 129, 0,     6, 1, 130, 0,    6, 1, 58, 0,     'Unbound Perk: Longer Legs'),
(200211, 192, 1, 21, 1, -1, 1,   6, 1, 129, 0,     0, 0, 0, 0,      0, 0, 0, 0,      'Unbound Perk: Relentless Pursuit'),
(200212, 192, 1, 21, 1, -1, 1,   6, 1, 10, 127,    0, 0, 0, 0,      0, 0, 0, 0,      'Unbound Perk: Threat'),
(200213, 192, 1, 21, 1, -1, 1,   6, 1, 149, 0,     6, 1, 232, 26,   6, 1, 232, 9,    'Unbound Perk: Steady Hands');
