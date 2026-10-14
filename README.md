# mod-unbound

Custom features for the WoW 3.3.5a Unbound server.

## Features

- **Transmogrify spell (200200)**: every character learns it on login. Casting it opens the
  mod-transmog-plus Transmogrify window anywhere (5 s cooldown, usable while mounted, not in combat).
  Requires mod-transmog-plus with `Transmog.OpenAnywhere = 1` and its `Transmog` addon in the client.
- **Loot Goblin companion (item 910001, spell 200201, creature 190100)**: sold for 10 gold by
  Grizzle Lootsnatch (vendor 190101, place with `.npc add 190101`). While the character's Loot Goblin
  is summoned, it auto-loots every corpse they may loot within `AOELoot.Range` once a second (gold is
  shared with the group; items needing a roll or the master looter, and anything that doesn't fit in
  the bags, stay on the corpse), and AoE looting (mod-aoe-loot) is on for corpses opened by hand.
  Without the goblin, both are off. Price/currency:
  `data/sql/db-world/unbound_loot_goblin.sql`.
- **Arcane Loot Scanner companion (item 910002, spell 200202, creature 190102)**: the Arcane Protector
  (16504) shrunk to companion size, also sold by Grizzle for 10 gold, with the same loot powers as the
  Loot Goblin.
- **Reset all instances resets everything**: the portrait menu's Reset all instances resets all of the
  player's raid saves (any difficulty) and heroic and normal dungeon saves, whatever the dungeon
  difficulty is set to. In a group only the leader can, and it resets the group's instances; an
  instance with players still inside isn't reset.
- **Classic heroic dungeons**: `tools/classic_heroics.py` lists the classic dungeons with a heroic mode
  (so far: Stormwind Stockades, The Deadmines, Ragefire Chasm). Heroic needs level 60; creatures are
  heroic copies (entry + 1000000) at level 60-62 with 1.5x health and damage. Loot is the normal loot
  unless the dungeon has heroic loot (below). Add a dungeon to `HEROIC_DUNGEONS`, then run
  `python tools/classic_heroics.py` and `python tools/custom_dbc.py`.
- **Heroic loot** (`tools/heroic_loot.py`): heroic bosses get their own loot tables and level 60 gold
  (20-40 silver, final boss 50 silver-1 gold). So far: The Deadmines. Every boss drops one item from a
  pool of three (tank, healer/caster, damage), and Edwin VanCleef drops two: level 60 blue remakes of the
  classic drops plus new pieces (items 910100-910121, item level 61-63, "Heroic" in the tooltip). The
  leather pieces form the **Blackened Defias Garb** set (item set 950: 2 pieces +12 Agility, 4 pieces
  +30 Attack Power), and Captain Greenskin has a 1% chance to drop the Hyacinth Macaw companion. Items,
  sets and loot are defined once in `heroic_loot.py`; after a change run `python tools/heroic_loot.py`,
  `python tools/classic_heroics.py` and `python tools/custom_dbc.py` (rebuilds the client patch), then
  restart the worldserver. Never delete an item that has dropped: take it out of `LOOT` instead.
- **World bosses** (`tools/world_bosses.py`): open-world bosses with a SmartAI fight (no C++), yells
  every player online hears, and their own loot. So far: **Hrimthar the Frostbound** (creature 190110),
  a level 63 frost giant on the ice of Lake Kel'Theril in Winterspring, tuned for about 10 players
  (one player plus bots), about 283k health, 3-day respawn. Neutral like Azuregos, so he only fights
  those who attack him. Frostbolt Volley, Frost Breath (frontal cone) and Frost Nova; at 50% he
  summons four Frostbound Shards (190111), at 20% he enrages. Drops one of six level 60 epics (items
  911000-911005, item level 66-68), 5-8 gold, and a 3% chance at the Reins of the Winterspring
  Frostsaber. After a change run `python tools/world_bosses.py` and `python tools/custom_dbc.py`, then
  restart the worldserver.
