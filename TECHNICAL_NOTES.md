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
- **Gear attunement** (all 4 stages: the collection, its stats, attuning by kills, the sacrifice altar, tooltips and the
  collection window): `src/unbound_attunement.cpp`. Each
  character's collection is `characters.character_unbound_attunement` (item, progress, attuned). Attuned
  items give `Unbound.Attunement.Percent` (20%) of their fixed stats, applied like equipped-item stats
  (`Player::_ApplyItemBonuses`), with diminishing returns against `ReferenceSetStats` (600 stat points =
  a full level-60 blue/epic set): full value until `FullValueUntil` (100%), half until `HalfValueUntil`
  (200%), a quarter beyond. Item rules: green or better weapons/armour (not shirts, tabards, bags, ammo),
  required level within `LevelRange` (10) of the level cap, fixed stats (random-stat "of the Bear" items
  have none), and an expansion up to `Unbound.ExpansionUnlocked`. The expansions are in
  `world.unbound_item_expansion`, made by `tools/item_expansions.py` from where each item comes from
  (creature, skinning and pickpocket loot by spawn map, chests, containers, disenchanting, vendors, quest
  starters/enders, crafting by its reagents, items made by using another item; greens/blues are also held
  to their expansion's item level range, because shared world-drop tables mix expansions). Run
  `python tools/item_expansions.py` again (database running) when loot, vendors or quests change;
  `--check <item ids>` explains single items. Attuning: `OnPlayerRewardKillRewarder` (each player credited
  for a kill, group members in range too); a creature counts if `Acore::XP::Gain` > 0 (would give
  experience); 1 kill, `EliteKills` (2) for elites, `BossKills` (10) for bosses; each equipped, counting,
  not yet attuned item gains them; `Kills` by quality (50/100/200/400). Progress is saved with the
  character (`OnPlayerSave`, one transaction); completing an item saves at once. Messages at 25/50/75%
  and on completion (achievement sound). GM commands: `.attune add|remove|check <item>`, `.attune info`,
  `.attune reset` (on the selected player, else yourself); players: `.attune progress`. Sacrifice: the Altar
  of Sacrifice (creature 190103, `npc_unbound_attunement_altar`, `data/sql/db-world/unbound_attunement_altar.sql`)
  lists the bag items that count and aren't attuned (28 per page); each gossip option carries the item entry
  (sender) and bag/slot (action) and uses the game's money confirmation box; on select the server checks the
  item, position and gold again, then takes the gold, destroys the item and attunes it. Prices:
  `SacrificeGold` by quality (2/10/50/250), times `SacrificeOwnGearMultiplier` (2) if `Player::CanUseItem`.
  Client: `addon/UnboundAttunement` (tooltips on GameTooltip/ItemRefTooltip/ShoppingTooltips, the collection window,
  the Attunement button in the micro menu after Help, `/attunement`; ElvUI's micro bar has a fixed button list, so
  the button styles itself like ElvUI's and re-places itself after `AB:UpdateMicroPositionDimensions`). It whispers its own character
  (prefix `UBATT`): `Q:<ids>` -> `I:<id>:<code>:<done>:<needed>:<price>:<reason>` (code A attuned, W wear to
  attune, S sacrifice only, N doesn't count); `COLL` -> `C:BEGIN`, `C:A:`, `C:P:`, `C:S:`, `C:T:`, `C:END`; the server
  pushes `P:` (kill progress), `A:<id>` (attuned) and `RESET` (a GM changed the collection).
- **Unbound addon** (`addon/Unbound`): difficulty menu from level 60, `/heroic`, `/normal`, and the
  chat-window load-error guard.
- **Expansion content lock:** `Unbound.ExpansionUnlocked` in `mod_unbound.conf` (0/1/2). Players in a
  locked zone go to their hearthstone, else their race's start, else their faction's capital; GMs with GM
  mode on, battlegrounds and arenas are exempt. Death Knights are GM-only through
  `CharacterCreating.Disabled.ClassMask = 32`. Releasing an expansion: raise `Unbound.ExpansionUnlocked`
  and `MaxPlayerLevel` (70/80) and, for Wrath, clear the class mask (see the cheat sheet for playerbots).
