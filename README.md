# mod-unbound

Custom features for the WoW 3.3.5a Unbound server.

## Changelog

Planned and possible features are in [ROADMAP.md](ROADMAP.md).

All features of the Unbound server, with the date each one was added. Dates are Pacific time. Features
from before this repository existed (2026-10-12 and 2026-10-13, before the first commit) are dated from
the work log. Newest first. Add every new or changed feature here under today's date, and update its row in the index.

### Feature index

| Feature | Added | Last changed | By |
|---|---|---|---|
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

### 2026-10-14

#### Added
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

#### Changed
- **Perk numbers scaled to normal WoW ranges** (about +10% per perk) instead of Peloria-sized values;
  Retribution went from Holy x59 / Physical x27 to +15% / +10%; Rapid Recovery from 15% after 3 seconds
  to 8% after 4 seconds; the stat-based perks now work with level 60 stats.
- **The client uses the official ElvUI 6.09** instead of Synastria's build (which errored on this
  server). Client-side only; see the README.

#### Fixed
- **Class perks only work for their own class**: the server refuses them for any other class (the window
  hid them, but a `/script` command could turn them on).

### 2026-10-13

#### Added
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

#### Changed
- **Transmog:** mod-transmog replaced by mod-transmog-plus.

### 2026-10-12

#### Added
- **Transmog** (first version, mod-transmog with the Warpweaver NPC). Replaced on 2026-10-13.
- **Client:** the Unbound client set up with Peloria's visual patch packs.

## Technical notes

How each system is built and what to run after changing it (what the features do and when they were
added is in the Changelog above).

- **Transmogrify spell (200200):** learned on login; opens the mod-transmog-plus window (5 s cooldown,
  usable while mounted, not in combat). Needs `Transmog.OpenAnywhere = 1` and the `Transmog` addon.
