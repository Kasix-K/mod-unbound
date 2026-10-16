/*
 * mod-unbound: gear attunement, stage 1 (the collection and its stats).
 *
 * Players see this system as "infusion" (infuse, infused, .infuse); the code, the database table, the
 * Unbound.Attunement.* settings and the addon keep the original name, attunement.
 *
 * Each character has a collection of attuned items (characters.character_unbound_attunement). Every
 * attuned item permanently gives the character Unbound.Attunement.Percent (20%) of the item's fixed stats
 * (primary stats, ratings, attack and spell power, regeneration, armour, block, resistances; not procs, set
 * bonuses, sockets or weapon damage), whatever happens to the item afterwards. The total has diminishing
 * returns against a reference set of gear (Unbound.Attunement.ReferenceSetStats stat points): full value
 * until the bonus reaches FullValueUntil percent of that set, half value until HalfValueUntil, a quarter
 * beyond. The stats are applied the same way the server applies an equipped item's stats
 * (Player::_ApplyItemBonuses), so they show on the character sheet like gear stats.
 *
 * Which items count (ItemRules): green or better weapons and armour (rings, necks, trinkets, shields too;
 * not shirts, tabards, bags, ammo); required level within Unbound.Attunement.LevelRange of the level cap;
 * from a released expansion (world.unbound_item_expansion, made by tools/item_expansions.py, compared with
 * Unbound.ExpansionUnlocked); with fixed stats (random-stat items such as "of the Bear" have none). Each item
 * counts once.
 *
 * Stage 2, attuning: every creature that would give experience (not grey, not a critter, totem, pet or
 * no-experience creature) gives progress to each equipped item that counts and isn't attuned yet, for every
 * player who gets credit for the kill (group members in range too). A normal creature counts as 1 kill, an
 * elite as Unbound.Attunement.EliteKills (2), a boss as BossKills (10). An item needs Unbound.Attunement.Kills
 * kills by quality (50 green, 100 blue, 200 epic, 400 legendary); at that point it is attuned for good.
 * Progress is kept per item (unequipping pauses it) and saved with the character; completing an item saves
 * at once. Players see their equipped items' progress with .infuse progress (.attune also works).
 *
 * Stage 3, tribute: the Altar of Tribute (creature 190103, placed with .npc add 190103) lists the items in
 * the player's bags that count and aren't attuned yet; choosing one shows the game's confirmation box with the
 * gold price (Unbound.Attunement.TributeGold by quality: 2 green, 10 blue, 50 epic, 250 legendary; times
 * TributeOwnGearMultiplier (2) for gear the player could attune by wearing it). The server checks the item, its
 * position and the gold again, then takes the gold, destroys the item and attunes it at once, at full value.
 *
 * Stage 4 (tooltips, collection window) comes next. See ROADMAP.md (Power budget, Attunement and tribute rules).
 */

#include "Bag.h"
#include "Chat.h"
#include "CommandScript.h"
#include "Config.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "Formulas.h"
#include "KillRewarder.h"
#include "ObjectMgr.h"
#include "Player.h"
#include "ScriptMgr.h"
#include "ScriptedGossip.h"
#include "StringConvert.h"
#include "StringFormat.h"
#include "Tokenize.h"
#include "WorldPacket.h"
#include "World.h"

#include <algorithm>
#include <cmath>
#include <map>
#include <unordered_map>
#include <unordered_set>
#include <vector>

using namespace Acore::ChatCommands;

namespace
{
    // ------------------------------------------------------------------ settings
    bool sEnabled = true;
    float sPercent = 20.0f;                // % of an item's stats
    uint32 sLevelRange = 10;               // required level within this of the level cap
    float sReferenceSetStats = 600.0f;     // stat points of a full set of level-60 blue/epic gear
    float sFullValueUntil = 100.0f;        // % of the reference set: full value until here
    float sHalfValueUntil = 200.0f;        // half value until here, a quarter beyond
    uint32 sExpansionUnlocked = 0;         // Unbound.ExpansionUnlocked (the content lock's setting)
    std::vector<uint32> sKillsByQuality = { 50, 100, 200, 400 }; // kills to attune: green, blue, epic, legendary
    uint32 sEliteKills = 2;                // an elite counts as this many kills
    uint32 sBossKills = 10;                // a boss counts as this many kills
    uint32 constexpr SOUND_ATTUNED = 12891; // the achievement sound
    std::vector<uint32> sTributeGold = { 2, 10, 50, 250 }; // tribute price: green, blue, epic, legendary
    uint32 sOwnGearMultiplier = 2;         // price multiplier for gear the player could attune by wearing it

    std::unordered_map<uint32, uint8> sItemExpansion;   // world.unbound_item_expansion

    // Stat keys: ItemModType values, plus these for the item's other fixed stats.
    enum ExtraStat : uint32
    {
        STAT_KEY_ARMOR = 1000,
        STAT_KEY_BLOCK,
        STAT_KEY_RES_HOLY,
        STAT_KEY_RES_FIRE,
        STAT_KEY_RES_NATURE,
        STAT_KEY_RES_FROST,
        STAT_KEY_RES_SHADOW,
        STAT_KEY_RES_ARCANE,
    };

    using StatTotals = std::map<uint32, float>;

