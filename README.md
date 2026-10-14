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

## Custom spells, items and companions

Spells, item DBC rows and Companions-tab entries are defined once in `tools/custom_dbc.py`. That script
generates both sides:

- server: `data/sql/db-world/unbound_custom_dbc.sql` (applied automatically when the worldserver starts)
- client: `E:\WoW 3.3.5a Unbound\Data\patch-Z.MPQ`

After changing one, run `python tools/custom_dbc.py`, restart the worldserver, and restart the client
(delete the client's `Cache` folder if the old tooltip still shows).
