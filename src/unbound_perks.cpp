/*
 * mod-unbound: perks (the Unbound Perks addon's Character Perks window, /perks).
 *
 * Permanent perks (always on for every player):
 *   No Resurrection Sickness   worldserver.conf: Death.SicknessLevel = 255 (apply-unbound-settings.ps1)
 *   No Daze                    worldserver.conf: Daze.Enabled = 0          (apply-unbound-settings.ps1)
 *   Rapid Recovery             below: after 3 seconds out of combat, restore 15% of maximum health and
 *                              mana every second until full.
 *
 * Toggled perks: the addon whispers the player's own character with prefix "UBPERK"
 *   SYNC                       send me my perks
 *   SET:<id>:<0|1>             turn one perk off/on
 *   LOAD:<id>,<id>,...         exactly these perks on (a loadout)
 * and the server answers with "STATE:<id>,<id>,..." (the active perks it knows) or "ERR:<text>".
 * Perks can't be changed in combat. Active perks are saved in characters.character_unbound_perks.
 * At most MAX_ACTIVE_OFFENSIVE (5) Offensive perks (ids 101-199) can be active at once; the addon uses
 * the same limit (CATEGORIES in addon/UnboundPerks/PerkData.lua).
 *
 * Working toggled perks (ids match addon/UnboundPerks/PerkData.lua; all also work for pets):
 *   101 Cyclic Power           damage done cycles between -50% and +100% over 25 seconds
 *   102 Critical Understanding every 300% crit chance above 100% = +1% crit damage, up to +200%
 *   103 Defensive Sacrifice    take 30% more damage; +10% of current attack power and spell power
 *   104 Desperate Power        -75% of your magic resistances (Fire, Nature, Frost, Shadow, Arcane);
 *                              +50% damage dealt
 *   105 Block Capping          block chance is capped at 60%; every 200% above the cap = +1% damage
 *   106 Dodge Capping          the same for dodge         (all three up to +200%; the caps apply to
 *   107 Parry Capping          the same for parry          melee attacks against you)
 *   108 Haste Capping          every 200% haste above 60% = +1% damage, up to +200%; take 10% more damage
 *   109 Pet Encouragement      your pets, guardians and totems deal 40% more damage
 *   110 Rolling Momentum       +2% damage per second in combat, up to +50%; out of combat it drops 2% per second
 *   111 Tunnel Vision          single-target damage +40%, area damage -30%
 *   112 Collateral Damage      area damage +40%, single-target damage -30%
 *                              (area = a spell that hits an area or chains to more targets; everything else,
 *                              melee and auto attacks included, is single-target)
 *   113 Giant Slayer           +25% damage to bosses (world bosses and dungeon/raid bosses)
 *   114 Merciless              damage-over-time ticks +50%
 *   115 Pressure               each hit on the same target +8% damage, up to 10 stacks (+80%); switching
 *                              targets resets it (tracked per attacker, so a pet keeps its own stacks;
 *                              direct hits add a stack, damage-over-time ticks use the current stacks)
 *   116 Chaos                  each damaging ability (a spell or a weapon strike, not auto attacks or
 *                              damage-over-time ticks) has a 10% chance to deal double damage
 *   117 Power Conversion       every 30000 of your highest base stat = +0.5% damage, up to +200%
 *   118 Healing Powah          healing done +25% (direct heals and heal-over-time ticks)
 *   119 Shadow Mastery         Shadow spell damage +30%
 *   120 Holy Mastery           Holy spell damage +30%
 *   121 Arcane Mastery         Arcane spell damage +30%
 *   122 Nature Mastery         Nature spell damage +30%
 *   123 Fire Mastery           Fire spell damage +30%
 *   124 Frost Mastery          Frost spell damage +30%
 *   125 Physical Mastery       Physical damage +30% (melee and auto attacks, weapon strikes, Physical
 *                              spells and bleeds)
 *                              (a spell counts for a school if that school is part of it, e.g. Shadowfrost)
 *
 * Settings (mod_unbound.conf): Unbound.Perks.RapidRecovery (on/off), .Delay (ms), .Percent.
 */

#include "Chat.h"
#include "Config.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "StringConvert.h"
#include "Tokenize.h"
#include "WorldPacket.h"

#include <algorithm>
#include <cmath>
#include <set>
#include <unordered_map>
#include <utility>

namespace
{
    // ------------------------------------------------------------------ Rapid Recovery settings
    bool sRapidRecovery = true;
    uint32 sRecoveryDelayMs = 3000;
    uint32 sRecoveryPercent = 15;
    constexpr uint32 RECOVERY_TICK_MS = 1000;

