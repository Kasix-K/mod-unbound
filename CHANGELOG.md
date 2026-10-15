# Changelog

All features of the Unbound server, with the date each one was added. Dates are Pacific time. Features
from before this repository existed (2026-10-12 and 2026-10-13, before the first commit) are dated from
the work log. Newest first. Add a line here (and a row in the index) with every change.

## Feature index

| Feature | Added | Last changed | By |
|---|---|---|---|
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
  targets every system is designed against (fully progressed player about 2.5-3x a normal level 60).

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
