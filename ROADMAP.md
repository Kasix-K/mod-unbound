# Roadmap

Work-on list for the Unbound server. Tick a box (`- [x]`) when a feature is done and add it to the
[CHANGELOG.md](CHANGELOG.md) under that day's date. Effort is a rough guess: **easy** (a config or ready-made
module), **moderate** (custom code or data), **large** (several parts, client changes).

Guiding idea: inspired by Peloria, not a copy. No Peloria-sized numbers (billions): a fully progressed
player is at most several times a normal level 60, and every number stays far below the 32-bit limits.

## Power budget

The endgame goal: **one player can solo a full Mythic raid** (the player count will be low). Raids are
scaled down to one player, and **gear attunement is the main lever** that lets a player climb Mythic
levels; perks and perk ranks add on top. Design every power system against these targets, and change the
numbers here first if testing says so. Every number below is meant to be a config setting.

### Content

| Lever | Target |
|---|---|
| Classic raids solo (mod-autobalance) | A solo player faces **about 3 players' worth** of a raid; a full raid is unchanged. 20-player raids: `AutoBalance.InflectionPointRaid20M.CurveFloor = 0.1` (2.9 players' worth); 40-player raids: `AutoBalance.InflectionPointRaid40M.CurveFloor = 0.03` (2.8). Set 2026-10-14. |
| Mythic scaling | **+10% per level, added** (not multiplied): Mythic +10 = 2x, +20 = 3x the solo raid |
| Mythic capstone | **Mythic +10** is the first goal for a fully attuned player |
| Mythic maximum | Configurable, start at **Mythic +30** (the long climb past the capstone); raise it as players progress |
| Safety clamp | No creature health or damage above **2 billion**, whatever the settings (the 3.3.5 client shows numbers above about 2.1 billion wrongly). With added scaling this is never reached in practice: the biggest classic boss (Vaelastrasz, 3.3 million health) would pass it only around Mythic +90,000 solo |

### Player power needed

| Raid | Player power needed (x a normal level 60) |
|---|---|
| Base solo raid | about 2.8x |
| Mythic +5 | about 4.2x |
| Mythic +10 (capstone) | about 5.6x |
| Mythic +20 | about 8.4x |

### Player

| Lever | Target |
|---|---|
| Gear | Normal level 60 gear: the baseline (1x) |
| Perks | About **x1.55** with five Offensive perks (about +10% per perk) |
| Perk ranks | Up to about **x1.3** more on top of perks (together about x2) |
| Gear attunement / sacrifice | About **+200% of gear stats** when well collected (about x3), the main lever: |
| - per item | **20%** of the item's fixed stats (tune 15-25% in testing); fixed stats only (no procs, set bonuses, weapon damage) |
| - which items count | **Every unique item** counts once (a second copy adds nothing); **green or better** |
| - minimum item level | Only items whose **required level is within 10 of the level cap** count (level 50+ while the cap is 60; it moves up with each expansion), so every attuned item matters and nobody grinds low-level items |
| - diminishing returns | Full value up to **+100%** of gear stats, half value up to **+200%**, a quarter beyond: early collecting feels strong, the long tail is the endgame grind (no hard cap) |
| - the grind | About **170 level 60 blue/epic items** for +200% (about 220 blues or 130 epics; raid epics are the fast track) |
| **Total** | About **6x** a normal level 60 when fully progressed: Mythic +10. Each further Mythic level needs more collected gear and higher perk ranks |

Numbers check: a 6x character has a few thousand of a primary stat and tens of thousands of health, well
above normal WoW but nowhere near Peloria's billions.

### Attunement and sacrifice rules

Both styles fill **one shared collection** per character, so the end result is the same: an item gives
its full 20% whichever way it was collected. Time versus cost is the whole trade-off.

