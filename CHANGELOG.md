# Changelog

All features of the Unbound server, with the date each one was added. Dates are Pacific time. Features
from before this repository existed (2026-10-12 and 2026-10-13, before the first commit) are dated from
the work log. Newest first. Add a line here (and a row in the index) with every change.

## Feature index

| Feature | Added | Last changed | By |
|---|---|---|---|
<<<<<<< Updated upstream
| Iron Will utility perk (shorter crowd control, 3 ranks by level) | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
| Perk ranks (first: Rapid Recovery, 3 ranks by level; `.perk rank`) | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
| Gear attunement, stage 2: attuning by kills (`.attune progress`) | 2026-10-14 | 2026-10-14 | Kasix-K |
| Gear attunement, stage 1: collection and stats (GM commands) | 2026-10-14 | 2026-10-14 | Kasix-K |
| Item expansion tags (attunement counts released expansions only) | 2026-10-14 | 2026-10-14 | Kasix-K |
=======
| Perk ranks (first: Rapid Recovery, 3 ranks by level; `.perk rank`) | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
>>>>>>> Stashed changes
| Classic raids soloable (raid scaling to about 3 players' worth) | 2026-10-14 | 2026-10-14 | Kasix-K |
| Power budget (endgame design targets, in the roadmap) | 2026-10-14 | 2026-10-14 | Kasix-K |
| Perks tab on the character sheet (ElvUI skinned) | 2026-10-14 | 2026-10-14 | Kasix-K |
| Perk window: talent-tree style | 2026-10-14 | 2026-10-14 | Kasix-K |
| Chat window load-error guard (Unbound addon) | 2026-10-14 | 2026-10-14 | Kasix-K |
| Paladin Retribution class perk | 2026-10-14 | 2026-10-14 | SaucyHobo54, Kasix-K |
| Offensive perks (25, at most 5 active) | 2026-10-14 | 2026-10-14 | SaucyHobo54, Kasix-K |
| Permanent perks: No Resurrection Sickness, No Daze, Rapid Recovery | 2026-10-14 | 2026-10-14 | SaucyHobo54, Kasix-K |
| Unbound Perks window (`/perks`) and loadouts | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
| World boss: Hrimthar the Frostbound | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
| Heroic loot for The Deadmines (Blackened Defias Garb set) | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
| Heroic The Deadmines and Ragefire Chasm | 2026-10-14 | 2026-10-14 | SaucyHobo54 |
| Collaborator setup script and server settings script | 2026-10-13 | 2026-10-14 | Kasix-K |
| Roadmap (work-on list) | 2026-10-13 | 2026-10-14 | Kasix-K |
| Expansion content lock (classic only) | 2026-10-13 | 2026-10-13 | Kasix-K |
| Death Knights limited to GM accounts | 2026-10-13 | 2026-10-13 | Kasix-K |
| Unbound addon: difficulty menu from level 60, `/heroic`, `/normal` | 2026-10-13 | 2026-10-14 | Kasix-K |
| Classic Heroic dungeons (Stormwind Stockades) | 2026-10-13 | 2026-10-14 | Kasix-K |
| Arcane Loot Scanner companion | 2026-10-13 | 2026-10-13 | Kasix-K |
| Solo dungeon finder (bots stay out of it) | 2026-10-13 | 2026-10-13 | Kasix-K |
| Reset all instances resets raids and heroics too | 2026-10-13 | 2026-10-13 | Kasix-K |
| No raid lockouts, no instances-per-hour limit | 2026-10-13 | 2026-10-13 | Kasix-K |
| Raids without a raid group | 2026-10-13 | 2026-10-13 | Kasix-K |
| Solo dungeon and raid scaling (floor 0.4) | 2026-10-13 | 2026-10-13 | Kasix-K |
| Cross-faction play (everything except battlegrounds) | 2026-10-13 | 2026-10-13 | Kasix-K |
| Loot Goblin companion with auto-loot (55 yards) | 2026-10-13 | 2026-10-13 | Kasix-K |
| AoE looting | 2026-10-13 | 2026-10-13 | Kasix-K |
| Transmog window (mod-transmog-plus), Warpweaver NPC kept | 2026-10-13 | 2026-10-13 | Kasix-K |
| Transmogrify spell | 2026-10-13 | 2026-10-13 | Kasix-K |
| Transmog (first version, mod-transmog) | 2026-10-12 | 2026-10-13 (replaced) | Kasix-K |

## 2026-10-14

### Added
<<<<<<< Updated upstream
- **Gear attunement, stage 2 of 4: attuning.** Equipped items that count progress with every kill of a creature
  that would give experience (1 kill, elites 2, bosses 10; group members in range get it too) and are attuned
  for good at 50 kills (green), 100 (blue), 200 (epic) or 400 (legendary). Progress is kept per item
  (unequipping pauses it); chat shows 25/50/75% and "fully attuned" with the achievement sound. Players see
  their equipped items' progress with `.attune progress`.
- **Class perk target** in the power budget: each spec's class perk is worth about +25-35% to that spec's
  single-target damage (Retribution estimated at about +35-40%, to confirm on a training dummy).
- **Iron Will** (Utility perk, id 303): enemy crowd control on you and your pets (stun, fear, root, silence,
  sleep, polymorph, charm, disorient, sap) lasts 10% shorter at Rank 1 (level 1), 20% at Rank 2 (level 30)
  and 30% at Rank 3 (level 60). Stacks with racials, talents and diminishing returns. Values and rank levels
  are in `mod_unbound.conf` (`Unbound.Perks.IronWill.*`); GMs can test ranks with `.perk rank 303 <rank>`.
=======
>>>>>>> Stashed changes
- **Perk ranks**, starting with Rapid Recovery: Rank 1 (6 seconds after combat, 4% health and mana per
  second) from level 1, Rank 2 (5 s, 6%) from level 30, Rank 3 (4 s, 8%) from level 60. Values and rank
  levels are in `mod_unbound.conf`. GMs set a rank with `.perk rank <perk id> <rank>` (saved per
  character; `.perk rank <perk id>` goes back to the level's rank). The perk window shows "2/3" badges and
  every rank in the tooltip.
<<<<<<< Updated upstream
- **Gear attunement, stage 1 of 4** (the collection and its stats): each character has a collection of
  attuned items that permanently give 20% of their fixed stats (applied like gear stats, shown on the
  character sheet), with diminishing returns (full value until 100% of a full set of gear, half until 200%,
  a quarter beyond). Counts: green or better weapons and armour, required level 50-60, fixed stats, from a
  released expansion. For now items are added with GM commands (`.attune add/remove/check/info/reset`);
  attuning by kills, the sacrifice altar and the tooltips/collection window follow.
- **Item expansion tags** (`tools/item_expansions.py`): 20,286 gear items tagged with the expansion they come
  from (8,612 classic, 4,870 TBC, 6,804 WotLK), so TBC and Wrath items can't count until those are released.
=======
>>>>>>> Stashed changes
- **Perks tab on the character sheet.** A "Perks" tab after Character, Pet, Reputation, Skills and
  Currency, built from the game's own tab template. It opens the perk window beside the character sheet.
  With ElvUI's character skin on, ElvUI skins it like its other tabs.
- **Perk window: talent-tree style** (chosen look). Perk icons in a grid with action-button frames and
  talent-style rank badges (0/1, 1/1), a gold glow on active perks, greyed icons when a category is full,
  tooltips, right-click or double-click to toggle. Uses the game's own frame art (dialog border, title
  banner, red buttons). A Blizzard-style list version came first the same day and was replaced.
- **Paladin Retribution class perk:** Divine Storm hits up to 6 enemies, each also taking a Crusader
  Strike; Judgements spread to up to 4 more enemies with a free Exorcism on each; Exorcism scales with 30%
  of attack power and spell power; Righteous Vengeance explosions on up to 5 enemies; Holy damage +15%,
  Physical +10%.
- **All 25 Offensive perks**, at most 5 active at once: Cyclic Power, Critical Understanding, Defensive
  Sacrifice, Desperate Power, Block/Dodge/Parry/Haste Capping, Pet Encouragement, Rolling Momentum,
  Tunnel Vision, Collateral Damage, Giant Slayer, Merciless, Pressure, Chaos, Power Conversion, Healing
  Powah and the seven school Masteries.
- **Permanent perks** for every player: No Resurrection Sickness, No Daze, Rapid Recovery (8% health and
  mana per second, 4 seconds after combat).
- **Unbound Perks window** (`/perks`): categories, search, saved loadouts; the server keeps each
  character's perks. Defensive and Utility perks are listed but don't work yet.
- **World boss: Hrimthar the Frostbound**, a level 63 frost giant on Lake Kel'Theril in Winterspring,
  tuned for about 10 players, with six level 60 epics and a 3% Winterspring Frostsaber.
- **Heroic loot for The Deadmines:** one level 60 blue per boss from a tank/healer/damage pool, two from
  Edwin VanCleef, the Blackened Defias Garb set, level 60 gold, a 1% Hyacinth Macaw from Captain Greenskin.
- **Heroic The Deadmines and Ragefire Chasm.**
- **Chat window guard** in the Unbound addon: stops a load-time chat error
  (`FloatingChatFrame.lua:1281`, seen with ElvUI's chat).
- **Power budget** in the roadmap: the endgame goal (one player solos a full Mythic raid) and the power
  targets every system is designed against. Gear attunement is the main lever: 20% of each unique item's
  stats, green or better, required level within 10 of the cap, diminishing returns past +100% and +200%;
  about 170 level 60 blue/epic items for about +200%. Mythic +10% per level (added), capstone Mythic +10,
  configurable maximum (start +30), 2 billion safety clamp. Fully progressed player about 6x a normal level 60.
  Attunement and sacrifice: both styles fill one shared collection at the full 20%; attuning is free but
  slow and only for gear the character can equip; sacrifice is instant, works on any item, costs gold (Heroic
  Badges later) scaled by quality, double for gear the character could attune. Collected stats are permanent
  (kept after unequipping, selling or deleting the item); attunement progress is saved per item; stats only
  arrive at 100%. Per character, with sacrifice at an altar NPC in the capital cities.
  Sacrifice prices: 2/10/50/250 gold for green/blue/epic/legendary, double for gear the character could attune.
- **Mythic+ design** in the roadmap: a Mythic Keystone NPC at the entrance of every dungeon and raid
  (spawned automatically), a Keystone window (tier picker with -/+, slider, +1, +5, Max and Last; run preview;
  best and last run; activate before the first pull; Missing Attunements for the instance), and rewards per
  level of faster attunement plus more gold.
<<<<<<< Updated upstream
- **Attunement kill rules** in the roadmap: 50/100/200 kills for green/blue/epic (elite 2, boss 10), only
  creatures that would give experience; only items from released expansions count (tagged per item, following
  `Unbound.ExpansionUnlocked`).
=======
>>>>>>> Stashed changes

### Changed
- **Classic raids soloable:** solo scaling for 20-player raids (Zul'Gurub, Ruins of Ahn'Qiraj) and
  40-player raids (Molten Core, Blackwing Lair, Temple of Ahn'Qiraj) lowered so one player faces about 3
  players' worth of the raid (was about 9 and 17); a full raid is unchanged. Dungeons are unchanged.
- **Perk numbers scaled to normal WoW ranges** (about +10% per perk) instead of Peloria-sized values;
  Retribution went from Holy x59 / Physical x27 to +15% / +10%; Rapid Recovery from 15% after 3 seconds
  to 8% after 4 seconds; the stat-based perks now work with level 60 stats.
- **The client uses the official ElvUI 6.09** instead of Synastria's build (which errored on this
  server). Client-side only; see the README.

### Fixed
- **Class perks only work for their own class**: the server refuses them for any other class (the window
  hid them, but a `/script` command could turn them on).

## 2026-10-13

### Added
- **Collaborator setup:** one script installs a complete copy of the server (pinned AzerothCore and
  module versions, all server settings, start/stop/rebuild scripts, client addons and patch), plus a
  script with every changed server setting. Step-by-step setup in the README.
- **Roadmap** (`ROADMAP.md`): the work-on list.
- **Expansion content lock:** classic only for now. The Burning Crusade and Wrath of the Lich King
  dungeons, raids, dungeon finder entries and zones are closed; level cap 60; playerbots stay in classic
  content. Blood Elf and Draenei starting zones stay open.
- **Death Knights limited to GM accounts** while Wrath is locked (Ebon Hold stays open for them).
- **Unbound addon:** Dungeon and Raid Difficulty in the portrait menu from level 60 (the game's own limit
  is 65), plus `/heroic` and `/normal`.
- **Classic Heroic dungeons**, starting with Stormwind Stockades: level 60 (any level above too), 60-62
  creatures with 1.5x health and damage, normal loot.
- **Arcane Loot Scanner companion:** a shrunken Arcane Protector with the Loot Goblin's loot powers, 10 gold
  from Grizzle Lootsnatch.
- **Solo dungeon finder**: queue alone or with bots and go straight in. Random playerbots no longer join
  the dungeon finder.
- **Reset all instances** (portrait menu) also resets raid and heroic saves.
- **No raid lockouts and no instances-per-hour limit.**
- **Raids can be entered without a raid group.**
- **Solo dungeon and raid scaling** (mod-autobalance), never below 40% strength; creature levels, XP and
  gold stay normal.
- **Cross-faction play:** groups, raids, guilds, chat, channels, trade, auction house and calendar
  (battlegrounds stay separate).
- **Loot Goblin companion** (10 gold from Grizzle Lootsnatch): while it's out, corpses within 55 yards are
  looted automatically and AoE looting is on.
- **AoE looting** (mod-aoe-loot), later tied to the loot companions.
- **Transmog window** from mod-transmog-plus (free, mixed armour types allowed), keeping the Warpweaver
  NPC (190010).
- **Transmogrify spell:** every character can open the transmog window from anywhere.

### Changed
- **Transmog:** mod-transmog replaced by mod-transmog-plus.

## 2026-10-12

### Added
- **Transmog** (first version, mod-transmog with the Warpweaver NPC). Replaced on 2026-10-13.
- **Client:** the Unbound client set up with Peloria's visual patch packs.