    char const* StatName(uint32 key)
    {
        switch (key)
        {
            case ITEM_MOD_MANA: return "mana";
            case ITEM_MOD_HEALTH: return "health";
            case ITEM_MOD_AGILITY: return "Agility";
            case ITEM_MOD_STRENGTH: return "Strength";
            case ITEM_MOD_INTELLECT: return "Intellect";
            case ITEM_MOD_SPIRIT: return "Spirit";
            case ITEM_MOD_STAMINA: return "Stamina";
            case ITEM_MOD_DEFENSE_SKILL_RATING: return "defense rating";
            case ITEM_MOD_DODGE_RATING: return "dodge rating";
            case ITEM_MOD_PARRY_RATING: return "parry rating";
            case ITEM_MOD_BLOCK_RATING: return "block rating";
            case ITEM_MOD_HIT_MELEE_RATING: return "melee hit rating";
            case ITEM_MOD_HIT_RANGED_RATING: return "ranged hit rating";
            case ITEM_MOD_HIT_SPELL_RATING: return "spell hit rating";
            case ITEM_MOD_CRIT_MELEE_RATING: return "melee crit rating";
            case ITEM_MOD_CRIT_RANGED_RATING: return "ranged crit rating";
            case ITEM_MOD_CRIT_SPELL_RATING: return "spell crit rating";
            case ITEM_MOD_HASTE_MELEE_RATING: return "melee haste rating";
            case ITEM_MOD_HASTE_RANGED_RATING: return "ranged haste rating";
            case ITEM_MOD_HASTE_SPELL_RATING: return "spell haste rating";
            case ITEM_MOD_HIT_RATING: return "hit rating";
            case ITEM_MOD_CRIT_RATING: return "crit rating";
            case ITEM_MOD_RESILIENCE_RATING: return "resilience rating";
            case ITEM_MOD_HASTE_RATING: return "haste rating";
            case ITEM_MOD_EXPERTISE_RATING: return "expertise rating";
            case ITEM_MOD_ATTACK_POWER: return "attack power";
            case ITEM_MOD_RANGED_ATTACK_POWER: return "ranged attack power";
            case ITEM_MOD_MANA_REGENERATION: return "mana per 5 sec";
            case ITEM_MOD_ARMOR_PENETRATION_RATING: return "armor penetration rating";
            case ITEM_MOD_SPELL_POWER: return "spell power";
            case ITEM_MOD_HEALTH_REGEN: return "health per 5 sec";
            case ITEM_MOD_SPELL_PENETRATION: return "spell penetration";
            case ITEM_MOD_BLOCK_VALUE: return "block value";
            case ITEM_MOD_SPELL_HEALING_DONE: return "healing";
            case ITEM_MOD_SPELL_DAMAGE_DONE: return "spell damage";
            case STAT_KEY_ARMOR: return "armor";
            case STAT_KEY_BLOCK: return "block value";
            case STAT_KEY_RES_HOLY: return "Holy resistance";
            case STAT_KEY_RES_FIRE: return "Fire resistance";
            case STAT_KEY_RES_NATURE: return "Nature resistance";
            case STAT_KEY_RES_FROST: return "Frost resistance";
            case STAT_KEY_RES_SHADOW: return "Shadow resistance";
            case STAT_KEY_RES_ARCANE: return "Arcane resistance";
            default: return "other";
        }
    }

    // ------------------------------------------------------------------ item rules
    enum class ItemCheck
    {
        Counts,
        NotGreenOrBetter,
        NotGear,
        WrongLevel,
        LockedExpansion,
        NoFixedStats,
    };

    // An item's fixed stats (100%) and its stat points (the sum of its positive stats, for the diminishing
    // returns; armour and resistances aren't stat points).
    StatTotals ItemStats(ItemTemplate const* proto, float& statPoints)
    {
        StatTotals stats;
        statPoints = 0.0f;
        if (!proto->ScalingStatDistribution) // scaling (heirloom) items have no fixed stats
        {
            for (uint8 i = 0; i < std::min<uint32>(proto->StatsCount, MAX_ITEM_PROTO_STATS); ++i)
            {
                int32 value = proto->ItemStat[i].ItemStatValue;
                if (!value)
                    continue;
                stats[proto->ItemStat[i].ItemStatType] += float(value);
                if (value > 0)
                    statPoints += float(value);
            }
        }
        if (proto->Armor)
            stats[STAT_KEY_ARMOR] += float(proto->Armor);
        if (proto->Block)
            stats[STAT_KEY_BLOCK] += float(proto->Block);
        int32 const res[] = { proto->HolyRes, proto->FireRes, proto->NatureRes, proto->FrostRes, proto->ShadowRes,
                              proto->ArcaneRes };
        for (uint32 i = 0; i < 6; ++i)
            if (res[i])
                stats[STAT_KEY_RES_HOLY + i] += float(res[i]);
        return stats;
    }

    ItemCheck CheckItem(ItemTemplate const* proto)
    {
        if (proto->Quality < ITEM_QUALITY_UNCOMMON)
            return ItemCheck::NotGreenOrBetter;
        if (proto->Class != ITEM_CLASS_WEAPON && proto->Class != ITEM_CLASS_ARMOR)
            return ItemCheck::NotGear;
        switch (proto->InventoryType)
        {
            case INVTYPE_NON_EQUIP:
            case INVTYPE_BODY:
            case INVTYPE_TABARD:
            case INVTYPE_BAG:
            case INVTYPE_AMMO:
            case INVTYPE_QUIVER:
                return ItemCheck::NotGear;
            default:
                break;
        }
        uint32 cap = sWorld->getIntConfig(CONFIG_MAX_PLAYER_LEVEL);
        if (proto->RequiredLevel > cap || proto->RequiredLevel + sLevelRange < cap)
            return ItemCheck::WrongLevel;
        // this module's own items (heroic and world boss loot, 900000-999999) are classic, like
        // tools/item_expansions.py tags them, so new ones count without running the tool again
        auto itr = sItemExpansion.find(proto->ItemId);
        bool custom = proto->ItemId >= 900000 && proto->ItemId < 1000000;
        if (itr == sItemExpansion.end() ? !custom : itr->second > sExpansionUnlocked)
            return ItemCheck::LockedExpansion;
        float statPoints;
        if (ItemStats(proto, statPoints).empty())
            return ItemCheck::NoFixedStats;
        return ItemCheck::Counts;
    }

    std::string CheckText(ItemCheck check)
    {
        uint32 cap = sWorld->getIntConfig(CONFIG_MAX_PLAYER_LEVEL);
        switch (check)
        {
            case ItemCheck::Counts: return "counts for infusion";
            case ItemCheck::NotGreenOrBetter: return "doesn't count: not green quality or better";
            case ItemCheck::NotGear: return "doesn't count: not a weapon or armor";
            case ItemCheck::WrongLevel:
                return Acore::StringFormat("doesn't count: required level must be {}-{}",
                    cap > sLevelRange ? cap - sLevelRange : 1, cap);
            case ItemCheck::LockedExpansion:
                return "doesn't count: not from a released expansion (or no known source)";
            case ItemCheck::NoFixedStats: return "doesn't count: no fixed stats (random stats like \"of the Bear\")";
        }
        return "";
    }

    // ------------------------------------------------------------------ per-character state
    struct AttunementState : public DataMap::Base
    {
        std::unordered_set<uint32> attuned;            // item entries, 100% attuned
        std::unordered_map<uint32, uint32> progress;   // item entry -> kills so far (not attuned yet)
        std::unordered_set<uint32> unsaved;            // items whose progress changed since the last save
        std::map<uint32, int32> applied;               // stat key -> amount currently applied
        float rawPercent = 0.0f;                       // collected stats as % of the reference set, before
        float effectivePercent = 0.0f;                 // and after the diminishing returns
    };

    AttunementState* StateOf(Player* player)
    {
        return player->CustomData.GetDefault<AttunementState>("unbound_attunement");
    }

    // Diminishing returns on the collected stats (both in % of the reference set).
    float Effective(float raw)
    {
        float halfSpan = 2.0f * std::max(0.0f, sHalfValueUntil - sFullValueUntil); // raw % covered at half value
        if (raw <= sFullValueUntil)
            return raw;
        if (raw <= sFullValueUntil + halfSpan)
            return sFullValueUntil + (raw - sFullValueUntil) / 2.0f;
        return sHalfValueUntil + (raw - sFullValueUntil - halfSpan) / 4.0f;
    }

