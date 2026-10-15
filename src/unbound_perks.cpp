/*
 * mod-unbound: perks (the Unbound Perks addon's Character Perks window, /perks).
 *
 * Permanent perks (always on for every player):
 *   No Resurrection Sickness   worldserver.conf: Death.SicknessLevel = 255 (apply-unbound-settings.ps1)
 *   No Daze                    worldserver.conf: Daze.Enabled = 0          (apply-unbound-settings.ps1)
 *   Rapid Recovery             below: after a few seconds out of combat, restore a percentage of maximum
 *                              health and mana every second until full. It has ranks (mod_unbound.conf):
 *                              Rank 1 6 s / 4% from level 1, Rank 2 5 s / 6% from level 30, Rank 3 4 s / 8%
 *                              from level 60.
 *
 * Perk ranks: a perk listed in RankedPerks() has several ranks. A character's rank comes from its level
 * (the rank levels in mod_unbound.conf) unless a GM set one with ".perk rank <perk id> <rank>" (saved in
 * characters.character_unbound_perk_ranks; ".perk rank <perk id>" without a rank goes back to the level).
 * The server tells the addon with "RANK:<perk>:<rank>:<max>:<values>" (values per rank, ';'-separated).
 *
 * Numbers are kept in normal WoW ranges (no Peloria-sized scaling): one perk is worth about +10%.
 *
 * Toggled perks: the addon whispers the player's own character with prefix "UBPERK"
 *   SYNC                       send me my perks
 *   SET:<id>:<0|1>             turn one perk off/on
 *   LOAD:<id>,<id>,...         exactly these perks on (a loadout)
 * and the server answers with "STATE:<id>,<id>,..." (the active perks it knows) or "ERR:<text>".
 * Perks can't be changed in combat. Active perks are saved in characters.character_unbound_perks.
 * At most 5 Offensive perks (ids 101-199), 3 Defensive (201-299) and 3 Utility (301-399) can be active at
 * once (CATEGORY_LIMITS); the addon uses the same limits (CATEGORIES in addon/UnboundPerks/PerkData.lua).
 * Exclusive groups (EXCLUSIVE_GROUPS): turning one on turns the others off. Class perks (ids 1001+) only work for
 * their class (CLASS_PERKS); the server refuses them for any other class.
 *
 * Working toggled perks (ids match addon/UnboundPerks/PerkData.lua; all also work for pets). The Offensive
 * numbers below are Rank 3 (level 60). Each has 5 ranks (RANKED_PERKS): Ranks 1-3 by level 1/30/60 at about
 * 0.4x/0.7x/1x, Ranks 4-5 at about 1.3x/1.5x for the endgame (a +10% perk: 4/7/10/13/15%). Ranks 4-5 unlock at
 * level 255, i.e. only with .perk rank, until a way to earn them exists. Only the upside is ranked; drawbacks,
 * caps and steps (FOCUS_PENALTY, AVOIDANCE_CAP, CHAOS_MULTIPLIER, ...) stay fixed.
 *   101 Cyclic Power           damage done cycles between -10% and +20% over 25 seconds
 *   102 Critical Understanding every 1% crit chance above 25% = +1% crit damage, up to +20%
 *   103 Defensive Sacrifice    take 10% more damage; +10% of current attack power and spell power
 *   104 Desperate Power        -50% of your magic resistances (Fire, Nature, Frost, Shadow, Arcane);
 *                              +10% damage dealt
 *   105 Block Capping          block chance is capped at 20%; every 1% above the cap = +1% damage
 *   106 Dodge Capping          the same for dodge         (each up to +10%; the caps apply to
 *   107 Parry Capping          the same for parry          melee attacks against you)
 *   108 Haste Capping          every 1% haste above 5% = +1% damage, up to +10%; take 5% more damage
 *   109 Pet Encouragement      your pets, guardians and totems deal 15% more damage
 *   110 Rolling Momentum       +1% damage per second in combat, up to +10%; out of combat it drops 1% per second
 *   111 Tunnel Vision          single-target damage +10%, area damage -10%
 *   112 Collateral Damage      area damage +10%, single-target damage -10%
 *                              (area = a spell that hits an area or chains to more targets; everything else,
 *                              melee and auto attacks included, is single-target)
 *   113 Giant Slayer           +10% damage to bosses (world bosses and dungeon/raid bosses)
 *   114 Merciless              damage-over-time ticks +15%
 *   115 Pressure               each hit on the same target +1% damage, up to 10 stacks (+10%); switching
 *                              targets resets it (tracked per attacker, so a pet keeps its own stacks;
 *                              direct hits add a stack, damage-over-time ticks use the current stacks)
 *   116 Chaos                  each damaging ability (a spell or a weapon strike, not auto attacks or
 *                              damage-over-time ticks) has a 10% chance to deal 50% more damage
 *   117 Power Conversion       every 100 of your highest base stat = +1% damage, up to +10%
 *   118 Healing Powah          healing done +10% (direct heals and heal-over-time ticks)
 *   119 Shadow Mastery         Shadow spell damage +10%
 *   120 Holy Mastery           Holy spell damage +10%
 *   121 Arcane Mastery         Arcane spell damage +10%
 *   122 Nature Mastery         Nature spell damage +10%
 *   123 Fire Mastery           Fire spell damage +10%
 *   124 Frost Mastery          Frost spell damage +10%
 *   125 Physical Mastery       Physical damage +10% (melee and auto attacks, weapon strikes, Physical
 *                              spells and bleeds)
 *                              (a spell counts for a school if that school is part of it, e.g. Shadowfrost)
 *
 * Defensive perks (ids 201-299, at most 3 active; 201-203 were placeholders, never reuse them). Rank 1/2/3 shown;
 * Ranks 4-5 (about 1.3x / 1.5x, GM-only for now) are in RANKED_PERKS:
 *   204 Greater Bulwark        all your Dodge and Parry become Block, at 100/110/120%  (needs a shield)
 *   205 Evasive Maneuvers      all your Block and Parry become Dodge, at 100/110/120%
 *   206 Parry King             all your Block and Dodge become Parry, at 100/110/120%
 *                              (204-206 are exclusive; melee attacks only, the character sheet shows the
 *                              unconverted chances)
 *   207 Reinforced Armor       physical damage taken -4/7/10%
 *   208 Spellwarded            magic damage taken -4/7/10%
 *   209 Stoicism               damage-over-time damage taken -8/14/20% (you and your pet)
 *   210 Defensive Momentum     each second moving: a stack of max/10, up to 5/7.5/10% damage reduction; all
 *                              stacks lost after 2 s standing still (you and your pet, each their own)
 *   211 Fortress               each second standing still: a stack of max/10, up to 5/7.5/10%; all stacks
 *                              lost after 3 s moving (you and your pet)          (210 and 211 are exclusive)
 *   212 Juggernaut             no single hit takes more than 40/35/30% of maximum health, once every 3 s
 *   213 Counterweight          after a dodge, parry or block, the next hit taken is reduced by 10/15/20%
 *   214 Titan's Resolve        damage reduction up to 5/7.5/10%, in proportion to the health missing
 *   215 Second Wind            a hit above 15% of maximum health: heal 1/1.5/2% of maximum health a second
 *                              for 5 s
 *   216 Hardened Flesh         the part of a hit above 10% of maximum health is reduced by 10/15/20%
 *   217 Pet's Blessing         your pet takes 10/15/20% less damage
 *   218 Shield Wall Training   each block: +0.5/0.75/1% block chance for 5 s, up to 5 stacks
 *   219 Survival Instinct      below 30% health, damage taken -8/12/15%
 *   220 Vital Reserve          maximum health +4/7/10%
 *   221 Enduring               healing received +4/7/10%
 *   222 Thornmail              melee attackers take 10/20/30% of the damage they deal back (as the warrior's
 *                              Damage Shield, Physical)
 *   223 Heavy Frame            armor +5/10/15%
 *   (212-223 all work for you and your pet, each with its own timers.) Vital Reserve and Heavy Frame are a
 *   server-only passive aura (SPELL_PERK_VITALITY); Counterweight, Shield Wall Training and Thornmail learn
 *   about melee attacks taken from a proc aura (SPELL_PERK_DEFENSE_PROC); Juggernaut, Hardened Flesh and
 *   Second Wind use the final damage in the DealDamage hook.
 *
 * Utility perks (ids 301-399, at most 3 active):
 *   303 Iron Will              crowd-control effects from enemies on you (and your pets) last shorter. Ranked
 *                              (mod_unbound.conf): Rank 1 -10% from level 1, Rank 2 -20% from level 30, Rank 3
 *                              -30% from level 60. Crowd control = charm, disorient, fear, root, silence, sleep,
 *                              stun, freeze, knockout, polymorph, horror, sap (by mechanic, or by aura type for
 *                              spells without one). Applied to the aura's base duration, so it stacks with
 *                              racials and talents (e.g. an Orc's 15% stun reduction) and diminishing returns.
 *   304 Longer Legs            run speed +4/7/10% (you and your pet), mounted speed +4/7/10%, swim speed
 *                              +20/35/50%, fall damage -20/35/50%
 *   305 Planting your legs     after standing still for 3 seconds: 0.5/0.75/1% of maximum health and
 *                              0.25/0.4/0.5% of maximum mana every second (in or out of combat)
 *   306 Relentless Pursuit     after you or your pet kill an enemy, you and your pet run 15/25/35% faster
 *                              for 10 seconds
 *   307 Vampirism              heal for 3/4/5% of the damage you deal                     (exclusive with 308)
 *   308 Soul Drain             heal for 6/8/10% of the damage you deal, your pet heals itself the same way
 *                              from its damage; direct healing on you and your pet -20%  (exclusive with 307)
 *   309 Pets replenishment     your pet takes 20/35/50% more healing
 *   310 Pets Roar              your pet generates 100/200/300% more threat
 *   311 Silent Killer          you generate 20/35/50% less threat (not your pet)          (exclusive with 312)
 *   312 Unbreakable Presence   you generate 50/100/150% more threat                       (exclusive with 311)
 *   313 Steady Hands           spell pushback -30/50/70%; interrupt lockouts and silences on you -10/20/30%
 *   314 Mana Leech             restore mana equal to 1/1.5/2% of the damage you deal, while using mana
 *   The numbers are Rank 1/2/3 (levels 1, 30, 60); Ranks 4-5 (about 1.3x / 1.5x, GM-only for now) and all
 *   values are in mod_unbound.conf (RANKED_PERKS). Speed, threat
 *   and Steady Hands are server-only passive auras (SPELL_PERK_*); the leech perks and fall damage use the
 *   DealDamage hook (leech from damage actually dealt to another unit, capped at the victim's health).
 *
 * Class perks (ids 1001+):
 *  1001 Retribution (Paladin)  Improved Divine Storm: Divine Storm hits up to 6 enemies (normally 4), and every
 *                              enemy it hits also takes a Crusader Strike.
 *                              All Will Be Judged!: a Judgement spreads to up to 4 more enemies within 10 yards
 *                              of the target, and every enemy a Judgement hits takes a free Exorcism (no cooldown).
 *                              Exorcist: Exorcism scales with 30% of attack power and 30% of spell power
 *                              (instead of 15% / 15%).
 *                              Righteous Explosion: an enemy dying with your Righteous Vengeance damage-over-
 *                              time deals the damage left on it to up to 5 enemies within 8 yards.
 *                              By Sword & Light: Holy damage +15%, Physical damage +10%.
 *                              The extra Crusader Strikes, Judgements and Exorcisms are free triggered casts.
 *
 * Settings (mod_unbound.conf): Unbound.Perks.RapidRecovery (on/off), .Delay (ms per rank), .Percent (per rank),
 * .RankLevels (level per rank); for every other ranked perk Unbound.Perks.<Key>.<Stat> (per rank) and
 * Unbound.Perks.<Key>.RankLevels (RANKED_PERKS lists the keys, stats and defaults).
 */

#include "Chat.h"
#include "ChatCommand.h"
#include "Config.h"
#include "CellImpl.h"
#include "Creature.h"
#include "DatabaseEnv.h"
#include "GridNotifiers.h"
#include "GridNotifiersImpl.h"
#include "ObjectAccessor.h"
#include "MoveSpline.h"
#include "Pet.h"
#include "Player.h"
#include "Random.h"
#include "ScriptMgr.h"
#include "SpellAuraEffects.h"
#include "SpellAuras.h"
#include "SpellInfo.h"
#include "SpellMgr.h"
#include "SpellScript.h"
#include "SpellScriptLoader.h"
#include "StringConvert.h"
#include "Tokenize.h"
#include "WorldPacket.h"

#include <algorithm>
#include <array>
#include <cmath>
#include <list>
#include <map>
#include <set>
#include <unordered_map>
#include <utility>
#include <vector>

namespace
{
    // ------------------------------------------------------------------ Rapid Recovery settings
    struct RecoveryRank
    {
        uint32 delayMs;
        uint32 percent;
        uint32 level;   // character level that reaches this rank
    };
    bool sRapidRecovery = true;
    std::vector<RecoveryRank> sRecoveryRanks = { { 6000, 4, 1 }, { 5000, 6, 30 }, { 4000, 8, 60 } };
    constexpr uint32 RECOVERY_TICK_MS = 1000;
    constexpr uint32 PERK_ID_RAPID_RECOVERY = 3;

    // ------------------------------------------------------------------ ranked perk settings
    // Every ranked perk except Rapid Recovery: one or more numbers per rank plus the level that reaches each
    // rank, read from mod_unbound.conf as Unbound.Perks.<Key>.<Stat> = "rank 1, rank 2, ..." and
    // Unbound.Perks.<Key>.RankLevels (see RANKED_PERKS below).
    struct PerkRanks
    {
        std::vector<std::vector<float>> values; // values[rank - 1][stat]
        std::vector<uint32> levels;             // character level that reaches each rank
    };
    std::map<uint32, PerkRanks> sPerkRanks;

