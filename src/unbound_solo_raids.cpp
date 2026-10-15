/*
 * mod-unbound: soloable raid mechanics.
 *
 * A few raid bosses have mechanics no single player can handle however strong they are (a mind
 * control on the only player, a debuff only a second tank can take, eggs only a mind-controlled boss
 * can break). These fixes only apply while a raid has at most one player in it (GMs don't count;
 * pets and guardians aren't players, so a hunter with a pet is still solo; playerbots are players, so
 * a raid with bots in it isn't solo). With two or more players every fight is unchanged.
 *
 * Blackwing Lair:
 *   Razorgore the Untamed  Grethok the Controller's Dominate Mind (14515) fails. During the egg
 *                          event, eggs (177807) break when the player walks over or clicks them,
 *                          instead of only by Razorgore under the Orb of Domination's control.
 *                          (Killing Razorgore before the last egg still blows up the room.)
 *   Vaelastrasz            Burning Adrenaline (18173) fails: every third one goes on his target and
 *                          kills them when it ends.
 *   Ebonroc                Shadow of Ebonroc (23340) fails: it heals him from every hit on the
 *                          debuffed tank, which a second tank normally takes over from.
 *   Chromaggus             Time Lapse (23310) fails: he ignores targets that have it, so with one
 *                          player he would have nobody to attack. Chromatic Mutation (23174, all five
 *                          Brood Afflictions) fails.
 *   Nefarian               Lord Victor Nefarius' Shadow Command (22667, a mind control) fails.
 *
 * The spells are bound to spell_unbound_solo_raid_block in data/sql/db-world/unbound_solo_raids.sql
 * and only fail when cast by the creature listed below, so the same spells used elsewhere are unchanged.
 * Each boss has an on/off setting in mod_unbound.conf (Unbound.SoloRaid.*).
 */

#include "Config.h"
#include "Creature.h"
#include "CreatureAI.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GameObjectScript.h"
#include "InstanceScript.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"

#include <array>

namespace
{
    enum SoloRaidFix : uint8
    {
        FIX_RAZORGORE,
        FIX_VAELASTRASZ,
        FIX_EBONROC,
        FIX_CHROMAGGUS,
        FIX_NEFARIAN,
        MAX_SOLO_RAID_FIX
    };

    // Config key suffix per fix (Unbound.SoloRaid.<key>)
    constexpr std::array<char const*, MAX_SOLO_RAID_FIX> FIX_KEYS =
    {
        "Razorgore", "Vaelastrasz", "Ebonroc", "Chromaggus", "Nefarian"
    };

    bool sEnabled = true;
    std::array<bool, MAX_SOLO_RAID_FIX> sFixEnabled = { };

    struct BlockedSpell
    {
        uint32 spellId;
        uint32 casterEntry;
        SoloRaidFix fix;
    };

    // Keep in sync with data/sql/db-world/unbound_solo_raids.sql
    constexpr std::array<BlockedSpell, 6> BLOCKED_SPELLS =
    {{
        { 14515, 12557, FIX_RAZORGORE   },  // Dominate Mind, Grethok the Controller
        { 18173, 13020, FIX_VAELASTRASZ },  // Burning Adrenaline, Vaelastrasz the Corrupt
        { 23340, 14601, FIX_EBONROC     },  // Shadow of Ebonroc, Ebonroc
        { 23310, 14020, FIX_CHROMAGGUS  },  // Time Lapse, Chromaggus
        { 23174, 14020, FIX_CHROMAGGUS  },  // Chromatic Mutation, Chromaggus
        { 22667, 10162, FIX_NEFARIAN    },  // Shadow Command, Lord Victor Nefarius
    }};

    // Razorgore's egg event (scripts/EasternKingdoms/BlackrockMountain/BlackwingLair/blackwing_lair.h)
    constexpr uint32 BWL_DATA_RAZORGORE = 0;          // DATA_RAZORGORE_THE_UNTAMED (GUID data)
    constexpr uint32 BWL_DATA_EGG_EVENT = 2;          // DATA_EGG_EVENT
    constexpr int32 BWL_TALK_EGG_BROKEN_RAND = 3;     // TALK_EGG_BROKEN_RAND (Razorgore DoAction)
    constexpr float EGG_STOMP_RANGE = 2.5f;           // walking this close to an egg breaks it
    constexpr uint32 EGG_CHECK_INTERVAL = 250;        // ms between walk-over checks

