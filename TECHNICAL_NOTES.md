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
  Creatures summoned without a spawn in the dungeon (event bosses such as Mutanus, Baron Aquanis, Grubbis, and
  event adds) are listed in `HEROIC_EXTRA_CREATURES` per map; find them by checking the dungeon's C++ script
  folder (NPC constants, SummonCreature), SmartAI summon actions (action 12, including timed action lists)
  and `creature_summon_groups`. Creatures already above level 60 (holiday bosses such as Apothecary Hummel in
  Shadowfang Keep) keep their normal version and don't stretch the level spread.
  The level spread uses only the dungeon's creatures with loot (the real mobs and bosses), so critters, triggers
  and trainers (Uldaman's level 54 trainer, level 60 triggers) don't squeeze it; every copy is clamped to
  60-62. Scarlet Monastery is one map (189) with one Heroic mode for all four wings.
  Creatures also spawned in another dungeon or raid get no heroic copy (it would show up in that map's heroic
  too); spawns in the open world (maps 0, 1, 530, 571, `OPEN_WORLD_MAPS`) don't count, since it is never heroic.
  Creatures that spells summon (Spell.dbc effect 28, from the dungeon's SmartAI, creature spells and C++ SPELL_
  constants) and creatures others transform into (UpdateEntry: Balnazzar, Dark Shade, Veng, Maraudos) are listed
  in `HEROIC_SPELL_SUMMONS`. Creatures above level 63 (`CLASSIC_MAX_LEVEL`) are holiday and event bosses and
  keep their normal version. `HEROIC_MAX_PLAYERS` sets a heroic group size other than 5 (Blackrock Spire: 15,
  like its normal mode); custom_dbc.py reads it.
- **Heroic loot:** `tools/heroic_loot.py` defines heroic items (910100-910999), sets (950-999) and boss
  loot. After a change run `python tools/heroic_loot.py`, `python tools/classic_heroics.py` and
  `python tools/custom_dbc.py`, then restart the worldserver. Never delete an item that has dropped: take
  it out of `LOOT` instead.
  Batch 1 loot (Wailing Caverns, Shadowfang Keep, Blackfathom Deeps, Gnomeregan) remakes each boss's own drops
  (up to 3, one tank / caster / damage piece where possible; final bosses two pools) as level 60 blues: same name,
  look and stat types, stats scaled to the median stat points of classic level 58-60 blues in that slot, armour,
  block and weapon damage per second from the same reference. Bosses without gear drops of their own (Kresh)
  drop gold only. Rare spawns are left out.
  Batch 2 loot (Razorfen Kraul, Scarlet Monastery, Razorfen Downs, Uldaman) is made the same way; each Scarlet
  Monastery wing's last boss (Thalnos, Doan, Herod, Whitemane) counts as a final boss. Revelosh drops gold only;
  Archaedas has one drop of his own, so he drops one item.
  Batch 3 loot (Zul'Farrak, Maraudon, Sunken Temple, Blackrock Depths): items dropped directly by 3 or more
  creatures are dungeon-wide drops and are left out when the boss has drops of its own; grouped rows with
  chance 0 (an equal share of the group) count as regular boss drops. Bosses that share a loot pool share the
  heroic items too (the four Sunken Temple dragons; Nekrum shares two of Theka's). Lord Incendius (only
  random-enchantment bracers) and Ribbly Screwspigot (bags) drop gold only. All six Ring of Law bosses have
  heroic loot; one of them spawns per run.
  Batch 4 loot (Blackrock Spire, Dire Maul, Scholomance, Stratholme): each wing's last boss counts as a final
  boss (Wyrmthalak, Drakkisath, Alzzin, Tortheldrin, Gordok, Balnazzar, Rivendare). The Gordok guards share one
  pool; Lady Illucia shares Malicia's and Krastinov's items. Pusillin, Fras Siabi, Jarien and Sothos drop gold
  only. Dungeon Set 1 remakes keep the name but not the set bonus.
  Each Heroic boss also gets its normal version's quest drops (item class 12, QuestRequired rows, items that
  start a quest; ungrouped rows only), copied by an INSERT ... SELECT in unbound_heroic_loot.sql when it is
  applied. The Deadmines items were hand-made first and rescaled on 2026-10-14 to the same reference as the
  generated ones.
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
  the Attunement button in the micro menu between Talents and Achievements, `/attunement`; ElvUI's micro bar has a fixed button list, so
  the button styles itself like ElvUI's and re-places itself after `AB:UpdateMicroPositionDimensions`). It whispers its own character
  (prefix `UBATT`): `Q:<ids>` -> `I:<id>:<code>:<done>:<needed>:<price>:<reason>` (code A attuned, W wear to
  attune, S sacrifice only, N doesn't count); `COLL` -> `C:BEGIN`, `C:A:`, `C:P:`, `C:S:`, `C:T:`, `C:END`; the server
  pushes `P:` (kill progress), `A:<id>` (attuned) and `RESET` (a GM changed the collection).
- **Soloable raid mechanics:** `src/unbound_solo_raids.cpp`. A fix applies while `Map::IsRaid()` and
  `GetPlayersCountExceptGMs() <= 1` (pets and guardians aren't players, playerbots are; a GM in GM mode
  isn't counted, so a GM alone also gets the solo version). Spells that must not happen solo are
  bound to `spell_unbound_solo_raid_block` (`data/sql/db-world/unbound_solo_raids.sql`), whose `OnCheckCast`
  fails them (`SPELL_FAILED_DONT_REPORT`) only for the caster entry listed in `BLOCKED_SPELLS`, so the same
  spell cast elsewhere is unchanged; add a spell to both lists. The check also runs for triggered casts.
  Razorgore's eggs (177807) get `go_unbound_solo_razorgore_egg`: while the instance's egg event is in progress
  (Razorgore engaged), a player within 2.5 yards or clicking breaks an egg the way `spell_egg_event` does
  (`SetData(DATA_EGG_EVENT, SPECIAL)`); the instance counts it and starts phase two after the last one. The
  BWL instance constants it uses are copied from `blackwing_lair.h`. Settings: `Unbound.SoloRaid.Enable` and
  one per boss.
- **Classic Onyxia's Lair:** `data/sql/db-world/unbound_classic_onyxia.sql` (entry level, creature stats from
  `creature_classlevelstats`, loot with references 9100100-9100101, team conditions on the heads, quest givers)
  and `src/unbound_classic_onyxia.cpp`. 3.3.5 kept the classic spell ids and raised their damage, so
  `CLASSIC_DAMAGE` scales damage from those ids (`ModifySpellDamageTaken`, `ModifyPeriodicDamageAurasTick`)
  in map 249 on difficulty 0 to classic / 3.3.5 average damage (1.12 and 3.3.5 Spell.dbc). Deep Breath and
  Heated Ground chain through many spell ids (each one triggers the next), all listed. The Onyxian Lair Guard
  (36561) has `npc_unbound_onyxia_no_lair_guard`, which despawns it. The map stays a 10-player map, so
  mod-autobalance gets `AutoBalance.InflectionPoint.PerInstance = "249 -1 0.058 0.25"`: solo about 2.8
  players' worth of the classic 40-player Onyxia, ten players about 10. After applying it, run
  `python tools/item_expansions.py` so her classic loot counts for attunement.
- **Unbound addon** (`addon/Unbound`): difficulty menu from level 60, `/heroic`, `/normal`, and the
  chat-window load-error guard.
- **Expansion content lock:** `Unbound.ExpansionUnlocked` in `mod_unbound.conf` (0/1/2). Players in a
  locked zone go to their hearthstone, else their race's start, else their faction's capital; GMs with GM
  mode on, battlegrounds and arenas are exempt. Death Knights are GM-only through
  `CharacterCreating.Disabled.ClassMask = 32`. Releasing an expansion: raise `Unbound.ExpansionUnlocked`
  and `MaxPlayerLevel` (70/80) and, for Wrath, clear the class mask (see the cheat sheet for playerbots).