    // Apply or remove one stat the same way Player::_ApplyItemBonuses does for equipped items.
    void ApplyStat(Player* player, uint32 key, int32 value, bool apply)
    {
        if (!value)
            return;
        float const v = float(value);
        auto rating = [&](CombatRating cr) { player->ApplyRatingMod(cr, value, apply); };
        auto primary = [&](UnitMods mod, Stats stat)
        {
            player->HandleStatFlatModifier(mod, BASE_VALUE, v, apply);
            player->UpdateStatBuffMod(stat);
        };
        switch (key)
        {
            case ITEM_MOD_MANA: player->HandleStatFlatModifier(UNIT_MOD_MANA, BASE_VALUE, v, apply); break;
            case ITEM_MOD_HEALTH: player->HandleStatFlatModifier(UNIT_MOD_HEALTH, BASE_VALUE, v, apply); break;
            case ITEM_MOD_AGILITY: primary(UNIT_MOD_STAT_AGILITY, STAT_AGILITY); break;
            case ITEM_MOD_STRENGTH: primary(UNIT_MOD_STAT_STRENGTH, STAT_STRENGTH); break;
            case ITEM_MOD_INTELLECT: primary(UNIT_MOD_STAT_INTELLECT, STAT_INTELLECT); break;
            case ITEM_MOD_SPIRIT: primary(UNIT_MOD_STAT_SPIRIT, STAT_SPIRIT); break;
            case ITEM_MOD_STAMINA: primary(UNIT_MOD_STAT_STAMINA, STAT_STAMINA); break;
            case ITEM_MOD_DEFENSE_SKILL_RATING: rating(CR_DEFENSE_SKILL); break;
            case ITEM_MOD_DODGE_RATING: rating(CR_DODGE); break;
            case ITEM_MOD_PARRY_RATING: rating(CR_PARRY); break;
            case ITEM_MOD_BLOCK_RATING: rating(CR_BLOCK); break;
            case ITEM_MOD_HIT_MELEE_RATING: rating(CR_HIT_MELEE); break;
            case ITEM_MOD_HIT_RANGED_RATING: rating(CR_HIT_RANGED); break;
            case ITEM_MOD_HIT_SPELL_RATING: rating(CR_HIT_SPELL); break;
            case ITEM_MOD_CRIT_MELEE_RATING: rating(CR_CRIT_MELEE); break;
            case ITEM_MOD_CRIT_RANGED_RATING: rating(CR_CRIT_RANGED); break;
            case ITEM_MOD_CRIT_SPELL_RATING: rating(CR_CRIT_SPELL); break;
            case ITEM_MOD_HIT_TAKEN_MELEE_RATING: rating(CR_HIT_TAKEN_MELEE); break;
            case ITEM_MOD_HIT_TAKEN_RANGED_RATING: rating(CR_HIT_TAKEN_RANGED); break;
            case ITEM_MOD_HIT_TAKEN_SPELL_RATING: rating(CR_HIT_TAKEN_SPELL); break;
            case ITEM_MOD_CRIT_TAKEN_MELEE_RATING: rating(CR_CRIT_TAKEN_MELEE); break;
            case ITEM_MOD_CRIT_TAKEN_RANGED_RATING: rating(CR_CRIT_TAKEN_RANGED); break;
            case ITEM_MOD_CRIT_TAKEN_SPELL_RATING: rating(CR_CRIT_TAKEN_SPELL); break;
            case ITEM_MOD_HASTE_MELEE_RATING: rating(CR_HASTE_MELEE); break;
            case ITEM_MOD_HASTE_RANGED_RATING: rating(CR_HASTE_RANGED); break;
            case ITEM_MOD_HASTE_SPELL_RATING: rating(CR_HASTE_SPELL); break;
            case ITEM_MOD_HIT_RATING:
                rating(CR_HIT_MELEE); rating(CR_HIT_RANGED); rating(CR_HIT_SPELL);
                break;
            case ITEM_MOD_CRIT_RATING:
                rating(CR_CRIT_MELEE); rating(CR_CRIT_RANGED); rating(CR_CRIT_SPELL);
                break;
            case ITEM_MOD_HIT_TAKEN_RATING:
                rating(CR_HIT_TAKEN_MELEE); rating(CR_HIT_TAKEN_RANGED); rating(CR_HIT_TAKEN_SPELL);
                break;
            case ITEM_MOD_CRIT_TAKEN_RATING:
            case ITEM_MOD_RESILIENCE_RATING:
                rating(CR_CRIT_TAKEN_MELEE); rating(CR_CRIT_TAKEN_RANGED); rating(CR_CRIT_TAKEN_SPELL);
                break;
            case ITEM_MOD_HASTE_RATING:
                rating(CR_HASTE_MELEE); rating(CR_HASTE_RANGED); rating(CR_HASTE_SPELL);
                break;
            case ITEM_MOD_EXPERTISE_RATING: rating(CR_EXPERTISE); break;
            case ITEM_MOD_ATTACK_POWER:
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER, TOTAL_VALUE, v, apply);
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, v, apply);
                break;
            case ITEM_MOD_RANGED_ATTACK_POWER:
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, v, apply);
                break;
            case ITEM_MOD_MANA_REGENERATION: player->ApplyManaRegenBonus(value, apply); break;
            case ITEM_MOD_ARMOR_PENETRATION_RATING: rating(CR_ARMOR_PENETRATION); break;
            case ITEM_MOD_SPELL_POWER: player->ApplySpellPowerBonus(value, apply); break;
            case ITEM_MOD_HEALTH_REGEN: player->ApplyHealthRegenBonus(value, apply); break;
            case ITEM_MOD_SPELL_PENETRATION: player->ApplySpellPenetrationBonus(value, apply); break;
            case ITEM_MOD_BLOCK_VALUE:
            case STAT_KEY_BLOCK: player->HandleBaseModFlatValue(SHIELD_BLOCK_VALUE, v, apply); break;
            case ITEM_MOD_SPELL_HEALING_DONE: player->ApplySpellHealingBonus(value, apply); break;
            case ITEM_MOD_SPELL_DAMAGE_DONE: player->ApplySpellDamageBonus(value, apply); break;
            case STAT_KEY_ARMOR: player->HandleStatFlatModifier(UNIT_MOD_ARMOR, BASE_VALUE, v, apply); break;
            case STAT_KEY_RES_HOLY:
            case STAT_KEY_RES_FIRE:
            case STAT_KEY_RES_NATURE:
            case STAT_KEY_RES_FROST:
            case STAT_KEY_RES_SHADOW:
            case STAT_KEY_RES_ARCANE:
                player->HandleStatFlatModifier(UnitMods(UNIT_MOD_RESISTANCE_HOLY + (key - STAT_KEY_RES_HOLY)),
                    BASE_VALUE, v, apply);
                break;
            default:
                break;
        }
    }

    // Recompute the character's attunement stats from the collection and apply the difference.
    void Recalculate(Player* player)
    {
        AttunementState* state = StateOf(player);

        StatTotals totals;
        float statPoints = 0.0f;
        if (sEnabled)
        {
            for (uint32 entry : state->attuned)
            {
                ItemTemplate const* proto = sObjectMgr->GetItemTemplate(entry);
                if (!proto || CheckItem(proto) != ItemCheck::Counts) // e.g. after a config change
                    continue;
                float points;
                for (auto const& [key, value] : ItemStats(proto, points))
                    totals[key] += value * sPercent / 100.0f;
                statPoints += points * sPercent / 100.0f;
            }
        }

        state->rawPercent = sReferenceSetStats > 0.0f ? statPoints / sReferenceSetStats * 100.0f : 0.0f;
        state->effectivePercent = Effective(state->rawPercent);
        float scale = state->rawPercent > 0.0f ? state->effectivePercent / state->rawPercent : 1.0f;

        std::map<uint32, int32> wanted;
        for (auto const& [key, value] : totals)
            if (int32 amount = int32(std::lround(value * scale)))
                wanted[key] = amount;

        for (auto const& [key, amount] : state->applied)
            ApplyStat(player, key, amount, false);
        for (auto const& [key, amount] : wanted)
            ApplyStat(player, key, amount, true);
        state->applied = std::move(wanted);
    }

    void LoadCollection(Player* player)
    {
        AttunementState* state = StateOf(player);
        state->attuned.clear();
        state->progress.clear();
        state->unsaved.clear();
        if (QueryResult result = CharacterDatabase.Query(
            "SELECT `item`, `progress`, `attuned` FROM `character_unbound_attunement` WHERE `guid` = {}",
            player->GetGUID().GetCounter()))
        {
            do
            {
                Field* fields = result->Fetch();
                uint32 item = fields[0].Get<uint32>();
                if (fields[2].Get<bool>())
                    state->attuned.insert(item);
                else
                    state->progress[item] = fields[1].Get<uint32>();
            } while (result->NextRow());
        }
    }

    std::string StatList(std::map<uint32, int32> const& stats)
    {
        std::string text;
        for (auto const& [key, amount] : stats)
        {
            if (!text.empty())
                text += ", ";
            text += Acore::StringFormat("{:+} {}", amount, StatName(key));
        }
        return text.empty() ? "none" : text;
    }

    std::string ItemLink(ItemTemplate const* proto)
    {
        return Acore::StringFormat("|c{:08x}|Hitem:{}:0:0:0:0:0:0:0:0|h[{}]|h|r", ItemQualityColors[proto->Quality],
            proto->ItemId, proto->Name1);
    }

    // ------------------------------------------------------------------ attuning (stage 2)
    char const* const PREFIX = "|cff4dc3ff[Infusion]|r ";

    // Kills an item needs, by quality.
    uint32 KillsNeeded(ItemTemplate const* proto)
    {
        if (sKillsByQuality.empty())
            return 100;
        uint32 index = proto->Quality > ITEM_QUALITY_UNCOMMON ? proto->Quality - ITEM_QUALITY_UNCOMMON : 0;
        return std::max<uint32>(1, sKillsByQuality[std::min<size_t>(index, sKillsByQuality.size() - 1)]);
    }

    // How many kills a creature is worth (0 = doesn't count: it wouldn't give experience).
    uint32 KillValue(Player* player, Creature* creature)
    {
        if (!creature || !Acore::XP::Gain(player, creature))
            return 0;
        if (creature->IsDungeonBoss() || creature->isWorldBoss())
            return sBossKills;
        if (creature->isElite())
            return sEliteKills;
        return 1;
    }

    // ------------------------------------------------------------------ addon messages (stage 4)
    // The UnboundAttunement addon (item tooltips, collection window) whispers its own character, prefix "UBATT":
    //   Q:<id>,<id>,...  -> one I:<id>:<code>:<kills done>:<kills needed>:<tribute price, copper>:<reason>
    //                       per item; code A attuned, W attunable by wearing it, S tribute only, N doesn't
    //                       count (reason says why)
    //   COLL             -> C:BEGIN, C:A:<id>,... (attuned), C:P:<id>=<done>=<needed>,... (in progress),
    //                       C:S:<items>:<collected %>:<after diminishing returns %>:<full until>:<half until>,
    //                       C:T:<stat>=<value>;... (attunement stats), C:END (lists are split over messages)
    // The server also pushes P:<id>=<done>=<needed>,... (kill progress), A:<id> (attuned) and RESET (a GM changed
    // the collection) so tooltips and the window stay current.
    constexpr char const* ADDON_PREFIX = "UBATT";
    constexpr size_t ADDON_CHUNK = 200;

    uint32 TributePrice(Player const* player, ItemTemplate const* proto);

    void SendAddon(Player* player, std::string const& text)
    {
        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player,
            std::string(ADDON_PREFIX) + "\t" + text);
        player->SendDirectMessage(&data);
    }

    // head + parts joined by sep, split over as many messages as needed
    void SendChunked(Player* player, std::string const& head, std::vector<std::string> const& parts, char sep)
    {
        std::string line;
        for (std::string const& part : parts)
        {
            if (!line.empty() && line.size() + part.size() + 1 > ADDON_CHUNK)
            {
                SendAddon(player, head + line);
                line.clear();
            }
            if (!line.empty())
                line += sep;
            line += part;
        }
        if (!line.empty())
            SendAddon(player, head + line);
    }

    std::string ItemInfo(Player* player, uint32 entry)
    {
        ItemTemplate const* proto = sObjectMgr->GetItemTemplate(entry);
        if (!proto)
            return Acore::StringFormat("I:{}:N:0:0:0:unknown item", entry);
        AttunementState* state = StateOf(player);
        uint32 needed = KillsNeeded(proto);
        if (state->attuned.count(entry))
            return Acore::StringFormat("I:{}:A:{}:{}:0:", entry, needed, needed);
        ItemCheck check = CheckItem(proto);
        if (check != ItemCheck::Counts)
            return Acore::StringFormat("I:{}:N:0:{}:0:{}", entry, needed, CheckText(check));
        auto itr = state->progress.find(entry);
        uint32 done = itr != state->progress.end() ? itr->second : 0;
        char code = player->CanUseItem(proto) == EQUIP_ERR_OK ? 'W' : 'S';
        return Acore::StringFormat("I:{}:{}:{}:{}:{}:", entry, code, done, needed, TributePrice(player, proto));
    }

    void SendCollection(Player* player)
    {
        AttunementState* state = StateOf(player);
        SendAddon(player, "C:BEGIN");
        std::vector<std::string> attuned;
        for (uint32 entry : state->attuned)
            attuned.push_back(std::to_string(entry));
        SendChunked(player, "C:A:", attuned, ',');
        std::vector<std::string> progress;
        for (auto const& [entry, done] : state->progress)
            if (ItemTemplate const* proto = sObjectMgr->GetItemTemplate(entry))
                progress.push_back(Acore::StringFormat("{}={}={}", entry, done, KillsNeeded(proto)));
        SendChunked(player, "C:P:", progress, ',');
        SendAddon(player, Acore::StringFormat("C:S:{}:{:.1f}:{:.1f}:{:.0f}:{:.0f}", state->attuned.size(),
            state->rawPercent, state->effectivePercent, sFullValueUntil, sHalfValueUntil));
        std::vector<std::string> stats;
        for (auto const& [key, amount] : state->applied)
            stats.push_back(Acore::StringFormat("{}={}", StatName(key), amount));
        SendChunked(player, "C:T:", stats, ';');
        SendAddon(player, "C:END");
    }

    void HandleAddonMessage(Player* player, std::string const& text)
    {
        if (text == "COLL")
        {
            SendCollection(player);
            return;
        }
        if (text.rfind("Q:", 0) == 0)
        {
            uint32 answered = 0;
            for (std::string_view id : Acore::Tokenize(std::string_view(text).substr(2), ',', false))
                if (Optional<uint32> entry = Acore::StringTo<uint32>(id); entry && ++answered <= 50)
                    SendAddon(player, ItemInfo(player, *entry));
        }
    }

    // Attune an item for good: the collection, the database, the stats, a message.
    void CompleteAttunement(Player* player, AttunementState* state, ItemTemplate const* proto, bool tribute = false)
    {
        state->progress.erase(proto->ItemId);
        state->unsaved.erase(proto->ItemId);
        state->attuned.insert(proto->ItemId);
        CharacterDatabase.Execute("REPLACE INTO `character_unbound_attunement` (`guid`, `item`, `progress`, `attuned`) "
            "VALUES ({}, {}, 0, 1)", player->GetGUID().GetCounter(), proto->ItemId);
        Recalculate(player);
        ChatHandler(player->GetSession()).PSendSysMessage(tribute ?
            "{}{} was offered as tribute and is fully infused! Its stats are yours for good ({} items infused)." :
            "{}{} is fully infused! Its stats are yours for good, even without the item ({} items infused).",
            PREFIX, ItemLink(proto), state->attuned.size());
        player->PlayDirectSound(SOUND_ATTUNED, player);
        SendAddon(player, "A:" + std::to_string(proto->ItemId));
    }

    // A kill: progress for every equipped item that counts and isn't attuned yet.
    void AddKill(Player* player, uint32 value)
    {
        AttunementState* state = StateOf(player);
        std::vector<std::string> changed; // for the addon
        for (uint8 slot = EQUIPMENT_SLOT_START; slot < EQUIPMENT_SLOT_END; ++slot)
        {
            Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot);
            ItemTemplate const* proto = item ? item->GetTemplate() : nullptr;
            if (!proto || state->attuned.count(proto->ItemId) || CheckItem(proto) != ItemCheck::Counts)
                continue;
            uint32 needed = KillsNeeded(proto);
            uint32& progress = state->progress[proto->ItemId];
            uint32 before = progress;
            progress = std::min(needed, progress + value);
            if (progress >= needed)
            {
                CompleteAttunement(player, state, proto);
                continue;
            }
            state->unsaved.insert(proto->ItemId);
            changed.push_back(Acore::StringFormat("{}={}={}", proto->ItemId, progress, needed));
            // a message at 25%, 50% and 75%
            if (before * 4 / needed != progress * 4 / needed)
                ChatHandler(player->GetSession()).PSendSysMessage("{}{} {}% ({}/{} kills).", PREFIX, ItemLink(proto),
                    progress * 100 / needed, progress, needed);
        }
        SendChunked(player, "P:", changed, ',');
    }

    // ------------------------------------------------------------------ tribute (stage 3)
    // Gold price to give an item in tribute: by quality, times sOwnGearMultiplier if the player could attune it by
    // wearing it (attuning stays the main route for one's own gear).
    uint32 TributePrice(Player const* player, ItemTemplate const* proto)
    {
        if (sTributeGold.empty())
            return 0;
        uint32 index = proto->Quality > ITEM_QUALITY_UNCOMMON ? proto->Quality - ITEM_QUALITY_UNCOMMON : 0;
        uint32 gold = sTributeGold[std::min<size_t>(index, sTributeGold.size() - 1)];
        if (player->CanUseItem(proto) == EQUIP_ERR_OK)
            gold *= sOwnGearMultiplier;
        return gold * GOLD;
    }

    // Save the progress that changed since the last save (with the character's own save).
    void SaveProgress(Player* player)
    {
        AttunementState* state = StateOf(player);
        if (state->unsaved.empty())
            return;
        CharacterDatabaseTransaction trans = CharacterDatabase.BeginTransaction();
        for (uint32 entry : state->unsaved)
        {
            auto itr = state->progress.find(entry);
            if (itr != state->progress.end())
                trans->Append("REPLACE INTO `character_unbound_attunement` (`guid`, `item`, `progress`, `attuned`) "
                    "VALUES ({}, {}, {}, 0)", player->GetGUID().GetCounter(), entry, itr->second);
        }
        CharacterDatabase.CommitTransaction(trans);
        state->unsaved.clear();
    }
}