    // ------------------------------------------------------------------ toggled perks
    enum PerkId : uint32
    {
        PERK_CYCLIC_POWER           = 101,
        PERK_CRITICAL_UNDERSTANDING = 102,
        PERK_DEFENSIVE_SACRIFICE    = 103,
        PERK_DESPERATE_POWER        = 104,
        PERK_BLOCK_CAPPING          = 105,
        PERK_DODGE_CAPPING          = 106,
        PERK_PARRY_CAPPING          = 107,
        PERK_HASTE_CAPPING          = 108,
        PERK_PET_ENCOURAGEMENT      = 109,
        PERK_ROLLING_MOMENTUM       = 110,
        PERK_TUNNEL_VISION          = 111,
        PERK_COLLATERAL_DAMAGE      = 112,
        PERK_GIANT_SLAYER           = 113,
        PERK_MERCILESS              = 114,
        PERK_PRESSURE               = 115,
        PERK_CHAOS                  = 116,
        PERK_POWER_CONVERSION       = 117,
        PERK_HEALING_POWAH          = 118,
        PERK_SHADOW_MASTERY         = 119,
        PERK_HOLY_MASTERY           = 120,
        PERK_ARCANE_MASTERY         = 121,
        PERK_NATURE_MASTERY         = 122,
        PERK_FIRE_MASTERY           = 123,
        PERK_FROST_MASTERY          = 124,
        PERK_PHYSICAL_MASTERY       = 125,
    };

    std::set<uint32> const IMPLEMENTED = {
        PERK_CYCLIC_POWER, PERK_CRITICAL_UNDERSTANDING, PERK_DEFENSIVE_SACRIFICE,
        PERK_DESPERATE_POWER, PERK_BLOCK_CAPPING, PERK_DODGE_CAPPING, PERK_PARRY_CAPPING,
        PERK_HASTE_CAPPING, PERK_PET_ENCOURAGEMENT, PERK_ROLLING_MOMENTUM,
        PERK_TUNNEL_VISION, PERK_COLLATERAL_DAMAGE, PERK_GIANT_SLAYER,
        PERK_MERCILESS, PERK_PRESSURE, PERK_CHAOS, PERK_POWER_CONVERSION,
        PERK_HEALING_POWAH, PERK_SHADOW_MASTERY, PERK_HOLY_MASTERY, PERK_ARCANE_MASTERY,
        PERK_NATURE_MASTERY, PERK_FIRE_MASTERY, PERK_FROST_MASTERY, PERK_PHYSICAL_MASTERY };

    constexpr char const* PREFIX = "UBPERK";
    constexpr uint32 MAX_ACTIVE_OFFENSIVE = 5;

    bool IsOffensive(uint32 perk) { return perk >= 101 && perk <= 199; }

    uint32 CountOffensive(std::set<uint32> const& perks)
    {
        return uint32(std::count_if(perks.begin(), perks.end(), IsOffensive));
    }
    constexpr uint32 STAT_REFRESH_MS = 2000;

    constexpr uint32 CYCLE_MS = 25000;               // Cyclic Power period
    constexpr float SACRIFICE_DAMAGE_TAKEN = 1.30f;  // Defensive Sacrifice
    constexpr float SACRIFICE_STAT_PCT = 0.10f;
    constexpr uint32 SPELL_CRIT_DAMAGE_AURA = 58670; // "Prey on the Weak": one aura, +X% crit damage, all schools
    constexpr float DESPERATE_DAMAGE_DONE = 1.50f;   // Desperate Power
    constexpr float DESPERATE_RESIST_PCT = 0.75f;
    constexpr float AVOIDANCE_CAP = 60.0f;           // Block/Dodge/Parry Capping: cap (%)
    constexpr float AVOIDANCE_STEP = 200.0f;         // ... +1% damage per this much above the cap
    constexpr int32 AVOIDANCE_MAX_BONUS = 200;       // ... up to +200%
    constexpr float HASTE_DAMAGE_TAKEN = 1.10f;      // Haste Capping
    constexpr float PET_DAMAGE_DONE = 1.40f;         // Pet Encouragement
    constexpr int32 MOMENTUM_STEP = 2;               // Rolling Momentum: % per second
    constexpr int32 MOMENTUM_MAX = 50;
    constexpr float FOCUS_BONUS = 1.40f;             // Tunnel Vision / Collateral Damage
    constexpr float FOCUS_PENALTY = 0.70f;
    constexpr float GIANT_SLAYER_BONUS = 1.25f;
    constexpr float MERCILESS_DOT_BONUS = 1.50f;
    constexpr float HEALING_POWAH_BONUS = 1.25f;
    constexpr float SCHOOL_MASTERY_BONUS = 1.30f;
    constexpr int32 PRESSURE_STEP = 8;               // % per stack
    constexpr uint32 PRESSURE_MAX_STACKS = 10;
    constexpr float CHAOS_CHANCE = 10.0f;            // %
    constexpr float POWER_CONVERSION_STAT = 30000.0f;   // +0.5% per this much of the highest base stat
    constexpr float POWER_CONVERSION_MAX = 200.0f;

