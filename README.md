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
  (so far: Stormwind Stockades). Heroic needs level 60; creatures are heroic copies (entry + 1000000)
  at level 60-62 with 1.5x health and damage and normal loot. Add a dungeon to `HEROIC_DUNGEONS`, then
  run `python tools/classic_heroics.py` and `python tools/custom_dbc.py`.
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

### First-time setup

1. Have an AzerothCore (mod-playerbots fork) server with mod-transmog-plus and mod-aoe-loot, laid out
   like the original: `<server root>\azerothcore\` with the extracted DBCs in `<server root>\data\dbc\`.
2. Clone this repository into the modules folder, keeping the folder name `mod-unbound`:

   ```bash
   git clone https://github.com/Kasix-K/mod-unbound.git azerothcore/modules/mod-unbound
   ```

3. Re-run CMake and rebuild the worldserver (the module's C++ is compiled into it).
4. Start the worldserver; it applies `data/sql/db-world` automatically.
5. Build the client patch into your own 3.3.5a client (the default `--client` path is the original PC's):

   ```bash
   python tools/custom_dbc.py --client "C:\path\to\your\WoW 3.3.5a client"
   ```

   Add `--dbc "<folder>"` if your server DBCs aren't in `<server root>\data\dbc`. The client also needs
   mod-transmog-plus's `Transmog` addon in `Interface\AddOns`.

### Day to day

- Before starting: `git pull`.
- When done: `git add -A`, `git commit -m "what changed"`, `git push`. If the push is rejected, `git pull`
  first, fix any conflicts, then push again.
- After pulling someone else's changes:
  - C++ changed (`src/`): rebuild the worldserver.
  - SQL changed (`data/sql/`): restart the worldserver.
  - `tools/custom_dbc.py` changed: run it again (with your `--client`), restart the worldserver and the
    client.
- New features go in their own `src/unbound_<feature>.cpp`, registered in `src/unbound_loader.cpp`, and get
  a line under Features above.
- Custom IDs are shared, so pick new ones next to the existing ones and say so in the commit: spells
  2002xx, items 9100xx, creatures 1901xx, SkillLineAbility 9000xx.