class unbound_attunement_world : public WorldScript
{
public:
    unbound_attunement_world() : WorldScript("unbound_attunement_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD,
        WORLDHOOK_ON_STARTUP
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sEnabled = sConfigMgr->GetOption<bool>("Unbound.Attunement.Enable", true);
        sPercent = std::max(0.0f, sConfigMgr->GetOption<float>("Unbound.Attunement.Percent", 20.0f));
        sLevelRange = sConfigMgr->GetOption<uint32>("Unbound.Attunement.LevelRange", 10);
        sReferenceSetStats = sConfigMgr->GetOption<float>("Unbound.Attunement.ReferenceSetStats", 600.0f);
        sFullValueUntil = sConfigMgr->GetOption<float>("Unbound.Attunement.FullValueUntil", 100.0f);
        sHalfValueUntil = std::max(sFullValueUntil, sConfigMgr->GetOption<float>("Unbound.Attunement.HalfValueUntil", 200.0f));
        sExpansionUnlocked = sConfigMgr->GetOption<uint32>("Unbound.ExpansionUnlocked", 0);

        // "50, 100, 200, 400" -> kills for green, blue, epic, legendary
        sKillsByQuality.clear();
        std::string const kills = sConfigMgr->GetOption<std::string>("Unbound.Attunement.Kills", "50, 100, 200, 400");
        for (std::string_view part : Acore::Tokenize(kills, ',', false))
        {
            while (!part.empty() && part.front() == ' ')
                part.remove_prefix(1);
            while (!part.empty() && part.back() == ' ')
                part.remove_suffix(1);
            if (Optional<uint32> value = Acore::StringTo<uint32>(part))
                sKillsByQuality.push_back(*value);
        }
        if (sKillsByQuality.empty())
            sKillsByQuality = { 50, 100, 200, 400 };
        sEliteKills = sConfigMgr->GetOption<uint32>("Unbound.Attunement.EliteKills", 2);
        sBossKills = sConfigMgr->GetOption<uint32>("Unbound.Attunement.BossKills", 10);

        // "2, 10, 50, 250" -> tribute price in gold for green, blue, epic, legendary
        sTributeGold.clear();
        std::string const prices = sConfigMgr->GetOption<std::string>("Unbound.Attunement.TributeGold",
            sConfigMgr->GetOption<std::string>("Unbound.Attunement.SacrificeGold", "2, 10, 50, 250", false));   // old name
        for (std::string_view part : Acore::Tokenize(prices, ',', false))
        {
            while (!part.empty() && part.front() == ' ')
                part.remove_prefix(1);
            while (!part.empty() && part.back() == ' ')
                part.remove_suffix(1);
            if (Optional<uint32> value = Acore::StringTo<uint32>(part))
                sTributeGold.push_back(*value);
        }
        if (sTributeGold.empty())
            sTributeGold = { 2, 10, 50, 250 };
        sOwnGearMultiplier = sConfigMgr->GetOption<uint32>("Unbound.Attunement.TributeOwnGearMultiplier",
            sConfigMgr->GetOption<uint32>("Unbound.Attunement.SacrificeOwnGearMultiplier", 2, false));   // old name
    }