| | Attune | Sacrifice |
|---|---|---|
| How | Equip the item and kill creatures until it reaches 100% | Destroy the item for its stats at once |
| Speed | Slow | Instant |
| The item | **Kept**: wear it, transmog it, sell it later | **Destroyed** |
| Which items | Only gear the character **can equip** (their armour type, their class's weapons) | **Any item** that counts (see the Player table), including gear the character could attune |
| Value | **Full 20%** | **Full 20%** (not reduced) |
| Cost | Free | A price scaled by quality: gold for now, Heroic Badges once they exist |
| Cost for gear the character could attune | (free) | **Double** the normal price, so attuning stays the main route for one's own gear |

- **Collected stats are permanent:** once an item is 100% attuned (or sacrificed), its 20% stays whatever
  happens to the item (unequipped, banked, sold, deleted). An upgrade never costs anything: attune it too
  and both count.
- **Progress is saved per item:** unequipping a partly attuned item pauses it (60% stays 60%); equipping it
  again carries on from there.
- **Stats only at 100%:** a partly attuned item gives nothing yet; its full 20% arrives when it reaches 100%.
- An item counts only once. Sacrificing a partly attuned item finishes it (the price still applies).
- Sacrifice always shows a confirmation (item and price) before destroying anything.
- Tooltips show "Attunement: 37%", "Attuned", or "Can't attune: sacrifice only".
- A collection window in the perks' talent-tree style shows every absorbed item and the stat totals.
- Still to decide: an altar NPC in the capitals, a Sacrifice spell, or both; per character or
  account-wide; the exact prices.

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

## Next up

- [ ] **Gear attunement and sacrifice** (large): absorb stats from acquired gear, either by attuning it
      (equip it and kill creatures until 100%, Synastria-style) or by sacrificing it (destroy it for its
      stats at once, Peloria-style). Both styles, one shared collection. The main lever for soloing
      Mythic raids: numbers, item rules, minimum item level and the attune/sacrifice rules per the Power
      budget. Still to decide: altar NPC or Sacrifice spell, per character or account-wide, prices.
- [ ] **Soloable raid mechanics** (moderate, per raid): script changes for bosses that need several
      players (Razorgore, Twin Emperors, C'Thun, ...).
- [ ] **Perk ranks** (moderate): ranks like spell ranks for perks with a number (Rapid Recovery,
      Masteries, Pressure, ...). Add the rank support soon (a rank column, per-rank values, "Rank 1 / 1" in
      the window, a GM command to set ranks) so new perks are written with ranks from the start; the rank
      values and how ranks are earned (levels, Heroic currency, quests) can come later.
- [ ] **Defensive and Utility perks** (moderate): Thick Skin, Second Wind, Steadfast, Fleet Foot,
      Treasure Sense are listed in the window but do nothing yet.
- [ ] **More class perks** (large, 1-3 hours each): one per spec, like Paladin Retribution, at the same
      scale (about +10-15%, not Peloria's x27/x59).

- [ ] **Remaining classic Heroic dungeons** (moderate): 16 more (Stockades, Deadmines and Ragefire Chasm
      are done), added in batches by level range.
      Each is one line in `tools/classic_heroics.py`. Also give heroic versions to creatures that boss
      scripts summon (Blackrock Depths' Ring of Law, the Zul'Farrak stairs, Razorfen Downs' gong,
      Stratholme's Baron run, Arugal's adds, Gnomeregan). Blackrock Spire keeps its larger group size.
- [ ] **Heroic loot for the other heroics** (moderate): same approach as The Deadmines, one dungeon at a
      time in `tools/heroic_loot.py`.
- [ ] **Heroic currency and vendor** (moderate): a token (e.g. "Heroic Badge") from Heroic bosses,
      spent on companions, mounts, transmog or gear. Becomes the Loot Goblin's currency.
- [ ] **Heroic classic raids** (moderate): Molten Core, Blackwing Lair, Zul'Gurub, Ruins and Temple of
      Ahn'Qiraj. (In 3.3.5, Onyxia and Naxxramas only exist as their level-80 versions.)
- [ ] **Raid Finder** (moderate to large): raids in the dungeon finder in level brackets. Still to
      decide: strict brackets or every raid up to the player's level; an addon window plus a
      server hook.

## Endgame and rewards

- [ ] **More world bosses** (moderate, mostly data): one per continent and level range, added to
      `tools/world_bosses.py`. Later a weekly rotation (boss of the week) with a first-kill bonus.

- [ ] **Mythic+** (large): player-chosen +1, +2, ... levels on top of Heroic, through mod-autobalance's
      multiplier hook. Still to decide: scaling per level (about +10% suggested), the cap, and how a
      level is chosen (NPC or command). Best after the Heroic currency.
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

- [ ] Disable the `.aoeloot on/off` commands, so AoE loot only comes from the loot companions?
- [ ] Confirm the content lock and Death Knight block in game on a non-GM account.
