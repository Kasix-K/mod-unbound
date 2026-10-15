/*
 * mod-unbound: Raid Finder, a "Raids" tab in the Dungeon Finder (addon/UnboundRaidFinder).
 *
 * The tab lists every raid, with its level and whether the player can enter it: available, level too
 * low (or, for classic Naxxramas, too high), attunement needed (classic Naxxramas), or not released
 * (Unbound.ExpansionUnlocked). There is no queue: the player picks a raid and enters.
 *  - Solo: the player is teleported to the raid's entrance.
 *  - In a group: only the leader can pick. The leader goes in first; once there, every other member
 *    gets the game's summon prompt from the leader (two minutes; the addon titles it "Enter Raid"), and
 *    accepting teleports them next to the leader, in the same raid. Members who can't enter (level,
 *    attunement) are told why. Playerbot accounts (Unbound.Naxx40.BotAccountRegex) come along without
 *    a prompt.
 *  - "Leave Raid" takes a player who entered this way back to where they were when they joined (for
 *    members who were in another instance: their hearthstone location). The spot is kept in
 *    characters.character_unbound_raid_finder, so it survives a relog.
 * The raid's difficulty is set first (classic Naxxramas is its 40-player difficulty, src/naxx40), and the
 * game's own entry checks (level, expansion lock, ...) still apply when teleporting.
 *
 * Addon messages (prefix UBRAID, the addon whispers its own character like the perk window):
 *   addon -> server: LIST, ENTER:<id>, LEAVE
 *   server -> addon: R:<id>:<status>:<min level>:<max level>:<players>:<expansion>:<name> per raid (status
 *                    A available, L level, Q attunement, E not released), then END:<id of the raid the
 *                    player entered through the finder and is in, or 0>:<1 if they may pick a raid>;
 *                    INVITE:<raid name> just before a summon prompt; MSG:<text>; ERR:<text>
 */

#include "Chat.h"
#include "Config.h"
#include "DatabaseEnv.h"
#include "DBCStores.h"
#include "GameTime.h"
#include "Group.h"
#include "Map.h"
#include "ObjectAccessor.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "WorldPacket.h"
#include "WorldSession.h"

#include "naxx40/unbound_naxx40_config.h"

#include <array>
#include <string>
#include <unordered_map>

namespace
{
    constexpr char const* PREFIX = "UBRAID";
    constexpr uint32 MAP_NAXXRAMAS_ID = 533;
    constexpr uint32 LEADER_ARRIVAL_TIMEOUT = 120;     // seconds the leader's teleport may take

    struct RaidDef
    {
        uint8 id;
        char const* name;
        uint32 mapId;
        Difficulty difficulty;
        uint8 expansion;            // 0 classic, 1 The Burning Crusade, 2 Wrath of the Lich King
        uint32 areaTrigger;         // the raid's entrance (areatrigger_teleport), or 0 for the position below
        float x, y, z, o;
    };