    // "6000, 5000, 4000" -> { 6000, 5000, 4000 }
    std::vector<uint32> ParseList(std::string const& text)
    {
        std::vector<uint32> values;
        for (std::string_view part : Acore::Tokenize(text, ',', false))
        {
            while (!part.empty() && part.front() == ' ')
                part.remove_prefix(1);
            while (!part.empty() && part.back() == ' ')
                part.remove_suffix(1);
            if (Optional<uint32> value = Acore::StringTo<uint32>(part))
                values.push_back(*value);
        }
        return values;
    }

    // "0.5, 0.75, 1" -> { 0.5, 0.75, 1 }
    std::vector<float> ParseFloatList(std::string const& text)
    {
        std::vector<float> values;
        for (std::string_view part : Acore::Tokenize(text, ',', false))
        {
            while (!part.empty() && part.front() == ' ')
                part.remove_prefix(1);
            while (!part.empty() && part.back() == ' ')
                part.remove_suffix(1);
            if (Optional<float> value = Acore::StringTo<float>(part))
                values.push_back(std::max(0.0f, *value));
        }
        return values;
    }

    // ------------------------------------------------------------------ toggled perks
    enum PerkId : uint32
    {
        PERK_CYCLIC_POWER           = 101,
        PERK_CRITICAL_UNDERSTANDING = 102,
        PERK_DEFENSIVE_SACRIFICE    = 103,
        PERK_DESPERATE_POWER        = 104,
        PERK_BLOCK_CAPPING          = 105,
        PERK_DODGE_CAPPING          = 106,
        PERK_PARRY_CAPPING          = 107,
        PERK_HASTE_CAPPING          = 108,
        PERK_PET_ENCOURAGEMENT      = 109,
        PERK_ROLLING_MOMENTUM       = 110,
        PERK_TUNNEL_VISION          = 111,
        PERK_COLLATERAL_DAMAGE      = 112,
        PERK_GIANT_SLAYER           = 113,
        PERK_MERCILESS              = 114,
        PERK_PRESSURE               = 115,
        PERK_CHAOS                  = 116,
        PERK_POWER_CONVERSION       = 117,
        PERK_HEALING_POWAH          = 118,
        PERK_SHADOW_MASTERY         = 119,
        PERK_HOLY_MASTERY           = 120,
        PERK_ARCANE_MASTERY         = 121,
        PERK_NATURE_MASTERY         = 122,
        PERK_FIRE_MASTERY           = 123,
        PERK_FROST_MASTERY          = 124,
        PERK_PHYSICAL_MASTERY       = 125,
        PERK_GREATER_BULWARK        = 204,  // 201-203 were placeholders: never reuse them
        PERK_EVASIVE_MANEUVERS      = 205,
        PERK_PARRY_KING             = 206,
        PERK_REINFORCED_ARMOR       = 207,
        PERK_SPELLWARDED            = 208,
        PERK_STOICISM               = 209,
        PERK_DEFENSIVE_MOMENTUM     = 210,
        PERK_FORTRESS               = 211,
        PERK_JUGGERNAUT             = 212,
        PERK_COUNTERWEIGHT          = 213,
        PERK_TITANS_RESOLVE         = 214,
        PERK_SECOND_WIND            = 215,
        PERK_HARDENED_FLESH         = 216,
        PERK_PETS_BLESSING          = 217,
        PERK_SHIELD_WALL_TRAINING   = 218,
        PERK_SURVIVAL_INSTINCT      = 219,
        PERK_VITAL_RESERVE          = 220,
        PERK_ENDURING               = 221,
        PERK_THORNMAIL              = 222,
        PERK_HEAVY_FRAME            = 223,
        PERK_IRON_WILL              = 303,
        PERK_LONGER_LEGS            = 304,
        PERK_PLANTED_FEET           = 305,  // "Planting your legs"
        PERK_RELENTLESS_PURSUIT     = 306,
        PERK_VAMPIRISM              = 307,
        PERK_SOUL_DRAIN             = 308,
        PERK_PET_REPLENISHMENT      = 309,
        PERK_PETS_ROAR              = 310,
        PERK_SILENT_KILLER          = 311,
        PERK_UNBREAKABLE_PRESENCE   = 312,
        PERK_STEADY_HANDS           = 313,  // "Spell-Protected Steady Hands"
        PERK_MANA_LEECH             = 314,
        PERK_RETRIBUTION            = 1001,  // Paladin
    };

    std::set<uint32> const IMPLEMENTED = {
        PERK_CYCLIC_POWER, PERK_CRITICAL_UNDERSTANDING, PERK_DEFENSIVE_SACRIFICE,
        PERK_DESPERATE_POWER, PERK_BLOCK_CAPPING, PERK_DODGE_CAPPING, PERK_PARRY_CAPPING,
        PERK_HASTE_CAPPING, PERK_PET_ENCOURAGEMENT, PERK_ROLLING_MOMENTUM,
        PERK_TUNNEL_VISION, PERK_COLLATERAL_DAMAGE, PERK_GIANT_SLAYER,
        PERK_MERCILESS, PERK_PRESSURE, PERK_CHAOS, PERK_POWER_CONVERSION,
        PERK_HEALING_POWAH, PERK_SHADOW_MASTERY, PERK_HOLY_MASTERY, PERK_ARCANE_MASTERY,
        PERK_NATURE_MASTERY, PERK_FIRE_MASTERY, PERK_FROST_MASTERY, PERK_PHYSICAL_MASTERY,
        PERK_IRON_WILL, PERK_LONGER_LEGS, PERK_PLANTED_FEET, PERK_RELENTLESS_PURSUIT, PERK_VAMPIRISM,
        PERK_SOUL_DRAIN, PERK_PET_REPLENISHMENT, PERK_PETS_ROAR, PERK_SILENT_KILLER, PERK_UNBREAKABLE_PRESENCE,
        PERK_STEADY_HANDS, PERK_MANA_LEECH, PERK_GREATER_BULWARK, PERK_EVASIVE_MANEUVERS, PERK_PARRY_KING,
        PERK_REINFORCED_ARMOR, PERK_SPELLWARDED, PERK_STOICISM, PERK_DEFENSIVE_MOMENTUM, PERK_FORTRESS,
        PERK_JUGGERNAUT, PERK_COUNTERWEIGHT, PERK_TITANS_RESOLVE, PERK_SECOND_WIND, PERK_HARDENED_FLESH,
        PERK_PETS_BLESSING, PERK_SHIELD_WALL_TRAINING, PERK_SURVIVAL_INSTINCT, PERK_VITAL_RESERVE, PERK_ENDURING,
        PERK_THORNMAIL, PERK_HEAVY_FRAME, PERK_RETRIBUTION };

    // Groups of perks that can't be active together: turning one on turns the others in its group off.
    std::vector<std::vector<uint32>> const EXCLUSIVE_GROUPS = {
        { PERK_VAMPIRISM, PERK_SOUL_DRAIN },
        { PERK_SILENT_KILLER, PERK_UNBREAKABLE_PRESENCE },
        { PERK_GREATER_BULWARK, PERK_EVASIVE_MANEUVERS, PERK_PARRY_KING },
        { PERK_DEFENSIVE_MOMENTUM, PERK_FORTRESS },
    };

    // Ranked perks read from mod_unbound.conf: perk, config key, and each stat with its default per rank.
    // Every one has 5 ranks: Ranks 1-3 by level (Rank 3 = the values from before Ranks 4-5 existed), Ranks 4-5
    // (about 1.3x / 1.5x of Rank 3) for the endgame. Level 255 can't be reached, so Ranks 4-5 are GM-only
    // (.perk rank) until a way to earn them is built. Fixed parts (thresholds, durations, drawbacks) repeat
    // the same value at every rank. Levels: Unbound.Perks.<Key>.RankLevels.
    constexpr char const* RANK_LEVELS = "1, 30, 60, 255, 255";
    struct RankedPerkDef
    {
        uint32 perk;
        char const* key;
        std::vector<std::pair<char const*, char const*>> stats; // stat name, default value per rank
        char const* levels = RANK_LEVELS;                       // default Unbound.Perks.<Key>.RankLevels
    };
    constexpr char const* PLUS_10 = "4, 7, 10, 13, 15";  // a +10% perk: 0.4x / 0.7x / 1x / 1.3x / 1.5x
    constexpr char const* PLUS_15 = "6, 10, 15, 19, 22";
    std::vector<RankedPerkDef> const RANKED_PERKS = {
        { PERK_CYCLIC_POWER,           "CyclicPower",           { { "High", "10, 15, 20, 25, 30" } } },
        { PERK_CRITICAL_UNDERSTANDING, "CriticalUnderstanding", { { "Max", "8, 14, 20, 26, 30" } } },
        { PERK_DEFENSIVE_SACRIFICE,    "DefensiveSacrifice",    { { "StatPercent", PLUS_10 } } },
        { PERK_DESPERATE_POWER,        "DesperatePower",        { { "Damage", PLUS_10 } } },
        { PERK_BLOCK_CAPPING,          "BlockCapping",          { { "Max", PLUS_10 } } },
        { PERK_DODGE_CAPPING,          "DodgeCapping",          { { "Max", PLUS_10 } } },
        { PERK_PARRY_CAPPING,          "ParryCapping",          { { "Max", PLUS_10 } } },
        { PERK_HASTE_CAPPING,          "HasteCapping",          { { "Max", PLUS_10 } } },
        { PERK_PET_ENCOURAGEMENT,      "PetEncouragement",      { { "Percent", PLUS_15 } } },
        { PERK_ROLLING_MOMENTUM,       "RollingMomentum",       { { "Max", PLUS_10 } } },
        { PERK_TUNNEL_VISION,          "TunnelVision",          { { "Bonus", PLUS_10 } } },
        { PERK_COLLATERAL_DAMAGE,      "CollateralDamage",      { { "Bonus", PLUS_10 } } },
        { PERK_GIANT_SLAYER,           "GiantSlayer",           { { "Percent", PLUS_10 } } },
        { PERK_MERCILESS,              "Merciless",             { { "Percent", PLUS_15 } } },
        { PERK_PRESSURE,               "Pressure",              { { "Stacks", PLUS_10 } } },
        { PERK_CHAOS,                  "Chaos",                 { { "Chance", PLUS_10 } } },
        { PERK_POWER_CONVERSION,       "PowerConversion",       { { "Max", PLUS_10 } } },
        { PERK_HEALING_POWAH,          "HealingPowah",          { { "Percent", PLUS_10 } } },
        { PERK_SHADOW_MASTERY,         "ShadowMastery",         { { "Percent", PLUS_10 } } },
        { PERK_HOLY_MASTERY,           "HolyMastery",           { { "Percent", PLUS_10 } } },
        { PERK_ARCANE_MASTERY,         "ArcaneMastery",         { { "Percent", PLUS_10 } } },
        { PERK_NATURE_MASTERY,         "NatureMastery",         { { "Percent", PLUS_10 } } },
        { PERK_FIRE_MASTERY,           "FireMastery",           { { "Percent", PLUS_10 } } },
        { PERK_FROST_MASTERY,          "FrostMastery",          { { "Percent", PLUS_10 } } },
        { PERK_PHYSICAL_MASTERY,       "PhysicalMastery",       { { "Percent", PLUS_10 } } },
        { PERK_IRON_WILL,            "IronWill",            { { "Percent", "10, 20, 30, 35, 40" } } },
        { PERK_LONGER_LEGS,          "LongerLegs",          { { "RunSpeed", "4, 7, 10, 13, 15" }, { "MountSpeed", "4, 7, 10, 13, 15" },
                                                              { "SwimSpeed", "20, 35, 50, 65, 75" }, { "FallDamage", "20, 35, 50, 65, 75" } } },
        { PERK_PLANTED_FEET,         "PlantedFeet",         { { "Health", "0.5, 0.75, 1, 1.3, 1.5" }, { "Mana", "0.25, 0.4, 0.5, 0.65, 0.75" },
                                                              { "Delay", "3, 3, 3, 3, 3" } } },
        { PERK_RELENTLESS_PURSUIT,   "RelentlessPursuit",   { { "Speed", "15, 25, 35, 45, 50" }, { "Duration", "10, 10, 10, 10, 10" } } },
        { PERK_VAMPIRISM,            "Vampirism",           { { "Percent", "3, 4, 5, 6.5, 7.5" } } },
        { PERK_SOUL_DRAIN,           "SoulDrain",           { { "Percent", "6, 8, 10, 13, 15" }, { "HealingTaken", "20, 20, 20, 20, 20" } } },
        { PERK_PET_REPLENISHMENT,    "PetReplenishment",    { { "Percent", "20, 35, 50, 65, 75" } } },
        { PERK_PETS_ROAR,            "PetsRoar",            { { "Percent", "100, 200, 300, 400, 450" } } },
        { PERK_SILENT_KILLER,        "SilentKiller",        { { "Percent", "20, 35, 50, 65, 75" } } },
        { PERK_UNBREAKABLE_PRESENCE, "UnbreakablePresence", { { "Percent", "50, 100, 150, 200, 225" } } },
        { PERK_STEADY_HANDS,         "SteadyHands",         { { "Pushback", "30, 50, 70, 80, 90" }, { "Lockout", "10, 20, 30, 35, 40" } } },
        { PERK_MANA_LEECH,           "ManaLeech",           { { "Percent", "1, 1.5, 2, 2.5, 3" } } },
        { PERK_GREATER_BULWARK,      "GreaterBulwark",      { { "Efficiency", "100, 110, 120, 125, 130" } } },
        { PERK_EVASIVE_MANEUVERS,    "EvasiveManeuvers",    { { "Efficiency", "100, 110, 120, 125, 130" } } },
        { PERK_PARRY_KING,           "ParryKing",           { { "Efficiency", "100, 110, 120, 125, 130" } } },
        { PERK_REINFORCED_ARMOR,     "ReinforcedArmor",     { { "Percent", "4, 7, 10, 13, 15" } } },
        { PERK_SPELLWARDED,          "Spellwarded",         { { "Percent", "4, 7, 10, 13, 15" } } },
        { PERK_STOICISM,             "Stoicism",            { { "Percent", "8, 14, 20, 26, 30" } } },
        { PERK_DEFENSIVE_MOMENTUM,   "DefensiveMomentum",   { { "Max", "5, 7.5, 10, 13, 15" }, { "ResetAfter", "2, 2, 2, 2, 2" } } },
        { PERK_FORTRESS,             "Fortress",            { { "Max", "5, 7.5, 10, 13, 15" }, { "ResetAfter", "3, 3, 3, 3, 3" } } },
        { PERK_JUGGERNAUT,           "Juggernaut",          { { "Cap", "40, 35, 30, 27, 25" }, { "Cooldown", "3, 3, 3, 3, 3" } } },
        { PERK_COUNTERWEIGHT,        "Counterweight",       { { "Percent", "10, 15, 20, 26, 30" } } },
        { PERK_TITANS_RESOLVE,       "TitansResolve",       { { "Max", "5, 7.5, 10, 13, 15" } } },
        { PERK_SECOND_WIND,          "SecondWind",          { { "Threshold", "15, 15, 15, 15, 15" }, { "Heal", "1, 1.5, 2, 2.6, 3" },
                                                              { "Duration", "5, 5, 5, 5, 5" } } },
        { PERK_HARDENED_FLESH,       "HardenedFlesh",       { { "Threshold", "10, 10, 10, 10, 10" }, { "Percent", "10, 15, 20, 26, 30" } } },
        { PERK_PETS_BLESSING,        "PetsBlessing",        { { "Percent", "10, 15, 20, 26, 30" } } },
        { PERK_SHIELD_WALL_TRAINING, "ShieldWallTraining",  { { "PerStack", "0.5, 0.75, 1, 1.3, 1.5" }, { "Stacks", "5, 5, 5, 5, 5" },
                                                              { "Duration", "5, 5, 5, 5, 5" } } },
        { PERK_SURVIVAL_INSTINCT,    "SurvivalInstinct",    { { "Below", "30, 30, 30, 30, 30" }, { "Percent", "8, 12, 15, 19, 22" } } },
        { PERK_VITAL_RESERVE,        "VitalReserve",        { { "Percent", "4, 7, 10, 13, 15" } } },
        { PERK_ENDURING,             "Enduring",            { { "Percent", "4, 7, 10, 13, 15" } } },
        { PERK_THORNMAIL,            "Thornmail",           { { "Percent", "10, 20, 30, 40, 45" } } },
        { PERK_HEAVY_FRAME,          "HeavyFrame",          { { "Percent", "5, 10, 15, 19, 22" } } },
    };

