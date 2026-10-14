/*
 * mod-unbound: loot companions (Loot Goblin, Arcane Loot Scanner).
 *
 * While a character's loot companion is summoned:
 *  - mod-aoe-loot is on for them, so opening one corpse also loots the corpses around it;
 *  - once a second the goblin loots every corpse within the AoE loot range (AOELoot.Range) that the
 *    character may loot, straight into their bags. It follows the normal loot rules: gold is shared
 *    with the group, items that need a group roll (or the master looter) stay on the corpse, and
 *    whatever doesn't fit in the bags stays too.
 * When the companion leaves the world (dismissed, replaced by another companion, zoning, logout) both
 * stop. The companion's spell, item and vendor are defined in tools/custom_dbc.py and
 * data/sql/db-world/unbound_loot_goblin.sql.
 */

#include "Chat.h"
#include "Creature.h"
#include "Group.h"
#include "LootMgr.h"
#include "ObjectAccessor.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "TemporarySummon.h"
#include "WorldPacket.h"

#include <list>
#include <unordered_map>
#include <vector>

// aoe_loot.h defines (not just declares) AddSC_AoeLoot(), so including it here as-is would define
// that function twice. Rename this file's copy; only the AoE loot switch and config are used from it.
#define AddSC_AoeLoot AddSC_AoeLoot_unbound_unused
#include "aoe_loot.h"
#undef AddSC_AoeLoot

enum UnboundLootCompanions
{
    // keep in sync with data/sql/db-world/unbound_loot_goblin.sql
    NPC_LOOT_GOBLIN         = 190100,
    NPC_ARCANE_LOOT_SCANNER = 190102,
};

static bool IsLootCompanion(uint32 entry)
{
    return entry == NPC_LOOT_GOBLIN || entry == NPC_ARCANE_LOOT_SCANNER;
}

static constexpr uint32 AUTO_LOOT_INTERVAL_MS = 1000;
static constexpr uint32 BAGS_FULL_WARNING_MS = 30000;

struct LootGoblinState
{
    uint32 lootTimer = 0;
    uint32 bagsFullCooldown = 0;
};

// player GUID -> auto-loot timers, only for characters that have had a goblin out
static std::unordered_map<ObjectGuid, LootGoblinState> sLootGoblinStates;

static void SetAoeLoot(ObjectGuid playerGuid, bool enabled)
{
    if (playerGuid.IsPlayer())
        AoeLootCommandScript::setPlayerAoeLootEnabled(playerGuid.GetRawValue(), enabled);
}

static ObjectGuid GetLootGoblinOwner(Creature* creature)
{
    if (!IsLootCompanion(creature->GetEntry()))
        return ObjectGuid::Empty;

    TempSummon* summon = creature->ToTempSummon();
    return summon ? summon->GetSummonerGUID() : ObjectGuid::Empty;
}

static bool HasLootCompanionOut(Player* player)
{
    ObjectGuid critterGuid = player->GetCritterGUID();
    if (!critterGuid)
        return false;

    Creature* critter = ObjectAccessor::GetCreature(*player, critterGuid);
    return critter && IsLootCompanion(critter->GetEntry());
}

// Same split as WorldSession::HandleLootMoneyOpcode: shared with group members in reward range.
static void LootMoney(Player* player, Loot* loot)
{
    sScriptMgr->OnPlayerBeforeLootMoney(player, loot);
    loot->NotifyMoneyRemoved();

    std::vector<Player*> receivers;
    Group* group = player->GetGroup();
    if (group)
    {
        for (GroupReference* itr = group->GetFirstMember(); itr != nullptr; itr = itr->next())
            if (Player* member = itr->GetSource())
                if (player->IsAtLootRewardDistance(member))
                    receivers.push_back(member);
    }

    if (receivers.empty())
        receivers.push_back(player);

    uint32 share = loot->gold / receivers.size();
    for (Player* receiver : receivers)
    {
        uint32 amount = share;
        if (receiver->HasPlayerFlag(PLAYER_FLAGS_NO_PLAY_TIME))
            continue;

        if (receiver->HasPlayerFlag(PLAYER_FLAGS_PARTIAL_PLAY_TIME))
            amount /= 2;

        if (!amount)
            continue;

        receiver->ModifyMoney(amount);
        receiver->UpdateAchievementCriteria(ACHIEVEMENT_CRITERIA_TYPE_LOOT_MONEY, amount);

        WorldPacket data(SMSG_LOOT_MONEY_NOTIFY, 4 + 1);
        data << uint32(amount);
        data << uint8(receivers.size() > 1 ? 0 : 1); // 0 = "Your share is...", 1 = "You loot..."
        receiver->SendDirectMessage(&data);
    }

    if (!group)
        sScriptMgr->OnPlayerAfterCreatureLootMoney(player);

    sScriptMgr->OnLootMoney(player, loot->gold);
    loot->gold = 0;
}

