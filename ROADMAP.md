# Roadmap

Work-on list for the Unbound server. Tick a box (`- [x]`) when a feature is done and add it to the
[CHANGELOG.md](CHANGELOG.md) under that day's date. Effort is a rough guess: **easy** (a config or ready-made
module), **moderate** (custom code or data), **large** (several parts, client changes).

Guiding idea: inspired by Peloria, not a copy. No Peloria-sized numbers (billions): a fully progressed
player is at most several times a normal level 60, and every number stays far below the 32-bit limits.

## Power budget

The endgame goal: **one player can solo a full Mythic raid** (the player count will be low). The realistic
goal is **classic Naxxramas on Mythic +1** solo; the stretch goal is **Naxxramas Mythic +10** (set 2026-10-15,
see Endgame goals below). Raids are
scaled down to one player, and **gear infusion is the main lever** that lets a player climb Mythic
levels; perks add on top (perk Ranks 4-5 are GM-only and not counted). Design every power system against these targets, and change the
numbers here first if testing says so. Every number below is meant to be a config setting.

### Content

| Lever | Target |
|---|---|
| Classic raids solo (mod-autobalance) | A solo player faces **about 3 players' worth** of a raid; a full raid is unchanged. 20-player raids: `AutoBalance.InflectionPointRaid20M.CurveFloor = 0.1` (2.9 players' worth); 40-player raids: `AutoBalance.InflectionPointRaid40M.CurveFloor = 0.03` (2.8). Set 2026-10-14. Onyxia's Lair (classic, a 10-player map) and classic Naxxramas (on the map's heroic slot) get the same 2.8 through `AutoBalance.InflectionPoint.PerInstance = "249 -1 0.058 0.25, 533 -1 0.03"` (2026-10-15). |
| Mythic scaling | **+10% per level, added** (not multiplied): Mythic +5 = 1.5x, Mythic +10 = 2x the solo raid |
| Mythic maximum | **Mythic +10 for every dungeon and raid** (decided 2026-10-15): the top of the climb, and the number every Mythic system is designed around (the Keystone's Max button, Mythic gear, upgrades, the power budget). A config setting, but raising it means redoing this budget |
| Safety clamp | No creature health or damage above **2 billion**, whatever the settings (the 3.3.5 client shows numbers above about 2.1 billion wrongly). With added scaling this is never reached in practice: the biggest classic boss (Vaelastrasz, 3.3 million health) would pass it only around Mythic +90,000 solo |

### Player power needed

| Raid | Player power needed (x a normal level 60) |
|---|---|
| Base solo raid | about 2.8x |
| Mythic +5 | about 4.2x |
| Mythic +10 (the maximum) | about 5.6x |

These are for a raid like Molten Core. Later raids have stronger bosses at the same player count (all scale
to about 2.8 players' worth solo), so they need more (estimates from boss health and damage; check in
testing):

| Raid (solo) | Biggest bosses (health, normal) | Player power needed |
|---|---|---|
| Molten Core | Ragnaros 1.1M | about 2.8x |
| Blackwing Lair, Ahn'Qiraj | Nefarian 2.2M, Viscidus 2.0M | about 3.5-4.5x |
| Naxxramas (classic) | Thaddius 6.7M, Loatheb 5.3M, Patchwerk 4.0M, Kel'Thuzad 3.2M | about 6-7x |

### Endgame goals

| Goal | Raid | Player power needed | Reached with (see Player, Mythic+ gear) |
|---|---|---|---|
| **Realistic endgame goal** | **Naxxramas (classic) Mythic +1** | about 6.6-7.7x | A fully infused character (normal gear, about +200%) with five Offensive perks and the class perk (about 5.8-6.3x), plus some Mythic gear from earlier Mythic runs for the last 20% or so (e.g. Mythic items infused around +3-5) |
| **Stretch goal** | **Naxxramas (classic) Mythic +10** | about 12-14x | Mythic gear infused around +10 on top (as tuned now about 8x before the class perk, about 10-11x with it: short of the goal, see Mythic+ gear) |

Mythic stops at +10, so the stretch goal is also the top of the game: Naxxramas Mythic +10 is the hardest
content there is. Change these targets here first if testing says otherwise.

### Player

| Lever | Target |
|---|---|
| Gear | Normal level 60 gear: the baseline (1x) |
| Perks | About **x1.55** with five Offensive perks (about +10% per perk) |
| Perk ranks | **None for players:** Ranks 1-3 are part of the perks above; Ranks 4-5 (about x1.3) are **GM-only** (decided 2026-10-15) and not counted |
| Class perk | About **x1.25-1.35**: each spec's class perk is worth about **+25-35% to that spec's single-target damage** (a lone raid boss is what a solo Mythic raid is about). Extra area damage on trash is fine on top. Every class perk is held to this target, so no spec pulls ahead. Measure with a damage meter on a training dummy, perk off vs on |
| Gear infusion / tribute | About **+200% of gear stats** when well collected (about x3), the main lever: |
| - per item | **20%** of the item's fixed stats (tune 15-25% in testing); fixed stats only (no procs, set bonuses, weapon damage) |
| - which items count | **Every unique item** counts once (a second copy adds nothing); **green or better** |
| - minimum item level | Only items whose **required level is within 10 of the level cap** count (level 50+ while the cap is 60; it moves up with each expansion), so every infused item matters and nobody grinds low-level items |
| - diminishing returns | Full value up to **+100%** of gear stats, half value up to **+200%**, a quarter beyond: early collecting feels strong, the long tail is the endgame grind (no hard cap) |
| - the grind | About **255 level 60 blue/epic items** for +200% with the diminishing returns (about 170 items give +150%); 20% of an item is about 7 stat points, a full set is about 600 (`ReferenceSetStats`). Tune `Percent` or the diminishing returns after testing |
| **Total** | About **4.6x** a normal level 60 with normal gear fully infused, before the class perk: Molten Core Mythic +6. With the class perk about **5.8-6.3x**: Molten Core Mythic +10, Naxxramas normal. Mythic gear on top leads to Naxxramas Mythic +1, the realistic endgame goal, and further (see Endgame goals) |

Numbers check: a 6x character (fully infused with the class perk) has a few thousand of a primary stat and tens of thousands of health, well
above normal WoW but nowhere near Peloria's billions.

### Infusion and tribute rules

Both styles fill **one shared collection** per character, so the end result is the same: an item gives
its full 20% whichever way it was collected. Time versus cost is the whole trade-off.

| | Infuse | Tribute |
|---|---|---|
| How | Equip the item and kill creatures until it reaches 100% | Destroy the item for its stats at once |
| Speed | Slow | Instant |
| The item | **Kept**: wear it, transmog it, sell it later | **Destroyed** |
| Which items | Only gear the character **can equip** (their armour type, their class's weapons) | **Any item** that counts (see the Player table), including gear the character could infuse |
| Value | **Full 20%** | **Full 20%** (not reduced) |
| Cost | Free | A price scaled by quality: gold for now, Heroic Sigils once they exist |
| Cost for gear the character could infuse | (free) | **Double** the normal price, so infusing stays the main route for one's own gear |

- **Collected stats are permanent:** once an item is 100% infused (or given in tribute), its 20% stays whatever
  happens to the item (unequipped, banked, sold, deleted). An upgrade never costs anything: infuse it too
  and both count. (The level copies of one Mythic item are the exception: the highest infused copy
  replaces the lower ones, see Mythic+ gear.)
- **Progress is saved per item:** unequipping a partly infused item pauses it (60% stays 60%); equipping it
  again carries on from there.
- **Stats only at 100%:** a partly infused item gives nothing yet; its full 20% arrives when it reaches 100%.
- **Kills needed** (config settings): about **50 kills** for a green, **100** for a blue, **200** for an epic.
  An elite counts as 2 kills, a boss as 10. Every eligible equipped item gets progress from each kill.
- **Which kills count:** only creatures that **would give experience** (not grey for the player's level,
  not a no-experience creature such as critters or training dummies). At the level cap players earn no
  experience, so the check is "would give", not "gave".
- **Released expansions only:** items from The Burning Crusade and Wrath of the Lich King don't count until
  that expansion is released. Every item is tagged with its expansion by a small tool (from where it comes
  from: classic or expansion zones, dungeons, quests, vendors), because the level rule alone isn't enough
  (some TBC items require level 58-60, and item levels overlap). Infusion only accepts items from
  expansions up to `Unbound.ExpansionUnlocked` (the content lock's setting), so releasing an expansion
  turns its items on with that one change.
- An item counts only once. Offering a partly infused item as tribute finishes it (the price still applies).
- Tribute always shows a confirmation (item and price) before destroying anything.
- Tooltips show "Infusion: 37%", "Infused", or "Infusion: tribute only".
- A collection window in the perks' talent-tree style shows every absorbed item and the stat totals.
- **Per character:** each character has its own collection (alts start their own).
- **Tribute at an altar NPC (the Altar of Tribute):** an altar in the capital cities (players of both factions can use any,
  as everything else is cross-faction). Talking to it opens the tribute window: pick an item from the bags,
  see its stats and the price, confirm.
- **Tribute prices** (gold, scaled by quality; config settings, Heroic Sigils later):

  | Quality | Price | Gear the character could infuse (double) |
  |---|---|---|
  | Green (uncommon) | 2 gold | 4 gold |
  | Blue (rare) | 10 gold | 20 gold |
  | Purple (epic) | 50 gold | 100 gold |
  | Orange (legendary) | 250 gold | 500 gold |

### Mythic+ gear

Mythic+ bosses drop **epic gear whose stats grow with the Mythic level it dropped at** (Option A, decided
2026-10-14): every Mythic item exists once per level as its own item, generated by a tool like the Heroic
loot, so a tooltip shows plain white stats ("+22 Stamina"), exactly like normal WoW gear. All numbers are
config settings (the item generator reads them).

| Lever | Target |
|---|---|
| The items | Epic remakes of each boss's drops (same names and looks as its Heroic blues), one per boss, two from the final boss, like Heroic |
| Mythic +1 stats | **Level 60 epic level**: about 1.3x the Heroic version |
| Per Mythic level | **+2% of the +1 stats, added**: +10 (the maximum) = about 1.2x the +1 item (helm: 20 Stamina at +1, about 22 at +5, about 24 at +10) |
| Drop level | An item drops at the level the run was cleared at (a +7 clear drops +7 gear) |
| Item count | About 450 dungeon items x 10 levels (about 4,500 entries, plus the raids' items; the client patch grows about 0.15 MB) |
| Infusion percent | **20% + 2% per Mythic level** for Mythic items (+1: 22%, +5: 30%, +10: 40%), so infusing high is worth much more than wearing high: the helm gives 4 Stamina infused at +1, about 10 at +10 |
| Infusion: one item | All level copies of a Mythic item count as **one item**: infusing (or giving in tribute) a higher copy **replaces** the lower copy's bonus, it never adds to it. Infusing early is never wasted, waiting for a higher copy pays more. (Heroic and Mythic versions of a piece are different items and both count.) |
| Infusion: kills | A higher copy needs its own kills (the normal epic count); an upgrade never changes what is already infused |
| Diminishing returns | A fourth step for the much larger Mythic totals: full value up to +100%, half to +200%, a quarter to +400%, **an eighth beyond** |

**Upgrading** (an Upgrade NPC next to the Keystone NPC): raise a Mythic item you own to a higher level, up to
**your best clear of that dungeon or raid** (each instance is worth pushing; gold can never buy a level you
haven't cleared). The item keeps its enchant, stays soulbound and only goes up (behind the scenes it is
swapped for the higher level's copy). Each level gained costs **gold and Mythic currency** (starting values,
config settings):

| Level gained (to +N) | Gold | Mythic currency |
|---|---|---|
| +2 to +5 | 5 x N gold (to +5: 25 gold) | 1 |
| +6 to +10 | 5 x N gold (to +10: 50 gold) | 2 |

e.g. +1 to +5 costs 70 gold and 4 currency; +5 to +10 costs 200 gold and 10 currency; +1 to +10 costs 270 gold
and 14 currency.

**Mythic currency** (new, name to be decided, e.g. "Mythic Shard"): a currency item from Mythic bosses,
more at higher levels (e.g. 1 per boss plus 1 per 5 Mythic levels, double from the final boss; config
settings). Used for upgrades; later also a vendor (cosmetics) like the Heroic currency.

**Effect on the climb** (estimates, to be checked in testing):

| Fully collected | Gear worn | Infused | Player power (with perks, before class perk) | Clears about |
|---|---|---|---|---|
| Before Mythic gear (normal infusion only) | 1x | +200% | about 4.6x (5.8-6.3x with the class perk) | Molten Core Mythic +6; with the class perk Molten Core Mythic +10 and Naxxramas normal |
| Every Mythic item infused at +10 | about 1.5x | about +380% | about 8x (10-11x with the class perk) | Naxxramas Mythic +2; with the class perk Naxxramas Mythic +5-6 |

Mythic gear is what carries a player to the realistic goal (Naxxramas +1; with perk Ranks 4-5 GM-only, normal
infusion alone stops at about Naxxramas normal) and on to the stretch goal (Naxxramas +10, the top). As tuned
above it stops around Naxxramas +5-6, so the stretch goal needs about 1.3x more from Mythic gear: when it's
built, try a Mythic infusion percent of 3% per level (+10: 50%) or more gear stats per level. If it gets there too fast, lower the infusion percent per level first (2% to 1%), then the
gear stats per level.

Mechanics are a separate problem: some bosses need more than one player whatever the numbers
(Razorgore's orb, the Twin Emperors' teleport tank swap, C'Thun's stomach phase). They need small script
changes, raid by raid (see Next up).

## Done

- [x] Transmogrify spell (mod-transmog-plus window from anywhere)
- [x] Loot Goblin and Arcane Loot Scanner companions (auto-loot within 55 yards, AoE loot)
- [x] Cross-faction grouping, raids, guilds, chat, trade and auction house (not battlegrounds)
- [x] Solo dungeon scaling (mod-autobalance, floor 0.4) and solo dungeon finder (mod-solo-lfg)
- [x] No raid-group requirement, no instances-per-hour limit, Reset all instances resets raids too
- [x] Classic Heroic dungeons: pilot with Stormwind Stockades (level 60, 1.5x health and damage)
- [x] Heroic The Deadmines and Ragefire Chasm
- [x] Heroic loot for The Deadmines: one item per boss from a tank/healer/damage pool, Blackened
      Defias Garb set, level 60 gold (`tools/heroic_loot.py`)
- [x] World boss: Hrimthar the Frostbound at Lake Kel'Theril, Winterspring (`tools/world_bosses.py`)
- [x] Expansion content lock (classic only; TBC and Wrath released later), Death Knights GM-only
- [x] Unbound Perks: `/perks` window, 3 Permanent perks, all 25 Offensive perks (5 active at once),
      Paladin Retribution class perk; numbers scaled to normal WoW ranges (about +10% per perk)

- [x] Gear infusion (all 4 stages, 2026-10-14): the collection and its stats (20% per item, diminishing
      returns), item expansion tags, infusing by kills, the Altar of Tribute, item tooltips and the collection
      window (Infusion micro menu button, `/infusion`)

- [x] Classic Heroic dungeons, batch 1 (2026-10-14): Wailing Caverns, Shadowfang Keep, Blackfathom Deeps,
      Gnomeregan, with their summoned creatures (Mutanus, Baron Aquanis, Grubbis, ...) and Heroic loot
      (59 level 60 blues, 910122-910180)

- [x] Classic Heroic dungeons, batch 2 (2026-10-14): Razorfen Kraul, Scarlet Monastery (all 4 wings), Razorfen
      Downs, Uldaman, with their summoned creatures (Tuten'kash, Plaguemaw, the Tomb Fiends, Scarlet Scryers,
      ...) and Heroic loot (68 level 60 blues, 910181-910248)

- [x] Classic Heroic dungeons, batch 3 (2026-10-14): Zul'Farrak, Maraudon, Sunken Temple, Blackrock Depths, with
      their summoned creatures (Gahz'rilla, the pyramid event, Avatar of Hakkar, the Ring of Law, ...) and Heroic
      loot (120 level 60 blues, 910249-910368)

- [x] Classic Heroic dungeons, batch 4 (2026-10-14): Blackrock Spire (Lower and Upper, 15 players), Dire Maul
      (East, West, North), Scholomance, Stratholme (Live and Undead), with their summoned creatures (Gyth, the
      Brazier of Beckoning bosses, Kirtonos, Balnazzar, Ramstein, ...) and Heroic loot (181 level 60 blues,
      910369-910549). All 19 classic dungeons now have a Heroic mode.
- [x] Heroic creatures summoned by spells or transformations (2026-10-14), in all 19 dungeons: Sneed, boss adds,
      totems and wards now come at Heroic level too

- [x] Defensive perks (2026-10-14): 20 working (Greater Bulwark to Heavy Frame, at most 3 active). The old
      placeholders (Thick Skin, Second Wind, Steadfast, Fleet Foot, Treasure Sense) were removed; their ids
      201-203 and 301-302 are not reused.

- [x] Classic Naxxramas (2026-10-15): the 40-player level 60 raid from mod-individual-progression (Naxxramas
      parts only), entrance runestone under the Necropolis in the Eastern Plaguelands, classic attunement,
      Tier 3 quests at Light's Hope

- [x] Onyxia's Lair as a classic level 60 raid (2026-10-15): classic Onyxia, Whelps and Warders, classic
      spell damage, no Lair Guards, classic loot and Head of Onyxia quests, solo scaling

- [x] Perk ranks (2026-10-15, Idea 1: Ranks 1-3 by level, Ranks 4-5 GM-only): 58 of 61 perks
      have ranks; all 57 Offensive, Defensive and Utility perks have 5 ranks (1-3 at levels 1 / 30 / 60, 4-5
      about 1.3x / 1.5x of Rank 3, GM-only via `.perk rank` by design, hidden from players' tooltips; Rapid
      Recovery keeps 3). Values and rank
      levels in `mod_unbound.conf`; "3/5" badges and every rank in the tooltip.

## Next up

- [ ] **Soloable raid mechanics** (moderate, per raid): changes for mechanics no single player can handle,
      only while a raid has one player (`src/unbound_solo_raids.cpp`). First the 13 that block a solo clear:
  - [x] Blackwing Lair (2026-10-15): Razorgore (Grethok's Dominate Mind, eggs broken by walking over them),
        Vaelastrasz (Burning Adrenaline), Ebonroc (Shadow of Ebonroc), Chromaggus (Time Lapse, Chromatic
        Mutation), Nefarian (Shadow Command)
  - [x] Molten Core (2026-10-15): Lucifron's Flamewaker Protectors (Dominate Mind)
  - [x] Zul'Gurub (2026-10-15): Jin'do (Brain Wash Totem, Banish), Hakkar (Cause Insanity, Blood Siphon)
  - [x] Ruins of Ahn'Qiraj (2026-10-15): Ayamiss (Paralyze, larva Feed); Ossirian (no Curse of Tongues, Enveloping
        Winds at most every 40 seconds)
  - [x] Temple of Ahn'Qiraj (2026-10-15): Viscidus (each hit counts 10 times towards freeze and shatter),
        Twin Emperors (Heal Brother), Skeram (True Fulfillment), Qiraji Mindslayer (Cause Insanity)
  - [x] Naxxramas (classic), Thaddius (2026-10-15): Stalagg and Feugen don't revive each other and don't
        overload their Tesla Coils (`Unbound.SoloRaid.Thaddius`)
  - [x] Naxxramas (classic), Gothik (2026-10-15): his phase two teleport keeps the player on his threat
        list (it dropped everyone on the other side, so solo he reset) and the gate is open
        (`Unbound.SoloRaid.Gothik`)
  - [ ] Naxxramas (classic), the rest (checked 2026-10-15): the Four Horsemen stay as they are (all four
        at once with stacking Marks: only beatable solo with `Unbound.Naxx40.Doable.FourHorsemen = 1`, kept
        a server choice on purpose). Sapphiron is fine solo by the script (the player is always the one
        ice-bolted, and the Frost Breath skips ice-bolted players; a pet dies unless behind the block): test
        in game. Fine solo, power checks only: Patchwerk (Hateful Strike falls back to
        the tank, scaled by autobalance like all creature damage), Razuvious, Gluth, Loatheb, Faerlina,
        Kel'Thuzad (his Chains are already off); no problem: Maexxna (never webs her target), Anub'Rekhan,
        Noth, Heigan, Grobbulus
  - [ ] Then, after testing, the risky ones: Core Hounds, Ragnaros' Magma Blast, Firemaw's Flame Buffet,
        Nefarian's Bone Constructs, Mandokir, Thekal, Ossirian, C'Thun, Anubisath Sentinels
  - Shadowflame (Firemaw, Ebonroc, Flamegor, Nefarian) still needs an Onyxia Scale Cloak, which can't be
    obtained on this server (Onyxia isn't skinnable, the pattern drops nowhere, both on purpose). A custom
    way to get one is planned.
- [ ] **More class perks** (large, 1-3 hours each): one per spec, like Paladin Retribution, each worth about
      +25-35% to its spec's single-target damage (the class perk target in the Power budget).
- [ ] **Heroic currency and vendor** (moderate; SaucyHobo54): a token ("Heroic Sigil", renamed from "Heroic Badge" on 2026-10-15) from Heroic bosses,
      spent on companions, mounts, transmog or gear. Becomes the Loot Goblin's currency. Starting values
      (2026-10-15, tune in testing):
  - **Drops:** 1 per Heroic boss, 2 from the final boss (about 7-10 a run), plus 10 from the weekly Heroic
    dungeon quest on the Bulletin Board (decided 2026-10-15: 10 sigils plus 75 gold, `tools/bulletin_board.py`).
  - **Delivery (decided 2026-10-15):** in the loot. `tools/heroic_loot.py` adds the sigil to every Heroic boss's
    loot table (1, or 2 for a final boss). The sigil has `ITEM_FLAG_MULTI_DROP`, so loot is free-for-all: every
    group member gets their own (bots too, harmlessly: an alt-bot's copy never reaches the account balance).
    Final bosses are marked `final=True` in `heroic_loot.py` (26: every dungeon and every wing, the same list as
    `DUNGEONS` in `tools/bulletin_board.py`), not taken from list order: the loot table is keyed by map, and
    the wings of Scarlet Monastery, Dire Maul, Blackrock Spire and Stratholme share one map each.
  - **Heroic gear at the vendor**, priced by item strength. Bosses already drop one Heroic item each (two from
    the final boss), so the vendor is for choosing a piece, not the main source of gear:

    | Item | Price | Runs to afford one |
    |---|---|---|
    | Rings, necks, cloaks, wrists, waists (item level 61) | 10 | 1-1.5 |
    | Head, shoulders, chest, hands, legs, feet (item level 62) | 15 | about 2 |
    | One-handed weapons, shields, off-hands | 20 | 2-3 |
    | Two-handed and ranged weapons, final-boss pieces (item level 63) | 25-30 | 3-4 |

    Kept above "free" on purpose: every unique item counts for infusion (about 255 for +200%), so cheap gear
    would let players buy their way to the endgame. The Mythic currency sits above this at similar ratios.
  - **The Heroic Quartermaster (decided 2026-10-15):** one NPC per capital with a menu of category pages (e.g.
    accessories, armor, weapons), each opening its own vendor list: a 3.3.5 vendor window holds at most 150
    items (`MAX_VENDOR_ITEMS`) and there are 450 Heroic items (910100-910549). Prices use `ItemExtendedCost`
    rows (one per price) in the client patch and on the server. Prices outside gear (companions, consumables,
    mounts, transmog) are still to be decided.
  - **In the Currency tab:** the token is an item in the hidden token bag (bag family "currency tokens"), with
    `CurrencyTypes.dbc` / `CurrencyCategory.dbc` rows in the client patch (e.g. an "Unbound" header). Icon:
    `Spell_Holy_SealOfRighteousness` (a gold lion's head on green); no item display uses it yet, so the patch
    adds a new `ItemDisplayInfo.dbc` row.
  - **Reserved IDs:** item 912000 (currencies 912000-912099), item display 70000, `ItemExtendedCost` 3000+,
    the Quartermaster creature 190104, and the next free `CurrencyTypes` bit (29 is the highest used).
  - **One shared amount per account:** a balance table in the character database (`account, currency item,
    amount`, so the Mythic currency is just another row), set on the character at login (after inventory
    loads) and written back from `OnPlayerSave` and at logout (`OnPlayerSave` has no transaction parameter, so
    it is saved at the same moment as the character, not in the same transaction). The item is soulbound and
    can't be sold, traded or mailed (no counting it twice), with a high stack limit. Only the character a
    player logged in touches the balance: account alt-bots are on (`Playerbots.AllowAccountBots = 1`), and a
    bot-controlled session is `GetSession()->IsHeadless()` (decided 2026-10-15; set when the session has no
    socket, the same check mod-playerbots uses; a real player's session stays non-headless even after a
    disconnect). Optionally store which character holds the balance and ignore writes from any other. GM
    accounts and playerbot (RNDBOT) accounts keep their own amounts.
  - **Tests:** earn on A then log into B (same total); spend on B then back to A; with A online, have alt B as
    a bot earn and spend (the balance must not change); restart mid-session (matches the last save); a vendor
    refund within 2 hours, then switch characters.
  - **Build order** (all SaucyHobo54): Stage A, testable with `.additem`: 1. the sigil (client patch rows and the
    server item; built 2026-10-15), 2. the account balance (built 2026-10-15, `src/unbound_account_currency.cpp`). Stage B: 3. boss drops (`heroic_loot.py`), 4. the Quartermaster, 5. the
    Bulletin Board reward, then the Loot Goblin's price and the Altar of Tribute's prices.
- [ ] **Heroic classic raids** (moderate): Molten Core, Blackwing Lair, Zul'Gurub, Ruins and Temple of
      Ahn'Qiraj, Onyxia's Lair, Naxxramas.
- [x] **Raid Finder** (2026-10-15): a Raids choice in the Dungeon Finder's dropdown listing every raid (those not
      available greyed out with the reason); no queue, the group leader enters first and the group gets a
      prompt to follow; Leave Raid. Later: Normal/Heroic choice once Heroic raids exist, 10/25-player
      choice for Wrath raids once Wrath is released.

## Endgame and rewards

- [x] **Bulletin Board** (2026-10-15): daily kill bounties and profession quests, weekly dungeon and raid quests
      per tier (Normal and Heroic dungeons, Normal raids so far), weekly elite bounty. Add the Mythic and Heroic raid weeklies to
      `tools/bulletin_board.py` when those modes exist; switch rewards to Heroic Sigils / Mythic currency then.

- [ ] **More world bosses** (moderate, mostly data): one per continent and level range, added to
      `tools/world_bosses.py`. Later a weekly rotation (boss of the week) with a first-kill bonus.

- [ ] **Mythic+** (large): player-chosen +1, +2, ... levels on top of Heroic, through mod-autobalance's
      multiplier hook. Scaling and limits per the Power budget (+10% per level added, **maximum +10 for every
      dungeon and raid**, 2 billion clamp). Best after gear infusion (its rewards
      feed infusion). Design (inspired by Peloria's Mythic Keystone, adapted):
  - **Mythic Keystone NPC** just inside the entrance of every dungeon and raid. Spawned automatically when
    an instance is created, at the instance's entry point (from the game's area trigger data), so every
    current and future instance gets one without placing it by hand.
  - **Keystone window** (same style as the perk window), opened by talking to the NPC:
    - **Tier picker:** - and + buttons, a slider from +1 to +10 (the maximum), and quick buttons
      **+1**, **+5**, **Max** (+10) and **Last** (the level of the last run).
    - **Run preview:** enemy power (x(1 + 0.1 x level), e.g. +10 shows x2.0) and the infusion and gold
      reward at that level.
    - **Best cleared** and **Last run**, per character and per instance.
    - **Activate Mythic +N:** group leader only, before the first pull; the level is locked once anything
      is pulled.
    - **Missing Infusions:** every item that can drop in this instance and counts for infusion (green
      or better, within the level rule), built from the instance's loot tables, with a collected count
      (e.g. "12 / 42 infused") and the items still missing highlighted.
  - **Rewards:** **Mythic epic gear** whose stats grow with the level cleared, and the Mythic currency (see
    Power budget, Mythic+ gear), plus **faster infusion** (each kill gives more infusion progress, about
    +10% per Mythic level) and **more gold** from bosses (config settings).
  - **Upgrade NPC** next to the Keystone NPC: raise an owned Mythic item up to your best clear of that
    instance, for gold and Mythic currency.
  - **Entry requirements** (proposed, to confirm before building the Keystone NPC): level cap (60); dungeons
    on Heroic, raids on normal; +1 needs one Heroic (dungeon) or normal (raid) clear of that instance; then
    up to your best clear there + 1, or your best clear anywhere - 5, whichever is higher; a group is
    limited by its lowest member (bots don't count); no item level gate; no keystone item and no timer to
    start with; a failed run costs nothing (the level just isn't recorded as cleared).
  - **Build order:** 1. scaling core (autobalance's `OnAfterDefaultMultiplier` hook, `.mythic set`);
    2. Keystone NPC with a plain menu, best/last per character; 3. Mythic gear generator, drops at the
    cleared level, infusion changes (one item per Mythic piece, percent per level, fourth diminishing
    step); 4. Mythic currency and the Upgrade NPC; 5. other rewards; 6. Keystone window; 7. Missing
    Infusions; 8. raids and tuning. About 8-11 sessions; 1-3 make it playable.
- [ ] **Heroic-only loot** (moderate, mostly data): better versions of drops, or extra drops, on Heroic.
- [ ] **Random item bonuses** (easy): drops sometimes roll an extra enchant (mod-random-enchants).
- [ ] **Daily "Heroic of the Day"** (moderate): one random Heroic gives bonus rewards each day.
- [ ] **Change the Loot Goblin's currency** (easy once the Heroic currency exists).

## Progression past 60

- [ ] **Paragon levels** (moderate to large): XP past 60 earns points for small bonuses (+1% steps).
- [ ] **Achievements for classic Heroics** (easy to moderate, needs a client patch), with titles or
      rewards.

## A living solo world

- [ ] **Auction House bot** (easy): fills the auction house with items (mod-ah-bot).
- [ ] **Bot dungeon groups** (configuration): playerbots fill the party as tank and healer.
- [ ] **Bot battlegrounds** (configuration): playerbots queue for battlegrounds.

## Quality of life

- [ ] **Teleporter NPC or spell** (easy): travel to dungeons, raids and cities.
- [ ] **Account-wide collections** (moderate): companions and mounts on every character.
- [ ] **Personal XP rates** (easy): each player sets their leveling speed (mod-individual-xp).
- [ ] **Challenge modes** (easy to moderate): optional Hardcore or Ironman runs with rewards
      (mod-challenge-modes).
- [ ] **Guild houses** (easy): a private area per guild (mod-guildhouse).

## Open questions

- [x] Disable the `.aoeloot on/off` commands, so AoE loot only comes from the loot companions (2026-10-15).
- [ ] Confirm the content lock and Death Knight block in game on a non-GM account.