    void OnStartup() override
    {
        sItemExpansion.clear();
        if (QueryResult result = WorldDatabase.Query("SELECT `item`, `expansion` FROM `unbound_item_expansion`"))
        {
            do
            {
                sItemExpansion[(*result)[0].Get<uint32>()] = (*result)[1].Get<uint8>();
            } while (result->NextRow());
        }
        LOG_INFO("server.loading", ">> mod-unbound: loaded {} gear item expansions for attunement", sItemExpansion.size());
    }
};

class unbound_attunement_player : public PlayerScript
{
public:
    unbound_attunement_player() : PlayerScript("unbound_attunement_player", {
        PLAYERHOOK_ON_LOGIN,
        PLAYERHOOK_ON_DELETE,
        PLAYERHOOK_ON_SAVE,
        PLAYERHOOK_ON_REWARD_KILL_REWARDER,
        PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT
    }) { }

    // The UnboundAttunement addon whispers its own character: handle it and don't deliver the whisper.
    bool OnPlayerCanUseChat(Player* player, uint32 type, uint32 language, std::string& msg, Player* receiver) override
    {
        if (type != CHAT_MSG_WHISPER || language != LANG_ADDON || receiver != player)
            return true;
        std::string const prefix = std::string(ADDON_PREFIX) + "\t";
        if (msg.rfind(prefix, 0) != 0)
            return true;
        HandleAddonMessage(player, msg.substr(prefix.size()));
        return false;
    }