    // In the order they came out. Entrances are the areatrigger_teleport rows players walk through.
    constexpr std::array<RaidDef, 24> RAIDS =
    {{
        { 1,  "Molten Core",                409, RAID_DIFFICULTY_10MAN_NORMAL, 0, 2886, 0, 0, 0, 0 },
        { 2,  "Onyxia's Lair",              249, RAID_DIFFICULTY_10MAN_NORMAL, 0, 2848, 0, 0, 0, 0 },
        { 3,  "Blackwing Lair",             469, RAID_DIFFICULTY_10MAN_NORMAL, 0, 3726, 0, 0, 0, 0 },
        { 4,  "Zul'Gurub",                  309, RAID_DIFFICULTY_10MAN_NORMAL, 0, 3928, 0, 0, 0, 0 },
        { 5,  "Ruins of Ahn'Qiraj",         509, RAID_DIFFICULTY_10MAN_NORMAL, 0, 4008, 0, 0, 0, 0 },
        { 6,  "Temple of Ahn'Qiraj",        531, RAID_DIFFICULTY_10MAN_NORMAL, 0, 4010, 0, 0, 0, 0 },
        // classic Naxxramas: the 40-player difficulty, where the runestone takes players (src/naxx40)
        { 7,  "Naxxramas",                  533, RAID_DIFFICULTY_10MAN_HEROIC, 0, 0, 3005.51f, -3434.64f, 304.195f, 6.2831f },
        { 8,  "Karazhan",                   532, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4131, 0, 0, 0, 0 },
        { 9,  "Gruul's Lair",               565, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4535, 0, 0, 0, 0 },
        { 10, "Magtheridon's Lair",         544, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4153, 0, 0, 0, 0 },
        { 11, "Serpentshrine Cavern",       548, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4416, 0, 0, 0, 0 },
        { 12, "Tempest Keep",               550, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4470, 0, 0, 0, 0 },
        { 13, "Hyjal Summit",               534, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4319, 0, 0, 0, 0 },
        { 14, "Zul'Aman",                   568, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4738, 0, 0, 0, 0 },
        { 15, "Black Temple",               564, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4598, 0, 0, 0, 0 },
        { 16, "Sunwell Plateau",            580, RAID_DIFFICULTY_10MAN_NORMAL, 1, 4889, 0, 0, 0, 0 },
        { 17, "Naxxramas (Northrend)",      533, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5191, 0, 0, 0, 0 },
        { 18, "The Obsidian Sanctum",       615, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5243, 0, 0, 0, 0 },
        { 19, "The Eye of Eternity",        616, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5290, 0, 0, 0, 0 },
        { 20, "Vault of Archavon",          624, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5258, 0, 0, 0, 0 },
        { 21, "Ulduar",                     603, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5379, 0, 0, 0, 0 },
        { 22, "Trial of the Crusader",      649, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5503, 0, 0, 0, 0 },
        { 23, "Icecrown Citadel",           631, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5670, 0, 0, 0, 0 },
        { 24, "The Ruby Sanctum",           724, RAID_DIFFICULTY_10MAN_NORMAL, 2, 5869, 0, 0, 0, 0 },
    }};

    bool sEnabled = true;
    uint32 sExpansionUnlocked = 0;

    struct PendingMember
    {
        uint8 raidId;
        WorldLocation returnTo;
        time_t expires;
    };
    std::unordered_map<ObjectGuid, std::pair<uint8, time_t>> sPendingLeaders;  // leader -> raid, give up after
    std::unordered_map<ObjectGuid, PendingMember> sPendingMembers;              // member -> summon offer

    RaidDef const* FindRaid(uint8 id)
    {
        for (RaidDef const& raid : RAIDS)
            if (raid.id == id)
                return &raid;
        return nullptr;
    }

    RaidDef const* FindRaid(uint32 mapId, Difficulty difficulty)
    {
        for (RaidDef const& raid : RAIDS)
            if (raid.mapId == mapId && raid.difficulty == difficulty)
                return &raid;
        return nullptr;
    }

    bool GetEntrance(RaidDef const& raid, WorldLocation& out)
    {
        if (!raid.areaTrigger)
        {
            out.WorldRelocate(raid.mapId, raid.x, raid.y, raid.z, raid.o);
            return true;
        }
        AreaTriggerTeleport const* at = sObjectMgr->GetAreaTriggerTeleport(raid.areaTrigger);
        if (!at || at->target_mapId != raid.mapId)
            return false;
        out.WorldRelocate(at->target_mapId, at->target_X, at->target_Y, at->target_Z, at->target_Orientation);
        return true;
    }

    void LevelRange(RaidDef const& raid, uint8& minLevel, uint8& maxLevel)
    {
        minLevel = 0;
        maxLevel = 0;
        if (DungeonProgressionRequirements const* ar = sObjectMgr->GetAccessRequirement(raid.mapId, raid.difficulty))
        {
            minLevel = ar->levelMin;
            maxLevel = ar->levelMax;
        }
    }

    uint32 MaxPlayers(RaidDef const& raid)
    {
        MapDifficulty const* diff = GetMapDifficultyData(raid.mapId, raid.difficulty);
        return diff ? diff->maxPlayers : 0;
    }

