/*
 * mod-unbound: perks (the Unbound Perks addon's Character Perks window, /perks).
 *
 * Permanent perks (always on for every player):
 *   No Resurrection Sickness   worldserver.conf: Death.SicknessLevel = 255 (apply-unbound-settings.ps1)
 *   No Daze                    worldserver.conf: Daze.Enabled = 0          (apply-unbound-settings.ps1)
 *   Rapid Recovery             below: after a few seconds out of combat, restore a percentage of maximum
 *                              health and mana every second until full. It has ranks (mod_unbound.conf):
 *                              Rank 1 6 s / 4% from level 1, Rank 2 5 s / 6% from level 30, Rank 3 4 s / 8%
 *                              from level 60.
 *
 * Perk ranks: a perk listed in RankedPerks() has several ranks. A character's rank comes from its level
 * (the rank levels in mod_unbound.conf) unless a GM set one with ".perk rank <perk id> <rank>" (saved in
 * characters.character_unbound_perk_ranks; ".perk rank <perk id>" without a rank goes back to the level).
 * The server tells the addon with "RANK:<perk>:<rank>:<max>:<values>" (values per rank, ';'-separated).
 *
 * Numbers are kept in normal WoW ranges (no Peloria-sized scaling): one perk is worth about +10%.
 *
 * Toggled perks: the addon whispers the player's own character with prefix "UBPERK"
 *   SYNC                       send me my perks
 *   SET:<id>:<0|1>             turn one perk off/on
 *   LOAD:<id>,<id>,...         exactly these perks on (a loadout)
 * and the server answers with "STATE:<id>,<id>,..." (the active perks it knows) or "ERR:<text>".
 * Perks can't be changed in combat. Active perks are saved in characters.character_unbound_perks.
 * At most MAX_ACTIVE_OFFENSIVE (5) Offensive perks (ids 101-199) can be active at once; the addon uses
 * the same limit (CATEGORIES in addon/UnboundPerks/PerkData.lua). Class perks (ids 1001+) only work for
 * their class (CLASS_PERKS); the server refuses them for any other class.
 *
 * Working toggled perks (ids match addon/UnboundPerks/PerkData.lua; all also work for pets):
 *   101 Cyclic Power           damage done cycles between -10% and +20% over 25 seconds
 *   102 Critical Understanding every 1% crit chance above 25% = +1% crit damage, up to +20%
 *   103 Defensive Sacrifice    take 10% more damage; +10% of current attack power and spell power
 *   104 Desperate Power        -50% of your magic resistances (Fire, Nature, Frost, Shadow, Arcane);
 *                              +10% damage dealt
 *   105 Block Capping          block chance is capped at 20%; every 1% above the cap = +1% damage
 *   106 Dodge Capping          the same for dodge         (each up to +10%; the caps apply to
 *   107 Parry Capping          the same for parry          melee attacks against you)
 *   108 Haste Capping          every 1% haste above 5% = +1% damage, up to +10%; take 5% more damage
 *   109 Pet Encouragement      your pets, guardians and totems deal 15% more damage
 *   110 Rolling Momentum       +1% damage per second in combat, up to +10%; out of combat it drops 1% per second
 *   111 Tunnel Vision          single-target damage +10%, area damage -10%
 *   112 Collateral Damage      area damage +10%, single-target damage -10%
 *                              (area = a spell that hits an area or chains to more targets; everything else,
 *                              melee and auto attacks included, is single-target)
 *   113 Giant Slayer           +10% damage to bosses (world bosses and dungeon/raid bosses)
 *   114 Merciless              damage-over-time ticks +15%
 *   115 Pressure               each hit on the same target +1% damage, up to 10 stacks (+10%); switching
 *                              targets resets it (tracked per attacker, so a pet keeps its own stacks;
 *                              direct hits add a stack, damage-over-time ticks use the current stacks)
 *   116 Chaos                  each damaging ability (a spell or a weapon strike, not auto attacks or
 *                              damage-over-time ticks) has a 10% chance to deal 50% more damage
 *   117 Power Conversion       every 100 of your highest base stat = +1% damage, up to +10%
 *   118 Healing Powah          healing done +10% (direct heals and heal-over-time ticks)
 *   119 Shadow Mastery         Shadow spell damage +10%
 *   120 Holy Mastery           Holy spell damage +10%
 *   121 Arcane Mastery         Arcane spell damage +10%
 *   122 Nature Mastery         Nature spell damage +10%
 *   123 Fire Mastery           Fire spell damage +10%
 *   124 Frost Mastery          Frost spell damage +10%
 *   125 Physical Mastery       Physical damage +10% (melee and auto attacks, weapon strikes, Physical
 *                              spells and bleeds)
 *                              (a spell counts for a school if that school is part of it, e.g. Shadowfrost)
 *
 * Utility perks (ids 301-399, no active limit):
 *   303 Iron Will              crowd-control effects from enemies on you (and your pets) last shorter. Ranked
 *                              (mod_unbound.conf): Rank 1 -10% from level 1, Rank 2 -20% from level 30, Rank 3
 *                              -30% from level 60. Crowd control = charm, disorient, fear, root, silence, sleep,
 *                              stun, freeze, knockout, polymorph, horror, sap (by mechanic, or by aura type for
 *                              spells without one). Applied to the aura's base duration, so it stacks with
 *                              racials and talents (e.g. an Orc's 15% stun reduction) and diminishing returns.
 *
 * Class perks (ids 1001+):
 *  1001 Retribution (Paladin)  Improved Divine Storm: Divine Storm hits up to 6 enemies (normally 4), and every
 *                              enemy it hits also takes a Crusader Strike.
 *                              All Will Be Judged!: a Judgement spreads to up to 4 more enemies within 10 yards
 *                              of the target, and every enemy a Judgement hits takes a free Exorcism (no cooldown).
 *                              Exorcist: Exorcism scales with 30% of attack power and 30% of spell power
 *                              (instead of 15% / 15%).
 *                              Righteous Explosion: an enemy dying with your Righteous Vengeance damage-over-
 *                              time deals the damage left on it to up to 5 enemies within 8 yards.
 *                              By Sword & Light: Holy damage +15%, Physical damage +10%.
 *                              The extra Crusader Strikes, Judgements and Exorcisms are free triggered casts.
 *
 * Settings (mod_unbound.conf): Unbound.Perks.RapidRecovery (on/off), .Delay (ms per rank), .Percent (per rank),
 * .RankLevels (level per rank); Unbound.Perks.IronWill.Percent (per rank), .RankLevels (level per rank).
 */