    enum class HitKind { Melee, Spell, Periodic };

    struct PressureTrack
    {
        ObjectGuid target;
        uint32 stacks = 0;
    };
    constexpr uint8 MAGIC_SCHOOLS[] = { SPELL_SCHOOL_FIRE, SPELL_SCHOOL_NATURE, SPELL_SCHOOL_FROST,
                                        SPELL_SCHOOL_SHADOW, SPELL_SCHOOL_ARCANE };

    struct PerkState
    {
        std::set<uint32> active;

        // Rapid Recovery
        uint32 outOfCombatMs = 0;
        uint32 tickMs = 0;

        // stat-based perks are re-evaluated every STAT_REFRESH_MS
        uint32 statTimer = 0;
        uint32 cycleStartMs = 0;    // Cyclic Power phase
        int32 sacrificeAP = 0;      // attack power currently added by Defensive Sacrifice
        int32 sacrificeSP = 0;      // spell power currently added by Defensive Sacrifice
        int32 critBonus = 0;        // Critical Understanding bonus currently applied (%)
        int32 desperateResist[MAX_SPELL_SCHOOL] = {};  // resistance currently removed by Desperate Power
        int32 cappingBonus = 0;     // Block/Dodge/Parry/Haste Capping damage bonus (%), summed
        float powerConversion = 0;  // Power Conversion bonus (%)
        std::unordered_map<ObjectGuid, PressureTrack> pressure; // Pressure: per attacking unit (player, pets)
        int32 momentum = 0;         // Rolling Momentum bonus (%)
        uint32 momentumTimer = 0;
    };

    std::unordered_map<ObjectGuid::LowType, PerkState> sStates;

    PerkState* StateOf(Player const* player)
    {
        auto itr = sStates.find(player->GetGUID().GetCounter());
        return itr == sStates.end() ? nullptr : &itr->second;
    }

    // The player whose perks apply to this unit: the player or the owner of a pet, guardian or totem.
    PerkState* PerkOwnerState(Unit const* unit)
    {
        if (!unit)
            return nullptr;
        Player* owner = unit->GetCharmerOrOwnerPlayerOrPlayerItself();
        return owner ? StateOf(owner) : nullptr;
    }

    bool Has(PerkState const* state, uint32 perk)
    {
        return state && state->active.count(perk);
    }

    // ------------------------------------------------------------------ damage multipliers
    float CyclicMultiplier(PerkState const* state)
    {
        // 0.5 .. 2.0 (-50% .. +100%), a smooth wave over CYCLE_MS starting at +25%
        uint32 t = (getMSTime() - state->cycleStartMs) % CYCLE_MS;
        return 1.25f + 0.75f * std::sin(2.0f * float(M_PI) * float(t) / float(CYCLE_MS));
    }

    bool IsAreaDamage(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false; // melee swings
        if (spellInfo->IsAffectingArea())
            return true;
        for (SpellEffectInfo const& effect : spellInfo->GetEffects())
            if (effect.IsEffect() && effect.ChainTarget > 1)
                return true;
        return false;
    }

    bool IsBoss(Unit const* unit)
    {
        Creature const* creature = unit ? unit->ToCreature() : nullptr;
        return creature && (creature->isWorldBoss() || creature->IsDungeonBoss());
    }

