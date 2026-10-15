/*
 * mod-unbound: world boss announcements and the unchallenged despawn.
 *
 * The world bosses themselves (creature, spawn, SmartAI fight, loot) come from tools/world_bosses.py
 * (data/sql/db-world/unbound_world_bosses.sql) and respawn on their spawn's timer (spawntimesecs, 3 days).
 * This adds, for every boss in WORLD_BOSSES, server-wide announcements:
 *   - a warning before it spawns (Unbound.WorldBoss.Warnings, default 10 and 5 minutes before)
 *   - when it spawns, with the location
 *   - when it dies, with who killed it
 *   - when nobody killed it within Unbound.WorldBoss.DespawnHours (default 24) of spawning: it despawns
 *     (out of combat only) and its normal respawn timer starts again
 *
 * A creature only respawns while its grid is loaded, so the grid is loaded shortly before the respawn time
 * and the boss is kept active (its grid stays loaded) while it is alive; the despawn timer and the
 * announcements then work with nobody nearby. The time it spawned is kept in a world state (index = the
 * spawn's guid), so a restart doesn't reset the despawn timer.
 */

#include "Chat.h"
#include "Config.h"
#include "Creature.h"
#include "GameTime.h"
#include "Group.h"
#include "Map.h"
#include "MapMgr.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "StringConvert.h"
#include "Tokenize.h"
#include "WorldPacket.h"
#include "WorldSessionMgr.h"
#include "WorldState.h"

#include <algorithm>
#include <string>
#include <vector>

namespace
{
    struct WorldBoss
    {
        uint32 entry;
        ObjectGuid::LowType spawnId;  // creature.guid of its spawn
        char const* name;
        char const* location;         // "at <location>"
    };

    // Keep in sync with tools/world_bosses.py (WORLD_BOSSES).
    std::vector<WorldBoss> const WORLD_BOSSES = {
        { 190110, 9190110, "Hrimthar the Frostbound", "Lake Kel'Theril in Winterspring" },
    };

    constexpr uint32 TICK_MS = 1000;
    constexpr time_t PRELOAD_SECONDS = 60;  // load the grid this long before the respawn time

    bool sAnnounce = true;
    std::vector<uint32> sWarningMinutes = { 10, 5 };  // descending
    uint32 sDespawnHours = 24;

    struct BossTrack
    {
        bool initialized = false;
        bool alive = false;
        time_t warnedFor = 0;     // the respawn time the warnings below belong to
        size_t warningsSent = 0;  // how many of sWarningMinutes were announced for it
    };
    std::vector<BossTrack> sTracks(WORLD_BOSSES.size());
    uint32 sTimer = 0;