    // Server-only passive spells (data/sql/db-world/unbound_perks_utility_spells.sql). Passive auras are never
    // sent to the client, so they need no client patch; the amounts are set here from the perk's rank.
    constexpr uint32 SPELL_PERK_MOVEMENT     = 200210;  // run speed, mounted speed, swim speed (%)
    constexpr uint32 SPELL_PERK_PURSUIT      = 200211;  // run speed (%), timed from the code
    constexpr uint32 SPELL_PERK_THREAT       = 200212;  // threat (%), all schools
    constexpr uint32 SPELL_PERK_STEADY_HANDS = 200213;  // pushback reduction (%), interrupt and silence duration (%)
    // data/sql/db-world/unbound_perks_defensive_spells.sql
    constexpr uint32 SPELL_PERK_VITALITY     = 200214;  // maximum health (%), armor (%)
    constexpr uint32 SPELL_PERK_DEFENSE_PROC = 200215;  // procs on melee hits/dodges/parries/blocks taken
    constexpr uint32 SPELL_DAMAGE_SHIELD     = 59653;   // the warrior's Damage Shield damage (Thornmail's hit)

    // Class perks: the class each one belongs to. The server refuses a class perk for any other class.
    std::unordered_map<uint32, uint8> const CLASS_PERKS = {
        { PERK_RETRIBUTION, CLASS_PALADIN },
    };

    // Retribution
    constexpr uint32 SPELL_CRUSADER_STRIKE = 35395;
    constexpr uint32 SPELL_EXORCISM_RANK_1 = 879;
    constexpr uint32 SPELL_RIGHTEOUS_VENGEANCE_DOT = 61840;
    constexpr int32 DIVINE_STORM_MAX_TARGETS = 6;     // normally 4
    constexpr float JUDGEMENT_SPREAD_RANGE = 10.0f;
    constexpr uint32 JUDGEMENT_SPREAD_TARGETS = 4;    // extra enemies besides the target
    constexpr float EXPLOSION_RANGE = 8.0f;
    constexpr uint32 EXPLOSION_MAX_TARGETS = 5;
    constexpr float EXORCIST_EXTRA_SCALING = 0.15f;   // 30% wanted, Exorcism already has 15% (spell_bonus_data)
    constexpr float SWORD_LIGHT_HOLY = 1.15f;         // +15%
    constexpr float SWORD_LIGHT_PHYSICAL = 1.10f;     // +10%

    constexpr char const* PREFIX = "UBPERK";
    // Categories with a limit on active perks (the addon uses the same limits, CATEGORIES in PerkData.lua).
    struct CategoryLimit
    {
        uint32 first;
        uint32 last;
        uint32 max;
        char const* name;
    };
    constexpr CategoryLimit CATEGORY_LIMITS[] = {
        { 101, 199, 5, "Offensive" },
        { 201, 299, 3, "Defensive" },
        { 301, 399, 3, "Utility" },
    };

    CategoryLimit const* LimitOf(uint32 perk)
    {
        for (CategoryLimit const& limit : CATEGORY_LIMITS)
            if (perk >= limit.first && perk <= limit.last)
                return &limit;
        return nullptr;
    }

    uint32 CountIn(std::set<uint32> const& perks, CategoryLimit const& limit)
    {
        return uint32(std::count_if(perks.begin(), perks.end(),
            [&limit](uint32 perk) { return perk >= limit.first && perk <= limit.last; }));
    }

    // An active perk from this one's exclusive group (at most one can be active), or 0.
    uint32 ActivePartner(std::set<uint32> const& perks, uint32 perk)
    {
        for (std::vector<uint32> const& group : EXCLUSIVE_GROUPS)
            if (std::find(group.begin(), group.end(), perk) != group.end())
                for (uint32 other : group)
                    if (other != perk && perks.count(other))
                        return other;
        return 0;
    }

    // False for a class perk of another class.
    bool CanUsePerk(Player const* player, uint32 perk)
    {
        auto itr = CLASS_PERKS.find(perk);
        return itr == CLASS_PERKS.end() || player->getClass() == itr->second;
    }

    constexpr uint32 STAT_REFRESH_MS = 2000;

    // Offensive perks: the numbers that grow with the rank are in RANKED_PERKS (mod_unbound.conf); these are
    // the fixed parts (drawbacks, caps, steps), which stay the same at every rank.
    constexpr uint32 CYCLE_MS = 25000;               // Cyclic Power period
    constexpr float CYCLE_LOW = -10.0f;              // Cyclic Power: the wave's low point (%); the high is ranked
    constexpr float SACRIFICE_DAMAGE_TAKEN = 1.10f;  // Defensive Sacrifice (the AP/SP share is ranked)
    constexpr uint32 SPELL_CRIT_DAMAGE_AURA = 58670; // "Prey on the Weak": one aura, +X% crit damage, all schools
    constexpr float CRIT_UNDERSTANDING_FLOOR = 25.0f;  // Critical Understanding: +1% crit damage per 1% crit above this
    constexpr float DESPERATE_RESIST_PCT = 0.50f;    // Desperate Power (the damage is ranked)
    constexpr float AVOIDANCE_CAP = 20.0f;           // Block/Dodge/Parry Capping: cap (%)
    constexpr float AVOIDANCE_STEP = 1.0f;           // ... +1% damage per this much above the cap (max is ranked)
    constexpr float HASTE_CAP = 5.0f;                // Haste Capping: +1% damage per 1% haste above this
    constexpr float HASTE_DAMAGE_TAKEN = 1.05f;
    constexpr int32 MOMENTUM_STEP = 1;               // Rolling Momentum: % per second (max is ranked)
    constexpr float FOCUS_PENALTY = 0.90f;           // Tunnel Vision / Collateral Damage (the bonus is ranked)
    constexpr int32 PRESSURE_STEP = 1;               // % per stack (max stacks are ranked)
    constexpr float CHAOS_MULTIPLIER = 1.50f;        // (the chance is ranked)
    constexpr float POWER_CONVERSION_STAT = 100.0f;  // +1% per this much of the highest base stat (max is ranked)

    enum class HitKind { Melee, Spell, Periodic };

    struct PressureTrack
    {
        ObjectGuid target;
        uint32 stacks = 0;
    };
    constexpr uint8 MAGIC_SCHOOLS[] = { SPELL_SCHOOL_FIRE, SPELL_SCHOOL_NATURE, SPELL_SCHOOL_FROST,
                                        SPELL_SCHOOL_SHADOW, SPELL_SCHOOL_ARCANE };

    // Defensive Momentum / Fortress: stacks of one unit (the player, or their pet), one per second of moving
    // (Momentum) or standing still (Fortress), up to STANCE_MAX_STACKS.
    constexpr uint32 STANCE_MAX_STACKS = 10;
    struct StanceTrack
    {
        ObjectGuid unit;
        uint32 movingMs = 0;    // time moving without a stop
        uint32 stillMs = 0;     // time standing still without moving
        uint32 tickMs = 0;
        uint32 stacks = 0;
    };

    // Per-unit state of the hit-based Defensive perks (the player, or their pet).
    struct DefenseTrack
    {
        ObjectGuid unit;
        uint32 juggernautCooldownMs = 0;  // Juggernaut can cap a hit again when this reaches 0
        uint32 secondWindMs = 0;          // Second Wind: healing time left
        uint32 secondWindTickMs = 0;
        bool counterweight = false;       // Counterweight: the next hit taken is reduced
        uint32 shieldWallStacks = 0;      // Shield Wall Training
        uint32 shieldWallMs = 0;          // time left on the stacks
    };

    struct PerkState
    {
        std::set<uint32> active;

        // Rapid Recovery
        uint32 outOfCombatMs = 0;
        uint32 tickMs = 0;

        // stat-based perks are re-evaluated every STAT_REFRESH_MS
        uint32 statTimer = 0;
        uint32 cycleStartMs = 0;    // Cyclic Power phase
        int32 sacrificeAP = 0;      // attack power currently added by Defensive Sacrifice
        int32 sacrificeSP = 0;      // spell power currently added by Defensive Sacrifice
        int32 critBonus = 0;        // Critical Understanding bonus currently applied (%)
        int32 desperateResist[MAX_SPELL_SCHOOL] = {};  // resistance currently removed by Desperate Power
        int32 cappingBonus = 0;     // Block/Dodge/Parry/Haste Capping damage bonus (%), summed
        float powerConversion = 0;  // Power Conversion bonus (%)
        std::unordered_map<ObjectGuid, PressureTrack> pressure; // Pressure: per attacking unit (player, pets)
        std::map<uint32, uint8> rankOverride;  // perk ranks set by a GM (.perk rank)
        int32 momentum = 0;         // Rolling Momentum bonus (%)
        uint32 momentumTimer = 0;
        uint32 stillMs = 0;         // Planting your legs: time standing still
        uint32 stillTickMs = 0;
        StanceTrack selfStance;     // Defensive Momentum / Fortress
        StanceTrack petStance;
        DefenseTrack selfDefense;   // Juggernaut, Second Wind, Counterweight, Shield Wall Training
        DefenseTrack petDefense;
    };

    std::unordered_map<ObjectGuid::LowType, PerkState> sStates;

    PerkState* StateOf(Player const* player)
    {
        auto itr = sStates.find(player->GetGUID().GetCounter());
        return itr == sStates.end() ? nullptr : &itr->second;
    }

    // The player whose perks apply to this unit: the player or the owner of a pet, guardian or totem.
    PerkState* PerkOwnerState(Unit const* unit)
    {
        if (!unit)
            return nullptr;
        Player* owner = unit->GetCharmerOrOwnerPlayerOrPlayerItself();
        return owner ? StateOf(owner) : nullptr;
    }

    bool Has(PerkState const* state, uint32 perk)
    {
        return state && state->active.count(perk);
    }

    // A ranked perk's number at the character's rank (defined with the perk ranks below).
    float RankValue(Player const* player, PerkState const& state, uint32 perk, size_t stat);
    float OwnerRankValue(Unit const* unit, uint32 perk, size_t stat);

    // "+x%" as a multiplier
    float Bonus(float percent)
    {
        return 1.0f + percent / 100.0f;
    }

    // ------------------------------------------------------------------ damage multipliers
    float CyclicMultiplier(PerkState const* state, float high)
    {
        // a smooth wave over CYCLE_MS between CYCLE_LOW and the rank's high point (Rank 3: -10% .. +20%)
        uint32 t = (getMSTime() - state->cycleStartMs) % CYCLE_MS;
        float center = 1.0f + (CYCLE_LOW + high) / 200.0f;
        float amplitude = (high - CYCLE_LOW) / 200.0f;
        return center + amplitude * std::sin(2.0f * float(M_PI) * float(t) / float(CYCLE_MS));
    }

    bool IsAreaDamage(SpellInfo const* spellInfo)
    {
        if (!spellInfo)
            return false; // melee swings
        if (spellInfo->IsAffectingArea())
            return true;
        for (SpellEffectInfo const& effect : spellInfo->GetEffects())
            if (effect.IsEffect() && effect.ChainTarget > 1)
                return true;
        return false;
    }