    float DamageDoneMultiplier(Unit const* attacker, Unit const* victim, SpellInfo const* spellInfo)
    {
        PerkState const* state = PerkOwnerState(attacker);
        if (!state)
            return 1.0f;
        float mult = 1.0f;
        if (Has(state, PERK_CYCLIC_POWER))
            mult *= CyclicMultiplier(state);
        if (Has(state, PERK_DESPERATE_POWER))
            mult *= DESPERATE_DAMAGE_DONE;
        if (state->cappingBonus)
            mult *= 1.0f + state->cappingBonus / 100.0f;
        if (Has(state, PERK_ROLLING_MOMENTUM) && state->momentum)
            mult *= 1.0f + state->momentum / 100.0f;
        if (Has(state, PERK_PET_ENCOURAGEMENT) && !attacker->IsPlayer())  // pets, guardians, totems
            mult *= PET_DAMAGE_DONE;
        if (Has(state, PERK_TUNNEL_VISION) || Has(state, PERK_COLLATERAL_DAMAGE))
        {
            bool area = IsAreaDamage(spellInfo);
            if (Has(state, PERK_TUNNEL_VISION))
                mult *= area ? FOCUS_PENALTY : FOCUS_BONUS;
            if (Has(state, PERK_COLLATERAL_DAMAGE))
                mult *= area ? FOCUS_BONUS : FOCUS_PENALTY;
        }
        if (Has(state, PERK_GIANT_SLAYER) && IsBoss(victim))
            mult *= GIANT_SLAYER_BONUS;
        // School masteries; melee swings (no spell) are Physical.
        static constexpr std::pair<uint32, uint32> MASTERIES[] = {
            { PERK_PHYSICAL_MASTERY, SPELL_SCHOOL_MASK_NORMAL }, { PERK_HOLY_MASTERY,   SPELL_SCHOOL_MASK_HOLY   },
            { PERK_FIRE_MASTERY,     SPELL_SCHOOL_MASK_FIRE   }, { PERK_NATURE_MASTERY, SPELL_SCHOOL_MASK_NATURE },
            { PERK_FROST_MASTERY,    SPELL_SCHOOL_MASK_FROST  }, { PERK_SHADOW_MASTERY, SPELL_SCHOOL_MASK_SHADOW },
            { PERK_ARCANE_MASTERY,   SPELL_SCHOOL_MASK_ARCANE },
        };
        uint32 schools = spellInfo ? uint32(spellInfo->GetSchoolMask()) : uint32(SPELL_SCHOOL_MASK_NORMAL);
        for (auto const& [perk, mask] : MASTERIES)
            if ((schools & mask) && Has(state, perk))
                mult *= SCHOOL_MASTERY_BONUS;
        return mult;
    }

    // ------------------------------------------------------------------ healing
    // The core calls ModifyHealReceived with (target, healer) for heal-over-time ticks but with
    // (healer, target) for direct heals (Unit::HealBySpell). A heal tick always calls
    // ModifyPeriodicDamageAurasTick first with the same heal value, so that call is remembered here
    // to tell the two apart.
    struct PendingHealTick
    {
        uint32 const* amount = nullptr;
        Unit const* target = nullptr;
        SpellInfo const* spellInfo = nullptr;
    };
    PendingHealTick sPendingHealTick;

    void ApplyHealingBonus(Unit const* healer, uint32& heal)
    {
        PerkState const* state = PerkOwnerState(healer);
        if (heal && Has(state, PERK_HEALING_POWAH))
            heal = uint32(std::round(float(heal) * HEALING_POWAH_BONUS));
    }

    float DamageTakenMultiplier(Unit const* victim)
    {
        PerkState const* state = PerkOwnerState(victim);
        if (!state)
            return 1.0f;
        float mult = 1.0f;
        if (Has(state, PERK_DEFENSIVE_SACRIFICE))
            mult *= SACRIFICE_DAMAGE_TAKEN;
        if (Has(state, PERK_HASTE_CAPPING))
            mult *= HASTE_DAMAGE_TAKEN;
        return mult;
    }

    // Perks that depend on the kind of hit or change state with every hit.
    float HitMultiplier(Unit const* attacker, Unit const* victim, HitKind kind)
    {
        PerkState* state = PerkOwnerState(attacker);
        if (!state || state->active.empty())
            return 1.0f;
        float mult = 1.0f;

        if (kind == HitKind::Periodic && Has(state, PERK_MERCILESS))
            mult *= MERCILESS_DOT_BONUS;

        if (kind == HitKind::Spell && Has(state, PERK_CHAOS) && roll_chance_f(CHAOS_CHANCE))
            mult *= 2.0f;

        if (state->powerConversion > 0.0f)
            mult *= 1.0f + state->powerConversion / 100.0f;

        if (Has(state, PERK_PRESSURE))
        {
            PressureTrack& track = state->pressure[attacker->GetGUID()];
            if (track.target != victim->GetGUID())
            {
                track.target = victim->GetGUID();
                track.stacks = 0;
            }
            mult *= 1.0f + (PRESSURE_STEP * track.stacks) / 100.0f;
            if (kind != HitKind::Periodic)
                track.stacks = std::min(PRESSURE_MAX_STACKS, track.stacks + 1);
        }
        return mult;
    }

    template <typename T>
    void ApplyMultipliers(Unit* victim, Unit* attacker, T& damage, SpellInfo const* spellInfo, HitKind kind)
    {
        if (damage <= 0 || !attacker || !victim || attacker == victim)
            return;
        float mult = DamageDoneMultiplier(attacker, victim, spellInfo) * HitMultiplier(attacker, victim, kind) *
                     DamageTakenMultiplier(victim);
        if (mult != 1.0f)
            damage = T(std::max(0.0f, std::round(float(damage) * mult)));
    }