- **Loot companions:** Loot Goblin (item 910001, spell 200201, creature 190100) and Arcane Loot Scanner
  (item 910002, spell 200202, creature 190102, the Arcane Protector 16504 shrunk), sold by Grizzle
  Lootsnatch (vendor 190101, `.npc add 190101`). While one is out, corpses within `AOELoot.Range` are
  auto-looted once a second (gold shared with the group; items needing a roll or the master looter, and
  anything that doesn't fit in the bags, stay on the corpse) and mod-aoe-loot is on. Price/currency:
  `data/sql/db-world/unbound_loot_goblin.sql`.
- **Reset all instances:** resets all raid saves (any difficulty) and heroic and normal dungeon saves,
  whatever the difficulty setting. In a group only the leader can, for the group's instances; an instance
  with players still inside isn't reset.
- **Classic heroics:** `tools/classic_heroics.py` lists them (`HEROIC_DUNGEONS`, only append: the order
  sets access ids). Heroic creatures are copies (entry + 1000000) at level 60-62 with 1.5x health and
  damage. After a change run `python tools/classic_heroics.py` and `python tools/custom_dbc.py`.
- **Heroic loot:** `tools/heroic_loot.py` defines heroic items (910100-910999), sets (950-999) and boss
  loot. After a change run `python tools/heroic_loot.py`, `python tools/classic_heroics.py` and
  `python tools/custom_dbc.py`, then restart the worldserver. Never delete an item that has dropped: take
  it out of `LOOT` instead.
- **World bosses:** `tools/world_bosses.py` (SmartAI fights, no C++; creatures 190110-190199, spawn guids
  9190110-9190199, loot 911000-911999). Hrimthar is creature 190110, adds 190111. After a change run
  `python tools/world_bosses.py` and `python tools/custom_dbc.py`, then restart the worldserver.
- **Perks:** window in `addon/UnboundPerks` (`PerkData.lua` = perk list and descriptions); server side in
  `src/unbound_perks.cpp`. The addon whispers its own character (prefix `UBPERK`: `SYNC`, `SET:<id>:<0|1>`,
  `LOAD:<ids>`; the server answers `STATE:<ids>` or `ERR:<text>`); active perks are saved in
  `characters.character_unbound_perks`. No changes in combat, at most 5 Offensive perks, class perks only
  for their class (`CLASS_PERKS`). No Resurrection Sickness and No Daze are `Death.SicknessLevel = 255` and
  `Daze.Enabled = 0` (set by `apply-unbound-settings.ps1`); Rapid Recovery is `Unbound.Perks.RapidRecovery*`
  in `mod_unbound.conf`. Retribution's spell scripts: `data/sql/db-world/unbound_perks_spells.sql`. Perk
  numbers stay in normal WoW ranges (about +10% per perk); they are constants at the top of
  `unbound_perks.cpp` and must match `PerkData.lua`. The perk code assumes `MapUpdate.Threads = 1`.
- **Unbound addon** (`addon/Unbound`): difficulty menu from level 60, `/heroic`, `/normal`, and the
  chat-window load-error guard.
- **Expansion content lock:** `Unbound.ExpansionUnlocked` in `mod_unbound.conf` (0/1/2). Players in a
  locked zone go to their hearthstone, else their race's start, else their faction's capital; GMs with GM
  mode on, battlegrounds and arenas are exempt. Death Knights are GM-only through
  `CharacterCreating.Disabled.ClassMask = 32`. Releasing an expansion: raise `Unbound.ExpansionUnlocked`
  and `MaxPlayerLevel` (70/80) and, for Wrath, clear the class mask (see the cheat sheet for playerbots).

## Custom spells, items and companions

Spells, item DBC rows and Companions-tab entries are defined once in `tools/custom_dbc.py`. That script
generates both sides:

- server: `data/sql/db-world/unbound_custom_dbc.sql` (applied automatically when the worldserver starts)
- client: `<client>\Data\patch-Z.MPQ` (`--client`, default `E:\WoW 3.3.5a Unbound`)

After changing one, run `python tools/custom_dbc.py`, restart the worldserver, and restart the client
(delete the client's `Cache` folder if the old tooltip still shows).

## Working together

This repository is private; the owner invites collaborators under Settings > Collaborators. Each person
runs their own server and database; Git shares only this module's code.

### First-time setup (a new PC)

`server-setup/setup-wow-server.ps1` installs a complete copy of the Unbound server: the build tools,
MySQL, AzerothCore and every module at the same versions as the original, your own databases, the
original's server settings, the start/stop/rebuild scripts and the cheat sheet. Your characters and
accounts are your own; all the custom game data (heroics, companions, vendors) builds itself.

**You need:**

- Windows 10/11, about 60 GB free for the server, plus room for the game client.
- [Git for Windows](https://git-scm.com/download/win), [Python 3](https://www.python.org/downloads/)
  (tick "Add python.exe to PATH" when installing), and
  [Visual Studio Build Tools 2022](https://visualstudio.microsoft.com/visual-cpp-build-tools/) (the script
  adds the C++ part itself).
- Access to this repository (the owner invites you under Settings > Collaborators).
- A copy of the **Unbound game client** from the owner (it is far too big for GitHub, around 40 GB, and
  includes the visual patch packs). Copy it anywhere, e.g. `D:\WoW 3.3.5a Unbound`. The owner can leave
  out its `WTF` and `Cache` folders (personal settings and saved account name).

**Steps:**

1. Download this repository: on GitHub, **Code > Download ZIP**, and unzip it anywhere (e.g. Downloads).
   This copy is only used to start the setup; the script clones its own copy into the server.
2. Open PowerShell and run the setup script, with `-Root` set to the folder for the server:

   ```bash
   powershell -ExecutionPolicy Bypass -File "$HOME\Downloads\mod-unbound-main\server-setup\setup-wow-server.ps1" -Root "D:\WoW Solo Server"
   ```

   It asks a few questions (a MySQL password to choose, a GitHub sign-in for this repository, the client
   folder at the end). The build takes 30-90 minutes. If anything stops it, fix that and run it again;
   finished steps are skipped.
3. Check the client points at your own PC: `Data\enUS\realmlist.wtf` in the client folder should say
   `set realmlist 127.0.0.1` (the owner's copy already does).
4. Double-click `Start Server.bat` in the server folder. The first start fills the databases and takes
   several minutes.
5. In the worldserver window, make your account and make it a GM:

   ```
   account create <name> <password>
   account set gmlevel <name> 3 -1
   ```

6. Log in. `Server Cheat Sheet.md` in the server folder has everything else (NPCs to place, commands).

**Setting up the client by hand** (if you skipped the script's last step): copy `addon\Unbound` and
`addon\UnboundPerks` from this repository and `addon\Transmog` from `azerothcore\modules\mod-transmog-plus` into the client's
`Interface\AddOns`, then build the client patch (with the game closed):

```bash
python tools/custom_dbc.py --client "D:\WoW 3.3.5a Unbound" --dbc "D:\WoW Solo Server\data\dbc"
```

**ElvUI: use the official 6.09.** The Unbound client first came with Synastria's build of ElvUI, which
changes 36 files (attunement icons that call Synastria-only client functions, plus changes to movers,
config, media, bars and skins). On this server it errors, e.g. with the character skin on:
`Interface\AddOns\ElvUI\Core\Attune.lua:91: attempt to call global 'ItemLocIsLoaded' (a nil value)`.
The fix is to replace `ElvUI` and `ElvUI_OptionsUI` in the client's `Interface\AddOns` with the official
ElvUI 6.09 for 3.3.5a (the version the Synastria build is based on), with the game closed:

```bash
git clone --depth 1 --branch 6.09 https://github.com/ElvUI-WotLK/ElvUI.git ElvUI-6.09
```

Then copy its `ElvUI` and `ElvUI_OptionsUI` folders over the client's (delete the old ones first). Keep
`ElvUI_AddOnSkins` (it has no Synastria code). ElvUI settings carry over (same save files). A client with
`Interface\AddOns\ElvUI\Core\Attune.lua` still has the Synastria build.

**Server settings:** `server-setup/apply-unbound-settings.ps1` holds every setting the Unbound server
changes from the defaults (level 60 cap, cross-faction, faster XP, solo scaling floor 0.4, transmog,
playerbots, ...). The setup script applies it to new config files; run it again (servers stopped) after
pulling a settings change:

```bash
powershell -ExecutionPolicy Bypass -File server-setup\apply-unbound-settings.ps1 -ConfigDir "D:\WoW Solo Server\server\configs"
```

**Module versions:** the AzerothCore and module versions are pinned in `server-setup/setup-wow-server.ps1`
(`$CoreCommit`, `$Modules`). When the original server updates one, update it there too.

### Day to day

- Before starting: `git pull`.
- When done: `git add -A`, `git commit -m "what changed"`, `git push`. If the push is rejected, `git pull`
  first, fix any conflicts, then push again.
- After pulling someone else's changes:
  - C++ changed (`src/`): rebuild the worldserver.
  - SQL changed (`data/sql/`): restart the worldserver.
  - `tools/custom_dbc.py` or `tools/classic_heroics.py` changed: run it again (custom_dbc.py with your
    `--client`), restart the worldserver and the client.
  - `server-setup/apply-unbound-settings.ps1` changed: run it on your configs, restart the worldserver.
  - `addon/` changed: copy the addon into your client's `Interface\AddOns` again.
- Keep `server-setup/Server Cheat Sheet.md` and `ROADMAP.md` up to date with your changes, and add every
  new or changed feature to the README's Changelog under today's date (and update its row in the feature
  index).
- New features go in their own `src/unbound_<feature>.cpp`, registered in `src/unbound_loader.cpp`, and get
  an entry in the Changelog above (plus Technical notes if others need to know how it works).
- Custom IDs are shared, so pick new ones next to the existing ones and say so in the commit: spells
  2002xx, items 9100xx (heroic loot 910100-910999, world boss loot 911000-911999), item sets 950-999,
  creatures 1901xx (world bosses 190110-190199, spawn guids 9190110-9190199),
  SkillLineAbility 9000xx.
