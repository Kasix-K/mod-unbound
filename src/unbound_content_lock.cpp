/*
 * mod-unbound: expansion content lock.
 *
 * Unbound.ExpansionUnlocked (0 = classic, 1 = + The Burning Crusade, 2 = + Wrath of the Lich King)
 * says which expansions' content is released. Locked content:
 *  - dungeons and raids of a locked expansion can't be entered (or queued for in the dungeon finder);
 *  - Northrend, and the Outland zones of map 530, send players home: their hearthstone location, or
 *    their race's starting area if that is locked too, or else their faction's capital. The Blood Elf
 *    and Draenei starting zones share map 530 with Outland and stay open, so those races remain
 *    playable; Ebon Hold stays open for Death Knights (only GM accounts can create them while Wrath is
 *    locked, see CharacterCreating.Disabled.ClassMask).
 * Battlegrounds and arenas are left alone. GMs (with GM mode on) are exempt.
 * The level cap and Death Knight creation are worldserver.conf settings (MaxPlayerLevel,
 * CharacterCreating.Disabled.ClassMask) and are changed alongside this when an expansion is released.
 */

#include "Chat.h"
#include "Config.h"
#include "DBCStores.h"
#include "MapMgr.h"
#include "Player.h"
#include "ScriptMgr.h"

#include <set>
#include <unordered_set>

static uint32 sExpansionUnlocked = 0;

// Zones of map 530 that are not Outland: the Blood Elf and Draenei starting areas and the seas around them.
static std::unordered_set<uint32> const sClassicZonesOnOutlandMap =
{
    3430, // Eversong Woods
    3433, // Ghostlands
    3487, // Silvermoon City
    3524, // Azuremyst Isle
    3525, // Bloodmyst Isle
    3557, // The Exodar
    3455, // The North Sea
    3479, // The Veiled Sea
};

static char const* ExpansionName(uint32 expansion)
{
    return expansion >= 2 ? "Wrath of the Lich King" : "The Burning Crusade";
}

// Expansion a location belongs to for this player, or 0 if it is classic content (or a battleground/arena).
static uint32 LocationExpansion(Player const* player, uint32 mapId, uint32 zoneId)
{
    MapEntry const* entry = sMapStore.LookupEntry(mapId);
    if (!entry || entry->IsBattlegroundOrArena())
        return 0;

    if (mapId == MAP_OUTLAND)
        return sClassicZonesOnOutlandMap.count(zoneId) ? 0 : 1;

    // The Death Knight starting area, like the Blood Elf and Draenei ones on map 530.
    if (mapId == MAP_EBON_HOLD && player->IsClass(CLASS_DEATH_KNIGHT))
        return 0;

    return entry->Expansion();
}

static bool IsLocked(Player const* player, WorldLocation const& location)
{
    return LocationExpansion(player, location.GetMapId(), sMapMgr->GetZoneId(PHASEMASK_NORMAL, location))
        > sExpansionUnlocked;
}

static void SendHomeFromLockedContent(Player* player, uint32 expansion)
{
    // Hearthstone, else the race's starting area, else the faction capital.
    WorldLocation destination(player->m_homebindMapId, player->m_homebindX, player->m_homebindY, player->m_homebindZ,
        player->GetOrientation());
    if (IsLocked(player, destination))
        destination = player->GetStartPosition();
    if (IsLocked(player, destination))
    {
        if (player->GetTeamId() == TEAM_ALLIANCE)
            destination = WorldLocation(0, -8833.38f, 628.62f, 94.01f, 1.07f);  // Stormwind
        else
            destination = WorldLocation(1, 1629.36f, -4373.39f, 31.26f, 3.55f); // Orgrimmar
    }

    ChatHandler(player->GetSession()).PSendSysMessage("{} has not been released yet.", ExpansionName(expansion));
    player->TeleportTo(destination);
}

class unbound_content_lock_world : public WorldScript
{
public:
    unbound_content_lock_world() : WorldScript("unbound_content_lock_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sExpansionUnlocked = sConfigMgr->GetOption<uint32>("Unbound.ExpansionUnlocked", 0);
    }
};

class unbound_content_lock_player : public PlayerScript
{
public:
    unbound_content_lock_player() : PlayerScript("unbound_content_lock_player", {
        PLAYERHOOK_ON_UPDATE_ZONE,
        PLAYERHOOK_CAN_ENTER_MAP,
        PLAYERHOOK_CAN_JOIN_LFG
    }) { }

    // Covers continents (Northrend, the Outland zones of map 530), which the map entry check skips.
    void OnPlayerUpdateZone(Player* player, uint32 newZone, uint32 /*newArea*/) override
    {
        if (player->IsGameMaster())
            return;

        uint32 expansion = LocationExpansion(player, player->GetMapId(), newZone);
        if (expansion <= sExpansionUnlocked)
            return;

        // Teleport outside the zone update itself.
        player->m_Events.AddEventAtOffset([player, expansion]()
        {
            SendHomeFromLockedContent(player, expansion);
        }, 1s);
    }

    // Dungeons and raids (the core only asks scripts about instanced maps; GMs never get here).
    bool OnPlayerCanEnterMap(Player* player, MapEntry const* entry, InstanceTemplate const* /*instance*/,
        MapDifficulty const* /*mapDiff*/, bool /*loginCheck*/) override
    {
        if (entry->IsBattlegroundOrArena() || entry->Expansion() <= sExpansionUnlocked)
            return true;

        ChatHandler(player->GetSession()).PSendSysMessage("{} has not been released yet.",
            ExpansionName(entry->Expansion()));
        return false;
    }

    bool OnPlayerCanJoinLfg(Player* player, uint8 /*roles*/, std::set<uint32>& dungeons,
        std::string const& /*comment*/) override
    {
        for (uint32 dungeonId : dungeons)
        {
            LFGDungeonEntry const* dungeon = sLFGDungeonStore.LookupEntry(dungeonId);
            if (dungeon && dungeon->ExpansionLevel > sExpansionUnlocked)
            {
                ChatHandler(player->GetSession()).PSendSysMessage("{} has not been released yet.",
                    ExpansionName(dungeon->ExpansionLevel));
                return false;
            }
        }
        return true;
    }
};

void AddSC_unbound_content_lock()
{
    new unbound_content_lock_world();
    new unbound_content_lock_player();
}
