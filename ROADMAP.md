# Roadmap

Work-on list for the Unbound server. Tick a box (`- [x]`) when a feature is done and add it to the
Features list in [README.md](README.md). Effort is a rough guess: **easy** (a config or ready-made
module), **moderate** (custom code or data), **large** (several parts, client changes).

Guiding idea: inspired by Peloria, not a copy. Stats stay in normal WoW ranges (no huge numbers).

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
