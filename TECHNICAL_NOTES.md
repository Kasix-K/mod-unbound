# Technical notes

How each system is built and what to run after changing it (what the features do and when they were
added is in [CHANGELOG.md](CHANGELOG.md)).

- **Transmogrify spell (200200):** learned on login; opens the mod-transmog-plus window (5 s cooldown,
  usable while mounted, not in combat). Needs `Transmog.OpenAnywhere = 1` and the `Transmog` addon.
- **Loot companions:** Loot Goblin (item 910001, spell 200201, creature 190100) and Arcane Loot Scanner
  (item 910002, spell 200202, creature 190102, the Arcane Protector 16504 shrunk), sold by Grizzle
  Lootsnatch (vendor 190101, `.npc add 190101`). While one is out, corpses within `AOELoot.Range` are
  auto-looted once a second (gold shared with the group; items needing a roll or the master looter, and
  anything that doesn't fit in the bags, stay on the corpse) and mod-aoe-loot is on. AoE loot comes only from
  loot companions: `.aoeloot on/off` is blocked for everyone (`unbound_loot_goblin_commands`,
  `OnTryExecuteCommand`, also catches abbreviations like `.aoe on`); a new loot companion only needs its entry
  in `IsLootCompanion`. Price/currency:
  `data/sql/db-world/unbound_loot_goblin.sql`.
  The **Scavenger Imp** (item 910003, spell 200203, creature 190210, sold for 160 Heroic Sigils on the Warden of
  Rare Wonders' Pets page) is not in `IsLootCompanion`: no mod-aoe-loot and no once-a-second loot. Instead
  `unbound_loot_goblin_server` (`CanPacketReceive`, `CMSG_LOOT`) loots the nearest
  `Unbound.ScavengerImp.ExtraCorpses` (4) other corpses within `Unbound.ScavengerImp.Range` (27 yards) of the
  player, by the same rules (`AutoLootCorpse`, which now restores a loot window the player has open), before
  the opened corpse's own loot window appears.
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
- **Client assets (icons, textures):** never in git. `data/client_assets.txt` lists client paths
  (`Interface\Icons\name.blp`); the files live in a local folder mirroring those paths (default
  `<server root>\unbound-assets`, outside the repo; `--assets` to change). `tools/fetch_assets.py --from <Data>`
  fills it from a local WoW client's MPQs (`tools/mpq_read.py`: read-only, zlib/bzip2, encrypted files; the
  archive that wins in game is used: patch-Z over patch-A over patch-enUS-3 over patch over base;
  `archive_priority`). `tools/custom_dbc.py` packs the
  listed files it finds into `patch-Z.MPQ` and warns about missing ones. Its client DBCs (Item, ItemDisplayInfo,
  ItemSet, ...) are the server's copy plus our rows, unless another patch in the client changed that DBC: then
  our rows go into the client's winning copy (`client_dbc`; same layout required), so an HD pack's
  ItemDisplayInfo changes survive. The server SQL always comes from the server's DBCs. Icons must be BLP2 (DXT1/3/5, palette
  or raw), 64x64. Addons use them by path; an item, currency or spell needs a client row naming the icon
  (ItemDisplayInfo, SpellIcon).
- **World bosses:** `tools/world_bosses.py` (SmartAI fights, no C++; creatures 190110-190199, spawn guids
  9190110-9190199, loot 911000-911999). Hrimthar is creature 190110, adds 190111. After a change run
  `python tools/world_bosses.py` and `python tools/custom_dbc.py`, then restart the worldserver.
