/*
 * mod-unbound: Onyxia's Lair as a classic level 60 raid.
 *
 * In 3.3.5 Onyxia's Lair is a level 80 raid. data/sql/db-world/unbound_classic_onyxia.sql makes it
 * classic again (entry from level 60, Onyxia level 63 with her classic health and melee, classic Whelps and
 * Warders, the classic loot and Head of Onyxia quests). Two things need code:
 *
 *  - Spell damage. Blizzard kept the classic spell ids for the level 80 fight and raised their damage
 *    (Flame Breath 3063-3937 became 18850-21150), so damage from these spells in the lair is scaled back to
 *    the classic value (classic average / 3.3.5 average, from the 1.12 and 3.3.5 Spell.dbc). Only in
 *    Onyxia's Lair (map 249) on its 10-player difficulty; the same spells elsewhere are unchanged.
 *  - Onyxian Lair Guards (36561), added in 3.2, despawn as soon as they appear. Their ScriptName points
 *    here instead of npc_onyxian_lair_guard.
 *
 * Scaling for solo players comes from mod-autobalance (AutoBalance.InflectionPoint.PerInstance for map
 * 249, set by server-setup/apply-unbound-settings.ps1).
 */

#include "Creature.h"
#include "CreatureAI.h"
#include "CreatureScript.h"
#include "Map.h"
#include "PassiveAI.h"
#include "ScriptMgr.h"
#include "SpellInfo.h"
#include "UnitScript.h"

#include <array>
#include <cmath>

namespace
{
    constexpr uint32 MAP_ONYXIAS_LAIR = 249;

    struct ClassicSpellDamage
    {
        uint32 firstId;
        uint32 lastId;      // inclusive
        float percent;      // of the 3.3.5 damage
    };

    // classic 1.12 damage / 3.3.5 damage (averages)
    constexpr std::array<ClassicSpellDamage, 16> CLASSIC_DAMAGE =
    {{
        { 18435, 18435, 17.50f },   // Flame Breath:  3063-3937  /  18850-21150
        { 18500, 18500,  3.26f },   // Wing Buffet:    563-937   /  21678-24322
        { 18392, 18392, 40.00f },   // Fireball:      1700-2300  /   4713-5287
        { 68867, 68867,  8.89f },   // Tail Sweep (3.2 version of 15847): 600-1000 / 8325-9675
        { 17731, 17731, 27.27f },   // Eruption:      1313-1687  /   5184-5816
        { 22191, 22202, 10.00f },   // Heated Ground (each patch triggers the next), per second: 413-587 / 4125-5875
        // Deep Breath: every breath and the breath patches it chains into: 1275-1725 / 6375-8625.
        // (The entrance breath chain 21131-21139 kept its classic damage and isn't listed.)
        { 17086, 17095, 20.00f },
        { 17097, 17097, 20.00f },
        { 18351, 18361, 20.00f },
        { 18564, 18576, 20.00f },
        { 18578, 18607, 20.00f },
        { 18609, 18609, 20.00f },
        { 18611, 18628, 20.00f },
        { 22267, 22268, 20.00f },
        // Onyxian Warder
        { 20203, 20203, 15.14f },   // Fire Nova:      464-596   /   3063-3937
        { 18958, 18958,  1.20f },   // Flame Lash:      56-64    /   4625-5375
    }};

    float ClassicPercent(Unit const* attacker, Unit const* target, SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return 100.0f;

        Map const* map = target ? target->GetMap() : (attacker ? attacker->GetMap() : nullptr);
        if (!map || map->GetId() != MAP_ONYXIAS_LAIR || map->GetDifficulty() != RAID_DIFFICULTY_10MAN_NORMAL)
            return 100.0f;

        for (ClassicSpellDamage const& entry : CLASSIC_DAMAGE)
            if (spellInfo->Id >= entry.firstId && spellInfo->Id <= entry.lastId)
                return entry.percent;

        return 100.0f;
    }
}

class unbound_classic_onyxia_unit : public UnitScript
{
public:
    unbound_classic_onyxia_unit() : UnitScript("unbound_classic_onyxia_unit", true, {
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
        UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK
    }) { }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        if (damage > 0)
        {
            float const percent = ClassicPercent(attacker, target, spellInfo);
            if (percent < 100.0f)
                damage = int32(std::lround(damage * percent / 100.0f));
        }
    }

    // Also called for heal-over-time ticks; none of the listed spells heals.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage, SpellInfo const* spellInfo) override
    {
        if (damage > 0)
        {
            float const percent = ClassicPercent(attacker, target, spellInfo);
            if (percent < 100.0f)
                damage = uint32(std::lround(damage * percent / 100.0f));
        }
    }
};

// Onyxian Lair Guard (36561): not part of the classic fight. Onyxia summons one when pulled and more
// during the air phase; each despawns on its first update without doing anything.
struct npc_unbound_onyxia_no_lair_guard : public NullCreatureAI
{
    npc_unbound_onyxia_no_lair_guard(Creature* creature) : NullCreatureAI(creature) { }

    void UpdateAI(uint32 /*diff*/) override
    {
        me->DespawnOrUnsummon();
    }
};

void AddSC_unbound_classic_onyxia()
{
    new unbound_classic_onyxia_unit();
    RegisterCreatureAI(npc_unbound_onyxia_no_lair_guard);
}