    // ------------------------------------------------------------------ stat-based perks
    float HighestCritChance(Player* player)
    {
        float crit = std::max(player->GetFloatValue(PLAYER_CRIT_PERCENTAGE), player->GetFloatValue(PLAYER_RANGED_CRIT_PERCENTAGE));
        for (uint8 school = SPELL_SCHOOL_HOLY; school < MAX_SPELL_SCHOOL; ++school)
            crit = std::max(crit, player->GetFloatValue(PLAYER_SPELL_CRIT_PERCENTAGE1 + school));
        return crit;
    }

    void SetCritBonus(Player* player, PerkState& state, int32 bonus)
    {
        if (bonus == state.critBonus)
            return;
        player->RemoveAurasDueToSpell(SPELL_CRIT_DAMAGE_AURA);
        state.critBonus = 0;
        if (bonus <= 0)
            return;
        player->CastCustomSpell(SPELL_CRIT_DAMAGE_AURA, SPELLVALUE_BASE_POINT0, bonus, player, true);
        if (Aura* aura = player->GetAura(SPELL_CRIT_DAMAGE_AURA))
        {
            aura->SetMaxDuration(-1);
            aura->SetDuration(-1);
            state.critBonus = bonus;
        }
    }

    int32 SpellPower(Player* player)
    {
        int32 best = player->SpellBaseHealingBonusDone(SPELL_SCHOOL_MASK_ALL);
        for (uint8 school = SPELL_SCHOOL_HOLY; school < MAX_SPELL_SCHOOL; ++school)
            best = std::max(best, player->SpellBaseDamageBonusDone(SpellSchoolMask(1 << school)));
        return best;
    }