    bool IsBoss(Unit const* unit)
    {
        Creature const* creature = unit ? unit->ToCreature() : nullptr;
        return creature && (creature->isWorldBoss() || creature->IsDungeonBoss());
    }

    float DamageDoneMultiplier(Unit const* attacker, Unit const* victim, SpellInfo const* spellInfo)
    {
        PerkState const* state = PerkOwnerState(attacker);
        if (!state)
            return 1.0f;
        float mult = 1.0f;
        if (Has(state, PERK_CYCLIC_POWER))
            mult *= CyclicMultiplier(state, OwnerRankValue(attacker, PERK_CYCLIC_POWER, 0));
        if (Has(state, PERK_DESPERATE_POWER))
            mult *= Bonus(OwnerRankValue(attacker, PERK_DESPERATE_POWER, 0));
        if (state->cappingBonus)
            mult *= 1.0f + state->cappingBonus / 100.0f;
        if (Has(state, PERK_ROLLING_MOMENTUM) && state->momentum)
            mult *= 1.0f + state->momentum / 100.0f;
        if (Has(state, PERK_PET_ENCOURAGEMENT) && !attacker->IsPlayer())  // pets, guardians, totems
            mult *= Bonus(OwnerRankValue(attacker, PERK_PET_ENCOURAGEMENT, 0));
        if (Has(state, PERK_TUNNEL_VISION) || Has(state, PERK_COLLATERAL_DAMAGE))
        {
            bool area = IsAreaDamage(spellInfo);
            if (Has(state, PERK_TUNNEL_VISION))
                mult *= area ? FOCUS_PENALTY : Bonus(OwnerRankValue(attacker, PERK_TUNNEL_VISION, 0));
            if (Has(state, PERK_COLLATERAL_DAMAGE))
                mult *= area ? Bonus(OwnerRankValue(attacker, PERK_COLLATERAL_DAMAGE, 0)) : FOCUS_PENALTY;
        }
        if (Has(state, PERK_GIANT_SLAYER) && IsBoss(victim))
            mult *= Bonus(OwnerRankValue(attacker, PERK_GIANT_SLAYER, 0));
        // School masteries; melee swings (no spell) are Physical.
        static constexpr std::pair<uint32, uint32> MASTERIES[] = {
            { PERK_PHYSICAL_MASTERY, SPELL_SCHOOL_MASK_NORMAL }, { PERK_HOLY_MASTERY,   SPELL_SCHOOL_MASK_HOLY   },
            { PERK_FIRE_MASTERY,     SPELL_SCHOOL_MASK_FIRE   }, { PERK_NATURE_MASTERY, SPELL_SCHOOL_MASK_NATURE },
            { PERK_FROST_MASTERY,    SPELL_SCHOOL_MASK_FROST  }, { PERK_SHADOW_MASTERY, SPELL_SCHOOL_MASK_SHADOW },
            { PERK_ARCANE_MASTERY,   SPELL_SCHOOL_MASK_ARCANE },
        };
        uint32 schools = spellInfo ? uint32(spellInfo->GetSchoolMask()) : uint32(SPELL_SCHOOL_MASK_NORMAL);
        for (auto const& [perk, mask] : MASTERIES)
            if ((schools & mask) && Has(state, perk))
                mult *= Bonus(OwnerRankValue(attacker, perk, 0));

        // Retribution - By Sword & Light (the Paladin's own damage)
        if (Has(state, PERK_RETRIBUTION) && attacker->IsPlayer())
        {
            if (schools & SPELL_SCHOOL_MASK_HOLY)
                mult *= SWORD_LIGHT_HOLY;
            else if (schools & SPELL_SCHOOL_MASK_NORMAL)
                mult *= SWORD_LIGHT_PHYSICAL;
        }
        return mult;
    }

    // ------------------------------------------------------------------ Retribution helpers
    bool HasRetribution(Unit const* unit)
    {
        return unit && unit->IsPlayer() && Has(StateOf(unit->ToPlayer()), PERK_RETRIBUTION);
    }

    bool IsExorcism(SpellInfo const* spellInfo)
    {
        return spellInfo && sSpellMgr->GetFirstSpellInChain(spellInfo->Id) == SPELL_EXORCISM_RANK_1;
    }

    // The highest Exorcism rank the player's level allows.
    uint32 ExorcismFor(Player const* player)
    {
        uint32 best = 0;
        for (uint32 id = SPELL_EXORCISM_RANK_1; id; id = sSpellMgr->GetNextSpellInChain(id))
            if (SpellInfo const* info = sSpellMgr->GetSpellInfo(id))
                if (info->SpellLevel <= player->GetLevel())
                    best = id;
        return best;
    }

    std::list<Unit*> EnemiesNear(WorldObject* center, Unit* caster, float range)
    {
        std::list<Unit*> units;
        Acore::AnyUnfriendlyUnitInObjectRangeCheck check(center, caster, range);
        Acore::UnitListSearcher<Acore::AnyUnfriendlyUnitInObjectRangeCheck> searcher(center, units, check);
        Cell::VisitObjects(center, searcher, range);
        units.remove_if([caster](Unit* u) { return !caster->IsValidAttackTarget(u); });
        return units;
    }

    // Righteous Explosion: deal what is left of the dying enemy's Righteous Vengeance around it.
    void ScheduleRighteousExplosion(Unit* victim)
    {
        for (AuraEffect const* eff : victim->GetAuraEffectsByType(SPELL_AURA_PERIODIC_DAMAGE))
        {
            if (eff->GetId() != SPELL_RIGHTEOUS_VENGEANCE_DOT)
                continue;
            Unit* caster = eff->GetCaster();
            if (!HasRetribution(caster))
                continue;
            int32 ticksLeft = eff->GetTotalTicks() - int32(eff->GetTickNumber());
            uint32 remaining = uint32(std::max(0, eff->GetAmount()) * std::max(0, ticksLeft));
            if (!remaining)
                continue;
            ObjectGuid victimGuid = victim->GetGUID();
            // after the killing blow has been dealt, never inside it
            caster->m_Events.AddEventAtOffset([caster, victimGuid, remaining]()
            {
                Unit* corpse = ObjectAccessor::GetUnit(*caster, victimGuid);
                SpellInfo const* spellInfo = sSpellMgr->GetSpellInfo(SPELL_RIGHTEOUS_VENGEANCE_DOT);
                if (!corpse || !spellInfo || !caster->IsInWorld() || corpse->GetMap() != caster->GetMap())
                    return;
                std::list<Unit*> enemies = EnemiesNear(corpse, caster, EXPLOSION_RANGE);
                enemies.sort(Acore::ObjectDistanceOrderPred(corpse));
                uint32 hits = 0;
                for (Unit* enemy : enemies)
                {
                    if (enemy == corpse || ++hits > EXPLOSION_MAX_TARGETS)
                        continue;
                    SpellNonMeleeDamage damageInfo(caster, enemy, spellInfo, SPELL_SCHOOL_MASK_HOLY);
                    damageInfo.damage = remaining;
                    caster->SendSpellNonMeleeDamageLog(&damageInfo);
                    caster->DealSpellDamage(&damageInfo, true);
                }
            }, 1ms);
        }
    }

    // ------------------------------------------------------------------ healing
    // The core calls ModifyHealReceived with (target, healer) for heal-over-time ticks but with
    // (healer, target) for direct heals (Unit::HealBySpell). A heal tick always calls
    // ModifyPeriodicDamageAurasTick first with the same heal value, so that call is remembered here
    // to tell the two apart.
    struct PendingHealTick
    {
        uint32 const* amount = nullptr;
        Unit const* target = nullptr;
        SpellInfo const* spellInfo = nullptr;
    };
    PendingHealTick sPendingHealTick;

    void ApplyHealingBonus(Unit const* healer, uint32& heal)
    {
        PerkState const* state = PerkOwnerState(healer);
        if (heal && Has(state, PERK_HEALING_POWAH))
            heal = uint32(std::round(float(heal) * Bonus(OwnerRankValue(healer, PERK_HEALING_POWAH, 0))));
    }

    float OwnerRankValue(Unit const* unit, uint32 perk, size_t stat);

    // "-x%" as a multiplier (never below 0)
    float Reduction(float percent)
    {
        return std::max(0.0f, 1.0f - percent / 100.0f);
    }

    float DamageTakenMultiplier(Unit const* victim, SpellInfo const* spellInfo, HitKind kind)
    {
        PerkState const* state = PerkOwnerState(victim);
        if (!state)
            return 1.0f;
        float mult = 1.0f;
        if (Has(state, PERK_DEFENSIVE_SACRIFICE))
            mult *= SACRIFICE_DAMAGE_TAKEN;
        if (Has(state, PERK_HASTE_CAPPING))
            mult *= HASTE_DAMAGE_TAKEN;

        // Reinforced Armor (physical) / Spellwarded (magic): melee swings are physical, a spell is physical if
        // its school includes Physical
        bool physical = !spellInfo || (spellInfo->GetSchoolMask() & SPELL_SCHOOL_MASK_NORMAL);
        if (physical && Has(state, PERK_REINFORCED_ARMOR))
            mult *= Reduction(OwnerRankValue(victim, PERK_REINFORCED_ARMOR, 0));
        if (!physical && Has(state, PERK_SPELLWARDED))
            mult *= Reduction(OwnerRankValue(victim, PERK_SPELLWARDED, 0));
        if (kind == HitKind::Periodic && Has(state, PERK_STOICISM))
            mult *= Reduction(OwnerRankValue(victim, PERK_STOICISM, 0));

        // Defensive Momentum / Fortress: the victim's own stacks
        for (uint32 perk : { PERK_DEFENSIVE_MOMENTUM, PERK_FORTRESS })
            if (Has(state, perk))
            {
                StanceTrack const& track = victim->IsPlayer() ? state->selfStance : state->petStance;
                if (track.unit == victim->GetGUID() && track.stacks)
                    mult *= Reduction(OwnerRankValue(victim, perk, 0) * track.stacks / STANCE_MAX_STACKS);
            }

        // Titan's Resolve: up to the max as health runs out; Survival Instinct: a flat reduction below a health %
        float missingPct = 100.0f - victim->GetHealthPct();
        if (Has(state, PERK_TITANS_RESOLVE))
            mult *= Reduction(OwnerRankValue(victim, PERK_TITANS_RESOLVE, 0) * missingPct / 100.0f);
        if (Has(state, PERK_SURVIVAL_INSTINCT) &&
            victim->GetHealthPct() < OwnerRankValue(victim, PERK_SURVIVAL_INSTINCT, 0))
            mult *= Reduction(OwnerRankValue(victim, PERK_SURVIVAL_INSTINCT, 1));
        // Pet's Blessing: the pet only
        if (!victim->IsPlayer() && Has(state, PERK_PETS_BLESSING))
            mult *= Reduction(OwnerRankValue(victim, PERK_PETS_BLESSING, 0));
        return mult;
    }

    // The hit-based Defensive perks' state for this unit (the player or their current pet), reset when the pet
    // changes.
    DefenseTrack& DefenseOf(PerkState& state, Unit const* unit)
    {
        DefenseTrack& track = unit->IsPlayer() ? state.selfDefense : state.petDefense;
        if (track.unit != unit->GetGUID())
        {
            track = DefenseTrack();
            track.unit = unit->GetGUID();
        }
        return track;
    }

    // Perks that depend on the kind of hit or change state with every hit.
    float HitMultiplier(Unit const* attacker, Unit const* victim, HitKind kind)
    {
        PerkState* state = PerkOwnerState(attacker);
        if (!state || state->active.empty())
            return 1.0f;
        float mult = 1.0f;

        if (kind == HitKind::Periodic && Has(state, PERK_MERCILESS))
            mult *= Bonus(OwnerRankValue(attacker, PERK_MERCILESS, 0));

        if (kind == HitKind::Spell && Has(state, PERK_CHAOS) && roll_chance_f(OwnerRankValue(attacker, PERK_CHAOS, 0)))
            mult *= CHAOS_MULTIPLIER;

        if (state->powerConversion > 0.0f)
            mult *= 1.0f + state->powerConversion / 100.0f;

        if (Has(state, PERK_PRESSURE))
        {
            PressureTrack& track = state->pressure[attacker->GetGUID()];
            if (track.target != victim->GetGUID())
            {
                track.target = victim->GetGUID();
                track.stacks = 0;
            }
            mult *= 1.0f + (PRESSURE_STEP * track.stacks) / 100.0f;
            if (kind != HitKind::Periodic)
                track.stacks = std::min(uint32(OwnerRankValue(attacker, PERK_PRESSURE, 0)), track.stacks + 1);
        }
        return mult;
    }

    template <typename T>
    void ApplyMultipliers(Unit* victim, Unit* attacker, T& damage, SpellInfo const* spellInfo, HitKind kind)
    {
        if (damage <= 0 || !attacker || !victim || attacker == victim)
            return;
        float mult = DamageDoneMultiplier(attacker, victim, spellInfo) * HitMultiplier(attacker, victim, kind) *
                     DamageTakenMultiplier(victim, spellInfo, kind);
        if (mult != 1.0f)
            damage = T(std::max(0.0f, std::round(float(damage) * mult)));
    }

    // ------------------------------------------------------------------ stat-based perks
    float HighestCritChance(Player* player)
    {
        float crit = std::max(player->GetFloatValue(PLAYER_CRIT_PERCENTAGE), player->GetFloatValue(PLAYER_RANGED_CRIT_PERCENTAGE));
        for (uint8 school = SPELL_SCHOOL_HOLY; school < MAX_SPELL_SCHOOL; ++school)
            crit = std::max(crit, player->GetFloatValue(PLAYER_SPELL_CRIT_PERCENTAGE1 + school));
        return crit;
    }

