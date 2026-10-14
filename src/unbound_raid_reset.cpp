/*
 * mod-unbound: "Reset all instances" resets every dungeon and raid save.
 *
 * The portrait menu's Reset all instances (CMSG_RESET_INSTANCES) normally resets only normal
 * 5-player dungeons, and only while the dungeon difficulty is set to Normal. Before the core handles
 * it, this resets all of the player's instance saves (raids of any difficulty, heroic and normal
 * dungeons) with the same rules: in a group only the leader can reset (and resets the group's
 * instances, since group binds are the leader's binds), and an instance with players still inside
 * isn't reset. The core's own pass then finds nothing left to reset.
 */

#include "InstanceSaveMgr.h"
#include "Group.h"
#include "Map.h"
#include "MapMgr.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "WorldSession.h"

#include <vector>

static void ResetAllInstances(Player* player)
{
    if (Group* group = player->GetGroup())
        if (!group->IsLeader(player->GetGUID()) || group->isBGGroup() || group->isBFGroup() || group->isLFGGroup())
            return;

    std::vector<InstanceSave*> saves;
    for (uint8 difficulty = 0; difficulty < MAX_DIFFICULTY; ++difficulty)
    {
        BoundInstancesMap const& binds = sInstanceSaveMgr->PlayerGetBoundInstances(player->GetGUID(), Difficulty(difficulty));
        for (auto const& [mapId, bind] : binds)
        {
            MapEntry const* entry = sMapStore.LookupEntry(mapId);
            if (entry && entry->IsDungeon() && bind.save)
                saves.push_back(bind.save);
        }
    }

    // Reset after collecting: unbinding changes the bind maps iterated above. InstanceSave::CanReset()
    // is deliberately not checked: it is false exactly for saves with a permanent (boss kill) bind,
    // which are the lockouts this is meant to clear.
    for (InstanceSave* save : saves)
    {
        uint32 mapId = save->GetMapId();
        Map* map = sMapMgr->FindMap(mapId, save->GetInstanceId());
        if (map && !map->ToInstanceMap()->Reset(INSTANCE_RESET_ALL))
        {
            player->SendResetInstanceFailed(INSTANCE_RESET_FAILED, mapId); // players still inside
            continue;
        }

        player->SendResetInstanceSuccess(mapId);
        sInstanceSaveMgr->DeleteInstanceSavedData(save->GetInstanceId());
        sInstanceSaveMgr->UnbindAllFor(save);
    }
}

class unbound_raid_reset_server : public ServerScript
{
public:
    unbound_raid_reset_server() : ServerScript("unbound_raid_reset_server", {
        SERVERHOOK_CAN_PACKET_RECEIVE
    }) { }

    // CMSG_RESET_INSTANCES is handled on the world thread (PROCESS_THREADUNSAFE), so instance
    // saves can be changed here. Return true so the core handler still runs as usual.
    bool CanPacketReceive(WorldSession* session, WorldPacket const& packet) override
    {
        if (packet.GetOpcode() == CMSG_RESET_INSTANCES)
            if (Player* player = session->GetPlayer())
                if (player->IsInWorld() && !player->GetMap()->Instanceable())
                    ResetAllInstances(player);

        return true;
    }
};

void AddSC_unbound_raid_reset()
{
    new unbound_raid_reset_server();
}