    void SetSacrificeBonus(Player* player, PerkState& state, int32 ap, int32 sp)
    {
        if (ap != state.sacrificeAP)
        {
            if (state.sacrificeAP)
            {
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER, TOTAL_VALUE, float(state.sacrificeAP), false);
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, float(state.sacrificeAP), false);
            }
            if (ap)
            {
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER, TOTAL_VALUE, float(ap), true);
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, float(ap), true);
            }
            state.sacrificeAP = ap;
            player->UpdateAttackPowerAndDamage(false);
            player->UpdateAttackPowerAndDamage(true);
        }
        if (sp != state.sacrificeSP)
        {
            if (state.sacrificeSP)
                player->ApplySpellPowerBonus(state.sacrificeSP, false);
            if (sp)
                player->ApplySpellPowerBonus(sp, true);
            state.sacrificeSP = sp;
        }
    }

    void SetDesperateResist(Player* player, PerkState& state, uint8 school, int32 amount)
    {
        if (amount == state.desperateResist[school])
            return;
        UnitMods mod = UnitMods(UNIT_MOD_RESISTANCE_START + school);
        if (state.desperateResist[school])
            player->HandleStatFlatModifier(mod, TOTAL_VALUE, float(state.desperateResist[school]), true);   // give back
        if (amount)
            player->HandleStatFlatModifier(mod, TOTAL_VALUE, float(amount), false);                         // take away
        state.desperateResist[school] = amount;
    }

    // Block/Dodge/Parry Capping: +1% damage per AVOIDANCE_STEP above the cap, up to AVOIDANCE_MAX_BONUS
    int32 OverCapBonus(float chance)
    {
        return std::min(AVOIDANCE_MAX_BONUS, int32(std::max(0.0f, chance - AVOIDANCE_CAP) / AVOIDANCE_STEP));
    }

    void RefreshStatPerks(Player* player, PerkState& state)
    {
        // Desperate Power: remove 75% of each magic resistance (not counting what it already removed)
        for (uint8 school : MAGIC_SCHOOLS)
        {
            int32 amount = 0;
            if (Has(&state, PERK_DESPERATE_POWER))
                amount = int32((int32(player->GetResistance(SpellSchools(school))) + state.desperateResist[school]) * DESPERATE_RESIST_PCT);
            SetDesperateResist(player, state, school, amount);
        }

        // Block/Dodge/Parry Capping (the character sheet shows the uncapped chance)
        int32 capping = 0;
        if (Has(&state, PERK_BLOCK_CAPPING))
            capping += OverCapBonus(player->GetFloatValue(PLAYER_BLOCK_PERCENTAGE));
        if (Has(&state, PERK_DODGE_CAPPING))
            capping += OverCapBonus(player->GetFloatValue(PLAYER_DODGE_PERCENTAGE));
        if (Has(&state, PERK_PARRY_CAPPING))
            capping += OverCapBonus(player->GetFloatValue(PLAYER_PARRY_PERCENTAGE));
        if (Has(&state, PERK_HASTE_CAPPING))
        {
            float haste = std::max({ player->GetRatingBonusValue(CR_HASTE_MELEE), player->GetRatingBonusValue(CR_HASTE_RANGED),
                                     player->GetRatingBonusValue(CR_HASTE_SPELL) });
            capping += OverCapBonus(haste);
        }
        state.cappingBonus = capping;

        // Power Conversion
        state.powerConversion = 0.0f;
        if (Has(&state, PERK_POWER_CONVERSION))
        {
            float highest = 0.0f;
            for (uint8 stat = STAT_STRENGTH; stat < MAX_STATS; ++stat)
                highest = std::max(highest, player->GetStat(Stats(stat)));
            state.powerConversion = std::min(POWER_CONVERSION_MAX, std::floor(highest / POWER_CONVERSION_STAT) * 0.5f);
        }
        if (!Has(&state, PERK_PRESSURE))
            state.pressure.clear();

        // Critical Understanding
        int32 crit = 0;
        if (Has(&state, PERK_CRITICAL_UNDERSTANDING))
            crit = std::min(200, int32(std::max(0.0f, HighestCritChance(player) - 100.0f) / 300.0f));
        SetCritBonus(player, state, crit);

        // Defensive Sacrifice: 10% of current attack power and spell power, not counting its own bonus
        int32 ap = 0, sp = 0;
        if (Has(&state, PERK_DEFENSIVE_SACRIFICE))
        {
            int32 currentAP = int32(player->GetTotalAttackPowerValue(BASE_ATTACK)) - state.sacrificeAP;
            int32 currentSP = SpellPower(player) - state.sacrificeSP;
            ap = std::max(0, int32(currentAP * SACRIFICE_STAT_PCT));
            sp = std::max(0, int32(currentSP * SACRIFICE_STAT_PCT));
        }
        SetSacrificeBonus(player, state, ap, sp);
    }

    // ------------------------------------------------------------------ addon messages
    void SendAddon(Player* player, std::string const& text)
    {
        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player, std::string(PREFIX) + "\t" + text);
        player->SendDirectMessage(&data);
    }

    void SendState(Player* player, PerkState const& state)
    {
        std::string ids;
        for (uint32 id : state.active)
        {
            if (!ids.empty())
                ids += ",";
            ids += std::to_string(id);
        }
        SendAddon(player, "STATE:" + ids);
    }

    void SavePerk(Player* player, uint32 perk, bool on)
    {
        uint32 guid = player->GetGUID().GetCounter();
        if (on)
            CharacterDatabase.Execute("REPLACE INTO `character_unbound_perks` (`guid`, `perk`) VALUES ({}, {})", guid, perk);
        else
            CharacterDatabase.Execute("DELETE FROM `character_unbound_perks` WHERE `guid` = {} AND `perk` = {}", guid, perk);
    }

    void SetPerk(Player* player, PerkState& state, uint32 perk, bool on)
    {
        if (!IMPLEMENTED.count(perk) || on == bool(state.active.count(perk)))
            return;
        if (on)
        {
            state.active.insert(perk);
            if (perk == PERK_CYCLIC_POWER)
                state.cycleStartMs = getMSTime();
        }
        else
            state.active.erase(perk);
        SavePerk(player, perk, on);
    }

    void HandleAddonMessage(Player* player, std::string const& text)
    {
        PerkState& state = sStates[player->GetGUID().GetCounter()];

        if (text == "SYNC")
        {
            SendState(player, state);
            return;
        }

        bool isSet = text.rfind("SET:", 0) == 0;
        bool isLoad = text.rfind("LOAD:", 0) == 0;
        if (!isSet && !isLoad)
            return;

        if (player->IsInCombat())
        {
            SendAddon(player, "ERR:You can't change perks in combat.");
            SendState(player, state);
            return;
        }

        if (isSet)
        {
            std::vector<std::string_view> parts = Acore::Tokenize(text, ':', false);
            if (parts.size() == 3)
                if (Optional<uint32> perk = Acore::StringTo<uint32>(parts[1]))
                {
                    bool on = parts[2] == "1";
                    if (on && IsOffensive(*perk) && !state.active.count(*perk) &&
                        CountOffensive(state.active) >= MAX_ACTIVE_OFFENSIVE)
                        SendAddon(player, "ERR:You can only have " + std::to_string(MAX_ACTIVE_OFFENSIVE) +
                            " Offensive perks active. Turn one off first.");
                    else
                        SetPerk(player, state, *perk, on);
                }
        }
        else
        {
            // a loadout: keep the first MAX_ACTIVE_OFFENSIVE Offensive perks in the order sent
            std::set<uint32> wanted;
            uint32 offensive = 0;
            bool trimmed = false;
            std::string_view list = std::string_view(text).substr(5);
            for (std::string_view id : Acore::Tokenize(list, ',', false))
                if (Optional<uint32> perk = Acore::StringTo<uint32>(id))
                    if (IMPLEMENTED.count(*perk) && !wanted.count(*perk))
                    {
                        if (IsOffensive(*perk) && ++offensive > MAX_ACTIVE_OFFENSIVE)
                        {
                            trimmed = true;
                            continue;
                        }
                        wanted.insert(*perk);
                    }
            for (uint32 perk : IMPLEMENTED)
                SetPerk(player, state, perk, wanted.count(perk) > 0);
            if (trimmed)
                SendAddon(player, "ERR:Only the first " + std::to_string(MAX_ACTIVE_OFFENSIVE) +
                    " Offensive perks of that loadout were turned on.");
        }

        RefreshStatPerks(player, state);
        SendState(player, state);
    }

    // ------------------------------------------------------------------ Rapid Recovery
    void RestoreTick(Player* player)
    {
        uint32 maxHealth = player->GetMaxHealth();
        if (player->GetHealth() < maxHealth)
        {
            uint32 gain = std::max<uint32>(1, player->CountPctFromMaxHealth(sRecoveryPercent));
            player->SetHealth(std::min<uint32>(maxHealth, player->GetHealth() + gain));
        }

        uint32 maxMana = player->GetMaxPower(POWER_MANA);
        if (maxMana && player->GetPower(POWER_MANA) < maxMana)
        {
            uint32 gain = std::max<uint32>(1, maxMana * sRecoveryPercent / 100);
            player->SetPower(POWER_MANA, std::min<uint32>(maxMana, player->GetPower(POWER_MANA) + gain));
        }
    }

    // Rolling Momentum: once a second, +2% in combat (up to +50%) or -2% out of combat.
    void UpdateMomentum(Player* player, PerkState& state, uint32 diff)
    {
        if (!Has(&state, PERK_ROLLING_MOMENTUM))
        {
            state.momentum = 0;
            state.momentumTimer = 0;
            return;
        }
        state.momentumTimer += diff;
        while (state.momentumTimer >= 1000)
        {
            state.momentumTimer -= 1000;
            if (player->IsInCombat())
                state.momentum = std::min(MOMENTUM_MAX, state.momentum + MOMENTUM_STEP);
            else
                state.momentum = std::max(0, state.momentum - MOMENTUM_STEP);
        }
    }

    void UpdateRapidRecovery(Player* player, PerkState& state, uint32 diff)
    {
        if (!sRapidRecovery)
            return;

        // In combat, dead, or a ghost: start over.
        if (player->IsInCombat() || !player->IsAlive())
        {
            state.outOfCombatMs = 0;
            state.tickMs = 0;
            return;
        }

        if (state.outOfCombatMs < sRecoveryDelayMs)
        {
            state.outOfCombatMs += diff;
            if (state.outOfCombatMs < sRecoveryDelayMs)
                return;
            state.tickMs = RECOVERY_TICK_MS; // first tick right at the delay mark
        }
        else
            state.tickMs += diff;

        if (state.tickMs < RECOVERY_TICK_MS)
            return;

        state.tickMs = 0;
        RestoreTick(player);
    }
}