    void OnPlayerLogin(Player* player) override
    {
        LoadCollection(player);
        Recalculate(player);
    }

    void OnPlayerSave(Player* player) override
    {
        SaveProgress(player);
    }

    // Called for every player who gets credit for a kill (the killer, or each group member in range).
    void OnPlayerRewardKillRewarder(Player* player, KillRewarder* rewarder, bool /*isDungeon*/, float& /*rate*/) override
    {
        if (!sEnabled)
            return;
        Unit* victim = rewarder->GetVictim();
        if (uint32 value = KillValue(player, victim ? victim->ToCreature() : nullptr))
            AddKill(player, value);
    }

    void OnPlayerDelete(ObjectGuid guid, uint32 /*accountId*/) override
    {
        CharacterDatabase.Execute("DELETE FROM `character_unbound_attunement` WHERE `guid` = {}", guid.GetCounter());
    }
};

class unbound_attunement_commands : public CommandScript
{
public:
    unbound_attunement_commands() : CommandScript("unbound_attunement_commands") { }

    ChatCommandTable GetCommands() const override
    {
        static ChatCommandTable attuneCommandTable =
        {
            { "add",    HandleAdd,    SEC_GAMEMASTER, Console::No },
            { "remove", HandleRemove, SEC_GAMEMASTER, Console::No },
            { "check",  HandleCheck,  SEC_GAMEMASTER, Console::No },
            { "info",   HandleInfo,   SEC_GAMEMASTER, Console::No },
            { "reset",  HandleReset,  SEC_GAMEMASTER, Console::No },
            { "fill",   HandleFill,   SEC_GAMEMASTER, Console::No },
            { "progress", HandleProgress, SEC_PLAYER, Console::No },
        };
        static ChatCommandTable commandTable =
        {
            { "infuse", attuneCommandTable },
            { "attune", attuneCommandTable },   // old name
        };
        return commandTable;
    }