    // A available, E not released, L level, Q attunement
    char Status(Player* player, RaidDef const& raid)
    {
        if (raid.expansion > sExpansionUnlocked)
            return 'E';
        uint8 minLevel, maxLevel;
        LevelRange(raid, minLevel, maxLevel);
        if (player->GetLevel() < minLevel || (maxLevel && player->GetLevel() > maxLevel))
            return 'L';
        if (raid.mapId == MAP_NAXXRAMAS_ID && raid.difficulty == RAID_DIFFICULTY_10MAN_HEROIC &&
            !UnboundNaxx40Config::IsAttuned(player))
            return 'Q';
        return 'A';
    }

    std::string StatusText(char status, RaidDef const& raid)
    {
        uint8 minLevel, maxLevel;
        LevelRange(raid, minLevel, maxLevel);
        switch (status)
        {
            case 'E': return std::string(raid.name) + " has not been released yet.";
            case 'L':
                if (maxLevel)
                    return std::string(raid.name) + " is for levels " + std::to_string(minLevel) + "-" + std::to_string(maxLevel) + ".";
                return std::string(raid.name) + " needs level " + std::to_string(minLevel) + ".";
            case 'Q': return std::string(raid.name) + " needs the attunement \"The Dread Citadel - Naxxramas\" (Archmage Angela Dosantos, Light's Hope Chapel).";
            default:  return "";
        }
    }

