#include "ScriptMgr.h"
#include "ScriptedCreature.h"
#include "SpellAuraEffects.h"
#include "SpellScript.h"
#include "Chat.h"
#include "GameObjectAI.h"
#include "Player.h"
#include "naxx40_instance.h"
#include "unbound_naxx40_config.h"

namespace UnboundNaxx40
{

class gobject_naxx40_tele : public GameObjectScript
{
public:
    gobject_naxx40_tele() : GameObjectScript("gobject_naxx40_tele") { }

    struct gobject_naxx40_teleAI: GameObjectAI
    {
        explicit gobject_naxx40_teleAI(GameObject* object) : GameObjectAI(object) { };

    };

    GameObjectAI* GetAI(GameObject* object) const override
    {
        return new gobject_naxx40_teleAI(object);
    }

    bool OnGossipHello(Player* player, GameObject* /*go*/) override
    {
        if (!player || !player->IsInWorld())
            return false;

        ChatHandler handler(player->GetSession());
        Group* group = player->GetGroup();

        if (player->GetLevel() <= 70)
        {
            bool allowed = true;

            if (!UnboundNaxx40Config::IsAttuned(player))
            {
                handler.PSendSysMessage("You are not attuned to Naxxramas.");
                allowed = false;
            }

            if (!allowed)
                return false;

            if (group)
            {
                group->SetRaidDifficulty(RAID_DIFFICULTY_10MAN_HEROIC);

                for (GroupReference* itr = group->GetFirstMember(); itr; itr = itr->next())
                {
                    Player* member = itr->GetSource();
                    if (!member)
                        continue;

                    if (UnboundNaxx40Config::IsBotAccount(member))
                    {
                        member->SetRaidDifficulty(RAID_DIFFICULTY_10MAN_HEROIC);
                        member->TeleportTo(533, 3005.51f, -3434.64f, 304.195f, 6.2831f);
                        continue;
                    }

                    if (member->GetGUID() == player->GetGUID()) // not checking the player who is using the teleporter again
                        continue;

                    bool allowed = true;

                    if (!UnboundNaxx40Config::IsAttuned(member))
                    {
                        handler.PSendSysMessage("|cff00ffff{}|r is not attuned to Naxxramas.", member->GetName());
                        allowed = false;
                    }

                    if (member->IsGameMaster())
                    {
                        handler.PSendSysMessage("|cff00ffff{}|r is a GM.", member->GetName());
                        allowed = true;
                    }

                    if (allowed)
                    {
                        handler.PSendSysMessage("|cff00ffff{}|r is allowed to enter.", member->GetName());
                        member->SetRaidDifficulty(RAID_DIFFICULTY_10MAN_HEROIC);

                        if (player->GetDistance(member) <= 30.0f && member->GetMapId() != 533) // teleport only if the player is close enough and not already in naxxramas
                            member->TeleportTo(533, 3005.51f, -3434.64f, 304.195f, 6.2831f);
                    }
                }
            }

            player->SetRaidDifficulty(RAID_DIFFICULTY_10MAN_HEROIC);
            player->TeleportTo(533, 3005.51f, -3434.64f, 304.195f, 6.2831f);
            return true;
        }
        else
        {
            handler.PSendSysMessage("You need to be level 70 or below to enter this version of Naxxramas.");
        }

        return false;
    }
};

void AddSC_custom_gameobjects_40()
{
    new gobject_naxx40_tele();
}

} // namespace UnboundNaxx40