- **Unbound Perks** (`addon/UnboundPerks`, copy to `Interface/AddOns`, open with `/perks`): the Character
  Perks window (drawn with the game's own Blizzard frame art: dialog border and title banner, red buttons,
  check boxes) with categories, search and saved loadouts. The three Permanent perks work for everyone:
  No Resurrection Sickness (`Death.SicknessLevel = 255`), No Daze (`Daze.Enabled = 0`), both set by
  `apply-unbound-settings.ps1`, and Rapid Recovery (`src/unbound_perks.cpp`: 4 seconds after leaving
  combat, 8% of maximum health and mana every second until full; `Unbound.Perks.RapidRecovery*` in
  `mod_unbound.conf`). Toggled perks are kept by the server (whispered addon messages, prefix `UBPERK`;
  saved in `characters.character_unbound_perks`; no changes in combat; at most 5 Offensive perks
  active at once; class perks only for their own class, checked by the server). Working so far: Cyclic Power,
  Critical Understanding, Defensive Sacrifice, Desperate Power, Block/Dodge/Parry/Haste
  Capping, Pet Encouragement, Rolling Momentum, Tunnel Vision, Collateral Damage, Giant Slayer, Merciless,
  Pressure, Chaos, Power Conversion, Healing Powah, and the seven school Masteries
  (Physical, Holy, Fire, Nature, Frost, Shadow, Arcane): all 25 Offensive perks.
  Class perks: Paladin **Retribution** (Divine Storm hits up to 6 enemies, each also taking a Crusader
  Strike; Judgements spread to up to 4 more enemies with free Exorcisms; Exorcism at 30% AP/SP; Righteous
  Vengeance explosions on up to 5 enemies; Holy damage +15% and Physical +10%; spell scripts in
  `data/sql/db-world/unbound_perks_spells.sql`). The other perks are listed but have no effect yet.
  **Perk numbers stay in normal WoW ranges** (no Peloria-sized scaling): one perk is worth about +10%
  (Masteries, Giant Slayer, Tunnel Vision, Healing Powah +10%, Merciless +15%, Pet Encouragement +15%,
  stat-based perks up to +10% with level-60 stats), so five Offensive perks together add roughly +50-60%.
  The numbers are constants at the top of `src/unbound_perks.cpp` and must match the descriptions in
  `addon/UnboundPerks/PerkData.lua`.
- **Unbound addon** (`addon/Unbound`, copy to the client's `Interface/AddOns`): shows Dungeon/Raid
  Difficulty in the portrait menu from level 60 (the client's own limit is 65) and adds `/heroic` and
  `/normal`.
- **Expansion content lock** (`Unbound.ExpansionUnlocked` in `mod_unbound.conf`, 0/1/2): locked expansions'
  dungeons, raids, dungeon finder entries and zones (Northrend, the Outland zones of map 530) are
  blocked; players there are sent to their hearthstone (or race start if that is locked too, or else
  their faction's capital). Blood Elf and Draenei starting zones stay open, and so does Ebon Hold for
  Death Knights; battlegrounds/arenas and GMs are exempt. While Wrath is locked, only GM accounts can
  create Death Knights (`CharacterCreating.Disabled.ClassMask = 32` in `worldserver.conf`). Releasing an
  expansion: raise `Unbound.ExpansionUnlocked`, `MaxPlayerLevel` (70/80) and, for Wrath, clear the class
  mask.

## Roadmap

Planned and possible features are tracked in [ROADMAP.md](ROADMAP.md).

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
- Keep `server-setup/Server Cheat Sheet.md` and `ROADMAP.md` up to date with your changes.
- New features go in their own `src/unbound_<feature>.cpp`, registered in `src/unbound_loader.cpp`, and get
  a line under Features above.
- Custom IDs are shared, so pick new ones next to the existing ones and say so in the commit: spells
  2002xx, items 9100xx (heroic loot 910100-910999, world boss loot 911000-911999), item sets 950-999,
  creatures 1901xx (world bosses 190110-190199, spawn guids 9190110-9190199),
  SkillLineAbility 9000xx.