    void SendAddon(Player* player, std::string const& text)
    {
        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player, std::string(PREFIX) + "\t" + text);
        player->SendDirectMessage(&data);
    }

    void Tell(Player* player, std::string const& text, bool error)
    {
        ChatHandler(player->GetSession()).SendSysMessage(("|cffff8000Raid Finder:|r " + text).c_str());
        SendAddon(player, (error ? "ERR:" : "MSG:") + text);
    }

    // ------------------------------------------------------------------ return spot (characters DB)
    void SaveReturn(Player* player, uint32 raidMap, WorldLocation const& spot)
    {
        CharacterDatabase.Execute("REPLACE INTO `character_unbound_raid_finder` (`guid`, `raid_map`, `map`, `x`, `y`, `z`, `o`) "
            "VALUES ({}, {}, {}, {}, {}, {}, {})", player->GetGUID().GetCounter(), raidMap, spot.GetMapId(),
            spot.GetPositionX(), spot.GetPositionY(), spot.GetPositionZ(), spot.GetOrientation());
    }

    bool LoadReturn(Player* player, uint32& raidMap, WorldLocation& spot)
    {
        QueryResult result = CharacterDatabase.Query("SELECT `raid_map`, `map`, `x`, `y`, `z`, `o` FROM "
            "`character_unbound_raid_finder` WHERE `guid` = {}", player->GetGUID().GetCounter());
        if (!result)
            return false;
        Field* f = result->Fetch();
        raidMap = f[0].Get<uint32>();
        spot.WorldRelocate(f[1].Get<uint32>(), f[2].Get<float>(), f[3].Get<float>(), f[4].Get<float>(), f[5].Get<float>());
        return true;
    }

    void DeleteReturn(Player* player)
    {
        CharacterDatabase.Execute("DELETE FROM `character_unbound_raid_finder` WHERE `guid` = {}", player->GetGUID().GetCounter());
    }

    // Where to send a player back to: where they are, or their hearthstone if they're in an instance.
    WorldLocation ReturnSpot(Player* player)
    {
        if (player->GetMap()->Instanceable())
            return WorldLocation(player->m_homebindMapId, player->m_homebindX, player->m_homebindY, player->m_homebindZ,
                                 player->GetOrientation());
        return WorldLocation(player->GetMapId(), player->GetPositionX(), player->GetPositionY(), player->GetPositionZ(),
                             player->GetOrientation());
    }

    // The raid the player entered through the finder and is still in, or nullptr.
    RaidDef const* CurrentFinderRaid(Player* player)
    {
        uint32 raidMap;
        WorldLocation spot;
        if (!LoadReturn(player, raidMap, spot) || player->GetMapId() != raidMap)
            return nullptr;
        return FindRaid(raidMap, player->GetMap()->GetDifficulty());
    }

    bool MayPick(Player* player)
    {
        Group* group = player->GetGroup();
        return !group || group->IsLeader(player->GetGUID());
    }

    // ------------------------------------------------------------------ actions
    void SendList(Player* player)
    {
        for (RaidDef const& raid : RAIDS)
        {
            uint8 minLevel, maxLevel;
            LevelRange(raid, minLevel, maxLevel);
            SendAddon(player, "R:" + std::to_string(raid.id) + ":" + Status(player, raid) + ":" +
                std::to_string(minLevel) + ":" + std::to_string(maxLevel) + ":" + std::to_string(MaxPlayers(raid)) + ":" +
                std::to_string(raid.expansion) + ":" + raid.name);
        }
        RaidDef const* current = CurrentFinderRaid(player);
        SendAddon(player, "END:" + std::to_string(current ? current->id : 0) + ":" + (MayPick(player) ? "1" : "0"));
    }

    void Enter(Player* player, uint8 raidId)
    {
        RaidDef const* raid = FindRaid(raidId);
        if (!raid)
            return;

        Group* group = player->GetGroup();
        if (group && !group->IsLeader(player->GetGUID()))
            return Tell(player, "Only your group leader can choose a raid.", true);
        if (group && (group->isBGGroup() || group->isBFGroup() || group->isLFGGroup()))
            return Tell(player, "You can't use the Raid Finder from this group.", true);
        if (player->GetMap()->Instanceable())
            return Tell(player, "Leave your current dungeon, raid or battleground first.", true);
        if (!player->IsAlive() || player->IsInCombat() || player->IsInFlight())
            return Tell(player, "You can't enter a raid right now (dead, in combat or flying).", true);

        char const status = Status(player, *raid);
        if (status != 'A')
            return Tell(player, StatusText(status, *raid), true);

        WorldLocation entrance;
        if (!GetEntrance(*raid, entrance))
            return Tell(player, std::string("No entrance is known for ") + raid->name + ".", true);

        if (group)
            group->SetRaidDifficulty(raid->difficulty);
        else
        {
            player->SetRaidDifficulty(raid->difficulty);
            player->SendRaidDifficulty(false);
        }

        SaveReturn(player, raid->mapId, ReturnSpot(player));
        if (group)
            sPendingLeaders[player->GetGUID()] = { raid->id, GameTime::GetGameTime().count() + LEADER_ARRIVAL_TIMEOUT };

        if (!player->TeleportTo(entrance))
        {
            sPendingLeaders.erase(player->GetGUID());
            DeleteReturn(player);
            return Tell(player, std::string("You couldn't enter ") + raid->name + ".", true);
        }
    }

    // The leader has arrived: offer the raid to the rest of the group.
    void InviteGroup(Player* leader, RaidDef const& raid)
    {
        Group* group = leader->GetGroup();
        if (!group)
            return;

        uint32 invited = 0;
        for (GroupReference* itr = group->GetFirstMember(); itr; itr = itr->next())
        {
            Player* member = itr->GetSource();
            if (!member || member == leader || !member->IsInWorld() || member->GetSession()->PlayerLogout())
                continue;
            if (member->GetMap() == leader->GetMap())
                continue;   // already in this raid

            if (UnboundNaxx40Config::IsBotAccount(member))
            {
                SaveReturn(member, raid.mapId, ReturnSpot(member));
                member->TeleportTo(leader->GetMapId(), leader->GetPositionX(), leader->GetPositionY(),
                                   leader->GetPositionZ(), leader->GetOrientation());
                continue;
            }

            char const status = Status(member, raid);
            if (status != 'A')
            {
                Tell(member, "You can't join your group: " + StatusText(status, raid), true);
                Tell(leader, member->GetName() + " can't join: " + StatusText(status, raid), true);
                continue;
            }

            sPendingMembers[member->GetGUID()] = { raid.id, ReturnSpot(member),
                GameTime::GetGameTime().count() + MAX_PLAYER_SUMMON_DELAY };
            SendAddon(member, std::string("INVITE:") + raid.name);

            // the game's summon prompt, from the leader inside the raid; accepting teleports next to them
            member->SetSummonPoint(leader->GetMapId(), leader->GetPositionX(), leader->GetPositionY(), leader->GetPositionZ());
            WorldPacket data(SMSG_SUMMON_REQUEST, 8 + 4 + 4);
            data << leader->GetGUID();
            data << uint32(leader->GetZoneId());
            data << uint32(MAX_PLAYER_SUMMON_DELAY * IN_MILLISECONDS);
            member->SendDirectMessage(&data);
            ++invited;
        }

        if (invited)
            Tell(leader, std::to_string(invited) + (invited == 1 ? " group member was" : " group members were") +
                " asked to join you.", false);
    }

    void Leave(Player* player)
    {
        uint32 raidMap;
        WorldLocation spot;
        if (!LoadReturn(player, raidMap, spot))
            return Tell(player, "You didn't enter a raid through the Raid Finder.", true);
        if (player->GetMapId() != raidMap)
        {
            DeleteReturn(player);
            return Tell(player, "You're no longer in the raid you entered through the Raid Finder.", true);
        }
        if (player->IsInCombat())
            return Tell(player, "You can't leave while in combat.", true);

        if (player->TeleportTo(spot))
            DeleteReturn(player);
        else
            Tell(player, "You couldn't be sent back.", true);
    }

    void HandleAddonMessage(Player* player, std::string const& text)
    {
        if (!sEnabled)
            return Tell(player, "The Raid Finder is turned off on this server.", true);

        if (text == "LIST")
            return SendList(player);
        if (text == "LEAVE")
            return Leave(player);
        if (text.rfind("ENTER:", 0) == 0)
        {
            uint32 id = 0;
            try { id = std::stoul(text.substr(6)); } catch (...) { return; }
            if (id && id < 256)
                Enter(player, uint8(id));
        }
    }
}