#include "Chat.h"
#include "ChatCommand.h"
#include "Config.h"
#include "CellImpl.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringConvert.h"
#include "Tokenize.h"
#include "WorldPacket.h"

#include <algorithm>
#include <cmath>
#include <list>
#include <map>
#include <set>
#include <unordered_map>
#include <utility>
#include <vector>

namespace
{
    // ------------------------------------------------------------------ Rapid Recovery settings
    struct RecoveryRank
    {
        uint32 delayMs;
        uint32 percent;
        uint32 level;   // character level that reaches this rank
    };
    bool sRapidRecovery = true;
    std::vector<RecoveryRank> sRecoveryRanks = { { 6000, 4, 1 }, { 5000, 6, 30 }, { 4000, 8, 60 } };
    constexpr uint32 RECOVERY_TICK_MS = 1000;
    constexpr uint32 PERK_ID_RAPID_RECOVERY = 3;

    // ------------------------------------------------------------------ Iron Will settings
    struct IronWillRank
    {
        uint32 percent; // crowd-control duration reduction
        uint32 level;   // character level that reaches this rank
    };
    std::vector<IronWillRank> sIronWillRanks = { { 10, 1 }, { 20, 30 }, { 30, 60 } };

    // "6000, 5000, 4000" -> { 6000, 5000, 4000 }
    std::vector<uint32> ParseList(std::string const& text)
    {
        std::vector<uint32> values;
        for (std::string_view part : Acore::Tokenize(text, ',', false))
        {
            while (!part.empty() && part.front() == ' ')
                part.remove_prefix(1);
            while (!part.empty() && part.back() == ' ')
                part.remove_suffix(1);
            if (Optional<uint32> value = Acore::StringTo<uint32>(part))
                values.push_back(*value);
        }
        return values;
    }

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
        PERK_IRON_WILL              = 303,
        PERK_RETRIBUTION            = 1001,  // Paladin
    };

    std::set<uint32> const IMPLEMENTED = {
        PERK_CYCLIC_POWER, PERK_CRITICAL_UNDERSTANDING, PERK_DEFENSIVE_SACRIFICE,
        PERK_DESPERATE_POWER, PERK_BLOCK_CAPPING, PERK_DODGE_CAPPING, PERK_PARRY_CAPPING,
        PERK_HASTE_CAPPING, PERK_PET_ENCOURAGEMENT, PERK_ROLLING_MOMENTUM,
        PERK_TUNNEL_VISION, PERK_COLLATERAL_DAMAGE, PERK_GIANT_SLAYER,
        PERK_MERCILESS, PERK_PRESSURE, PERK_CHAOS, PERK_POWER_CONVERSION,
        PERK_HEALING_POWAH, PERK_SHADOW_MASTERY, PERK_HOLY_MASTERY, PERK_ARCANE_MASTERY,
        PERK_NATURE_MASTERY, PERK_FIRE_MASTERY, PERK_FROST_MASTERY, PERK_PHYSICAL_MASTERY,
        PERK_IRON_WILL, PERK_RETRIBUTION };

    // Class perks: the class each one belongs to. The server refuses a class perk for any other class.
    std::unordered_map<uint32, uint8> const CLASS_PERKS = {
        { PERK_RETRIBUTION, CLASS_PALADIN },
    };

    // Retribution
    constexpr uint32 SPELL_CRUSADER_STRIKE = 35395;
    constexpr uint32 SPELL_EXORCISM_RANK_1 = 879;
    constexpr uint32 SPELL_RIGHTEOUS_VENGEANCE_DOT = 61840;
    constexpr int32 DIVINE_STORM_MAX_TARGETS = 6;     // normally 4
    constexpr float JUDGEMENT_SPREAD_RANGE = 10.0f;
    constexpr uint32 JUDGEMENT_SPREAD_TARGETS = 4;    // extra enemies besides the target
    constexpr float EXPLOSION_RANGE = 8.0f;
    constexpr uint32 EXPLOSION_MAX_TARGETS = 5;
    constexpr float EXORCIST_EXTRA_SCALING = 0.15f;   // 30% wanted, Exorcism already has 15% (spell_bonus_data)
    constexpr float SWORD_LIGHT_HOLY = 1.15f;         // +15%
    constexpr float SWORD_LIGHT_PHYSICAL = 1.10f;     // +10%

    constexpr char const* PREFIX = "UBPERK";
    constexpr uint32 MAX_ACTIVE_OFFENSIVE = 5;

    bool IsOffensive(uint32 perk) { return perk >= 101 && perk <= 199; }

    // False for a class perk of another class.
    bool CanUsePerk(Player const* player, uint32 perk)
    {
        auto itr = CLASS_PERKS.find(perk);
        return itr == CLASS_PERKS.end() || player->getClass() == itr->second;
    }

    uint32 CountOffensive(std::set<uint32> const& perks)
    {
        return uint32(std::count_if(perks.begin(), perks.end(), IsOffensive));
    }
    constexpr uint32 STAT_REFRESH_MS = 2000;

    constexpr uint32 CYCLE_MS = 25000;               // Cyclic Power period
    constexpr float CYCLE_CENTER = 1.05f;            // Cyclic Power: 0.90 .. 1.20 (-10% .. +20%)
    constexpr float CYCLE_AMPLITUDE = 0.15f;
    constexpr float SACRIFICE_DAMAGE_TAKEN = 1.10f;  // Defensive Sacrifice
    constexpr float SACRIFICE_STAT_PCT = 0.10f;
    constexpr uint32 SPELL_CRIT_DAMAGE_AURA = 58670; // "Prey on the Weak": one aura, +X% crit damage, all schools
    constexpr float CRIT_UNDERSTANDING_FLOOR = 25.0f;  // Critical Understanding: +1% crit damage per 1% crit above this
    constexpr int32 CRIT_UNDERSTANDING_MAX = 20;
    constexpr float DESPERATE_DAMAGE_DONE = 1.10f;   // Desperate Power
    constexpr float DESPERATE_RESIST_PCT = 0.50f;
    constexpr float AVOIDANCE_CAP = 20.0f;           // Block/Dodge/Parry Capping: cap (%)
    constexpr float AVOIDANCE_STEP = 1.0f;           // ... +1% damage per this much above the cap
    constexpr int32 AVOIDANCE_MAX_BONUS = 10;        // ... up to +10% each
    constexpr float HASTE_CAP = 5.0f;                // Haste Capping: +1% damage per 1% haste above this
    constexpr float HASTE_DAMAGE_TAKEN = 1.05f;
    constexpr float PET_DAMAGE_DONE = 1.15f;         // Pet Encouragement
    constexpr int32 MOMENTUM_STEP = 1;               // Rolling Momentum: % per second
    constexpr int32 MOMENTUM_MAX = 10;
    constexpr float FOCUS_BONUS = 1.10f;             // Tunnel Vision / Collateral Damage
    constexpr float FOCUS_PENALTY = 0.90f;
    constexpr float GIANT_SLAYER_BONUS = 1.10f;
    constexpr float MERCILESS_DOT_BONUS = 1.15f;
    constexpr float HEALING_POWAH_BONUS = 1.10f;
    constexpr float SCHOOL_MASTERY_BONUS = 1.10f;
    constexpr int32 PRESSURE_STEP = 1;               // % per stack
    constexpr uint32 PRESSURE_MAX_STACKS = 10;
    constexpr float CHAOS_CHANCE = 10.0f;            // %
    constexpr float CHAOS_MULTIPLIER = 1.50f;
    constexpr float POWER_CONVERSION_STAT = 100.0f;  // +1% per this much of the highest base stat
    constexpr float POWER_CONVERSION_MAX = 10.0f;

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
        std::map<uint32, uint8> rankOverride;  // perk ranks set by a GM (.perk rank)
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
        // 0.9 .. 1.2 (-10% .. +20%), a smooth wave over CYCLE_MS starting at +5%
        uint32 t = (getMSTime() - state->cycleStartMs) % CYCLE_MS;
        return CYCLE_CENTER + CYCLE_AMPLITUDE * std::sin(2.0f * float(M_PI) * float(t) / float(CYCLE_MS));
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

        // Retribution - By Sword & Light (the Paladin's own damage)
        if (Has(state, PERK_RETRIBUTION) && attacker->IsPlayer())
        {
            if (schools & SPELL_SCHOOL_MASK_HOLY)
                mult *= SWORD_LIGHT_HOLY;
            else if (schools & SPELL_SCHOOL_MASK_NORMAL)
                mult *= SWORD_LIGHT_PHYSICAL;
        }
        return mult;
    }

    // ------------------------------------------------------------------ Retribution helpers
    bool HasRetribution(Unit const* unit)
    {
        return unit && unit->IsPlayer() && Has(StateOf(unit->ToPlayer()), PERK_RETRIBUTION);
    }

    bool IsExorcism(SpellInfo const* spellInfo)
    {
        return spellInfo && sSpellMgr->GetFirstSpellInChain(spellInfo->Id) == SPELL_EXORCISM_RANK_1;
    }

    // The highest Exorcism rank the player's level allows.
    uint32 ExorcismFor(Player const* player)
    {
        uint32 best = 0;
        for (uint32 id = SPELL_EXORCISM_RANK_1; id; id = sSpellMgr->GetNextSpellInChain(id))
            if (SpellInfo const* info = sSpellMgr->GetSpellInfo(id))
                if (info->SpellLevel <= player->GetLevel())
                    best = id;
        return best;
    }

    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* caster, float range)
    {
        std::list<Unit*> units;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, caster, range);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, units, check);
        Cell::VisitObjects(center, searcher, range);
        units.remove_if([caster](Unit* u) { return !caster->IsValidAttackTarget(u); });
        return units;
    }

    // Righteous Explosion: deal what is left of the dying enemy's Righteous Vengeance around it.
    void ScheduleRighteousExplosion(Unit* victim)
    {
        for (AuraEffect const* eff : victim->GetAuraEffectsByType(SPELL_AURA_PERIODIC_DAMAGE))
        {
            if (eff->GetId() != SPELL_RIGHTEOUS_VENGEANCE_DOT)
                continue;
            Unit* caster = eff->GetCaster();
            if (!HasRetribution(caster))
                continue;
            int32 ticksLeft = eff->GetTotalTicks() - int32(eff->GetTickNumber());
            uint32 remaining = uint32(std::max(0, eff->GetAmount()) * std::max(0, ticksLeft));
            if (!remaining)
                continue;
            ObjectGuid victimGuid = victim->GetGUID();
            // after the killing blow has been dealt, never inside it
            caster->m_Events.AddEventAtOffset([caster, victimGuid, remaining]()
            {
                Unit* corpse = ObjectAccessor::GetUnit(*caster, victimGuid);
                SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(SPELL_RIGHTEOUS_VENGEANCE_DOT);
                if (!corpse || !spellInfo || !caster->IsInWorld() || corpse->GetMap() != caster->GetMap())
                    return;
                std::list<Unit*> enemies = EnemiesNear(corpse, caster, EXPLOSION_RANGE);
                enemies.sort(Acore::ObjectDistanceOrderPred(corpse));
                uint32 hits = 0;
                for (Unit* enemy : enemies)
                {
                    if (enemy == corpse || ++hits > EXPLOSION_MAX_TARGETS)
                        continue;
                    SpellNonMeleeDamage damageInfo(caster, enemy, spellInfo, SPELL_SCHOOL_MASK_HOLY);
                    damageInfo.damage = remaining;
                    caster->SendSpellNonMeleeDamageLog(&damageInfo);
                    caster->DealSpellDamage(&damageInfo, true);
                }
            }, 1ms);
        }
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
            mult *= CHAOS_MULTIPLIER;

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

    // Block/Dodge/Parry/Haste Capping: +1% damage per AVOIDANCE_STEP above the cap, up to AVOIDANCE_MAX_BONUS
    int32 OverCapBonus(float chance, float cap = AVOIDANCE_CAP)
    {
        return std::min(AVOIDANCE_MAX_BONUS, int32(std::max(0.0f, chance - cap) / AVOIDANCE_STEP));
    }

    void RefreshStatPerks(Player* player, PerkState& state)
    {
        // Desperate Power: remove 50% of each magic resistance (not counting what it already removed)
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
            capping += OverCapBonus(haste, HASTE_CAP);
        }
        state.cappingBonus = capping;

        // Power Conversion
        state.powerConversion = 0.0f;
        if (Has(&state, PERK_POWER_CONVERSION))
        {
            float highest = 0.0f;
            for (uint8 stat = STAT_STRENGTH; stat < MAX_STATS; ++stat)
                highest = std::max(highest, player->GetStat(Stats(stat)));
            state.powerConversion = std::min(POWER_CONVERSION_MAX, std::floor(highest / POWER_CONVERSION_STAT));
        }
        if (!Has(&state, PERK_PRESSURE))
            state.pressure.clear();

        // Critical Understanding
        int32 crit = 0;
        if (Has(&state, PERK_CRITICAL_UNDERSTANDING))
            crit = std::min(CRIT_UNDERSTANDING_MAX, int32(std::max(0.0f, HighestCritChance(player) - CRIT_UNDERSTANDING_FLOOR)));
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

    // ------------------------------------------------------------------ perk ranks
    // Ranked perks and their number of ranks (more perks get ranks later).
    std::map<uint32, uint8> RankedPerks()
    {
        return { { PERK_ID_RAPID_RECOVERY, uint8(sRecoveryRanks.size()) },
                 { PERK_IRON_WILL, uint8(sIronWillRanks.size()) } };
    }

    // The highest rank whose level the character has reached.
    template <typename Rank>
    uint8 RankForLevel(Player const* player, std::vector<Rank> const& ranks)
    {
        uint8 rank = 1;
        for (uint8 i = 0; i < ranks.size(); ++i)
            if (player->GetLevel() >= ranks[i].level)
                rank = i + 1;
        return rank;
    }

    uint8 MaxRank(uint32 perk)
    {
        auto ranks = RankedPerks();
        auto itr = ranks.find(perk);
        return itr == ranks.end() ? 1 : itr->second;
    }

    // The rank a character has: a GM-set rank, or the highest rank its level reaches.
    uint8 PerkRank(Player const* player, PerkState const& state, uint32 perk)
    {
        uint8 maxRank = MaxRank(perk);
        auto set = state.rankOverride.find(perk);
        if (set != state.rankOverride.end())
            return std::clamp<uint8>(set->second, 1, maxRank);
        if (perk == PERK_ID_RAPID_RECOVERY)
            return RankForLevel(player, sRecoveryRanks);
        if (perk == PERK_IRON_WILL)
            return RankForLevel(player, sIronWillRanks);
        return 1;
    }

    RecoveryRank const& RecoveryFor(Player const* player, PerkState const& state)
    {
        return sRecoveryRanks[PerkRank(player, state, PERK_ID_RAPID_RECOVERY) - 1];
    }

    void SendRanks(Player* player, PerkState const& state)
    {
        for (auto const& [perk, maxRank] : RankedPerks())
        {
            std::string values;
            if (perk == PERK_ID_RAPID_RECOVERY)
                for (RecoveryRank const& r : sRecoveryRanks)
                    values += (values.empty() ? "" : ";") + std::to_string(r.delayMs) + "," +
                              std::to_string(r.percent) + "," + std::to_string(r.level);
            else if (perk == PERK_IRON_WILL)
                for (IronWillRank const& r : sIronWillRanks)
                    values += (values.empty() ? "" : ";") + std::to_string(r.percent) + "," + std::to_string(r.level);
            SendAddon(player, "RANK:" + std::to_string(perk) + ":" + std::to_string(PerkRank(player, state, perk)) +
                ":" + std::to_string(maxRank) + ":" + values);
        }
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
        if (!IMPLEMENTED.count(perk) || on == bool(state.active.count(perk)) || (on && !CanUsePerk(player, perk)))
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
            SendRanks(player, state);
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
                    if (on && !CanUsePerk(player, *perk))
                        SendAddon(player, "ERR:That perk belongs to another class.");
                    else if (on && IsOffensive(*perk) && !state.active.count(*perk) &&
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
                    if (IMPLEMENTED.count(*perk) && CanUsePerk(player, *perk) && !wanted.count(*perk))
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
    void RestoreTick(Player* player, uint32 percent)
    {
        uint32 maxHealth = player->GetMaxHealth();
        if (player->GetHealth() < maxHealth)
        {
            uint32 gain = std::max<uint32>(1, player->CountPctFromMaxHealth(percent));
            player->SetHealth(std::min<uint32>(maxHealth, player->GetHealth() + gain));
        }

        uint32 maxMana = player->GetMaxPower(POWER_MANA);
        if (maxMana && player->GetPower(POWER_MANA) < maxMana)
        {
            uint32 gain = std::max<uint32>(1, maxMana * percent / 100);
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

        RecoveryRank const& rank = RecoveryFor(player, state);
        if (state.outOfCombatMs < rank.delayMs)
        {
            state.outOfCombatMs += diff;
            if (state.outOfCombatMs < rank.delayMs)
                return;
            state.tickMs = RECOVERY_TICK_MS; // first tick right at the delay mark
        }
        else
            state.tickMs += diff;

        if (state.tickMs < RECOVERY_TICK_MS)
            return;

        state.tickMs = 0;
        RestoreTick(player, rank.percent);
    }

    // ------------------------------------------------------------------ Iron Will
    constexpr uint64 CROWD_CONTROL_MECHANICS =
        (1ULL << MECHANIC_CHARM) | (1ULL << MECHANIC_DISORIENTED) | (1ULL << MECHANIC_FEAR) |
        (1ULL << MECHANIC_ROOT) | (1ULL << MECHANIC_SILENCE) | (1ULL << MECHANIC_SLEEP) |
        (1ULL << MECHANIC_STUN) | (1ULL << MECHANIC_FREEZE) | (1ULL << MECHANIC_KNOCKOUT) |
        (1ULL << MECHANIC_POLYMORPH) | (1ULL << MECHANIC_HORROR) | (1ULL << MECHANIC_SAPPED);

    bool IsCrowdControl(SpellInfo const* spellInfo)
    {
        if (spellInfo->GetAllEffectsMechanicMask() & CROWD_CONTROL_MECHANICS)
            return true;
        // spells without a mechanic: go by what the aura does
        for (AuraType type : { SPELL_AURA_MOD_STUN, SPELL_AURA_MOD_FEAR, SPELL_AURA_MOD_CONFUSE, SPELL_AURA_MOD_ROOT,
                               SPELL_AURA_MOD_CHARM, SPELL_AURA_MOD_POSSESS, SPELL_AURA_MOD_SILENCE,
                               SPELL_AURA_MOD_PACIFY_SILENCE })
            if (spellInfo->HasAura(type))
                return true;
        return false;
    }

    // Iron Will: shorten an enemy's crowd control on a player (or their pet) with the perk on.
    void ApplyIronWill(Aura const* aura, int32& maxDuration)
    {
        if (maxDuration <= 0 || aura->GetType() != UNIT_AURA_TYPE)
            return;
        Unit* target = aura->GetUnitOwner();
        PerkState const* state = PerkOwnerState(target);
        if (!Has(state, PERK_IRON_WILL))
            return;
        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (spellInfo->IsPositive() || !IsCrowdControl(spellInfo))
            return;
        Unit* caster = aura->GetCaster();
        if (!caster || caster == target || !caster->IsHostileTo(target))
            return;
        Player* owner = target->GetCharmerOrOwnerPlayerOrPlayerItself();
        uint32 percent = sIronWillRanks[PerkRank(owner, *state, PERK_IRON_WILL) - 1].percent;
        maxDuration = std::max<int32>(1, maxDuration - int32(int64(maxDuration) * percent / 100));
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
        // one value per rank; a single value means one rank
        std::vector<uint32> delays = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.RapidRecovery.Delay", "6000, 5000, 4000"));
        std::vector<uint32> percents = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.RapidRecovery.Percent", "4, 6, 8"));
        std::vector<uint32> levels = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.RapidRecovery.RankLevels", "1, 30, 60"));
        size_t count = std::min(delays.size(), percents.size());
        if (!count)
        {
            delays = { 4000 };
            percents = { 8 };
            count = 1;
        }
        sRecoveryRanks.clear();
        for (size_t i = 0; i < count; ++i)
            sRecoveryRanks.push_back({ delays[i], std::clamp<uint32>(percents[i], 1, 100),
                                       i < levels.size() ? levels[i] : (i == 0 ? 1 : 255) });

        std::vector<uint32> willPercents = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.IronWill.Percent", "10, 20, 30"));
        std::vector<uint32> willLevels = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.IronWill.RankLevels", "1, 30, 60"));
        if (willPercents.empty())
            willPercents = { 30 };
        sIronWillRanks.clear();
        for (size_t i = 0; i < willPercents.size(); ++i)
            sIronWillRanks.push_back({ std::min<uint32>(willPercents[i], 100),
                                       i < willLevels.size() ? willLevels[i] : (i == 0 ? 1 : 255) });
    }
};

class unbound_perks_spell : public AllSpellScript
{
public:
    unbound_perks_spell() : AllSpellScript("unbound_perks_spell", {
        ALLSPELLHOOK_ON_CALC_MAX_DURATION
    }) { }

    void OnCalcMaxDuration(Aura const* aura, int32& maxDuration) override
    {
        ApplyIronWill(aura, maxDuration);
    }
};

class unbound_perks_player : public PlayerScript
{
public:
    unbound_perks_player() : PlayerScript("unbound_perks_player", {
        PLAYERHOOK_ON_LEVEL_CHANGED,
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
                if (!IMPLEMENTED.count(perk))
                    continue;
                if (CanUsePerk(player, perk))
                    state.active.insert(perk);
                else
                    SavePerk(player, perk, false); // another class's perk: switch it off for good
            } while (result->NextRow());
        }
        if (QueryResult result = CharacterDatabase.Query("SELECT `perk`, `rank` FROM `character_unbound_perk_ranks` WHERE `guid` = {}",
            player->GetGUID().GetCounter()))
        {
            do
                state.rankOverride[(*result)[0].Get<uint32>()] = (*result)[1].Get<uint8>();
            while (result->NextRow());
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
        CharacterDatabase.Execute("DELETE FROM `character_unbound_perk_ranks` WHERE `guid` = {}", guid.GetCounter());
    }

    // ranks that come from the level change with it
    void OnPlayerLevelChanged(Player* player, uint8 /*oldLevel*/) override
    {
        if (PerkState* state = StateOf(player))
            SendRanks(player, *state);
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
        // Retribution - Exorcist: Exorcism gets 60% of attack power and spell power
        if (damage > 0 && IsExorcism(spellInfo) && HasRetribution(attacker))
            damage += int32(EXORCIST_EXTRA_SCALING * (attacker->GetTotalAttackPowerValue(BASE_ATTACK) +
                                                      attacker->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_HOLY)));
        ApplyMultipliers(target, attacker, damage, spellInfo, HitKind::Spell);
    }

    // Retribution - Righteous Explosion: notice the killing blow while the dying enemy still has its auras.
    uint32 DealDamage(Unit* /*attacker*/, Unit* victim, uint32 damage, DamageEffectType /*damagetype*/) override
    {
        if (victim && damage && victim->IsAlive() && damage >= victim->GetHealth() &&
            victim->HasAura(SPELL_RIGHTEOUS_VENGEANCE_DOT))
            ScheduleRighteousExplosion(victim);
        return damage;
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

// 53385 - Divine Storm (Retribution perk: up to 6 targets, a Crusader Strike on every enemy hit)
class spell_unbound_ret_divine_storm : public SpellScript
{
    PrepareSpellScript(spell_unbound_ret_divine_storm);

    void RaiseTargetCap()
    {
        if (HasRetribution(GetCaster()))
            GetSpell()->SetSpellValue(SPELLVALUE_MAX_TARGETS, DIVINE_STORM_MAX_TARGETS);
    }

    void CrusaderStrike()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (target && target != caster && HasRetribution(caster) && caster->IsValidAttackTarget(target))
            caster->CastSpell(target, SPELL_CRUSADER_STRIKE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_unbound_ret_divine_storm::RaiseTargetCap);
        AfterHit += SpellHitFn(spell_unbound_ret_divine_storm::CrusaderStrike);
    }
};

// 20271, 53407, 53408 - Judgements (Retribution perk: spread to 4 more enemies within 10 yards, a free Exorcism
// on each enemy)
class spell_unbound_ret_judgement : public SpellScript
{
    PrepareSpellScript(spell_unbound_ret_judgement);

    void JudgeAll()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target || !HasRetribution(caster) || !caster->IsValidAttackTarget(target))
            return;

        if (uint32 exorcism = ExorcismFor(caster->ToPlayer()))
            caster->CastSpell(target, exorcism, TRIGGERED_FULL_MASK);

        if (GetSpell()->IsTriggered()) // the spread Judgements don't spread again
            return;
        std::list<Unit*> enemies = EnemiesNear(target, caster, JUDGEMENT_SPREAD_RANGE);
        enemies.remove(target);
        enemies.sort(Acore::ObjectDistanceOrderPred(target));
        uint32 spread = 0;
        for (Unit* enemy : enemies)
        {
            if (++spread > JUDGEMENT_SPREAD_TARGETS)
                break;
            caster->CastSpell(enemy, GetSpellInfo()->Id, TRIGGERED_FULL_MASK);
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_unbound_ret_judgement::JudgeAll);
    }
};

// .perk rank <perk id> [rank]: set the selected player's (or your own) rank of a perk, for testing.
// Without a rank the perk goes back to the rank the character's level gives.
class unbound_perks_command : public CommandScript
{
public:
    unbound_perks_command() : CommandScript("unbound_perks_command") { }

    Acore::ChatCommands::ChatCommandTable GetCommands() const override
    {
        using namespace Acore::ChatCommands;
        static ChatCommandTable perkTable =
        {
            { "rank", HandlePerkRank, rbac::RBAC_PERM_COMMAND_MODIFY, Console::No },
        };
        static ChatCommandTable commandTable =
        {
            { "perk", perkTable },
        };
        return commandTable;
    }

    static bool HandlePerkRank(ChatHandler* handler, uint32 perk, Optional<uint8> rank)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        PerkState* state = target ? StateOf(target) : nullptr;
        if (!state)
            return false;
        uint8 maxRank = MaxRank(perk);
        if (!RankedPerks().count(perk))
        {
            handler->PSendSysMessage("Perk {} has no ranks. Ranked perks: 3 (Rapid Recovery), 303 (Iron Will).", perk);
            return true;
        }
        uint32 guid = target->GetGUID().GetCounter();
        if (rank)
        {
            uint8 value = std::clamp<uint8>(*rank, 1, maxRank);
            state->rankOverride[perk] = value;
            CharacterDatabase.Execute("REPLACE INTO `character_unbound_perk_ranks` (`guid`, `perk`, `rank`) VALUES ({}, {}, {})",
                guid, perk, value);
        }
        else
        {
            state->rankOverride.erase(perk);
            CharacterDatabase.Execute("DELETE FROM `character_unbound_perk_ranks` WHERE `guid` = {} AND `perk` = {}", guid, perk);
        }
        uint8 now = PerkRank(target, *state, perk);
        handler->PSendSysMessage("{}: perk {} is now Rank {} / {}{}.", target->GetName(), perk, now, maxRank,
            rank ? "" : " (from level)");
        SendRanks(target, *state);
        return true;
    }
};

void AddSC_unbound_perks()
{
    new unbound_perks_world();
    new unbound_perks_command();
    new unbound_perks_player();
    new unbound_perks_unit();
    new unbound_perks_spell();
    RegisterSpellScript(spell_unbound_ret_divine_storm);
    RegisterSpellScript(spell_unbound_ret_judgement);
}
