/*
 * mod-unbound: classic Naxxramas (40 players, level 60) in Naxxramas' map 533 on its third difficulty,
 * next to the level 80 10 and 25 player versions (which the expansion lock keeps closed).
 *
 * The scripts in this folder come from mod-individual-progression (ZhengPeiRu21, Naxx 40 scripts and
 * data by Sogladev; MIT license, see LICENSE-mod-individual-progression), with only the Naxxramas parts
 * taken. Changes for Unbound:
 *  - everything is in namespace UnboundNaxx40: several classes have the same names as AzerothCore's own
 *    Naxxramas scripts (instance_naxxramas, npc_mr_bigglesworth, spell_gluth_decimate, ...), which would
 *    clash when both are linked into the worldserver. Script names (the strings the database uses) are
 *    unchanged, so the module's instance_naxxramas still replaces the core's for map 533;
 *  - naxxramas.h is naxx40_instance.h, so it can't be mistaken for the core's header;
 *  - the progression system's checks are replaced by UnboundNaxx40Config (classic attunement quest, bot
 *    accounts, the "doable" boss options); the Death Knight check and the Stratholme entrance are left out
 *    (entry only through the runestone under the Necropolis in the Eastern Plaguelands);
 *  - the logout teleport only covers Naxxramas (Onyxia's Lair is converted differently, see
 *    src/unbound_classic_onyxia.cpp).
 * The database side is data/sql/db-world/unbound_naxx40*.sql.
 */

#include "unbound_naxx40_config.h"

#include "AccountMgr.h"
#include "Config.h"
#include "Log.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "WorldSession.h"

#include <regex>
#include <string>

bool UnboundNaxx40Config::Doable4H = false;
bool UnboundNaxx40Config::DoableGluth = false;
bool UnboundNaxx40Config::DoablePatchwerk = false;
bool UnboundNaxx40Config::DoableRazuvious = false;

namespace
{
    constexpr uint32 QUEST_DREAD_CITADEL[] = { 9121, 9122, 9123 };   // by Argent Dawn reputation
    std::regex sBotAccountRegex;
    bool sBotAccountRegexValid = false;
}

bool UnboundNaxx40Config::IsAttuned(Player* player)
{
    if (!player || !player->IsInWorld())
        return false;

    for (uint32 quest : QUEST_DREAD_CITADEL)
        if (player->GetQuestStatus(quest) == QUEST_STATUS_REWARDED)
            return true;

    return false;
}

bool UnboundNaxx40Config::IsBotAccount(Player* player)
{
    if (!player || !sBotAccountRegexValid)
        return false;

    std::string accountName;
    return AccountMgr::GetName(player->GetSession()->GetAccountId(), accountName) &&
           std::regex_match(accountName, sBotAccountRegex);
}

class unbound_naxx40_world : public WorldScript
{
public:
    unbound_naxx40_world() : WorldScript("unbound_naxx40_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        UnboundNaxx40Config::Doable4H = sConfigMgr->GetOption<bool>("Unbound.Naxx40.Doable.FourHorsemen", false);
        UnboundNaxx40Config::DoableGluth = sConfigMgr->GetOption<bool>("Unbound.Naxx40.Doable.Gluth", false);
        UnboundNaxx40Config::DoablePatchwerk = sConfigMgr->GetOption<bool>("Unbound.Naxx40.Doable.Patchwerk", false);
        UnboundNaxx40Config::DoableRazuvious = sConfigMgr->GetOption<bool>("Unbound.Naxx40.Doable.Razuvious", false);

        std::string const pattern = sConfigMgr->GetOption<std::string>("Unbound.Naxx40.BotAccountRegex", "^RNDBOT.*");
        sBotAccountRegexValid = false;
        if (!pattern.empty())
        {
            try
            {
                sBotAccountRegex = std::regex(pattern, std::regex::icase);
                sBotAccountRegexValid = true;
            }
            catch (std::regex_error const&)
            {
                LOG_ERROR("server.loading", "mod-unbound: Unbound.Naxx40.BotAccountRegex '{}' is not a valid regular expression.", pattern);
            }
        }
    }
};

namespace UnboundNaxx40
{
    void AddSC_instance_naxxramas();
    void AddSC_boss_anubrekhan_40();
    void AddSC_boss_faerlina_40();
    void AddSC_boss_four_horsemen_40();
    void AddSC_boss_gluth_40();
    void AddSC_boss_gothik_40();
    void AddSC_boss_grobbulus_40();
    void AddSC_boss_heigan_40();
    void AddSC_boss_kelthuzad_40();
    void AddSC_boss_loatheb_40();
    void AddSC_boss_maexxna_40();
    void AddSC_boss_noth_40();
    void AddSC_boss_patchwerk_40();
    void AddSC_boss_razuvious_40();
    void AddSC_boss_sapphiron_40();
    void AddSC_boss_thaddius_40();
    void AddSC_npc_omarion_40();
    void AddSC_custom_spells_40();
    void AddSC_custom_creatures_40();
    void AddSC_custom_gameobjects_40();
    void AddSC_custom_scripts_40();
}

void AddSC_unbound_naxx40()
{
    new unbound_naxx40_world();

    using namespace UnboundNaxx40;
    AddSC_instance_naxxramas();
    AddSC_boss_anubrekhan_40();
    AddSC_boss_faerlina_40();
    AddSC_boss_four_horsemen_40();
    AddSC_boss_gluth_40();
    AddSC_boss_gothik_40();
    AddSC_boss_grobbulus_40();
    AddSC_boss_heigan_40();
    AddSC_boss_kelthuzad_40();
    AddSC_boss_loatheb_40();
    AddSC_boss_maexxna_40();
    AddSC_boss_noth_40();
    AddSC_boss_patchwerk_40();
    AddSC_boss_razuvious_40();
    AddSC_boss_sapphiron_40();
    AddSC_boss_thaddius_40();
    AddSC_npc_omarion_40();
    AddSC_custom_spells_40();
    AddSC_custom_creatures_40();
    AddSC_custom_gameobjects_40();
    AddSC_custom_scripts_40();
}
