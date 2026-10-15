# Technical notes

How each system is built and what to run after changing it (what the features do and when they were
added is in [CHANGELOG.md](CHANGELOG.md)).

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