    // .infuse add <item>: attune an item for the selected player (or yourself)
    static bool HandleAdd(ChatHandler* handler, ItemTemplate const* proto)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        ItemCheck check = CheckItem(proto);
        if (check != ItemCheck::Counts)
        {
            handler->PSendSysMessage("{} {}.", ItemLink(proto), CheckText(check));
            return true;
        }
        AttunementState* state = StateOf(target);
        if (state->attuned.count(proto->ItemId))
        {
            handler->PSendSysMessage("{} already has {} infused.", target->GetName(), ItemLink(proto));
            return true;
        }
        CharacterDatabase.Execute("REPLACE INTO `character_unbound_attunement` (`guid`, `item`, `progress`, `attuned`) "
            "VALUES ({}, {}, 0, 1)", target->GetGUID().GetCounter(), proto->ItemId);
        state->progress.erase(proto->ItemId);
        state->attuned.insert(proto->ItemId);
        Recalculate(target);
        SendAddon(target, "RESET");
        handler->PSendSysMessage("{} infused for {} ({} items, {:.0f}% of a full set).", ItemLink(proto),
            target->GetName(), state->attuned.size(), state->effectivePercent);
        return true;
    }

    // .infuse remove <item>
    static bool HandleRemove(ChatHandler* handler, ItemTemplate const* proto)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        AttunementState* state = StateOf(target);
        if (!state->attuned.erase(proto->ItemId) && !state->progress.erase(proto->ItemId))
        {
            handler->PSendSysMessage("{} has no infusion for {}.", target->GetName(), ItemLink(proto));
            return true;
        }
        CharacterDatabase.Execute("DELETE FROM `character_unbound_attunement` WHERE `guid` = {} AND `item` = {}",
            target->GetGUID().GetCounter(), proto->ItemId);
        Recalculate(target);
        SendAddon(target, "RESET");
        handler->PSendSysMessage("Removed {} from {}'s infusions.", ItemLink(proto), target->GetName());
        return true;
    }

    // .infuse check <item>: does it count, and what it gives at full value
    static bool HandleCheck(ChatHandler* handler, ItemTemplate const* proto)
    {
        ItemCheck check = CheckItem(proto);
        handler->PSendSysMessage("{} {}.", ItemLink(proto), CheckText(check));
        float points;
        std::map<uint32, int32> gives;
        for (auto const& [key, value] : ItemStats(proto, points))
            if (int32 amount = int32(std::lround(value * sPercent / 100.0f)))
                gives[key] = amount;
        handler->PSendSysMessage("Infused, it gives {:.0f}% of its stats (before diminishing returns): {}.", sPercent,
            StatList(gives));
        return true;
    }

    // .infuse info: the selected player's (or your) collection and its stats
    static bool HandleInfo(ChatHandler* handler)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        AttunementState* state = StateOf(target);
        handler->PSendSysMessage("{}: {} items infused, {} in progress.", target->GetName(), state->attuned.size(),
            state->progress.size());
        handler->PSendSysMessage("Collected {:.0f}% of a full set of gear's stats; after diminishing returns {:.0f}% "
            "(full value until {:.0f}%, half until {:.0f}%, a quarter beyond).", state->rawPercent,
            state->effectivePercent, sFullValueUntil, sHalfValueUntil);
        handler->PSendSysMessage("Infusion stats: {}.", StatList(state->applied));
        return true;
    }

    // .infuse progress (any player): your equipped items' attunement
    static bool HandleProgress(ChatHandler* handler)
    {
        Player* player = handler->GetSession() ? handler->GetSession()->GetPlayer() : nullptr;
        if (!player)
            return false;
        AttunementState* state = StateOf(player);
        handler->PSendSysMessage("{}{} items infused, {:.0f}% of a full set's stats (after diminishing returns). "
            "Equipped:", PREFIX, state->attuned.size(), state->effectivePercent);
        for (uint8 slot = EQUIPMENT_SLOT_START; slot < EQUIPMENT_SLOT_END; ++slot)
        {
            Item* item = player->GetItemByPos(INVENTORY_SLOT_BAG_0, slot);
            if (!item)
                continue;
            ItemTemplate const* proto = item->GetTemplate();
            if (state->attuned.count(proto->ItemId))
                handler->PSendSysMessage("  {}: infused", ItemLink(proto));
            else if (ItemCheck check = CheckItem(proto); check != ItemCheck::Counts)
                handler->PSendSysMessage("  {}: {}", ItemLink(proto), CheckText(check));
            else
            {
                uint32 needed = KillsNeeded(proto);
                auto itr = state->progress.find(proto->ItemId);
                uint32 done = itr != state->progress.end() ? itr->second : 0;
                handler->PSendSysMessage("  {}: {}% ({}/{} kills)", ItemLink(proto), done * 100 / needed, done, needed);
            }
        }
        return true;
    }

    // .infuse fill <100|200|full> (testing): infuse real items for the selected player (or yourself) until the
    // infusion bonus reaches +100% or +200% of a full set's stats after the diminishing returns, or infuse every
    // item that counts. Items the target can use come first, best first, so the stats look like a real
    // collection; .infuse reset undoes it.
    static bool HandleFill(ChatHandler* handler, std::string level)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        bool const full = level == "full";
        float wantedEffective = 0.0f;
        if (!full)
        {
            wantedEffective = level == "100" ? 100.0f : level == "200" ? 200.0f : 0.0f;
            if (wantedEffective <= 0.0f)
            {
                handler->SendSysMessage("Usage: .infuse fill 100 | 200 | full");
                return true;
            }
        }

        // the raw % (before diminishing returns) that gives that effective %: the inverse of Effective()
        float const halfTop = std::max(sHalfValueUntil, sFullValueUntil);
        float wantedRaw = wantedEffective;
        if (wantedEffective > sFullValueUntil)
            wantedRaw = wantedEffective <= halfTop
                ? sFullValueUntil + 2.0f * (wantedEffective - sFullValueUntil)
                : sFullValueUntil + 2.0f * (halfTop - sFullValueUntil) + 4.0f * (wantedEffective - halfTop);

        AttunementState* state = StateOf(target);
        if (!full && state->rawPercent >= wantedRaw)
        {
            handler->PSendSysMessage("{} already has {:.0f}% after diminishing returns.", target->GetName(),
                state->effectivePercent);
            return true;
        }

        // candidates: every item that counts and isn't infused yet, usable by the target first, then by item level
        struct Candidate { ItemTemplate const* proto; bool usable; float points; };
        std::vector<Candidate> candidates;
        for (auto const& [entry, proto] : *sObjectMgr->GetItemTemplateStore())
        {
            if (state->attuned.count(entry) || CheckItem(&proto) != ItemCheck::Counts)
                continue;
            float points = 0.0f;
            ItemStats(&proto, points);
            if (points <= 0.0f)
                continue;
            candidates.push_back({ &proto, target->CanUseItem(&proto) == EQUIP_ERR_OK, points });
        }
        std::sort(candidates.begin(), candidates.end(), [](Candidate const& a, Candidate const& b)
        {
            if (a.usable != b.usable)
                return a.usable;
            if (a.proto->ItemLevel != b.proto->ItemLevel)
                return a.proto->ItemLevel > b.proto->ItemLevel;
            return a.proto->ItemId < b.proto->ItemId;
        });

        // pick until the raw % is reached (each item gives sPercent of its stat points)
        float raw = state->rawPercent;
        std::vector<uint32> picked;
        for (Candidate const& candidate : candidates)
        {
            if (!full && raw >= wantedRaw)
                break;
            picked.push_back(candidate.proto->ItemId);
            if (sReferenceSetStats > 0.0f)
                raw += candidate.points * sPercent / 100.0f / sReferenceSetStats * 100.0f;
        }
        if (picked.empty())
        {
            handler->PSendSysMessage("{} has no more items to infuse.", target->GetName());
            return true;
        }

        // save in chunks, then apply once
        uint32 const guid = target->GetGUID().GetCounter();
        CharacterDatabaseTransaction trans = CharacterDatabase.BeginTransaction();
        for (std::size_t i = 0; i < picked.size(); i += 500)
        {
            std::string values;
            for (std::size_t j = i; j < std::min(picked.size(), i + 500); ++j)
                values += Acore::StringFormat("{}({}, {}, 0, 1)", values.empty() ? "" : ", ", guid, picked[j]);
            trans->Append("REPLACE INTO `character_unbound_attunement` (`guid`, `item`, `progress`, `attuned`) VALUES {}",
                values);
        }
        CharacterDatabase.CommitTransaction(trans);
        for (uint32 entry : picked)
        {
            state->progress.erase(entry);
            state->attuned.insert(entry);
        }
        Recalculate(target);
        SendAddon(target, "RESET");
        handler->PSendSysMessage("Infused {} items for {}: {} items in total, {:.0f}% of a full set collected, {:.0f}% "
            "after diminishing returns.", picked.size(), target->GetName(), state->attuned.size(), state->rawPercent,
            state->effectivePercent);
        return true;
    }

    // .infuse reset: remove the selected player's (or your) whole collection
    static bool HandleReset(ChatHandler* handler)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        AttunementState* state = StateOf(target);
        CharacterDatabase.Execute("DELETE FROM `character_unbound_attunement` WHERE `guid` = {}",
            target->GetGUID().GetCounter());
        state->attuned.clear();
        state->progress.clear();
        state->unsaved.clear();
        Recalculate(target);
        SendAddon(target, "RESET");
        handler->PSendSysMessage("Removed all of {}'s infusions.", target->GetName());
        return true;
    }
};