    // A system chat line to every player online. (ChatHandler::SendWorldText only sends to its own session,
    // and crashes without one.)
    void Announce(std::string const& text)
    {
        if (!sAnnounce)
            return;
        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_SYSTEM, LANG_UNIVERSAL, nullptr, nullptr,
            "|cffff8000[World Boss]|r " + text);
        sWorldSessionMgr->SendGlobalMessage(&data);
    }

    // 259200 -> "3 days", 5400 -> "1 hour 30 minutes"
    std::string Duration(time_t seconds)
    {
        seconds = std::max<time_t>(seconds, 60);
        time_t days = seconds / DAY, hours = (seconds % DAY) / HOUR, minutes = (seconds % HOUR) / MINUTE;
        auto part = [](time_t n, char const* unit) {
            return std::to_string(n) + " " + unit + (n == 1 ? "" : "s");
        };
        if (days)
            return part(days, "day") + (hours ? " " + part(hours, "hour") : "");
        if (hours)
            return part(hours, "hour") + (minutes ? " " + part(minutes, "minute") : "");
        return part(minutes, "minute");
    }

    std::string ReturnsIn(WorldBoss const& boss)
    {
        CreatureData const* data = sObjectMgr->GetCreatureData(boss.spawnId);
        return data ? " It returns in " + Duration(data->spawntimesecs) + "." : "";
    }

    Creature* FindBoss(Map* map, WorldBoss const& boss)
    {
        auto bounds = map->GetCreatureBySpawnIdStore().equal_range(boss.spawnId);
        for (auto itr = bounds.first; itr != bounds.second; ++itr)
            if (itr->second->IsInWorld())
                return itr->second;
        return nullptr;
    }

    void UpdateBoss(WorldBoss const& boss, BossTrack& track)
    {
        CreatureData const* data = sObjectMgr->GetCreatureData(boss.spawnId);
        if (!data)
            return;
        Map* map = sMapMgr->CreateBaseMap(data->mapid);
        if (!map)
            return;

        time_t now = GameTime::GetGameTime().count();
        time_t respawnAt = map->GetCreatureRespawnTime(boss.spawnId);  // 0 = not dead

        // load the grid when the boss should be alive (or is about to respawn) so it spawns on time
        if (!respawnAt || respawnAt - now <= PRELOAD_SECONDS)
            if (!map->IsGridLoaded(data->posX, data->posY))
                map->LoadGrid(data->posX, data->posY);

        Creature* creature = FindBoss(map, boss);
        bool alive = creature && creature->IsAlive();
        if (alive && !creature->isActiveObject())
            creature->setActive(true);  // keeps its grid loaded while it lives

        // the warnings before it spawns, once each per respawn
        if (!alive && respawnAt > now)
        {
            if (track.warnedFor != respawnAt)
            {
                track.warnedFor = respawnAt;
                track.warningsSent = 0;
                // warnings whose time already passed (e.g. after a restart) are skipped, except the last one
                while (track.warningsSent + 1 < sWarningMinutes.size() &&
                       respawnAt - now <= time_t(sWarningMinutes[track.warningsSent + 1]) * MINUTE)
                    ++track.warningsSent;
            }
            if (track.warningsSent < sWarningMinutes.size() &&
                respawnAt - now <= time_t(sWarningMinutes[track.warningsSent]) * MINUTE)
            {
                ++track.warningsSent;
                Announce(Acore::StringFormat("{} will awaken at {} in {}!", boss.name, boss.location,
                    Duration(respawnAt - now + MINUTE - 1)));
            }
        }

        // spawned (not announced for a boss already alive when the server starts)
        if (alive && !track.alive)
        {
            if (track.initialized)
                Announce(Acore::StringFormat("{} has awakened at {}!", boss.name, boss.location));
            if (!sWorldState->getWorldState(boss.spawnId))
                sWorldState->setWorldState(boss.spawnId, uint64(now));
        }
        if (!alive && track.alive)
            sWorldState->setWorldState(boss.spawnId, 0);
        track.alive = alive;
        track.initialized = true;

        // nobody killed it in time: despawn (never mid-fight); its normal respawn timer starts again
        if (alive && sDespawnHours && !creature->IsInCombat())
        {
            time_t since = time_t(sWorldState->getWorldState(boss.spawnId));
            if (since && now - since >= time_t(sDespawnHours) * HOUR)
            {
                Announce(Acore::StringFormat("Nobody challenged {}. It vanishes from {}.{}", boss.name, boss.location,
                    ReturnsIn(boss)));
                sWorldState->setWorldState(boss.spawnId, 0);
                creature->DespawnOrUnsummon();
                track.alive = false;
            }
        }
    }

    WorldBoss const* BossOf(Creature const* creature)
    {
        for (WorldBoss const& boss : WORLD_BOSSES)
            if (creature->GetSpawnId() == boss.spawnId)
                return &boss;
        return nullptr;
    }
}

class unbound_world_bosses_world : public WorldScript
{
public:
    unbound_world_bosses_world() : WorldScript("unbound_world_bosses_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD,
        WORLDHOOK_ON_UPDATE
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sAnnounce = sConfigMgr->GetOption<bool>("Unbound.WorldBoss.Announce", true);
        sDespawnHours = sConfigMgr->GetOption<uint32>("Unbound.WorldBoss.DespawnHours", 24);
        sWarningMinutes.clear();
        std::string const warnings = sConfigMgr->GetOption<std::string>("Unbound.WorldBoss.Warnings", "10, 5");
        for (std::string_view part : Acore::Tokenize(warnings, ',', false))
        {
            while (!part.empty() && part.front() == ' ')
                part.remove_prefix(1);
            if (Optional<uint32> minutes = Acore::StringTo<uint32>(part))
                if (*minutes)
                    sWarningMinutes.push_back(*minutes);
        }
        std::sort(sWarningMinutes.begin(), sWarningMinutes.end(), std::greater<uint32>());
    }

    void OnUpdate(uint32 diff) override
    {
        sTimer += diff;
        if (sTimer < TICK_MS)
            return;
        sTimer = 0;
        for (size_t i = 0; i < WORLD_BOSSES.size(); ++i)
            UpdateBoss(WORLD_BOSSES[i], sTracks[i]);
    }
};

class unbound_world_bosses_unit : public UnitScript
{
public:
    unbound_world_bosses_unit() : UnitScript("unbound_world_bosses_unit", true, {
        UNITHOOK_ON_UNIT_DEATH
    }) { }

    // "slain by <player>" (or "<player> and their group")
    void OnUnitDeath(Unit* unit, Unit* killer) override
    {
        Creature* creature = unit ? unit->ToCreature() : nullptr;
        WorldBoss const* boss = creature ? BossOf(creature) : nullptr;
        if (!boss)
            return;
        Player* player = killer ? killer->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
        if (!player)
            player = creature->GetLootRecipient();
        std::string by = player ? Acore::StringFormat(" by {}{}", player->GetName(),
                                      player->GetGroup() ? " and their group" : "") : "";
        Announce(Acore::StringFormat("{} has been slain{} at {}!{}", boss->name, by, boss->location,
            ReturnsIn(*boss)));
    }
};

void AddSC_unbound_world_bosses()
{
    new unbound_world_bosses_world();
    new unbound_world_bosses_unit();
}