class unbound_perks_world : public WorldScript
{
public:
    unbound_perks_world() : WorldScript("unbound_perks_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sRapidRecovery = sConfigMgr->GetOption<bool>("Unbound.Perks.RapidRecovery", true);
        sRecoveryDelayMs = sConfigMgr->GetOption<uint32>("Unbound.Perks.RapidRecovery.Delay", 3000);
        sRecoveryPercent = std::clamp<uint32>(sConfigMgr->GetOption<uint32>("Unbound.Perks.RapidRecovery.Percent", 15), 1, 100);
    }
};

class unbound_perks_player : public PlayerScript
{
public:
    unbound_perks_player() : PlayerScript("unbound_perks_player", {
        PLAYERHOOK_ON_LOGIN,
        PLAYERHOOK_ON_LOGOUT,
        PLAYERHOOK_ON_UPDATE,
        PLAYERHOOK_ON_DELETE,
        PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT
    }) { }

    void OnPlayerLogin(Player* player) override
    {
        PerkState& state = sStates[player->GetGUID().GetCounter()];
        state = PerkState();
        state.cycleStartMs = getMSTime();
        player->RemoveAurasDueToSpell(SPELL_CRIT_DAMAGE_AURA); // saved with the character; re-added below if earned
        if (QueryResult result = CharacterDatabase.Query("SELECT `perk` FROM `character_unbound_perks` WHERE `guid` = {}",
            player->GetGUID().GetCounter()))
        {
            do
            {
                uint32 perk = (*result)[0].Get<uint32>();
                if (IMPLEMENTED.count(perk))
                    state.active.insert(perk);
            } while (result->NextRow());
        }
        // saved before the Offensive limit existed: keep the lowest ids, switch the rest off
        while (CountOffensive(state.active) > MAX_ACTIVE_OFFENSIVE)
        {
            auto last = std::find_if(state.active.rbegin(), state.active.rend(), IsOffensive);
            uint32 perk = *last;
            state.active.erase(perk);
            SavePerk(player, perk, false);
        }
        RefreshStatPerks(player, state);
    }