- **Bounty Wayfinder:** creature 190211 (spawn guids 9190211-9190212, beside `BOARD_SPAWNS`),
  `src/unbound_bounty_teleporter.cpp`: a gossip menu (the player's active board quests, then all) that
  teleports to the world table `unbound_bounty_teleports` (quest, name, zone, map, x, y, z, o), loaded at
  startup. `tools/bounty_teleporter.py` writes it; `--find` recomputes the landing spots from the live database
  (densest group of each quest's targets; nearest gameobject, friendly creature or graveyard spot 60-250 yards
  away, then 400, 600, 1500, that is 35 yards plus wander radius from every creature hostile to either faction
  and from its patrol path points (`waypoint_data`, SmartAI `waypoints`), 80 from guards; hostility from
  FactionTemplate.dbc). Then a drop point: from the camp's centre out towards that ground spot, the first
  point (40+ yards out) as safe as a ground spot, 90 yards above the highest known ground within 150. The
  player arrives there; `unbound_bounty_teleporter_player` (OnPlayerUpdate) adds Wayfinder's Descent (spell
  200204: Slow Fall's feather fall aura, `SPELL_ATTR0_NO_AURA_CANCEL`, 2 minutes, re-added while still in the
  air) once the teleport has finished, and removes it when the player stops falling (after a 2 second grace),
  dies, or after 5 minutes; logging in removes a left-over one. `GROUND_ONLY` (caves, tunnels) teleports to the
  ground spot. New board quests need a spot: run `--find`, paste the result into `SPOTS`.
- **Shadowflame Ward:** `tools/shadowflame_ward.py` writes `unbound_shadowflame_ward.sql` (items 912100-912109,
  NPCs 190206-190209 with spawn guids + 9000000, quests 921001-921012, the scale drops). The core only checks
  the Onyxia Scale Cloak's aura (22683) against Shadowflame (`SpellEffects.cpp`, `instance_blackwing_lair.cpp`),
  so the cloak just has that aura on equip. The five flights' last quests share each-from-all exclusive group
  -921010, so The Scales Assembled (921010) needs all of them. The three elites are copies (template, model,
  SmartAI) of rares 7846, 2447 and 10202. The Scale of Onyxia drop is in `unbound_classic_onyxia.sql`, since
  that file rebuilds Onyxia's loot. After a change run the tool and `python tools/custom_dbc.py --client ...`.