    void SetCritBonus(Player* player, PerkState& state, int32 bonus)
    {
        if (bonus == state.critBonus)
            return;
        player->RemoveAurasDueToSpell(SPELL_CRIT_DAMAGE_AURA);
        state.critBonus = 0;
        if (bonus <= 0)
            return;
        player->CastCustomSpell(SPELL_CRIT_DAMAGE_AURA, SPELLVALUE_BASE_POINT0, bonus, player, true);
        if (Aura* aura = player->GetAura(SPELL_CRIT_DAMAGE_AURA))
        {
            aura->SetMaxDuration(-1);
            aura->SetDuration(-1);
            state.critBonus = bonus;
        }
    }

    int32 SpellPower(Player* player)
    {
        int32 best = player->SpellBaseHealingBonusDone(SPELL_SCHOOL_MASK_ALL);
        for (uint8 school = SPELL_SCHOOL_HOLY; school < MAX_SPELL_SCHOOL; ++school)
            best = std::max(best, player->SpellBaseDamageBonusDone(SpellSchoolMask(1 << school)));
        return best;
    }

    void SetSacrificeBonus(Player* player, PerkState& state, int32 ap, int32 sp)
    {
        if (ap != state.sacrificeAP)
        {
            if (state.sacrificeAP)
            {
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER, TOTAL_VALUE, float(state.sacrificeAP), false);
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, float(state.sacrificeAP), false);
            }
            if (ap)
            {
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER, TOTAL_VALUE, float(ap), true);
                player->HandleStatFlatModifier(UNIT_MOD_ATTACK_POWER_RANGED, TOTAL_VALUE, float(ap), true);
            }
            state.sacrificeAP = ap;
            player->UpdateAttackPowerAndDamage(false);
            player->UpdateAttackPowerAndDamage(true);
        }
        if (sp != state.sacrificeSP)
        {
            if (state.sacrificeSP)
                player->ApplySpellPowerBonus(state.sacrificeSP, false);
            if (sp)
                player->ApplySpellPowerBonus(sp, true);
            state.sacrificeSP = sp;
        }
    }

    void SetDesperateResist(Player* player, PerkState& state, uint8 school, int32 amount)
    {
        if (amount == state.desperateResist[school])
            return;
        UnitMods mod = UnitMods(UNIT_MOD_RESISTANCE_START + school);
        if (state.desperateResist[school])
            player->HandleStatFlatModifier(mod, TOTAL_VALUE, float(state.desperateResist[school]), true);   // give back
        if (amount)
            player->HandleStatFlatModifier(mod, TOTAL_VALUE, float(amount), false);                         // take away
        state.desperateResist[school] = amount;
    }

    // Block/Dodge/Parry/Haste Capping: +1% damage per AVOIDANCE_STEP above the cap, up to the rank's maximum
    int32 OverCapBonus(float chance, float max, float cap = AVOIDANCE_CAP)
    {
        return std::min(int32(max), int32(std::max(0.0f, chance - cap) / AVOIDANCE_STEP));
    }

    void RefreshUtilityAuras(Player* player, PerkState const& state);

    void RefreshStatPerks(Player* player, PerkState& state)
    {
        // Desperate Power: remove 50% of each magic resistance (not counting what it already removed)
        for (uint8 school : MAGIC_SCHOOLS)
        {
            int32 amount = 0;
            if (Has(&state, PERK_DESPERATE_POWER))
                amount = int32((int32(player->GetResistance(SpellSchools(school))) + state.desperateResist[school]) * DESPERATE_RESIST_PCT);
            SetDesperateResist(player, state, school, amount);
        }

        // Block/Dodge/Parry Capping (the character sheet shows the uncapped chance)
        auto rank = [&](uint32 perk) { return RankValue(player, state, perk, 0); };
        int32 capping = 0;
        if (Has(&state, PERK_BLOCK_CAPPING))
            capping += OverCapBonus(player->GetFloatValue(PLAYER_BLOCK_PERCENTAGE), rank(PERK_BLOCK_CAPPING));
        if (Has(&state, PERK_DODGE_CAPPING))
            capping += OverCapBonus(player->GetFloatValue(PLAYER_DODGE_PERCENTAGE), rank(PERK_DODGE_CAPPING));
        if (Has(&state, PERK_PARRY_CAPPING))
            capping += OverCapBonus(player->GetFloatValue(PLAYER_PARRY_PERCENTAGE), rank(PERK_PARRY_CAPPING));
        if (Has(&state, PERK_HASTE_CAPPING))
        {
            float haste = std::max({ player->GetRatingBonusValue(CR_HASTE_MELEE), player->GetRatingBonusValue(CR_HASTE_RANGED),
                                     player->GetRatingBonusValue(CR_HASTE_SPELL) });
            capping += OverCapBonus(haste, rank(PERK_HASTE_CAPPING), HASTE_CAP);
        }
        state.cappingBonus = capping;

        // Power Conversion
        state.powerConversion = 0.0f;
        if (Has(&state, PERK_POWER_CONVERSION))
        {
            float highest = 0.0f;
            for (uint8 stat = STAT_STRENGTH; stat < MAX_STATS; ++stat)
                highest = std::max(highest, player->GetStat(Stats(stat)));
            state.powerConversion = std::min(rank(PERK_POWER_CONVERSION), std::floor(highest / POWER_CONVERSION_STAT));
        }
        if (!Has(&state, PERK_PRESSURE))
            state.pressure.clear();

        // Critical Understanding
        int32 crit = 0;
        if (Has(&state, PERK_CRITICAL_UNDERSTANDING))
            crit = std::min(int32(rank(PERK_CRITICAL_UNDERSTANDING)),
                            int32(std::max(0.0f, HighestCritChance(player) - CRIT_UNDERSTANDING_FLOOR)));
        SetCritBonus(player, state, crit);

        // Defensive Sacrifice: 10% of current attack power and spell power, not counting its own bonus
        int32 ap = 0, sp = 0;
        if (Has(&state, PERK_DEFENSIVE_SACRIFICE))
        {
            int32 currentAP = int32(player->GetTotalAttackPowerValue(BASE_ATTACK)) - state.sacrificeAP;
            int32 currentSP = SpellPower(player) - state.sacrificeSP;
            float share = rank(PERK_DEFENSIVE_SACRIFICE) / 100.0f;
            ap = std::max(0, int32(currentAP * share));
            sp = std::max(0, int32(currentSP * share));
        }
        SetSacrificeBonus(player, state, ap, sp);

        RefreshUtilityAuras(player, state);
    }

    // ------------------------------------------------------------------ addon messages
    void SendAddon(Player* player, std::string const& text)
    {
        WorldPacket data;
        ChatHandler::BuildChatPacket(data, CHAT_MSG_WHISPER, LANG_ADDON, player, player, std::string(PREFIX) + "\t" + text);
        player->SendDirectMessage(&data);
    }

    void SendState(Player* player, PerkState const& state)
    {
        std::string ids;
        for (uint32 id : state.active)
        {
            if (!ids.empty())
                ids += ",";
            ids += std::to_string(id);
        }
        SendAddon(player, "STATE:" + ids);
    }

    // ------------------------------------------------------------------ perk ranks
    // Ranked perks and their number of ranks.
    std::map<uint32, uint8> RankedPerks()
    {
        std::map<uint32, uint8> ranked = { { PERK_ID_RAPID_RECOVERY, uint8(sRecoveryRanks.size()) } };
        for (auto const& [perk, ranks] : sPerkRanks)
            ranked[perk] = uint8(ranks.values.size());
        return ranked;
    }

    // The highest rank whose level the character has reached (levels[i] reaches rank i + 1).
    uint8 RankForLevel(Player const* player, std::vector<uint32> const& levels)
    {
        uint8 rank = 1;
        for (uint8 i = 0; i < levels.size(); ++i)
            if (player->GetLevel() >= levels[i])
                rank = i + 1;
        return rank;
    }

    // (a direct lookup: the Offensive perks ask for their rank on every hit)
    uint8 MaxRank(uint32 perk)
    {
        if (perk == PERK_ID_RAPID_RECOVERY)
            return uint8(sRecoveryRanks.size());
        auto itr = sPerkRanks.find(perk);
        return itr == sPerkRanks.end() || itr->second.values.empty() ? 1 : uint8(itr->second.values.size());
    }

    // The rank a character has: a GM-set rank, or the highest rank its level reaches.
    uint8 PerkRank(Player const* player, PerkState const& state, uint32 perk)
    {
        uint8 maxRank = MaxRank(perk);
        auto set = state.rankOverride.find(perk);
        if (set != state.rankOverride.end())
            return std::clamp<uint8>(set->second, 1, maxRank);
        if (perk == PERK_ID_RAPID_RECOVERY)
        {
            std::vector<uint32> levels;
            for (RecoveryRank const& r : sRecoveryRanks)
                levels.push_back(r.level);
            return RankForLevel(player, levels);
        }
        auto ranks = sPerkRanks.find(perk);
        if (ranks != sPerkRanks.end())
            return std::min<uint8>(RankForLevel(player, ranks->second.levels), maxRank);
        return 1;
    }

    RecoveryRank const& RecoveryFor(Player const* player, PerkState const& state)
    {
        return sRecoveryRanks[PerkRank(player, state, PERK_ID_RAPID_RECOVERY) - 1];
    }

    // One number of a ranked perk at the character's rank (stat = its position in RANKED_PERKS).
    float RankValue(Player const* player, PerkState const& state, uint32 perk, size_t stat)
    {
        auto ranks = sPerkRanks.find(perk);
        if (ranks == sPerkRanks.end() || ranks->second.values.empty())
            return 0.0f;
        std::vector<float> const& values = ranks->second.values[PerkRank(player, state, perk) - 1];
        return stat < values.size() ? values[stat] : 0.0f;
    }

    // The same for whoever's perks apply to a unit (the player, or the owner of a pet).
    float OwnerRankValue(Unit const* unit, uint32 perk, size_t stat)
    {
        Player const* owner = unit ? unit->GetCharmerOrOwnerPlayerOrPlayerItself() : nullptr;
        PerkState const* state = owner ? StateOf(owner) : nullptr;
        return Has(state, perk) ? RankValue(owner, *state, perk, stat) : 0.0f;
    }

    // RANK:<perk>:<rank>:<max>:<values>, values "a,b,...,level;a,b,...,level" per rank
    void SendRanks(Player* player, PerkState const& state)
    {
        for (auto const& [perk, maxRank] : RankedPerks())
        {
            std::string values;
            if (perk == PERK_ID_RAPID_RECOVERY)
                for (RecoveryRank const& r : sRecoveryRanks)
                    values += (values.empty() ? "" : ";") + std::to_string(r.delayMs) + "," +
                              std::to_string(r.percent) + "," + std::to_string(r.level);
            else if (auto ranks = sPerkRanks.find(perk); ranks != sPerkRanks.end())
                for (size_t i = 0; i < ranks->second.values.size(); ++i)
                {
                    values += values.empty() ? "" : ";";
                    for (float value : ranks->second.values[i])
                        values += Acore::StringFormat("{:g},", value);
                    values += std::to_string(ranks->second.levels[i]);
                }
            SendAddon(player, "RANK:" + std::to_string(perk) + ":" + std::to_string(PerkRank(player, state, perk)) +
                ":" + std::to_string(maxRank) + ":" + values);
        }
    }

    // ------------------------------------------------------------------ utility perk auras
    // Adds, updates or removes one of the server-only perk auras (all amounts 0 = remove).
    Aura* SetPerkAura(Unit* unit, uint32 spellId, std::array<int32, MAX_SPELL_EFFECTS> const& amounts)
    {
        if (!unit)
            return nullptr;
        bool wanted = std::any_of(amounts.begin(), amounts.end(), [](int32 amount) { return amount != 0; });
        Aura* aura = unit->GetAura(spellId);
        if (!wanted)
        {
            if (aura)
                unit->RemoveAurasDueToSpell(spellId);
            return nullptr;
        }
        if (!aura)
            aura = unit->AddAura(spellId, unit);
        if (!aura)
            return nullptr;
        for (uint8 i = 0; i < MAX_SPELL_EFFECTS; ++i)
            if (AuraEffect* effect = aura->GetEffect(i))
                if (effect->GetAmount() != amounts[i])
                    effect->ChangeAmount(amounts[i]);
        return aura;
    }

    // Longer Legs, Pets Roar, Silent Killer, Unbreakable Presence and Steady Hands, on the player and the pet.
    // Called with the stat perks (every STAT_REFRESH_MS while perks are active, and on every change), which
    // also picks up a newly summoned pet.
    void RefreshUtilityAuras(Player* player, PerkState const& state)
    {
        auto value = [&](uint32 perk, size_t stat) {
            return Has(&state, perk) ? int32(RankValue(player, state, perk, stat)) : 0;
        };

        int32 run = value(PERK_LONGER_LEGS, 0);
        int32 swim = value(PERK_LONGER_LEGS, 2);
        SetPerkAura(player, SPELL_PERK_MOVEMENT, { run, value(PERK_LONGER_LEGS, 1), swim });
        int32 threat = value(PERK_UNBREAKABLE_PRESENCE, 0) - value(PERK_SILENT_KILLER, 0);
        SetPerkAura(player, SPELL_PERK_THREAT, { threat, 0, 0 });
        int32 lockout = -value(PERK_STEADY_HANDS, 1);
        SetPerkAura(player, SPELL_PERK_STEADY_HANDS, { value(PERK_STEADY_HANDS, 0), lockout, lockout });
        // Vital Reserve (maximum health) and Heavy Frame (armor), you and your pet
        std::array<int32, MAX_SPELL_EFFECTS> vitality = { value(PERK_VITAL_RESERVE, 0), value(PERK_HEAVY_FRAME, 0), 0 };
        SetPerkAura(player, SPELL_PERK_VITALITY, vitality);
        // the proc aura that tells Counterweight, Shield Wall Training and Thornmail about melee attacks taken
        int32 defenseProc = Has(&state, PERK_COUNTERWEIGHT) || Has(&state, PERK_SHIELD_WALL_TRAINING) ||
                            Has(&state, PERK_THORNMAIL) ? 1 : 0;
        SetPerkAura(player, SPELL_PERK_DEFENSE_PROC, { defenseProc, 0, 0 });

        if (Pet* pet = player->GetPet())
        {
            SetPerkAura(pet, SPELL_PERK_MOVEMENT, { run, 0, swim });
            SetPerkAura(pet, SPELL_PERK_THREAT, { value(PERK_PETS_ROAR, 0), 0, 0 });
            SetPerkAura(pet, SPELL_PERK_VITALITY, vitality);
            SetPerkAura(pet, SPELL_PERK_DEFENSE_PROC, { defenseProc, 0, 0 });
        }
    }

    // Relentless Pursuit: a burst of run speed for the player and the pet after a kill.
    void StartPursuit(Player* player)
    {
        PerkState const* state = StateOf(player);
        if (!Has(state, PERK_RELENTLESS_PURSUIT))
            return;
        int32 speed = int32(RankValue(player, *state, PERK_RELENTLESS_PURSUIT, 0));
        int32 durationMs = int32(RankValue(player, *state, PERK_RELENTLESS_PURSUIT, 1) * IN_MILLISECONDS);
        for (Unit* unit : { static_cast<Unit*>(player), static_cast<Unit*>(player->GetPet()) })
            if (unit && unit->IsAlive())
                if (Aura* aura = SetPerkAura(unit, SPELL_PERK_PURSUIT, { speed, 0, 0 }))
                {
                    aura->SetMaxDuration(durationMs);
                    aura->SetDuration(durationMs);
                }
    }

    void SavePerk(Player* player, uint32 perk, bool on)
    {
        uint32 guid = player->GetGUID().GetCounter();
        if (on)
            CharacterDatabase.Execute("REPLACE INTO `character_unbound_perks` (`guid`, `perk`) VALUES ({}, {})", guid, perk);
        else
            CharacterDatabase.Execute("DELETE FROM `character_unbound_perks` WHERE `guid` = {} AND `perk` = {}", guid, perk);
    }

    void SetPerk(Player* player, PerkState& state, uint32 perk, bool on)
    {
        if (!IMPLEMENTED.count(perk) || on == bool(state.active.count(perk)) || (on && !CanUsePerk(player, perk)))
            return;
        if (on)
        {
            if (uint32 partner = ActivePartner(state.active, perk))
            {
                state.active.erase(partner);
                SavePerk(player, partner, false);
            }
            state.active.insert(perk);
            if (perk == PERK_CYCLIC_POWER)
                state.cycleStartMs = getMSTime();
        }
        else
            state.active.erase(perk);
        SavePerk(player, perk, on);
    }

    void HandleAddonMessage(Player* player, std::string const& text)
    {
        PerkState& state = sStates[player->GetGUID().GetCounter()];

        if (text == "SYNC")
        {
            SendState(player, state);
            SendRanks(player, state);
            return;
        }

        bool isSet = text.rfind("SET:", 0) == 0;
        bool isLoad = text.rfind("LOAD:", 0) == 0;
        if (!isSet && !isLoad)
            return;

        if (player->IsInCombat())
        {
            SendAddon(player, "ERR:You can't change perks in combat.");
            SendState(player, state);
            return;
        }

        if (isSet)
        {
            std::vector<std::string_view> parts = Acore::Tokenize(text, ':', false);
            if (parts.size() == 3)
                if (Optional<uint32> perk = Acore::StringTo<uint32>(parts[1]))
                {
                    bool on = parts[2] == "1";
                    CategoryLimit const* limit = LimitOf(*perk);
                    if (on && !CanUsePerk(player, *perk))
                        SendAddon(player, "ERR:That perk belongs to another class.");
                    else if (on && limit && !state.active.count(*perk) && !ActivePartner(state.active, *perk) &&
                        CountIn(state.active, *limit) >= limit->max)
                        SendAddon(player, "ERR:You can only have " + std::to_string(limit->max) + " " + limit->name +
                            " perks active. Turn one off first.");
                    else
                        SetPerk(player, state, *perk, on);
                }
        }
        else
        {
            // a loadout: in the order sent, keep perks until a category is full (and only the first of two
            // exclusive perks)
            std::set<uint32> wanted;
            bool trimmed = false;
            std::string_view list = std::string_view(text).substr(5);
            for (std::string_view id : Acore::Tokenize(list, ',', false))
                if (Optional<uint32> perk = Acore::StringTo<uint32>(id))
                    if (IMPLEMENTED.count(*perk) && CanUsePerk(player, *perk) && !wanted.count(*perk))
                    {
                        CategoryLimit const* limit = LimitOf(*perk);
                        if (ActivePartner(wanted, *perk) || (limit && CountIn(wanted, *limit) >= limit->max))
                        {
                            trimmed = true;
                            continue;
                        }
                        wanted.insert(*perk);
                    }
            for (uint32 perk : IMPLEMENTED)
                SetPerk(player, state, perk, wanted.count(perk) > 0);
            if (trimmed)
                SendAddon(player, "ERR:Not every perk of that loadout fit (Offensive at most 5, Defensive and Utility at most 3).");
        }

        RefreshStatPerks(player, state);
        SendState(player, state);
    }

    // ------------------------------------------------------------------ Rapid Recovery
    void RestoreTick(Player* player, uint32 percent)
    {
        uint32 maxHealth = player->GetMaxHealth();
        if (player->GetHealth() < maxHealth)
        {
            uint32 gain = std::max<uint32>(1, player->CountPctFromMaxHealth(percent));
            player->SetHealth(std::min<uint32>(maxHealth, player->GetHealth() + gain));
        }

        uint32 maxMana = player->GetMaxPower(POWER_MANA);
        if (maxMana && player->GetPower(POWER_MANA) < maxMana)
        {
            uint32 gain = std::max<uint32>(1, maxMana * percent / 100);
            player->SetPower(POWER_MANA, std::min<uint32>(maxMana, player->GetPower(POWER_MANA) + gain));
        }
    }

    // Rolling Momentum: once a second, +1% in combat (up to the rank's maximum) or -1% out of combat.
    void UpdateMomentum(Player* player, PerkState& state, uint32 diff)
    {
        if (!Has(&state, PERK_ROLLING_MOMENTUM))
        {
            state.momentum = 0;
            state.momentumTimer = 0;
            return;
        }
        state.momentumTimer += diff;
        while (state.momentumTimer >= 1000)
        {
            state.momentumTimer -= 1000;
            if (player->IsInCombat())
                state.momentum = std::min(int32(RankValue(player, state, PERK_ROLLING_MOMENTUM, 0)), state.momentum + MOMENTUM_STEP);
            else
                state.momentum = std::max(0, state.momentum - MOMENTUM_STEP);
        }
    }

    void UpdateRapidRecovery(Player* player, PerkState& state, uint32 diff)
    {
        if (!sRapidRecovery)
            return;

        // In combat, dead, or a ghost: start over.
        if (player->IsInCombat() || !player->IsAlive())
        {
            state.outOfCombatMs = 0;
            state.tickMs = 0;
            return;
        }

        RecoveryRank const& rank = RecoveryFor(player, state);
        if (state.outOfCombatMs < rank.delayMs)
        {
            state.outOfCombatMs += diff;
            if (state.outOfCombatMs < rank.delayMs)
                return;
            state.tickMs = RECOVERY_TICK_MS; // first tick right at the delay mark
        }
        else
            state.tickMs += diff;

        if (state.tickMs < RECOVERY_TICK_MS)
            return;

        state.tickMs = 0;
        RestoreTick(player, rank.percent);
    }

    // ------------------------------------------------------------------ Iron Will
    constexpr uint64 CROWD_CONTROL_MECHANICS =
        (1ULL << MECHANIC_CHARM) | (1ULL << MECHANIC_DISORIENTED) | (1ULL << MECHANIC_FEAR) |
        (1ULL << MECHANIC_ROOT) | (1ULL << MECHANIC_SILENCE) | (1ULL << MECHANIC_SLEEP) |
        (1ULL << MECHANIC_STUN) | (1ULL << MECHANIC_FREEZE) | (1ULL << MECHANIC_KNOCKOUT) |
        (1ULL << MECHANIC_POLYMORPH) | (1ULL << MECHANIC_HORROR) | (1ULL << MECHANIC_SAPPED);

    bool IsCrowdControl(SpellInfo const* spellInfo)
    {
        if (spellInfo->GetAllEffectsMechanicMask() & CROWD_CONTROL_MECHANICS)
            return true;
        // spells without a mechanic: go by what the aura does
        for (AuraType type : { SPELL_AURA_MOD_STUN, SPELL_AURA_MOD_FEAR, SPELL_AURA_MOD_CONFUSE, SPELL_AURA_MOD_ROOT,
                               SPELL_AURA_MOD_CHARM, SPELL_AURA_MOD_POSSESS, SPELL_AURA_MOD_SILENCE,
                               SPELL_AURA_MOD_PACIFY_SILENCE })
            if (spellInfo->HasAura(type))
                return true;
        return false;
    }

    // Iron Will: shorten an enemy's crowd control on a player (or their pet) with the perk on.
    void ApplyIronWill(Aura const* aura, int32& maxDuration)
    {
        if (maxDuration <= 0 || aura->GetType() != UNIT_AURA_TYPE)
            return;
        Unit* target = aura->GetUnitOwner();
        PerkState const* state = PerkOwnerState(target);
        if (!Has(state, PERK_IRON_WILL))
            return;
        SpellInfo const* spellInfo = aura->GetSpellInfo();
        if (spellInfo->IsPositive() || !IsCrowdControl(spellInfo))
            return;
        Unit* caster = aura->GetCaster();
        if (!caster || caster == target || !caster->IsHostileTo(target))
            return;
        float percent = std::min(100.0f, OwnerRankValue(target, PERK_IRON_WILL, 0));
        maxDuration = std::max<int32>(1, maxDuration - int32(maxDuration * percent / 100.0f));
    }

    // ------------------------------------------------------------------ Planting your legs
    // After standing still for the delay, restore a percentage of maximum health and mana every second.
    void UpdatePlantedFeet(Player* player, PerkState& state, uint32 diff)
    {
        if (!Has(&state, PERK_PLANTED_FEET) || !player->IsAlive() || player->isMoving())
        {
            state.stillMs = 0;
            state.stillTickMs = 0;
            return;
        }
        uint32 delayMs = uint32(RankValue(player, state, PERK_PLANTED_FEET, 2) * IN_MILLISECONDS);
        if (state.stillMs < delayMs)
        {
            state.stillMs += diff;
            if (state.stillMs < delayMs)
                return;
            state.stillTickMs = RECOVERY_TICK_MS; // first tick right at the delay mark
        }
        else
            state.stillTickMs += diff;
        if (state.stillTickMs < RECOVERY_TICK_MS)
            return;
        state.stillTickMs = 0;

        float healthPct = RankValue(player, state, PERK_PLANTED_FEET, 0);
        float manaPct = RankValue(player, state, PERK_PLANTED_FEET, 1);
        if (player->GetHealth() < player->GetMaxHealth())
            player->ModifyHealth(std::max<int32>(1, int32(player->GetMaxHealth() * healthPct / 100.0f)));
        uint32 maxMana = player->GetMaxPower(POWER_MANA);
        if (maxMana && player->GetPower(POWER_MANA) < maxMana)
            player->ModifyPower(POWER_MANA, std::max<int32>(1, int32(maxMana * manaPct / 100.0f)));
    }

    // ------------------------------------------------------------------ Defensive Momentum / Fortress
    bool IsUnitMoving(Unit const* unit)
    {
        return unit->IsPlayer() ? unit->isMoving() : !unit->movespline->Finalized();
    }

    // Once a second: Momentum gains a stack while moving and loses them all after ResetAfter seconds standing
    // still; Fortress gains a stack while standing still and loses them all after ResetAfter seconds moving.
    void UpdateStance(Unit* unit, PerkState const& state, StanceTrack& track, uint32 diff)
    {
        uint32 perk = Has(&state, PERK_DEFENSIVE_MOMENTUM) ? PERK_DEFENSIVE_MOMENTUM :
                      Has(&state, PERK_FORTRESS) ? PERK_FORTRESS : 0;
        if (!unit || !perk || !unit->IsAlive())
        {
            track = StanceTrack();
            return;
        }
        if (track.unit != unit->GetGUID())
        {
            track = StanceTrack();
            track.unit = unit->GetGUID();
        }
        bool moving = IsUnitMoving(unit);
        track.movingMs = moving ? track.movingMs + diff : 0;
        track.stillMs = moving ? 0 : track.stillMs + diff;

        uint32 resetMs = uint32(OwnerRankValue(unit, perk, 1) * IN_MILLISECONDS);
        bool building = perk == PERK_DEFENSIVE_MOMENTUM ? moving : !moving;
        if ((perk == PERK_DEFENSIVE_MOMENTUM ? track.stillMs : track.movingMs) >= std::max<uint32>(resetMs, 1))
            track.stacks = 0;

        track.tickMs += diff;
        if (track.tickMs < 1000)
            return;
        track.tickMs -= 1000;
        if (building)
            track.stacks = std::min(STANCE_MAX_STACKS, track.stacks + 1);
    }

    // ------------------------------------------------------------------ avoidance conversion
    // Greater Bulwark / Evasive Maneuvers / Parry King: move the other two avoidance chances into one (melee
    // attacks; chances are x100), times the rank's efficiency. Greater Bulwark needs a shield, since a block
    // without one stops no damage.
    void ConvertAvoidance(Unit const* victim, int32& dodge, int32& parry, int32& block)
    {
        PerkState const* state = PerkOwnerState(victim);
        if (!state || state->active.empty())
            return;
        auto efficiency = [victim](uint32 perk) { return OwnerRankValue(victim, perk, 0) / 100.0f; };
        if (Has(state, PERK_GREATER_BULWARK) && victim->IsPlayer() && victim->ToPlayer()->GetShield())
        {
            block += int32((std::max(0, dodge) + std::max(0, parry)) * efficiency(PERK_GREATER_BULWARK));
            dodge = parry = 0;
        }
        else if (Has(state, PERK_EVASIVE_MANEUVERS))
        {
            dodge += int32((std::max(0, block) + std::max(0, parry)) * efficiency(PERK_EVASIVE_MANEUVERS));
            block = parry = 0;
        }
        else if (Has(state, PERK_PARRY_KING))
        {
            parry += int32((std::max(0, block) + std::max(0, dodge)) * efficiency(PERK_PARRY_KING));
            block = dodge = 0;
        }
    }

    // ------------------------------------------------------------------ leech perks
    // Vampirism (the player heals), Soul Drain (the player and their pet heal from their own damage) and
    // Mana Leech (the player, while using mana), from damage actually dealt to another unit.
    void ApplyLeech(Unit* attacker, Unit* victim, uint32 damage)
    {
        if (!attacker || !victim || attacker == victim || !damage || !attacker->IsAlive())
            return;
        PerkState const* state = PerkOwnerState(attacker);
        if (!state || state->active.empty())
            return;
        damage = std::min<uint32>(damage, victim->GetHealth());

        float healPct = 0.0f;
        if (attacker->IsPlayer())
            healPct += OwnerRankValue(attacker, PERK_VAMPIRISM, 0);
        if (attacker->IsPlayer() || attacker->IsPet())
            healPct += OwnerRankValue(attacker, PERK_SOUL_DRAIN, 0);
        if (healPct > 0.0f && attacker->GetHealth() < attacker->GetMaxHealth())
            if (int32 heal = int32(damage * healPct / 100.0f))
                attacker->ModifyHealth(heal);

        if (attacker->IsPlayer() && attacker->getPowerType() == POWER_MANA)
            if (int32 mana = int32(damage * OwnerRankValue(attacker, PERK_MANA_LEECH, 0) / 100.0f))
                attacker->ModifyPower(POWER_MANA, mana);
    }

    // Pets replenishment (the pet takes more healing) and Soul Drain (direct healing on the player and their
    // pet is reduced).
    void ApplyHealingTaken(Unit* target, uint32& heal, bool isTick)
    {
        if (!target || !heal)
            return;
        if (!target->IsPlayer())
            if (float bonus = OwnerRankValue(target, PERK_PET_REPLENISHMENT, 0))
                heal = uint32(heal * (1.0f + bonus / 100.0f));
        if (target->IsPlayer() || target->IsPet())
            if (float bonus = OwnerRankValue(target, PERK_ENDURING, 0))  // Enduring: you and your pet
                heal = uint32(heal * (1.0f + bonus / 100.0f));
        if (!isTick)
            if (float penalty = OwnerRankValue(target, PERK_SOUL_DRAIN, 1))
                heal = uint32(heal * std::max(0.0f, 1.0f - penalty / 100.0f));
    }

    // Longer Legs: less fall damage. Fall damage is the only self-damage dealt while the player still has the
    // falling flag (the landing packet is handled before the new movement state is stored).
    uint32 ApplyFallDamage(Unit* attacker, Unit* victim, uint32 damage, DamageEffectType damageType)
    {
        if (damageType != SELF_DAMAGE || attacker != victim || !victim->IsPlayer() ||
            !victim->HasUnitMovementFlag(MOVEMENTFLAG_FALLING | MOVEMENTFLAG_FALLING_FAR))
            return damage;
        float reduction = std::min(100.0f, OwnerRankValue(victim, PERK_LONGER_LEGS, 3));
        return uint32(damage * (1.0f - reduction / 100.0f));
    }

    // ------------------------------------------------------------------ hit-based Defensive perks
    // On the final damage of a hit from another unit (after armor, resistances and the other perks): Counterweight
    // (the charged hit is reduced), Hardened Flesh (the part above the threshold is reduced), Juggernaut (no hit
    // above the cap, then a cooldown) and Second Wind (a big hit starts the healing).
    uint32 ApplyBigHitPerks(Unit* attacker, Unit* victim, uint32 damage)
    {
        if (!attacker || attacker == victim || !damage)
            return damage;
        PerkState* state = PerkOwnerState(victim);
        if (!state || state->active.empty() || (!victim->IsPlayer() && !victim->IsPet()))
            return damage;
        DefenseTrack& track = DefenseOf(*state, victim);
        float maxHealth = float(victim->GetMaxHealth());

        if (track.counterweight && Has(state, PERK_COUNTERWEIGHT))
        {
            damage = uint32(damage * Reduction(OwnerRankValue(victim, PERK_COUNTERWEIGHT, 0)));
            track.counterweight = false;
        }
        if (Has(state, PERK_HARDENED_FLESH))
        {
            float threshold = maxHealth * OwnerRankValue(victim, PERK_HARDENED_FLESH, 0) / 100.0f;
            if (damage > threshold)
                damage = uint32(threshold + (damage - threshold) * Reduction(OwnerRankValue(victim, PERK_HARDENED_FLESH, 1)));
        }
        if (Has(state, PERK_JUGGERNAUT) && !track.juggernautCooldownMs)
        {
            uint32 cap = uint32(maxHealth * OwnerRankValue(victim, PERK_JUGGERNAUT, 0) / 100.0f);
            if (damage > cap)
            {
                damage = cap;
                track.juggernautCooldownMs = uint32(OwnerRankValue(victim, PERK_JUGGERNAUT, 1) * IN_MILLISECONDS);
            }
        }
        if (Has(state, PERK_SECOND_WIND) && damage > maxHealth * OwnerRankValue(victim, PERK_SECOND_WIND, 0) / 100.0f)
        {
            track.secondWindMs = uint32(OwnerRankValue(victim, PERK_SECOND_WIND, 2) * IN_MILLISECONDS);
            track.secondWindTickMs = 0;
        }
        return damage;
    }

    // Counterweight, Shield Wall Training and Thornmail, from the defense proc aura (a melee attack taken).
    void HandleDefenseProc(Unit* victim, Unit* attacker, uint32 hitMask, uint32 damage)
    {
        PerkState* state = PerkOwnerState(victim);
        if (!state || !victim->IsAlive())
            return;
        DefenseTrack& track = DefenseOf(*state, victim);
        if ((hitMask & (PROC_HIT_DODGE | PROC_HIT_PARRY | PROC_HIT_BLOCK)) && Has(state, PERK_COUNTERWEIGHT))
            track.counterweight = true;
        if ((hitMask & PROC_HIT_BLOCK) && Has(state, PERK_SHIELD_WALL_TRAINING))
        {
            track.shieldWallStacks = std::min<uint32>(track.shieldWallStacks + 1,
                uint32(OwnerRankValue(victim, PERK_SHIELD_WALL_TRAINING, 1)));
            track.shieldWallMs = uint32(OwnerRankValue(victim, PERK_SHIELD_WALL_TRAINING, 2) * IN_MILLISECONDS);
        }
        if (damage && attacker && attacker != victim && attacker->IsAlive() && Has(state, PERK_THORNMAIL))
            if (int32 thorns = int32(damage * OwnerRankValue(victim, PERK_THORNMAIL, 0) / 100.0f))
                victim->CastCustomSpell(SPELL_DAMAGE_SHIELD, SPELLVALUE_BASE_POINT0, thorns, attacker, true);
    }

    // Shield Wall Training's block chance (x100, for the melee roll).
    int32 ShieldWallBonus(Unit const* victim)
    {
        PerkState* state = PerkOwnerState(victim);
        if (!Has(state, PERK_SHIELD_WALL_TRAINING))
            return 0;
        DefenseTrack const& track = victim->IsPlayer() ? state->selfDefense : state->petDefense;
        if (track.unit != victim->GetGUID() || !track.shieldWallStacks)
            return 0;
        return int32(track.shieldWallStacks * OwnerRankValue(victim, PERK_SHIELD_WALL_TRAINING, 0) * 100.0f);
    }

    // Timers of the hit-based perks, and Second Wind's healing once a second.
    void UpdateDefense(Unit* unit, PerkState& state, uint32 diff)
    {
        if (!unit)
            return;
        DefenseTrack& track = DefenseOf(state, unit);
        track.juggernautCooldownMs = track.juggernautCooldownMs > diff ? track.juggernautCooldownMs - diff : 0;
        if (track.shieldWallMs)
        {
            track.shieldWallMs = track.shieldWallMs > diff ? track.shieldWallMs - diff : 0;
            if (!track.shieldWallMs)
                track.shieldWallStacks = 0;
        }
        if (!track.secondWindMs)
            return;
        if (!unit->IsAlive() || !Has(&state, PERK_SECOND_WIND))
        {
            track.secondWindMs = 0;
            return;
        }
        track.secondWindTickMs += diff;
        while (track.secondWindTickMs >= 1000 && track.secondWindMs)
        {
            track.secondWindTickMs -= 1000;
            track.secondWindMs = track.secondWindMs > 1000 ? track.secondWindMs - 1000 : 0;
            if (unit->GetHealth() < unit->GetMaxHealth())
                unit->ModifyHealth(std::max<int32>(1, int32(unit->GetMaxHealth() * OwnerRankValue(unit, PERK_SECOND_WIND, 1) / 100.0f)));
        }
    }
}