    void OnPlayerLogout(Player* player) override
    {
        sStates.erase(player->GetGUID().GetCounter());
    }

    void OnPlayerDelete(ObjectGuid guid, uint32 /*accountId*/) override
    {
        CharacterDatabase.Execute("DELETE FROM `character_unbound_perks` WHERE `guid` = {}", guid.GetCounter());
    }

    void OnPlayerUpdate(Player* player, uint32 diff) override
    {
        PerkState& state = sStates[player->GetGUID().GetCounter()];
        UpdateRapidRecovery(player, state, diff);
        UpdateMomentum(player, state, diff);

        if (state.active.empty() && !state.sacrificeAP && !state.sacrificeSP && !state.critBonus &&
            std::none_of(std::begin(state.desperateResist), std::end(state.desperateResist), [](int32 r) { return r != 0; }))
            return;
        state.statTimer += diff;
        if (state.statTimer >= STAT_REFRESH_MS)
        {
            state.statTimer = 0;
            RefreshStatPerks(player, state);
        }
    }

    // The addon whispers its own character: handle it and don't deliver the whisper.
    bool OnPlayerCanUseChat(Player* player, uint32 type, uint32 language, std::string& msg, Player* receiver) override
    {
        if (type != CHAT_MSG_WHISPER || language != LANG_ADDON || receiver != player)
            return true;
        std::string const prefix = std::string(PREFIX) + "\t";
        if (msg.rfind(prefix, 0) != 0)
            return true;
        HandleAddonMessage(player, msg.substr(prefix.size()));
        return false;
    }
};

class unbound_perks_unit : public UnitScript
{
public:
    unbound_perks_unit() : UnitScript("unbound_perks_unit", true, {
        UNITHOOK_MODIFY_MELEE_DAMAGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
        UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK,
        UNITHOOK_MODIFY_HEAL_RECEIVED,
        UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST
    }) { }

    // Healing Powah (see PendingHealTick for the argument order).
    void ModifyHealReceived(Unit* first, Unit* second, uint32& heal, SpellInfo const* spellInfo) override
    {
        PendingHealTick tick = sPendingHealTick;
        sPendingHealTick = PendingHealTick();
        bool isTick = tick.amount == &heal && tick.target == first && tick.spellInfo == spellInfo;
        Unit* healer = isTick ? second : first;
        ApplyHealingBonus(healer, heal);
    }

    // Block/Dodge/Parry Capping: melee attacks against a capped player use at most 60% (chances are x100).
    void OnBeforeRollMeleeOutcomeAgainst(Unit const* /*attacker*/, Unit const* victim, WeaponAttackType /*attType*/,
        int32& /*attackerMaxSkillValueForLevel*/, int32& /*victimMaxSkillValueForLevel*/, int32& /*attackerWeaponSkill*/,
        int32& /*victimDefenseSkill*/, int32& /*crit_chance*/, int32& /*miss_chance*/, int32& dodge_chance,
        int32& parry_chance, int32& block_chance) override
    {
        PerkState const* state = PerkOwnerState(victim);
        if (!state || state->active.empty())
            return;
        int32 const cap = int32(AVOIDANCE_CAP * 100);
        if (Has(state, PERK_BLOCK_CAPPING))
            block_chance = std::min(block_chance, cap);
        if (Has(state, PERK_DODGE_CAPPING))
            dodge_chance = std::min(dodge_chance, cap);
        if (Has(state, PERK_PARRY_CAPPING))
            parry_chance = std::min(parry_chance, cap);
    }

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        ApplyMultipliers(target, attacker, damage, nullptr, HitKind::Melee);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        ApplyMultipliers(target, attacker, damage, spellInfo, HitKind::Spell);
    }

    // Also called for heal-over-time ticks: only scale ticks on hostile targets.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage, SpellInfo const* spellInfo) override
    {
        sPendingHealTick = { &damage, target, spellInfo };  // a heal tick calls ModifyHealReceived next
        if (target && attacker && target->IsFriendlyTo(attacker))
            return;
        ApplyMultipliers(target, attacker, damage, spellInfo, HitKind::Periodic);
    }
};

void AddSC_unbound_perks()
{
    new unbound_perks_world();
    new unbound_perks_player();
    new unbound_perks_unit();
}