// 190103 - Altar of Tribute: lists the items in the player's bags that can be given in tribute; choosing one shows the
// game's confirmation box with the gold price; the server checks everything again before destroying the item.
class npc_unbound_attunement_altar : public CreatureScript
{
public:
    npc_unbound_attunement_altar() : CreatureScript("npc_unbound_attunement_altar") { }

    static constexpr uint32 NPC_TEXT_ALTAR = 190103;
    static constexpr uint32 ITEMS_PER_PAGE = 28;      // the menu holds 32 lines; the rest are page buttons
    static constexpr uint32 SENDER_PAGE = 0;          // sender 0: a page button (action = page)

    struct Offer
    {
        uint8 bag;
        uint8 slot;
        ItemTemplate const* proto;
    };

    // The items in the bags that can be given in tribute: counting, not attuned yet, each entry once.
    static std::vector<Offer> Offers(Player* player)
    {
        AttunementState* state = StateOf(player);
        std::vector<Offer> offers;
        std::unordered_set<uint32> seen;
        auto consider = [&](uint8 bag, uint8 slot)
        {
            Item* item = player->GetItemByPos(bag, slot);
            ItemTemplate const* proto = item ? item->GetTemplate() : nullptr;
            if (!proto || state->attuned.count(proto->ItemId) || seen.count(proto->ItemId) ||
                CheckItem(proto) != ItemCheck::Counts)
                return;
            seen.insert(proto->ItemId);
            offers.push_back({ bag, slot, proto });
        };
        for (uint8 slot = INVENTORY_SLOT_ITEM_START; slot < INVENTORY_SLOT_ITEM_END; ++slot)
            consider(INVENTORY_SLOT_BAG_0, slot);
        for (uint8 bag = INVENTORY_SLOT_BAG_START; bag < INVENTORY_SLOT_BAG_END; ++bag)
            if (Bag* container = player->GetBagByPos(bag))
                for (uint8 slot = 0; slot < container->GetBagSize(); ++slot)
                    consider(bag, slot);
        return offers;
    }

    static void ShowPage(Player* player, Creature* creature, uint32 page)
    {
        ClearGossipMenuFor(player);
        if (!sEnabled)
        {
            SendGossipMenuFor(player, NPC_TEXT_ALTAR, creature);
            return;
        }
        AttunementState* state = StateOf(player);
        std::vector<Offer> offers = Offers(player);
        uint32 pages = std::max<uint32>(1, (offers.size() + ITEMS_PER_PAGE - 1) / ITEMS_PER_PAGE);
        page = std::min(page, pages - 1);
        for (uint32 i = page * ITEMS_PER_PAGE; i < std::min<uint32>(offers.size(), (page + 1) * ITEMS_PER_PAGE); ++i)
        {
            Offer const& offer = offers[i];
            uint32 price = TributePrice(player, offer.proto);
            std::string text = Acore::StringFormat("|c{:08x}{}|r", ItemQualityColors[offer.proto->Quality], offer.proto->Name1);
            auto progress = state->progress.find(offer.proto->ItemId);
            if (progress != state->progress.end() && progress->second)
                text += Acore::StringFormat(" ({}% infused)", progress->second * 100 / KillsNeeded(offer.proto));
            if (player->CanUseItem(offer.proto) == EQUIP_ERR_OK)
                text += " - you could infuse it by wearing it";
            std::string confirm = Acore::StringFormat("Offer {} as tribute? It is destroyed, and {:.0f}% of its stats are yours "
                "for good.", offer.proto->Name1, sPercent);
            AddGossipItemFor(player, GOSSIP_ICON_MONEY_BAG, text, offer.proto->ItemId,
                (uint32(offer.bag) << 8) | offer.slot, confirm, price, false);
        }
        if (page + 1 < pages)
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, Acore::StringFormat("Next page ({}/{})", page + 2, pages),
                SENDER_PAGE, page + 1);
        if (page > 0)
            AddGossipItemFor(player, GOSSIP_ICON_CHAT, "Previous page", SENDER_PAGE, page - 1);
        if (offers.empty())
            ChatHandler(player->GetSession()).PSendSysMessage("{}Nothing in your bags can be offered as tribute: only gear "
                "that counts for infusion and isn't infused yet.", PREFIX);
        SendGossipMenuFor(player, NPC_TEXT_ALTAR, creature);
    }

    bool OnGossipHello(Player* player, Creature* creature) override
    {
        ShowPage(player, creature, 0);
        return true;
    }

    bool OnGossipSelect(Player* player, Creature* creature, uint32 sender, uint32 action) override
    {
        if (sender == SENDER_PAGE)
        {
            ShowPage(player, creature, action);
            return true;
        }

        // sender = item entry, action = bag << 8 | slot; everything is checked again before anything happens
        uint8 bag = uint8(action >> 8);
        uint8 slot = uint8(action & 0xFF);
        Item* item = player->GetItemByPos(bag, slot);
        ItemTemplate const* proto = item ? item->GetTemplate() : nullptr;
        AttunementState* state = StateOf(player);
        ChatHandler chat(player->GetSession());
        if (!sEnabled || !proto || proto->ItemId != sender || !Player::IsInventoryPos(bag, slot) ||
            state->attuned.count(proto->ItemId) || CheckItem(proto) != ItemCheck::Counts)
            chat.PSendSysMessage("{}That item is no longer in your bags or can't be offered as tribute.", PREFIX);
        else if (uint32 price = TributePrice(player, proto); !player->HasEnoughMoney(price))
            chat.PSendSysMessage("{}You need {} gold to offer {} as tribute.", PREFIX, price / GOLD, ItemLink(proto));
        else
        {
            player->ModifyMoney(-int32(price));
            player->DestroyItem(bag, slot, true);
            CompleteAttunement(player, state, proto, true);
        }
        ShowPage(player, creature, 0);
        return true;
    }
};

void AddSC_unbound_attunement()
{
    new npc_unbound_attunement_altar();
    new unbound_attunement_world();
    new unbound_attunement_player();
    new unbound_attunement_commands();
}