class unbound_raid_finder_player : public PlayerScript
{
public:
    unbound_raid_finder_player() : PlayerScript("unbound_raid_finder_player", {
        PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT,
        PLAYERHOOK_ON_MAP_CHANGED,
        PLAYERHOOK_ON_LOGOUT
    }) { }

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

    void OnPlayerMapChanged(Player* player) override
    {
        time_t const now = GameTime::GetGameTime().count();

        auto leader = sPendingLeaders.find(player->GetGUID());
        if (leader != sPendingLeaders.end())
        {
            RaidDef const* raid = FindRaid(leader->second.first);
            bool const expired = leader->second.second < now;
            sPendingLeaders.erase(leader);
            if (raid && !expired && player->GetMapId() == raid->mapId)
                InviteGroup(player, *raid);
        }

        auto member = sPendingMembers.find(player->GetGUID());
        if (member != sPendingMembers.end())
        {
            RaidDef const* raid = FindRaid(member->second.raidId);
            if (raid && player->GetMapId() == raid->mapId)
            {
                SaveReturn(player, raid->mapId, member->second.returnTo);
                sPendingMembers.erase(member);
            }
            else if (member->second.expires < now)
                sPendingMembers.erase(member);
        }
    }

    void OnPlayerLogout(Player* player) override
    {
        sPendingLeaders.erase(player->GetGUID());
        sPendingMembers.erase(player->GetGUID());
    }
};

class unbound_raid_finder_world : public WorldScript
{
public:
    unbound_raid_finder_world() : WorldScript("unbound_raid_finder_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sEnabled = sConfigMgr->GetOption<bool>("Unbound.RaidFinder.Enable", true);
        sExpansionUnlocked = sConfigMgr->GetOption<uint32>("Unbound.ExpansionUnlocked", 0);
    }
};

void AddSC_unbound_raid_finder()
{
    new unbound_raid_finder_player();
    new unbound_raid_finder_world();
}