// Loot one corpse into the player's bags. Returns false if something didn't fit.
static bool AutoLootCorpse(Player* player, Creature* corpse)
{
    Loot* loot = &corpse->loot;
    if (loot->loot_type == LOOT_SKINNING || loot->loot_type == LOOT_PICKPOCKETING)
        return true;

    // A corpse nobody has opened yet still has LOOT_NONE (Player::SendLoot sets the type); the loot
    // achievements read it, so set it the way opening the corpse would.
    if (loot->loot_type == LOOT_NONE)
        loot->loot_type = LOOT_CORPSE;

    // Shared (non-personal) loot: solo, free for all, or this player's turn in the group. Items at or
    // above the group's threshold go to a roll or the master looter, so they stay on the corpse.
    Group* group = player->GetGroup();
    LootMethod method = group ? group->GetLootMethod() : FREE_FOR_ALL;
    bool myTurn = !loot->roundRobinPlayer || loot->roundRobinPlayer == player->GetGUID();
    bool canTakeShared = !group || method == FREE_FOR_ALL || (method != MASTER_LOOT && myTurn);
    bool thresholdRolls = method == GROUP_LOOT || method == NEED_BEFORE_GREED || method == MASTER_LOOT;

    uint32 goldBefore = loot->gold;
    uint32 unlootedBefore = loot->unlootedCount;

    if (loot->gold && canTakeShared)
        LootMoney(player, loot);

    uint32 slotCount = loot->items.size();
    auto questItems = loot->GetPlayerQuestItems().find(player->GetGUID());
    if (questItems != loot->GetPlayerQuestItems().end())
        slotCount += questItems->second->size();

    bool allFit = true;
    player->SetLootGUID(corpse->GetGUID()); // StoreLootItem and its hooks read the loot source from here
    for (uint32 slot = 0; slot < slotCount; ++slot)
    {
        QuestItem* questItem = nullptr;
        QuestItem* ffaItem = nullptr;
        QuestItem* condItem = nullptr;
        LootItem* item = loot->LootItemInSlot(slot, player, &questItem, &ffaItem, &condItem);
        if (!item)
            continue;

        bool personal = questItem || ffaItem || condItem;
        if (!personal && (!canTakeShared || item->is_blocked || (thresholdRolls && !item->is_underthreshold)))
            continue; // someone else's, or needs a roll or the master looter: leave it for the loot window

        if (!item->AllowedForPlayer(player, loot->sourceWorldObjectGUID))
            continue;

        if (item->rollWinnerGUID && item->rollWinnerGUID != player->GetGUID())
            continue;

        ItemPosCountVec dest;
        if (player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, item->itemid, item->count) != EQUIP_ERR_OK)
        {
            allFit = false;
            continue;
        }

        InventoryResult msg;
        player->StoreLootItem(slot, loot, msg);
    }
    player->SetLootGUID(ObjectGuid::Empty);

    // Same cleanup as WorldSession::DoLootRelease for a creature.
    if (loot->isLooted())
    {
        corpse->AllLootRemovedFromCorpse();
        corpse->RemoveDynamicFlag(UNIT_DYNFLAG_LOOTABLE);
        loot->clear();
    }
    else if (loot->gold != goldBefore || loot->unlootedCount != unlootedBefore)
        corpse->ForceValuesUpdateAtIndex(UNIT_DYNAMIC_FLAGS); // refresh who sees it as lootable

    return allFit;
}

static void AutoLootNearby(Player* player, LootGoblinState& state)
{
    // Don't touch loot while the player has a loot window open, is dead, or is flying.
    if (player->GetLootGUID() || !player->IsAlive() || player->IsInFlight())
        return;

    std::list<Creature*> corpses;
    player->GetDeadCreatureListInGrid(corpses, AOELootConfig::instance()->range);

    bool allFit = true;
    for (Creature* corpse : corpses)
        if (player->isAllowedToLoot(corpse) && !AutoLootCorpse(player, corpse))
            allFit = false;

    if (!allFit && !state.bagsFullCooldown)
    {
        ChatHandler(player->GetSession()).SendSysMessage("Your loot companion can't fit any more loot in your bags.");
        state.bagsFullCooldown = BAGS_FULL_WARNING_MS;
    }
}

class unbound_loot_goblin_creature : public AllCreatureScript
{
public:
    unbound_loot_goblin_creature() : AllCreatureScript("unbound_loot_goblin_creature") { }

    void OnCreatureAddWorld(Creature* creature) override
    {
        SetAoeLoot(GetLootGoblinOwner(creature), true);
    }

    void OnCreatureRemoveWorld(Creature* creature) override
    {
        ObjectGuid ownerGuid = GetLootGoblinOwner(creature);
        if (!ownerGuid)
            return;

        // Swapping companions removes the old one after the new one is already out: keep AoE loot on
        // if the owner's current companion is a different loot companion.
        if (Player* owner = ObjectAccessor::FindConnectedPlayer(ownerGuid))
            if (owner->GetCritterGUID() != creature->GetGUID() && HasLootCompanionOut(owner))
                return;

        SetAoeLoot(ownerGuid, false);
    }
};

class unbound_loot_goblin_player : public PlayerScript
{
public:
    unbound_loot_goblin_player() : PlayerScript("unbound_loot_goblin_player", {
        PLAYERHOOK_ON_LOGIN,
        PLAYERHOOK_ON_LOGOUT,
        PLAYERHOOK_ON_UPDATE
    }) { }

    // Companions don't survive a logout, so every login starts with regular looting.
    void OnPlayerLogin(Player* player) override
    {
        SetAoeLoot(player->GetGUID(), false);
    }

    void OnPlayerLogout(Player* player) override
    {
        sLootGoblinStates.erase(player->GetGUID());
    }

    void OnPlayerUpdate(Player* player, uint32 diff) override
    {
        if (!player->GetCritterGUID())
            return;

        LootGoblinState& state = sLootGoblinStates[player->GetGUID()];
        state.bagsFullCooldown = state.bagsFullCooldown > diff ? state.bagsFullCooldown - diff : 0;
        state.lootTimer += diff;
        if (state.lootTimer < AUTO_LOOT_INTERVAL_MS)
            return;

        state.lootTimer = 0;
        if (HasLootCompanionOut(player))
            AutoLootNearby(player, state);
    }
};

void AddSC_unbound_loot_goblin()
{
    new unbound_loot_goblin_creature();
    new unbound_loot_goblin_player();
}