class unbound_perks_world : public WorldScript
{
public:
    unbound_perks_world() : WorldScript("unbound_perks_world", {
        WORLDHOOK_ON_AFTER_CONFIG_LOAD
    }) { }

    void OnAfterConfigLoad(bool /*reload*/) override
    {
        sRapidRecovery = sConfigMgr->GetOption<bool>("Unbound.Perks.RapidRecovery", true);
        // one value per rank; a single value means one rank
        std::vector<uint32> delays = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.RapidRecovery.Delay", "6000, 5000, 4000"));
        std::vector<uint32> percents = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.RapidRecovery.Percent", "4, 6, 8"));
        std::vector<uint32> levels = ParseList(sConfigMgr->GetOption<std::string>("Unbound.Perks.RapidRecovery.RankLevels", "1, 30, 60"));
        size_t count = std::min(delays.size(), percents.size());
        if (!count)
        {
            delays = { 4000 };
            percents = { 8 };
            count = 1;
        }
        sRecoveryRanks.clear();
        for (size_t i = 0; i < count; ++i)
            sRecoveryRanks.push_back({ delays[i], std::clamp<uint32>(percents[i], 1, 100),
                                       i < levels.size() ? levels[i] : (i == 0 ? 1 : 255) });

        // the other ranked perks: the number of ranks is the shortest stat list
        sPerkRanks.clear();
        for (RankedPerkDef const& def : RANKED_PERKS)
        {
            std::string prefix = std::string("Unbound.Perks.") + def.key + ".";
            std::vector<std::vector<float>> stats;
            size_t rankCount = SIZE_MAX;
            for (auto const& [stat, defaults] : def.stats)
            {
                std::vector<float> values = ParseFloatList(sConfigMgr->GetOption<std::string>(prefix + stat, defaults));
                if (values.empty())
                    values = ParseFloatList(defaults);
                rankCount = std::min(rankCount, values.size());
                stats.push_back(std::move(values));
            }
            std::vector<uint32> rankLevels = ParseList(sConfigMgr->GetOption<std::string>(prefix + "RankLevels", def.levels));

            PerkRanks& ranks = sPerkRanks[def.perk];
            for (size_t rank = 0; rank < rankCount; ++rank)
            {
                std::vector<float> values;
                for (std::vector<float> const& stat : stats)
                    values.push_back(stat[rank]);
                ranks.values.push_back(std::move(values));
                ranks.levels.push_back(rank < rankLevels.size() ? rankLevels[rank] : (rank == 0 ? 1 : 255));
            }
        }
    }
};

