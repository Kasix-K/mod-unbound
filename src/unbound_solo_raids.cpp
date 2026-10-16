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
 *                          His add waves come at most every Unbound.SoloRaid.RazorgoreWaveInterval
 *                          seconds (the instance script sends one every 15): a wave that comes sooner
 *                          is removed as it appears.
 *   Vaelastrasz            Burning Adrenaline (18173) fails: every third one goes on his target and
 *                          kills them when it ends.
 *   Ebonroc                Shadow of Ebonroc (23340) fails: it heals him from every hit on the
 *                          debuffed tank, which a second tank normally takes over from.
 *   Chromaggus             Time Lapse (23310) fails: he ignores targets that have it, so with one
 *                          player he would have nobody to attack. Chromatic Mutation (23174, all five
 *                          Brood Afflictions) fails.
 *   Nefarian               Lord Victor Nefarius' Shadow Command (22667, a mind control) fails.
 *
 * Molten Core:
 *   Lucifron               His Flamewaker Protectors' Dominate Mind (20604) fails.
 *   Firelords              Soul Burn (19393: fire damage over time that also silences) fails. (For groups,
 *                          unbound_solo_raids.sql slows it to every 25 seconds.)
 *
 * Zul'Gurub:
 *   Jin'do the Hexxer      Brain Wash Totem (24262, the totem mind controls a player) and Banish (24466,
 *                          teleports the only player away into the pit) fail.
 *   Hakkar                 Cause Insanity (24327, a mind control) fails. Blood Siphon (24324) fails: it
 *                          heals him from every player without Poisonous Blood, which the raid gets
 *                          from killing his Sons.
 *
 * Ruins of Ahn'Qiraj:
 *   Ayamiss the Hunter     Paralyze (25725) fails, and so does the Hive'Zara Larva's Feed (25721) on the
 *                          paralyzed player, which a stunned solo player can't stop.
 *   Ossirian the Unscarred Curse of Tongues (25195) fails, and Enveloping Winds (25189, every 20 seconds)
 *                          fails if it comes less than Unbound.SoloRaid.OssirianWindsInterval seconds after
 *                          the last one that landed.
 *
 * Temple of Ahn'Qiraj:
 *   The Prophet Skeram     True Fulfillment (785, a mind control) fails.
 *   Twin Emperors          Heal Brother (7393) fails: it heals each emperor whenever they're close, and
 *                          keeping them apart takes two groups.
 *   Viscidus               Every hit counts several times (Unbound.SoloRaid.ViscidusHitMultiplier) towards
 *                          freezing him (200 frost hits) and shattering him (150 hits within 15 seconds
 *                          of freezing), which one player can't reach.
 *   Qiraji Mindslayer      Cause Insanity (26079, a mind control) fails.
 *
 * Naxxramas (classic, src/naxx40):
 *   Thaddius               Stalagg and Feugen don't revive each other (normally both must die within 5
 *                          seconds, on platforms far apart) and don't overload their Tesla Coils when
 *                          they follow the player off their platforms. The fix is in
 *                          boss_thaddius_40.cpp, through UnboundSoloThaddius() (unbound_solo_raids.h).
 *   Gothik the Harvester   His phase two teleport between the live and dead sides keeps the player on his
 *                          threat list instead of dropping everyone on the other side (with one player
 *                          that empties it and he resets). Solo the gate is open by then (it opens when
 *                          the raid isn't split between the sides), so he follows the player through it.
 *                          The fix is in boss_gothik_40.cpp, through UnboundSoloGothik().
 *
 * The spells are bound to spell_unbound_solo_raid_block in data/sql/db-world/unbound_solo_raids.sql
 * and only fail when cast by the creature listed below, so the same spells used elsewhere are unchanged.
 * Each boss has an on/off setting in mod_unbound.conf (Unbound.SoloRaid.*).
 */

#include "unbound_solo_raids.h"

#include "Config.h"
#include "Creature.h"
#include "AllCreatureScript.h"
#include "GameTime.h"
#include "CreatureAI.h"
#include "GameObject.h"
#include "GameObjectAI.h"
#include "GameObjectScript.h"
#include "InstanceScript.h"
#include "ItemTemplate.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "SpellInfo.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "UnitScript.h"

#include <algorithm>
#include <array>
#include <mutex>
#include <unordered_map>

namespace
{
    enum SoloRaidFix : uint8
    {
        FIX_RAZORGORE,
        FIX_VAELASTRASZ,
        FIX_EBONROC,
        FIX_CHROMAGGUS,
        FIX_NEFARIAN,
        FIX_LUCIFRON,
        FIX_JINDO,
        FIX_HAKKAR,
        FIX_AYAMISS,
        FIX_SKERAM,
        FIX_TWIN_EMPERORS,
        FIX_VISCIDUS,
        FIX_QIRAJI_MINDSLAYER,
        FIX_THADDIUS,
        FIX_GOTHIK,
        FIX_OSSIRIAN,
        FIX_FIRELORD,
        MAX_SOLO_RAID_FIX
    };

    // Config key suffix per fix (Unbound.SoloRaid.<key>)
    constexpr std::array<char const*, MAX_SOLO_RAID_FIX> FIX_KEYS =
    {
        "Razorgore", "Vaelastrasz", "Ebonroc", "Chromaggus", "Nefarian",
        "Lucifron", "Jindo", "Hakkar", "Ayamiss", "Skeram", "TwinEmperors", "Viscidus", "QirajiMindslayer",
        "Thaddius", "Gothik", "Ossirian", "Firelord"
    };

    bool sEnabled = true;
    std::array<bool, MAX_SOLO_RAID_FIX> sFixEnabled = { };
    uint32 sViscidusHitMultiplier = 10;
    uint32 sRazorgoreWaveInterval = 30;    // seconds
    uint32 sOssirianWindsInterval = 40;    // seconds

    struct BlockedSpell
    {
        uint32 spellId;
        uint32 casterEntry;
        SoloRaidFix fix;
    };

    // Keep in sync with data/sql/db-world/unbound_solo_raids.sql
    constexpr std::array<BlockedSpell, 19> BLOCKED_SPELLS =
    {{
        { 14515, 12557, FIX_RAZORGORE         },  // Dominate Mind, Grethok the Controller
        { 18173, 13020, FIX_VAELASTRASZ       },  // Burning Adrenaline, Vaelastrasz the Corrupt
        { 23340, 14601, FIX_EBONROC           },  // Shadow of Ebonroc, Ebonroc
        { 23310, 14020, FIX_CHROMAGGUS        },  // Time Lapse, Chromaggus
        { 23174, 14020, FIX_CHROMAGGUS        },  // Chromatic Mutation, Chromaggus
        { 22667, 10162, FIX_NEFARIAN          },  // Shadow Command, Lord Victor Nefarius
        { 20604, 12119, FIX_LUCIFRON          },  // Dominate Mind, Flamewaker Protector
        { 19393, 11668, FIX_FIRELORD          },  // Soul Burn (silences), Firelord
        { 24262, 11380, FIX_JINDO             },  // Brain Wash Totem, Jin'do the Hexxer
        { 24466, 11380, FIX_JINDO             },  // Banish, Jin'do the Hexxer
        { 24327, 14834, FIX_HAKKAR            },  // Cause Insanity, Hakkar
        { 24324, 14834, FIX_HAKKAR            },  // Blood Siphon, Hakkar
        { 25725, 15369, FIX_AYAMISS           },  // Paralyze, Ayamiss the Hunter
        { 25721, 15555, FIX_AYAMISS           },  // Feed, Hive'Zara Larva
        { 25195, 15339, FIX_OSSIRIAN          },  // Curse of Tongues, Ossirian the Unscarred
        { 785,   15263, FIX_SKERAM            },  // True Fulfillment, The Prophet Skeram (and his images)
        { 7393,  15275, FIX_TWIN_EMPERORS     },  // Heal Brother, Emperor Vek'nilash
        { 7393,  15276, FIX_TWIN_EMPERORS     },  // Heal Brother, Emperor Vek'lor
        { 26079, 15246, FIX_QIRAJI_MINDSLAYER },  // Cause Insanity, Qiraji Mindslayer
    }};

    constexpr uint32 NPC_VISCIDUS = 15299;
    constexpr uint32 NPC_OSSIRIAN = 15339;

    // Razorgore's add waves (instance_blackwing_lair.cpp, EVENT_RAZOR_SPAWN: 2-5 adds every 15 seconds)
    constexpr uint32 MAP_BWL_RAZORGORE_WAVES = 469;
    constexpr uint32 NPC_BLACKWING_DRAGON = 12422;
    constexpr uint32 NPC_BLACKWING_LEGIONAIRE = 12416;
    constexpr uint32 NPC_BLACKWING_MAGE = 12420;
    constexpr uint32 WAVE_GROUP_MS = 2000;            // adds summoned this close together are one wave

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

bool UnboundSoloThaddius(Map const* map)
{
    return IsFixActive(FIX_THADDIUS) && IsSoloRaid(map);
}

bool UnboundSoloGothik(Map const* map)
{
    return IsFixActive(FIX_GOTHIK) && IsSoloRaid(map);
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

// Enveloping Winds (25189), Ossirian the Unscarred: his script casts it on his target every 20 seconds. Solo, a
// cast less than sOssirianWindsInterval seconds after the last one that landed fails.
class spell_unbound_solo_ossirian_winds : public SpellScript
{
    PrepareSpellScript(spell_unbound_solo_ossirian_winds);

    SpellCastResult CheckCast()
    {
        Unit* caster = GetCaster();
        if (!caster || caster->GetEntry() != NPC_OSSIRIAN || !IsFixActive(FIX_OSSIRIAN) || !IsSoloRaid(caster->GetMap()))
            return SPELL_CAST_OK;

        uint32 const now = GameTime::GetGameTimeMS().count();
        std::lock_guard<std::mutex> lock(_mutex);   // instances update on several threads at once
        auto itr = _lastCast.find(caster->GetGUID());
        if (itr != _lastCast.end() && now - itr->second < sOssirianWindsInterval * IN_MILLISECONDS)
            return SPELL_FAILED_DONT_REPORT;
        _lastCast[caster->GetGUID()] = now;
        return SPELL_CAST_OK;
    }

    void Register() override
    {
        OnCheckCast += SpellCheckCastFn(spell_unbound_solo_ossirian_winds::CheckCast);
    }

    static std::mutex _mutex;
    static std::unordered_map<ObjectGuid, uint32> _lastCast;   // Ossirian -> when Enveloping Winds last landed
};

std::mutex spell_unbound_solo_ossirian_winds::_mutex;
std::unordered_map<ObjectGuid, uint32> spell_unbound_solo_ossirian_winds::_lastCast;

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

// Viscidus (Temple of Ahn'Qiraj): his script counts frost hits to freeze him (200) and, once frozen,
// melee hits to shatter him (150 within 15 seconds). Solo, every hit counts sViscidusHitMultiplier times:
// the extra counts go through his own script (SpellHit and DamageTaken), so its thresholds, emotes and
// phases work unchanged.
class unbound_solo_viscidus_unit : public UnitScript
{
public:
    unbound_solo_viscidus_unit() : UnitScript("unbound_solo_viscidus_unit", true, {
        UNITHOOK_MODIFY_MELEE_DAMAGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN
    }) { }

    // A melee swing at him (his script only counts these while he's frozen)
    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& /*damage*/) override
    {
        Creature* viscidus = SoloViscidus(target);
        if (!viscidus || !attacker)
            return;

        for (uint32 i = 1; i < sViscidusHitMultiplier && viscidus->IsAlive() && viscidus->IsAIEnabled; ++i)
        {
            uint32 noDamage = 0;
            viscidus->AI()->DamageTaken(attacker, noDamage, DIRECT_DAMAGE, SPELL_SCHOOL_MASK_NORMAL);
        }
    }

    // A damaging spell on him (his script counts frost spells before he's frozen)
    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& /*damage*/, SpellInfo const* spellInfo) override
    {
        Creature* viscidus = SoloViscidus(target);
        if (!viscidus || !attacker || !spellInfo)
            return;

        // his script reads a wand's damage type from the caster's wand, which only players have
        bool const wand = spellInfo->EquippedItemClass == ITEM_CLASS_WEAPON &&
            (spellInfo->EquippedItemSubClassMask & (1 << ITEM_SUBCLASS_WEAPON_WAND));
        if (wand && !attacker->IsPlayer())
            return;

        for (uint32 i = 1; i < sViscidusHitMultiplier && viscidus->IsAlive() && viscidus->IsAIEnabled; ++i)
            viscidus->AI()->SpellHit(attacker, spellInfo);
    }

private:
    static Creature* SoloViscidus(Unit* target)
    {
        if (!target || !target->IsCreature() || target->GetEntry() != NPC_VISCIDUS)
            return nullptr;

        if (!IsFixActive(FIX_VISCIDUS) || !IsSoloRaid(target->GetMap()))
            return nullptr;

        Creature* viscidus = target->ToCreature();
        return viscidus->IsAIEnabled ? viscidus : nullptr;
    }
};

// Razorgore (Blackwing Lair): the instance script summons a wave of 2-5 adds every 15 seconds until 12 dragonkin
// and 40 orcs have come. Solo, a wave that comes less than sRazorgoreWaveInterval seconds after the last one
// kept is removed as it appears (the instance still counts it towards those totals, so fewer come in all).
class unbound_solo_razorgore_waves : public AllCreatureScript
{
public:
    unbound_solo_razorgore_waves() : AllCreatureScript("unbound_solo_razorgore_waves") { }

    void OnCreatureAddWorld(Creature* creature) override
    {
        uint32 const entry = creature->GetEntry();
        if (entry != NPC_BLACKWING_DRAGON && entry != NPC_BLACKWING_LEGIONAIRE && entry != NPC_BLACKWING_MAGE)
            return;
        if (!creature->IsSummon() || creature->GetMapId() != MAP_BWL_RAZORGORE_WAVES)
            return;
        if (!IsFixActive(FIX_RAZORGORE) || !IsSoloRaid(creature->GetMap()))
            return;

        uint32 const now = GameTime::GetGameTimeMS().count();
        bool keep;
        {
            // instances update on several threads at once
            std::lock_guard<std::mutex> lock(_mutex);
            Waves& waves = _waves[creature->GetInstanceId()];
            if (!waves.started || now - waves.waveStart > WAVE_GROUP_MS)   // a new wave
            {
                waves.waveStart = now;
                waves.waveKept = !waves.started || now - waves.lastKept >= sRazorgoreWaveInterval * IN_MILLISECONDS;
                if (waves.waveKept)
                    waves.lastKept = now;
                waves.started = true;
            }
            keep = waves.waveKept;
        }

        if (!keep)
        {
            creature->SetVisible(false);
            creature->DespawnOrUnsummon(1ms);   // after this update, not while it's being added
        }
    }

private:
    struct Waves
    {
        bool started = false;
        uint32 waveStart = 0;   // first add of the current wave
        bool waveKept = false;
        uint32 lastKept = 0;    // start of the last wave kept
    };

    std::mutex _mutex;
    std::unordered_map<uint32, Waves> _waves;   // instance id -> its waves
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
        sViscidusHitMultiplier = std::max<uint32>(1, sConfigMgr->GetOption<uint32>("Unbound.SoloRaid.ViscidusHitMultiplier", 10));
        sRazorgoreWaveInterval = sConfigMgr->GetOption<uint32>("Unbound.SoloRaid.RazorgoreWaveInterval", 30);
        sOssirianWindsInterval = sConfigMgr->GetOption<uint32>("Unbound.SoloRaid.OssirianWindsInterval", 40);
    }
};

void AddSC_unbound_solo_raids()
{
    RegisterSpellScript(spell_unbound_solo_raid_block);
    RegisterSpellScript(spell_unbound_solo_ossirian_winds);
    RegisterGameObjectAI(go_unbound_solo_razorgore_egg);
    new unbound_solo_viscidus_unit();
    new unbound_solo_razorgore_waves();
    new unbound_solo_raids_world();
}
