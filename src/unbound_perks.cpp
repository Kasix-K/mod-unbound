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
 *
 * Settings (mod_unbound.conf): Unbound.Perks.RapidRecovery (on/off), .Delay (ms), .Percent.
 */

#include "Chat.h"
#include "Config.h"
#include "DatabaseEnv.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellAuras.h"
#include "StringConvert.h"
#include "Tokenize.h"
#include "WorldPacket.h"

#include <algorithm>
#include <cmath>
#include <set>
#include <unordered_map>

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
    };

    std::set<uint32> const IMPLEMENTED = {
        PERK_CYCLIC_POWER, PERK_CRITICAL_UNDERSTANDING, PERK_DEFENSIVE_SACRIFICE,
        PERK_DESPERATE_POWER, PERK_BLOCK_CAPPING, PERK_DODGE_CAPPING, PERK_PARRY_CAPPING,
        PERK_HASTE_CAPPING, PERK_PET_ENCOURAGEMENT, PERK_ROLLING_MOMENTUM };

    constexpr char const* PREFIX = "UBPERK";
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
    PerkState const* PerkOwnerState(Unit const* unit)
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

    float DamageDoneMultiplier(Unit const* attacker)
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
        return mult;
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

    template <typename T>
    void ApplyMultipliers(Unit* victim, Unit* attacker, T& damage)
    {
        if (damage <= 0 || attacker == victim)
            return;
        float mult = DamageDoneMultiplier(attacker) * DamageTakenMultiplier(victim);
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
                    SetPerk(player, state, *perk, parts[2] == "1");
        }
        else
        {
            std::set<uint32> wanted;
            std::string_view list = std::string_view(text).substr(5);
            for (std::string_view id : Acore::Tokenize(list, ',', false))
                if (Optional<uint32> perk = Acore::StringTo<uint32>(id))
                    if (IMPLEMENTED.count(*perk))
                        wanted.insert(*perk);
            for (uint32 perk : IMPLEMENTED)
                SetPerk(player, state, perk, wanted.count(perk) > 0);
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
        UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST
    }) { }

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
        ApplyMultipliers(target, attacker, damage);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* /*spellInfo*/) override
    {
        ApplyMultipliers(target, attacker, damage);
    }

    // Also called for heal-over-time ticks: only scale ticks on hostile targets.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage, SpellInfo const* /*spellInfo*/) override
    {
        if (target && attacker && target->IsFriendlyTo(attacker))
            return;
        ApplyMultipliers(target, attacker, damage);
    }
};

void AddSC_unbound_perks()
{
    new unbound_perks_world();
    new unbound_perks_player();
    new unbound_perks_unit();
}