class unbound_perks_spell : public AllSpellScript
{
public:
    unbound_perks_spell() : AllSpellScript("unbound_perks_spell", {
        ALLSPELLHOOK_ON_CALC_MAX_DURATION
    }) { }

    void OnCalcMaxDuration(Aura const* aura, int32& maxDuration) override
    {
        ApplyIronWill(aura, maxDuration);
    }
};

class unbound_perks_player : public PlayerScript
{
public:
    unbound_perks_player() : PlayerScript("unbound_perks_player", {
        PLAYERHOOK_ON_LEVEL_CHANGED,
        PLAYERHOOK_ON_LOGIN,
        PLAYERHOOK_ON_LOGOUT,
        PLAYERHOOK_ON_UPDATE,
        PLAYERHOOK_ON_DELETE,
        PLAYERHOOK_CAN_PLAYER_USE_PRIVATE_CHAT,
        PLAYERHOOK_ON_CREATURE_KILL,
        PLAYERHOOK_ON_CREATURE_KILLED_BY_PET,
        PLAYERHOOK_ON_PVP_KILL
    }) { }

    // Relentless Pursuit
    void OnPlayerCreatureKill(Player* killer, Creature* /*killed*/) override { StartPursuit(killer); }
    void OnPlayerCreatureKilledByPet(Player* owner, Creature* /*killed*/) override { StartPursuit(owner); }
    void OnPlayerPVPKill(Player* killer, Player* /*killed*/) override { StartPursuit(killer); }