- **Perks:** window in `addon/UnboundPerks` (`PerkData.lua` = perk list and descriptions); server side in
  `src/unbound_perks.cpp`. The addon whispers its own character (prefix `UBPERK`: `SYNC`, `SET:<id>:<0|1>`,
  `LOAD:<ids>`, `CHOICE:<id>:<n>`; the server answers `STATE:<ids>`, `RANK:`, `CHOICE:`, `VARIANT:` or
  `ERR:<text>`); active perks are saved in
  `characters.character_unbound_perks`. No changes in combat, at most 5 Offensive perks, class perks only
  for their class (`CLASS_PERKS`). No Resurrection Sickness and No Daze are `Death.SicknessLevel = 255` and
  `Daze.Enabled = 0` (set by `apply-unbound-settings.ps1`); Rapid Recovery is `Unbound.Perks.RapidRecovery*`
  in `mod_unbound.conf`. Retribution's spell scripts: `data/sql/db-world/unbound_perks_spells.sql`.
  **Crusader's Oath** (perk 1001, the Paladin class perk; at most 1 class perk active, `CATEGORY_LIMITS`): Holy
  Power is the stacks of a visible buff (spell 200220, 3 stacks, 20 s), gained in `OnPlayerSpellCast` (Crusader
  Strike, the three Judgements, any Hammer of Wrath rank; not triggered casts) and spent by Templar's Verdict
  (200221, a copy of Crusader Strike: Holy, 200% weapon damage scaled in `OnHit` by Holy Power, rank and oath;
  a crit is read from the spell's `TargetInfo`, rolled before the damage) and Inquisition (200222, Avenging
  Wrath's damage aura on Holy; amount and duration set after the hit). Ashbringer's Call (200223, a copy of
  Shadowfiend) summons guardian 190220 (`unbound_crusaders_oath.sql`, Spirit of Mograine's look); its swing is
  set in `ModifyMeleeDamage` (75% of the Paladin's `UNIT_FIELD_MIN/MAXDAMAGE` average) and its hits counted in
  `DealDamage`. Divine Storm's script serves both perk versions. The spells come from `tools/custom_dbc.py`
  and are learned by `UpdateOathSpells` while the perk is on (also on level and rank changes) and unlearned when
  it is off. They are saved like trained spells, not temporary: action buttons load before the perks at login and
  a button for an unknown spell is deleted; temporary spells also got the learned packet twice (Spellbook doubles). Ranks: `RANKED_PERKS` key `CrusadersOath` (3 ranks; `Oaths`/`Ashbringer` are 0/1
  unlocks). The oath is `characters.character_unbound_perk_choices` (`CHOICE:<perk>:<choice>` both ways); the
  server also sends `VARIANT:1001:<oath|classic>`. `Unbound.Perks.Retribution.Classic = 1` runs the original
  Retribution perk instead (its ranks are dropped, no spells; `HasRetribution` is only true then) and the addon
  shows that perk's `classic` text. Its long text is split for the window: `crusadersOath()` in `PerkData.lua`
  sets `perk.intro`, `perk.spells` (icon, name, kind, text, status, on), `perk.mid` and `perk.spells2` (the
  "Your oath" heading and the two oath icons; the chosen one lit, the other dimmed) and `perk.rest` (Physical
  damage); `UnboundPerks.lua` shows the intro, the icons (`updateSpellRow(row, spells)`, hover tooltips), the
  heading and second row when set, then the rest. Any perk can use `spells` (and `spells2`) the same way. Ranked perks set `perk.rankText` and `perk.rankLines` (`setRankInfo` in `PerkData.lua`):
  one gold line in the window, every rank in its hover tooltip; `perk.note` keeps only the extra grey note. Holy Power can't make Hammer of Wrath usable above 20% health: the client
  checks that aura state itself.
  **Bulwark's Oath** (perk 1002, the Paladin Protection class perk) reuses Crusader's Oath's machinery: the same
  Holy Power aura (200220, gained in `OnBulwarkSpellCast` from Hammer of the Righteous, the Judgements and any
  Avenger's Shield rank), the same 30/65/100% spend shares (`VERDICT_SHARE`), the same choices table and bar.
  The two class perks are an `EXCLUSIVE_GROUPS` pair (and `excludes` in `PerkData.lua`), so turning one on swaps
  them. Aegis Strike (200224) is a copy of Shield of Righteousness Rank 1 (level 75, so no Paladin here has it)
  with its family flags cleared (the core's block value formula is skipped); its damage is set in `OnHit` from
  `GetShieldBlockValue()` + 50% attack power. Word of Glory (200225, a copy of Flash of Light, instant on self) sets
  its heal in `OnHit`. Bastion (200227) is a plain buff (damage taken -10%, block +10%, 6 s); `bastionGlory`
  marks the full-strength Word of Glory. Guardian of the Light (200226, a copy of Shadowfiend) summons guardian
  190221 (`unbound_bulwarks_oath.sql`, the Ghost of Uther's look) and carries the -30% damage taken aura itself;
  its swing and hit count share the Ashbringer's code (`ApplyAshbringerHit`, `CountAshbringerHit`). Oath of
  Retaliation's block damage comes from the defense proc aura (200215, now also on with Bulwark's Oath), using
  `DamageInfo::GetBlock()`, cast as Retaliation (200228, a Holy copy of Damage Shield). Ranks: `RANKED_PERKS` key
  `BulwarksOath`; `bulwarksOath()` in `PerkData.lua` builds the window text like `crusadersOath()`.
  **Lightbringer's Oath** (perk 1003, Paladin Holy) uses the same machinery; the three Paladin class perks are
  one `EXCLUSIVE_GROUPS` group. Holy Power from `OnLightSpellCast` (the Judgements, any Exorcism and any Holy
  Shock you cast); Oath of the Dawn's crit Holy Power from `spell_unbound_lightbringer_dawn_crit` on the Holy
  Shock damage and Exorcism chains (-25912, -879; the crit is read from the spell's `TargetInfo`). Light of Dawn
  (200229, a copy of Exorcism Rank 1, instant) sets its damage in `OnHit` (400 at level 60 + the rank's share of
  `SpellPower()`, times the Holy Power share) and heals in `AfterHit`. Atonement (200230) is a dummy buff; its
  duration is set after the hit. The conversion is `ApplyLightbringerHeal`, last in `ModifyHealReceived`: it
  adds the share of the heal (effective healing in full, overhealing times `GroupOverheal`% when
  `InGroupWithOtherPlayers`, i.e. a group member whose session isn't headless) to `atonementPending`, which
  `FlushAtonement` deals on the next player update as one Holy hit (`DealSpellDamage` with Atonement's spell
  info) to `AtonementTarget()`: never inside the heal, so leech perks can't recurse. `AtonementTarget` skips
  `HasBreakableByDamageCrowdControlAura`, Holy-immune, evading, out-of-range (40 yards) and (except your own
  enemy target) out-of-combat enemies. Naaru's Blessing (200231, a copy of Shadowfiend summoned at the caster)
  summons 190222 (`unbound_lightbringers_oath.sql`: A'dal's model at 0.15 scale, pacified, not attackable, not
  selectable); `UpdateNaaru` finds it in the grid every 2 s and has it cast Smite (585) and Flash Heal (2061)
  with server-set amounts; the heal goes to the Paladin and every group member (bots too) within 10 yards of
  the Naaru, 2% of each one's maximum health, and counts as one spell for Holy Power. Ranks: `RANKED_PERKS` key `LightbringersOath`; `lightbringersOath()` in `PerkData.lua`. Perk
  numbers stay in normal WoW ranges (about +10% per perk); they are constants at the top of
  `unbound_perks.cpp` and must match `PerkData.lua`. The perk code assumes `MapUpdate.Threads = 1`.
- **Gear infusion** (all 4 stages: the collection, its stats, infusing by kills, the tribute altar, tooltips and the
  collection window): `src/unbound_attunement.cpp`. Each
  character's collection is `characters.character_unbound_attunement` (item, progress, attuned). Infused
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
  `--check <item ids>` explains single items. Infusing: `OnPlayerRewardKillRewarder` (each player credited
  for a kill, group members in range too); a creature counts if `Acore::XP::Gain` > 0 (would give
  experience); 1 kill, `EliteKills` (2) for elites, `BossKills` (10) for bosses; each equipped, counting,
  not yet infused item gains them; `Kills` by quality (50/100/200/400). Progress is saved with the
  character (`OnPlayerSave`, one transaction); completing an item saves at once. Messages at 25/50/75%
  and on completion (achievement sound). GM commands: `.infuse add|remove|check <item>`, `.infuse info`,
  `.infuse reset` (on the selected player, else yourself); players: `.infuse progress` (`.attune` is the old name, still works; players see "infusion", the code, table, settings and addon keep "attunement"). Tribute: the Altar
  of Tribute (creature 190103, called the Altar of Sacrifice before 2026-10-15; `npc_unbound_attunement_altar`, `data/sql/db-world/unbound_attunement_altar.sql`)
  lists the bag items that count and aren't infused (28 per page); each gossip option carries the item entry
  (sender) and bag/slot (action) and uses the game's money confirmation box; on select the server checks the
  item, position and gold again, then takes the gold, destroys the item and infuses it. Prices:
  `TributeGold` by quality (2/10/50/250), times `TributeOwnGearMultiplier` (2; the old `Sacrifice*` names are still
  read) if `Player::CanUseItem`.
  Client: `addon/UnboundAttunement` (tooltips on GameTooltip/ItemRefTooltip/ShoppingTooltips, the collection window
  in pages of `PER_PAGE` = 60 items: only 60 item buttons exist, refilled per page, since one button per item
  lagged the game at 2,500+ items; each tab remembers its page,
  the Infusion side tab on the character sheet's right edge, `/infusion`). The side tabs (Perks from UnboundPerks, Infusion below
  it) use the Spellbook's `SpellBookSkillLineTabTemplate`; opening one window closes the other, and with ElvUI's character skin
  they get ElvUI's side tab look on the first character sheet open. (It was a micro menu button until 2026-10-15; ElvUI's
  micro bar sometimes drew over its icon.) It whispers its own character
  (prefix `UBATT`): `Q:<ids>` -> `I:<id>:<code>:<done>:<needed>:<price>:<reason>` (code A infused, W wear to
  infuse, S tribute only, N doesn't count); `COLL` -> `C:BEGIN`, `C:A:`, `C:P:`, `C:S:`, `C:T:`, `C:END`; the server
  pushes `P:` (kill progress), `A:<id>` (infused) and `RESET` (a GM changed the collection).
- **Soloable raid mechanics:** `src/unbound_solo_raids.cpp`. A fix applies while `Map::IsRaid()` and
  `GetPlayersCountExceptGMs() <= 1` (pets and guardians aren't players, playerbots are; a GM in GM mode
  isn't counted, so a GM alone also gets the solo version). Spells that must not happen solo are
  bound to `spell_unbound_solo_raid_block` (`data/sql/db-world/unbound_solo_raids.sql`), whose `OnCheckCast`
  fails them (`SPELL_FAILED_DONT_REPORT`) only for the caster entry listed in `BLOCKED_SPELLS`, so the same
  spell cast elsewhere is unchanged; add a spell to both lists. The check also runs for triggered casts.
  Razorgore's eggs (177807) get `go_unbound_solo_razorgore_egg`: while the instance's egg event is in progress
  (Razorgore engaged), a player within 2.5 yards or clicking breaks an egg the way `spell_egg_event` does
  (`SetData(DATA_EGG_EVENT, SPECIAL)`); the instance counts it and starts phase two after the last one. The
  BWL instance constants it uses are copied from `blackwing_lair.h`. Viscidus (`unbound_solo_viscidus_unit`,
  a UnitScript): his core script counts frost hits (`SpellHit`) and, frozen, melee hits (`DamageTaken` with
  `DIRECT_DAMAGE`) against fixed thresholds; solo, `ModifyMeleeDamage` and `ModifySpellDamageTaken` call those
  AI functions `ViscidusHitMultiplier - 1` more times (with no damage), so the thresholds, emotes and phases of
  his own script do the rest. Swings count before the hit roll, so misses count too. Settings:
  `Unbound.SoloRaid.Enable`, one per boss, `Unbound.SoloRaid.ViscidusHitMultiplier` and
  `Unbound.SoloRaid.RazorgoreWaveInterval`. Ossirian's Enveloping Winds (`spell_unbound_solo_ossirian_winds`,
  spell 25189) fails in `OnCheckCast` if it comes less than `Unbound.SoloRaid.OssirianWindsInterval` seconds after
  the last one that landed (per Ossirian, under a mutex). Razorgore's waves (`unbound_solo_razorgore_waves`, an
  AllCreatureScript): `OnCreatureAddWorld` sees each summoned Blackwing Legionnaire / Mage / Dragonkin in map 469,
  groups adds summoned within 2 seconds as one wave, and despawns a whole wave that comes less than the interval
  after the last wave kept (per instance id, under a mutex: instances update on several threads). Thaddius' fix is in
  `src/naxx40/boss_thaddius_40.cpp` (the boss skips the 5-second revive, the minions skip the Tesla Coil
  overload), asking `UnboundSoloThaddius()` from `src/unbound_solo_raids.h`; Gothik's is in
  `boss_gothik_40.cpp` (`EVENT_TELEPORT` skips clearing threat, phase two opens the gate), asking
  `UnboundSoloGothik()`. Keep these checks when updating the Naxx 40 scripts from upstream.
- **Classic Onyxia's Lair:** `data/sql/db-world/unbound_classic_onyxia.sql` (entry level, creature stats from
  `creature_classlevelstats`, loot with references 9100100-9100101, team conditions on the heads, quest givers)
  and `src/unbound_classic_onyxia.cpp`. 3.3.5 kept the classic spell ids and raised their damage, so
  `CLASSIC_DAMAGE` scales damage from those ids (`ModifySpellDamageTaken`, `ModifyPeriodicDamageAurasTick`)
  in map 249 on difficulty 0 to classic / 3.3.5 average damage (1.12 and 3.3.5 Spell.dbc). Deep Breath and
  Heated Ground chain through many spell ids (each one triggers the next), all listed. The Onyxian Lair Guard
  (36561) has `npc_unbound_onyxia_no_lair_guard`, which despawns it. The map stays a 10-player map, so
  mod-autobalance gets `AutoBalance.InflectionPoint.PerInstance = "249 -1 0.058 0.25, 533 -1 0.03"`: solo about 2.8
  players' worth of the classic 40-player Onyxia, ten players about 10. After applying it, run
  `python tools/item_expansions.py` so her classic loot counts for infusion.
- **Classic Naxxramas:** `src/naxx40` and `data/sql/db-world/unbound_naxx40*.sql`, from mod-individual-progression
  (MIT, `src/naxx40/LICENSE-mod-individual-progression`; what was changed is listed at the top of
  `src/naxx40/unbound_naxx40_config.cpp`). It is map 533's third difficulty slot (10-player heroic) made a
  40-player raid by a `mapdifficulty_dbc` row, with its own creatures (entries 351000-351097, spawn guids
  361000-362114, spawnMask 4), gameobjects 361000 (Four Horsemen chest) and 361001 (runestone, spawn guids
  361001-361003 with the Necropolis transport and meeting stone) and spells 90001-90008. Its
  `instance_naxxramas` replaces the core's (module scripts with the same script name win) and handles all
  three difficulties. The code is in namespace `UnboundNaxx40` because 20 of its classes have the same names
  as the core's Naxxramas scripts and would clash at link time; keep it there when updating from upstream.
  The runestone (`gobject_naxx40_tele`) checks the attunement quests 9121-9123, sets the raid difficulty to
  10-player heroic and teleports the group (members within 30 yards; playerbot accounts always). The
  expansion lock (`src/unbound_content_lock.cpp`) treats map 533 on that difficulty as classic.
  `tools/item_expansions.py` counts the 351000-351099 creatures and chest 361000 as classic.
  Solo scaling: classic Naxxramas is map 533's heroic difficulty slot, and mod-autobalance picks its curve by
  difficulty before size, so it would use `InflectionPointRaidHeroic` (floor 0.4, about 17 players' worth solo).
  The `533 -1 0.03` entry in `AutoBalance.InflectionPoint.PerInstance` gives it the 40-player raids' floor
  (about 2.8 players' worth). The entry is per map, so it also covers the level 80 Naxxramas: revisit it when
  Wrath is released.
- **Raid Finder:** `src/unbound_raid_finder.cpp` and `addon/UnboundRaidFinder`. The addon adds a "Raids"
  entry (value `unbound_raids`) to the Dungeon Finder's type dropdown by wrapping the global
  `LFDQueueFrameTypeDropDown_Initialize` (the dropdown is set up again on every OnShow, by name), and wraps
  `LFDQueueFrame_SetType`: for Raids it hides the `LFDQueueFrameSpecific` / `LFDQueueFrameRandom`
  frames and shows its own list (rows from the game's `LFGSpecificChoiceTemplate`, anchored to the specific
  list's first row so ElvUI's layout applies too); any other choice goes to the game's function. On Raids the
  game's own Find Group button is Enter Raid / Leave Raid (its OnClick is wrapped, and a hook on
  `LFDQueueFrameFindGroupButton_Update` puts the raid text back whenever the game updates it), so it looks
  exactly like Find Group with or without ElvUI. The raids are `RAIDS` in the
  C++ (id, name, map, difficulty, expansion, entrance area trigger or a fixed position for classic Naxxramas);
  levels come from `dungeon_access_template`, player counts from MapDifficulty. The addon whispers its own
  character (prefix `UBRAID`: `LIST`, `ENTER:<id>`, `LEAVE`; answers `R:<id>:<status>:<min>:<max>:<players>:
  <expansion>:<name>`, `END:<current raid>:<may pick>`, `INVITE:<raid>`, `MSG:`, `ERR:`). Entering sets the
  raid difficulty (the group's, or the player's), saves the return spot in
  `characters.character_unbound_raid_finder`, and teleports. When the leader's map changes to the raid
  (`OnPlayerMapChanged`), each other member is checked and sent `SMSG_SUMMON_REQUEST` from the leader after
  `SetSummonPoint` at the leader's position; the core's summon accept does the teleport into the leader's
  instance, and the member's return spot is saved when they arrive. Playerbot accounts
  (`UnboundNaxx40Config::IsBotAccount`) are teleported directly. The addon sets the text and buttons of the
  game's `CONFIRM_SUMMON` popup on `INVITE` and restores them when it closes. The tabs are
  `LFDParentFrameTab1/2` (CharacterFrameTabButtonTemplate) and switch between `LFDQueueFrame` and
  `UnboundRaidFinderFrame`.
- **Bulletin Board:** `tools/bulletin_board.py` generates `data/sql/db-world/unbound_bulletin_board.sql` (the board,
  gameobject 920000 spawned as guids 9920000-9920001; quests 920001-920999; pools 920000-920012; conditions).
  Dailies are core quest pools (`pool_template` / `pool_quest`, rerolled at the daily reset); profession quests
  have `RequiredSkillID` / `RequiredSkillPoints`. Weeklies: one quest per tier and dungeon (raid), ids
  920100 + i (Normal dungeon), 920200 + i (Heroic, the boss's heroic copy entry + 1000000), 920300 (Mythic,
  none yet), 920400 + i (Normal raid), 920500 / 920600 (Heroic / Mythic raid, none yet), each with a
  `CONDITION_WORLD_STATE` condition (source type 19). `src/unbound_bulletin_board.cpp` sets world states
  920001-920003 (dungeon per tier) and 920004-920006 (raid per tier) to distinct positions in DUNGEONS / RAIDS
  whenever the core's weekly reset time (world state 20002) changes; 920009 remembers which reset the picks
  were for; 920007 is the week's elite bounty (920900 + i), any but last week's. Append to DUNGEONS / RAIDS /
  ELITE_QUESTS only (positions are stored) and keep the counts in the C++ in sync. `QuestType` must be 2: 0
  makes a quest auto-complete.
  Weekly quests ask for the boss's normal entry in every tier: `Player::KilledMonsterCredit` matches objectives
  against the creature's normal entry (`GetEntry()`), even for a heroic copy. `unbound_bulletin_board_player`
  (`OnPlayerPassedQuestKilledMonsterCredit`, which also gets the killed template's entry) lets a Normal weekly
  (9201xx, 9204xx) count only a Normal kill and a Heroic / Mythic weekly only a Heroic one.
  Quest log headers: each board quest's `QuestSortID` is minus one of `QUEST_SORTS` in the tool (920 Open World,
  921-923 Normal / Heroic / Mythic Dungeon, 924 Raids, 925 Gathering, 926 Crafting), new QuestSort.dbc rows that
  `tools/custom_dbc.py` adds to the client patch and to `questsort_dbc` (a client without the new patch shows the
  quests without headers). Run both tools after changing them.
  Elite bounty creatures that were raid-tuned (HealthModifier 7-100) are set to 3 (Lord Lakmaeran 6) in
  `unbound_elite_bounty_scaling.sql`, which lists the original values; check new bounty camps the same way (the open
  world isn't scaled by mod-autobalance).
- **Account-wide currencies** (the Heroic Sigil, item 912000): the item is defined in
  `data/sql/db-world/unbound_currencies.sql` (soulbound, multi-drop, currency token bag) and on the client side in
  `tools/custom_dbc.py` (icon display 70000, currency 400 bit 30 under an "Unbound" header, prices 3000-3004; run
  `python tools/custom_dbc.py --client <client>` after changing them). `src/unbound_account_currency.cpp` keeps one
  amount per account in `characters.account_unbound_currency`: at login the character's stack is set to the
  account's amount, at every save (and logout) it is written back. Only a player-logged-in character takes part:
  bot sessions (`WorldSession::IsHeadless()`, which covers account alt-bots) keep their own amount, and so do GM
  accounts unless `Unbound.AccountCurrency.GMAccounts = 1`. `holder` = the character that loaded the balance last;
  only it may write. A character's own stack is added to the account once, the first time it logs in
  (`character_unbound_currency_merged`). The latest balances are cached in memory, so a quick relog doesn't read a
  balance whose database write is still queued. A new shared currency only needs its entry in `SHARED_CURRENCIES`.
  **Earning and spending** (`tools/heroic_loot.py`): every heroic boss's loot table gets the Sigil (`SIGILS` = 1,
  `SIGILS_FINAL` = 2 for `final=True` bosses; `check()` makes sure the final bosses are exactly
  `bulletin_board.DUNGEONS`). Bosses with `normal_loot=True` (Stockade, Ragefire Chasm) copy the normal boss's
  whole loot table. The Heroic Quartermaster (`src/unbound_heroic_quartermaster.cpp`, creature 190104 in
  `unbound_heroic_quartermaster.sql`) shows a menu of `QUARTERMASTER_PAGES`; each opens a never-spawned page
  creature's (190105-190109) vendor list through `SendListInventory(guid, pageEntry)` (a vendor window holds at
  most 150 items; `check()` enforces it), its items ordered by `quartermaster_sort_key` (slot, then armor or weapon
  type, then name) into the `slot` column. The Warden of Rare Wonders (creature 190200,
  `unbound_warden_of_rare_wonders.sql`, Tyrande Whisperwind's display 7274) is the same script
  (`npc_unbound_sigil_vendor`) with `WARDEN_PAGES` (Mounts, Pets, Tabards, Fun items; page creatures 190201-190204;
  items listed by hand); 190205 is a copy with Ysera's night elf display 28640 (same script and pages). NPCs
  190200-190299. Prices: `SIGIL_EXTENDED_COSTS` (Sigils -> ItemExtendedCost id), which
  `tools/custom_dbc.py` turns into the client and server rows. The Bulletin Board's weekly Heroic dungeon quests give
  `TIER_SIGILS` Sigils (`RewardItem1`). After a change run `python tools/heroic_loot.py`, `python
  tools/classic_heroics.py` (for `normal_loot` bosses' loot ids) and `python tools/bulletin_board.py`.
- **Unbound addon** (`addon/Unbound`): difficulty menu from level 60, `/heroic`, `/normal`, and the
  chat-window load-error guard.
- **Expansion content lock:** `Unbound.ExpansionUnlocked` in `mod_unbound.conf` (0/1/2). Dungeon finder: at startup
  (`OnBeforeWorldInitialized`) every `LFGDungeonData` of a locked expansion (except classic Naxxramas) gets
  expansion 255, above any account's. The server then leaves those random dungeons out of the random list (the
  client's dropdown shows what the server sends) and reports the specific ones as
  `LFG_LOCKSTATUS_INSUFFICIENT_EXPANSION` (1). The client builds the specific list itself from its own
  LFGDungeons.dbc (level and account expansion), so the Unbound addon wraps `LFD_CURRENT_FILTER` to drop
  dungeons whose `GetLFDLockInfo(id, 1)` reason is 1; empty headers then drop out on their own. The dropdown's
  random dungeons come from the client too (greyed out when locked): the addon wraps
  `LFDQueueFrameTypeDropDown_Initialize` and, while it runs, swaps `GetNumRandomDungeons` /
  `GetLFGRandomDungeonInfo` for versions without the ones locked with reason 1. A changed
  `Unbound.ExpansionUnlocked` applies after a restart. Players in a
  locked zone go to their hearthstone, else their race's start, else their faction's capital; GMs with GM
  mode on, battlegrounds and arenas are exempt. Death Knights are GM-only through
  `CharacterCreating.Disabled.ClassMask = 32`. Releasing an expansion: raise `Unbound.ExpansionUnlocked`
  and `MaxPlayerLevel` (70/80) and, for Wrath, clear the class mask (see the cheat sheet for playerbots).
