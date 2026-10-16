/*
 * mod-unbound: account-wide currencies (ROADMAP.md "Heroic currency and vendor").
 *
 * Each currency in SHARED_CURRENCIES (the Heroic Sigil so far; the Mythic currency later) has one amount per account,
 * kept in characters.account_unbound_currency. While a character plays, the currency is an ordinary item (earned
 * from loot, spent at vendors); this keeps every character of the account on the same amount:
 *   - Login: the character's stack is set to the account's amount (after its inventory loaded). The first time a
 *     character logs in after a currency became shared, whatever it already had is added to the account first
 *     (character_unbound_currency_merged), so nothing is lost.
 *   - Save (every save, including the one at logout): the character's amount is written back to the account.
 *     OnPlayerSave has no transaction parameter, so this is saved at the same moment as the character, not in the
 *     same transaction.
 * Safe because only one character per account is played at a time, with three rules for the exceptions:
 *   - Only the character a player logged in touches the balance. Account alt-bots are on
 *     (Playerbots.AllowAccountBots = 1), so an alt can be online as a bot next to the player's character: a bot
 *     session has no socket (WorldSession::IsHeadless(), the same check mod-playerbots uses), and headless
 *     characters keep their own amount. Random bots are headless too.
 *   - `holder` is the character that loaded the balance last; a save from any other character is ignored.
 *   - GM accounts keep their own amounts unless Unbound.AccountCurrency.GMAccounts = 1 (for testing with .additem).
 * The currency is soulbound (can't be traded or mailed, so it can't be counted twice). The latest amounts are also
 * kept in memory (sBalances), so a login right after a logout uses the amount just saved even if the database write
 * hasn't run yet.
 *
 * Settings (mod_unbound.conf): Unbound.AccountCurrency.Enable, Unbound.AccountCurrency.GMAccounts.
 */

#include "Config.h"
#include "DatabaseEnv.h"
#include "Item.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "WorldSession.h"

#include <map>
#include <utility>
#include <vector>

namespace
{
    // Currencies shared per account (item entries).
    std::vector<uint32> const SHARED_CURRENCIES = {
        912000,  // Heroic Sigil
    };

    bool sEnabled = true;
    bool sGMAccounts = false;

    struct Balance
    {
        uint32 amount = 0;
        ObjectGuid::LowType holder = 0;  // the character that loaded it last
    };
    std::map<std::pair<uint32, uint32>, Balance> sBalances;  // (account, item) -> latest balance

    // Only a character a player logged in (not a bot, not a GM account unless allowed) shares the balance.
    bool Shares(Player const* player)
    {
        WorldSession const* session = player->GetSession();
        if (!sEnabled || !session || session->IsHeadless())
            return false;
        return sGMAccounts || session->GetSecurity() <= SEC_PLAYER;
    }

    Balance LoadBalance(uint32 account, uint32 item)
    {
        auto key = std::make_pair(account, item);
        auto itr = sBalances.find(key);
        if (itr != sBalances.end())
            return itr->second;
        Balance balance;
        if (QueryResult result = CharacterDatabase.Query(
                "SELECT `amount`, `holder` FROM `account_unbound_currency` WHERE `account` = {} AND `item` = {}", account, item))
        {
            balance.amount = (*result)[0].Get<uint32>();
            balance.holder = (*result)[1].Get<uint32>();
        }
        return balance;
    }

    void StoreBalance(uint32 account, uint32 item, Balance const& balance)
    {
        sBalances[std::make_pair(account, item)] = balance;
        CharacterDatabase.Execute("REPLACE INTO `account_unbound_currency` (`account`, `item`, `amount`, `holder`) "
                                  "VALUES ({}, {}, {}, {})", account, item, balance.amount, balance.holder);
    }

    // Adds or removes items until the character has `amount`, without "You receive" messages.
    void SetItemCount(Player* player, uint32 item, uint32 amount)
    {
        uint32 have = player->GetItemCount(item);
        if (have > amount)
            player->DestroyItemCount(item, have - amount, true);
        else if (have < amount)
        {
            ItemPosCountVec dest;
            uint32 noSpace = 0;
            if (player->CanStoreNewItem(NULL_BAG, NULL_SLOT, dest, item, amount - have, &noSpace) == EQUIP_ERR_OK ||
                !dest.empty())
                player->StoreNewItem(dest, item, true);
        }
    }

    // First login since the currency became shared: add what the character already had to the account.
    bool MergeOnce(Player* player, uint32 item, Balance& balance)
    {
        ObjectGuid::LowType guid = player->GetGUID().GetCounter();
        if (CharacterDatabase.Query("SELECT 1 FROM `character_unbound_currency_merged` WHERE `guid` = {} AND `item` = {}",
                guid, item))
            return false;
        balance.amount += player->GetItemCount(item);
        CharacterDatabase.Execute("INSERT IGNORE INTO `character_unbound_currency_merged` (`guid`, `item`) VALUES ({}, {})",
            guid, item);
        return true;
    }
}

class unbound_account_currency_world : public WorldScript
{
public:
    unbound_account_currency_world() : WorldScript("unbound_account_currency_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sEnabled = sConfigMgr->GetOption<bool>("Unbound.AccountCurrency.Enable", true);
        sGMAccounts = sConfigMgr->GetOption<bool>("Unbound.AccountCurrency.GMAccounts", false);
    }
};

class unbound_account_currency_player : public PlayerScript
{
public:
    unbound_account_currency_player() : PlayerScript("unbound_account_currency_player", {
        PLAYERHOOK_ON_LOGIN,
        PLAYERHOOK_ON_SAVE
    }) { }

    // The character takes over the account's balance.
    void OnPlayerLogin(Player* player) override
    {
        if (!Shares(player))
            return;
        uint32 account = player->GetSession()->GetAccountId();
        for (uint32 item : SHARED_CURRENCIES)
        {
            Balance balance = LoadBalance(account, item);
            MergeOnce(player, item, balance);
            balance.holder = player->GetGUID().GetCounter();
            SetItemCount(player, item, balance.amount);
            StoreBalance(account, item, balance);
        }
    }

    // Every save (and the one at logout): the holder writes its amount back to the account.
    void OnPlayerSave(Player* player) override
    {
        if (!Shares(player))
            return;
        uint32 account = player->GetSession()->GetAccountId();
        ObjectGuid::LowType guid = player->GetGUID().GetCounter();
        for (uint32 item : SHARED_CURRENCIES)
        {
            Balance balance = LoadBalance(account, item);
            if (balance.holder != guid)
                continue;  // another character loaded the balance since: this one's amount is stale
            balance.amount = player->GetItemCount(item);
            StoreBalance(account, item, balance);
        }
    }
};

void AddSC_unbound_account_currency()
{
    new unbound_account_currency_world();
    new unbound_account_currency_player();
}