    void OnPlayerLogin(Player* player) override
    {
        PerkState& state = sStates[player->GetGUID().GetCounter()];
        state = PerkState();
        state.cycleStartMs = getMSTime();
        player->RemoveAurasDueToSpell(SPELL_CRIT_DAMAGE_AURA); // saved with the character; re-added below if earned
        if (QueryResult result = CharacterDatabase.Query("SELECT `perk` FROM `character_unbound_perks` WHERE `guid` = {}",
            player->GetGUID().GetCounter()))
        {
            do
            {
                uint32 perk = (*result)[0].Get<uint32>();
                if (!IMPLEMENTED.count(perk))
                    continue;
                if (CanUsePerk(player, perk))
                    state.active.insert(perk);
                else
                    SavePerk(player, perk, false); // another class's perk: switch it off for good
            } while (result->NextRow());
        }
        if (QueryResult result = CharacterDatabase.Query("SELECT `perk`, `rank` FROM `character_unbound_perk_ranks` WHERE `guid` = {}",
            player->GetGUID().GetCounter()))
        {
            do
                state.rankOverride[(*result)[0].Get<uint32>()] = (*result)[1].Get<uint8>();
            while (result->NextRow());
        }
        // saved before a category limit (or an exclusive pair) existed: keep the lowest ids, switch the rest off
        for (CategoryLimit const& limit : CATEGORY_LIMITS)
            while (CountIn(state.active, limit) > limit.max)
            {
                auto last = std::find_if(state.active.rbegin(), state.active.rend(),
                    [&limit](uint32 perk) { return perk >= limit.first && perk <= limit.last; });
                uint32 perk = *last;
                state.active.erase(perk);
                SavePerk(player, perk, false);
            }
        for (std::vector<uint32> const& group : EXCLUSIVE_GROUPS)
        {
            bool kept = false;
            for (uint32 perk : group)
                if (state.active.count(perk))
                {
                    if (kept)
                    {
                        state.active.erase(perk);
                        SavePerk(player, perk, false);
                    }
                    kept = true;
                }
        }
        RefreshStatPerks(player, state);
    }

    void OnPlayerLogout(Player* player) override
    {
        sStates.erase(player->GetGUID().GetCounter());
    }

    void OnPlayerDelete(ObjectGuid guid, uint32 /*accountId*/) override
    {
        CharacterDatabase.Execute("DELETE FROM `character_unbound_perks` WHERE `guid` = {}", guid.GetCounter());
        CharacterDatabase.Execute("DELETE FROM `character_unbound_perk_ranks` WHERE `guid` = {}", guid.GetCounter());
    }

    // ranks that come from the level change with it
    void OnPlayerLevelChanged(Player* player, uint8 /*oldLevel*/) override
    {
        if (PerkState* state = StateOf(player))
            SendRanks(player, *state);
    }

    void OnPlayerUpdate(Player* player, uint32 diff) override
    {
        PerkState& state = sStates[player->GetGUID().GetCounter()];
        UpdateRapidRecovery(player, state, diff);
        UpdateMomentum(player, state, diff);
        UpdatePlantedFeet(player, state, diff);
        UpdateStance(player, state, state.selfStance, diff);
        UpdateStance(player->GetPet(), state, state.petStance, diff);
        UpdateDefense(player, state, diff);
        UpdateDefense(player->GetPet(), state, diff);

        if (state.active.empty() && !state.sacrificeAP && !state.sacrificeSP && !state.critBonus &&
            std::none_of(std::begin(state.desperateResist), std::end(state.desperateResist), [](int32 r) { return r != 0; }))
            return;
        state.statTimer += diff;
        if (state.statTimer >= STAT_REFRESH_MS)
        {
            state.statTimer = 0;
            RefreshStatPerks(player, state);
        }
    }

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
};

class unbound_perks_unit : public UnitScript
{
public:
    unbound_perks_unit() : UnitScript("unbound_perks_unit", true, {
        UNITHOOK_MODIFY_MELEE_DAMAGE,
        UNITHOOK_MODIFY_SPELL_DAMAGE_TAKEN,
        UNITHOOK_MODIFY_PERIODIC_DAMAGE_AURAS_TICK,
        UNITHOOK_MODIFY_HEAL_RECEIVED,
        UNITHOOK_ON_BEFORE_ROLL_MELEE_OUTCOME_AGAINST
    }) { }

    // Healing Powah (see PendingHealTick for the argument order).
    void ModifyHealReceived(Unit* first, Unit* second, uint32& heal, SpellInfo const* spellInfo) override
    {
        PendingHealTick tick = sPendingHealTick;
        sPendingHealTick = PendingHealTick();
        bool isTick = tick.amount == &heal && tick.target == first && tick.spellInfo == spellInfo;
        Unit* healer = isTick ? second : first;
        Unit* target = isTick ? first : second;
        ApplyHealingBonus(healer, heal);
        ApplyHealingTaken(target, heal, isTick);
    }

    // Greater Bulwark / Evasive Maneuvers / Parry King convert avoidance first; then Block/Dodge/Parry Capping:
    // melee attacks against a capped player use at most the cap (chances are x100).
    void OnBeforeRollMeleeOutcomeAgainst(Unit const* /*attacker*/, Unit const* victim, WeaponAttackType /*attType*/,
        int32& /*attackerMaxSkillValueForLevel*/, int32& /*victimMaxSkillValueForLevel*/, int32& /*attackerWeaponSkill*/,
        int32& /*victimDefenseSkill*/, int32& /*crit_chance*/, int32& /*miss_chance*/, int32& dodge_chance,
        int32& parry_chance, int32& block_chance) override
    {
        PerkState const* state = PerkOwnerState(victim);
        if (!state || state->active.empty())
            return;
        ConvertAvoidance(victim, dodge_chance, parry_chance, block_chance);  // before the caps below
        if (block_chance > 0)
            block_chance += ShieldWallBonus(victim);  // Shield Wall Training (only with a block chance, i.e. a shield)
        int32 const cap = int32(AVOIDANCE_CAP * 100);
        if (Has(state, PERK_BLOCK_CAPPING))
            block_chance = std::min(block_chance, cap);
        if (Has(state, PERK_DODGE_CAPPING))
            dodge_chance = std::min(dodge_chance, cap);
        if (Has(state, PERK_PARRY_CAPPING))
            parry_chance = std::min(parry_chance, cap);
    }

    void ModifyMeleeDamage(Unit* target, Unit* attacker, uint32& damage) override
    {
        ApplyMultipliers(target, attacker, damage, nullptr, HitKind::Melee);
    }

    void ModifySpellDamageTaken(Unit* target, Unit* attacker, int32& damage, SpellInfo const* spellInfo) override
    {
        // Retribution - Exorcist: Exorcism gets 60% of attack power and spell power
        if (damage > 0 && IsExorcism(spellInfo) && HasRetribution(attacker))
            damage += int32(EXORCIST_EXTRA_SCALING * (attacker->GetTotalAttackPowerValue(BASE_ATTACK) +
                                                      attacker->SpellBaseDamageBonusDone(SPELL_SCHOOL_MASK_HOLY)));
        ApplyMultipliers(target, attacker, damage, spellInfo, HitKind::Spell);
    }

    // Retribution - Righteous Explosion: notice the killing blow while the dying enemy still has its auras.
    // Also Longer Legs (fall damage) and the leech perks (Vampirism, Soul Drain, Mana Leech).
    uint32 DealDamage(Unit* attacker, Unit* victim, uint32 damage, DamageEffectType damagetype) override
    {
        if (!victim)
            return damage;
        damage = ApplyFallDamage(attacker, victim, damage, damagetype);
        damage = ApplyBigHitPerks(attacker, victim, damage);
        ApplyLeech(attacker, victim, damage);
        if (damage && victim->IsAlive() && damage >= victim->GetHealth() &&
            victim->HasAura(SPELL_RIGHTEOUS_VENGEANCE_DOT))
            ScheduleRighteousExplosion(victim);
        return damage;
    }

    // Also called for heal-over-time ticks: only scale ticks on hostile targets.
    void ModifyPeriodicDamageAurasTick(Unit* target, Unit* attacker, uint32& damage, SpellInfo const* spellInfo) override
    {
        sPendingHealTick = { &damage, target, spellInfo };  // a heal tick calls ModifyHealReceived next
        if (target && attacker && target->IsFriendlyTo(attacker))
            return;
        ApplyMultipliers(target, attacker, damage, spellInfo, HitKind::Periodic);
    }
};

// 53385 - Divine Storm (Retribution perk: up to 6 targets, a Crusader Strike on every enemy hit)
class spell_unbound_ret_divine_storm : public SpellScript
{
    PrepareSpellScript(spell_unbound_ret_divine_storm);

    void RaiseTargetCap()
    {
        if (HasRetribution(GetCaster()))
            GetSpell()->SetSpellValue(SPELLVALUE_MAX_TARGETS, DIVINE_STORM_MAX_TARGETS);
    }

    void CrusaderStrike()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (target && target != caster && HasRetribution(caster) && caster->IsValidAttackTarget(target))
            caster->CastSpell(target, SPELL_CRUSADER_STRIKE, TRIGGERED_FULL_MASK);
    }

    void Register() override
    {
        BeforeCast += SpellCastFn(spell_unbound_ret_divine_storm::RaiseTargetCap);
        AfterHit += SpellHitFn(spell_unbound_ret_divine_storm::CrusaderStrike);
    }
};

// 20271, 53407, 53408 - Judgements (Retribution perk: spread to 4 more enemies within 10 yards, a free Exorcism
// on each enemy)
class spell_unbound_ret_judgement : public SpellScript
{
    PrepareSpellScript(spell_unbound_ret_judgement);

    void JudgeAll()
    {
        Unit* caster = GetCaster();
        Unit* target = GetHitUnit();
        if (!target || !HasRetribution(caster) || !caster->IsValidAttackTarget(target))
            return;

        if (uint32 exorcism = ExorcismFor(caster->ToPlayer()))
            caster->CastSpell(target, exorcism, TRIGGERED_FULL_MASK);

        if (GetSpell()->IsTriggered()) // the spread Judgements don't spread again
            return;
        std::list<Unit*> enemies = EnemiesNear(target, caster, JUDGEMENT_SPREAD_RANGE);
        enemies.remove(target);
        enemies.sort(Acore::ObjectDistanceOrderPred(target));
        uint32 spread = 0;
        for (Unit* enemy : enemies)
        {
            if (++spread > JUDGEMENT_SPREAD_TARGETS)
                break;
            caster->CastSpell(enemy, GetSpellInfo()->Id, TRIGGERED_FULL_MASK);
        }
    }

    void Register() override
    {
        AfterHit += SpellHitFn(spell_unbound_ret_judgement::JudgeAll);
    }
};

// 200215 - Unbound perk defense proc (server-only passive aura on a player and pet with Counterweight, Shield
// Wall Training or Thornmail; spell_proc: melee attacks taken that hit, crit, or are dodged, parried, blocked)
class spell_unbound_perk_defense_proc : public AuraScript
{
    PrepareAuraScript(spell_unbound_perk_defense_proc);

    void OnProc(AuraEffect const* /*aurEff*/, ProcEventInfo& eventInfo)
    {
        PreventDefaultAction();
        DamageInfo* damageInfo = eventInfo.GetDamageInfo();
        uint32 damage = damageInfo ? damageInfo->GetDamage() + damageInfo->GetAbsorb() : 0;
        HandleDefenseProc(GetTarget(), eventInfo.GetProcTarget(), eventInfo.GetHitMask(), damage);
    }

    void Register() override
    {
        OnEffectProc += AuraEffectProcFn(spell_unbound_perk_defense_proc::OnProc, EFFECT_0, SPELL_AURA_DUMMY);
    }
};

// .perk rank <perk id> [rank]: set the selected player's (or your own) rank of a perk, for testing.
// Without a rank the perk goes back to the rank the character's level gives.
class unbound_perks_command : public CommandScript
{
public:
    unbound_perks_command() : CommandScript("unbound_perks_command") { }

    Acore::ChatCommands::ChatCommandTable GetCommands() const override
    {
        using namespace Acore::ChatCommands;
        static ChatCommandTable perkTable =
        {
            { "rank", HandlePerkRank, rbac::RBAC_PERM_COMMAND_MODIFY, Console::No },
        };
        static ChatCommandTable commandTable =
        {
            { "perk", perkTable },
        };
        return commandTable;
    }

    static bool HandlePerkRank(ChatHandler* handler, uint32 perk, Optional<uint8> rank)
    {
        Player* target = handler->getSelectedPlayerOrSelf();
        PerkState* state = target ? StateOf(target) : nullptr;
        if (!state)
            return false;
        uint8 maxRank = MaxRank(perk);
        if (!RankedPerks().count(perk))
        {
            handler->PSendSysMessage("Perk {} has no ranks. Ranked perks: 3 (Rapid Recovery), 303 (Iron Will).", perk);
            return true;
        }
        uint32 guid = target->GetGUID().GetCounter();
        if (rank)
        {
            uint8 value = std::clamp<uint8>(*rank, 1, maxRank);
            state->rankOverride[perk] = value;
            CharacterDatabase.Execute("REPLACE INTO `character_unbound_perk_ranks` (`guid`, `perk`, `rank`) VALUES ({}, {}, {})",
                guid, perk, value);
        }
        else
        {
            state->rankOverride.erase(perk);
            CharacterDatabase.Execute("DELETE FROM `character_unbound_perk_ranks` WHERE `guid` = {} AND `perk` = {}", guid, perk);
        }
        uint8 now = PerkRank(target, *state, perk);
        handler->PSendSysMessage("{}: perk {} is now Rank {} / {}{}.", target->GetName(), perk, now, maxRank,
            rank ? "" : " (from level)");
        SendRanks(target, *state);
        return true;
    }
};

void AddSC_unbound_perks()
{
    new unbound_perks_world();
    new unbound_perks_command();
    new unbound_perks_player();
    new unbound_perks_unit();
    new unbound_perks_spell();
    RegisterSpellScript(spell_unbound_ret_divine_storm);
    RegisterSpellScript(spell_unbound_ret_judgement);
    RegisterSpellScript(spell_unbound_perk_defense_proc);
}