    bool IsFixActive(SoloRaidFix fix)
    {
        return sEnabled && sFixEnabled[fix];
    }

    // A raid with at most one player in it (GMs not counted).
    bool IsSoloRaid(Map const* map)
    {
        return map && map->IsRaid() && map->GetPlayersCountExceptGMs() <= 1;
    }
}

class spell_unbound_solo_raid_block : public SpellScript
{
    PrepareSpellScript(spell_unbound_solo_raid_block);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster || !caster->IsCreature() || !IsSoloRaid(caster->GetMap()))
            return SPELL_CAST_OK;

        uint32 const spellId = GetSpellInfo()->Id;
        for (BlockedSpell const& blocked : BLOCKED_SPELLS)
            if (blocked.spellId == spellId && blocked.casterEntry == caster->GetEntry() && IsFixActive(blocked.fix))
                return SPELL_FAILED_DONT_REPORT;

        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_unbound_solo_raid_block::CheckCast);
    }
};

// Black Dragon Egg (177807) in Razorgore's room. Normally only Razorgore, controlled through the Orb of
// Domination, can break them (spell_egg_event); solo, the player breaks them by walking over or clicking.
struct go_unbound_solo_razorgore_egg : public GameObjectAI
{
    go_unbound_solo_razorgore_egg(GameObject* go) : GameObjectAI(go), _checkTimer(EGG_CHECK_INTERVAL) { }

    void UpdateAI(uint32 diff) override
    {
        if (_checkTimer > diff)
        {
            _checkTimer -= diff;
            return;
        }
        _checkTimer = EGG_CHECK_INTERVAL;

        if (CanBreak())
            if (me->SelectNearestPlayer(EGG_STOMP_RANGE))
                Break();
    }

    bool GossipHello(Player* /*player*/, bool /*reportUse*/) override
    {
        if (!CanBreak())
            return false;   // the game's normal handling, as without this script

        Break();
        return true;
    }

private:
    bool CanBreak() const
    {
        if (!IsFixActive(FIX_RAZORGORE) || !IsSoloRaid(me->GetMap()))
            return false;

        if (!me->isSpawned() || me->getLootState() != GO_READY)
            return false;   // already broken

        InstanceScript* instance = me->GetInstanceScript();
        return instance && instance->GetData(BWL_DATA_EGG_EVENT) == IN_PROGRESS;   // Razorgore is engaged
    }

    // What spell_egg_event does when Razorgore breaks an egg.
    void Break()
    {
        InstanceScript* instance = me->GetInstanceScript();
        instance->SetData(BWL_DATA_EGG_EVENT, SPECIAL);   // counts the egg; the last one starts phase two

        if (Creature* razorgore = ObjectAccessor::GetCreature(*me, instance->GetGuidData(BWL_DATA_RAZORGORE)))
            if (razorgore->AI())
                razorgore->AI()->DoAction(BWL_TALK_EGG_BROKEN_RAND);

        me->SetLootState(GO_READY);
        me->UseDoorOrButton(10000);
        me->SetRespawnTime(WEEK);
    }

    uint32 _checkTimer;
};

class unbound_solo_raids_world : public WorldScript
{
public:
    unbound_solo_raids_world() : WorldScript("unbound_solo_raids_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sEnabled = sConfigMgr->GetOption<bool>("Unbound.SoloRaid.Enable", true);
        for (uint8 fix = 0; fix < MAX_SOLO_RAID_FIX; ++fix)
            sFixEnabled[fix] = sConfigMgr->GetOption<bool>(std::string("Unbound.SoloRaid.") + FIX_KEYS[fix], true);
    }
};

void AddSC_unbound_solo_raids()
{
    RegisterSpellScript(spell_unbound_solo_raid_block);
    RegisterGameObjectAI(go_unbound_solo_razorgore_egg);
    new unbound_solo_raids_world();
}
