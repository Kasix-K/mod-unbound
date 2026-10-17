# Server Cheat Sheet

## Tips

- **An NPC, item or quest still shows an old name** (e.g. "Altar of Sacrifice" instead of "Altar of Tribute"):
  the game client caches names. Exit the game, delete the client's `Cache\WDB` folder, and start again; it
  rebuilds the cache from the server (settings and addon data are in `WTF`, not touched).
- **Preview a creature's size without restarting:** summon or spawn it, target it, and type
  `.modify scale <number>` on a GM account (for example `.modify scale 0.08`). The change only lasts
  until the creature despawns or is dismissed. When you find the size you like, ask Claude to make it
  permanent. Permanent size changes need a server restart.
- **ElvUI:** use the official ElvUI 6.09 for 3.3.5a (github.com/ElvUI-WotLK/ElvUI, tag 6.09), not
  Synastria's build (errors like `Attune.lua:91: attempt to call global 'ItemLocIsLoaded'`). If
  `Interface\AddOns\ElvUI\Core\Attune.lua` exists, it's still Synastria's build: see the README to swap it.
  Done on the original PC on 2026-10-14; the Synastria build and all ElvUI settings files are backed up in
  `E:\WoW Solo Server\Backups\ElvUI-Synastria-20261014-165615` (copy them back to undo).

## Starting and stopping

| What | How |
|---|---|
| Start everything | Run `Start Server.bat` (it skips MySQL if MySQL is already running) |
| Stop the game servers | Type `server shutdown 1` in the **worldserver** window, then close the **authserver** window |
| Make a regular (non-GM) test account | Type `account create <name> <password>` in the worldserver window |
| Stop MySQL | Run `Stop MySQL.bat` (after the game servers are stopped) |
| Rebuild after code changes | Run `Rebuild Server.bat` with the servers stopped |
| Apply `.conf` changes without a restart | Type `reload config` in the worldserver window, or `.reload config` in game (not every setting reloads) |

## NPCs to place (stand where you want them, then type the command)

| NPC | Command |
|---|---|
| Grizzle Lootsnatch (companion vendor) | `.npc add 190101` |
| Altar of Tribute (infusion; one per capital city) | `.npc add 190103` |
| Heroic Quartermaster (Heroic gear for Heroic Sigils; one per capital city) | `.npc add 190104` |
| Warden of Rare Wonders (cosmetics for Heroic Sigils: mounts, pets, tabards, fun items; one per capital city) | `.npc add 190200` |
| Warden of Rare Wonders with Ysera's night elf look (same vendor) | `.npc add 190205` |

## Client assets (icons, textures)

Never in git: the repo lists them in `data/client_assets.txt`, the files live in `E:\WoW Solo Server\unbound-assets`.
After the list changes (game closed):

```
python tools/fetch_assets.py --from "T:\Ascension\resources\ascension-live\Data"
python tools/custom_dbc.py --client "E:\WoW 3.3.5a Unbound"
```

## Custom IDs

| Thing | Creature | Item | Spell |
|---|---|---|---|
| Transmogrify spell | (none) | (none) | 200200 |
| Perk auras (server-only, invisible) | (none) | (none) | 200210-200217 |
| Heroic Sigil (account-wide currency; icon display 70000, currency 400 bit 30, prices 3000-3010) | (none) | 912000 (currencies 912000-912099) | (none) |
| Loot Goblin companion | 190100 | 910001 | 200201 |
| Arcane Loot Scanner companion | 190102 (size 0.08) | 910002 | 200202 |
| Scavenger Imp companion (85 Heroic Sigils, Warden of Rare Wonders) | 190210 | 910003 | 200203 |
| Bounty Wayfinder (beside each Bulletin Board; spawn guids 9190211-9190212) | 190211 | (none) | (none) |
| Heroic Deadmines loot | (heroic bosses: entry + 1000000) | 910100-910121 | (none) |
| Heroic loot: Wailing Caverns, Shadowfang Keep, Blackfathom Deeps, Gnomeregan | (heroic bosses: entry + 1000000) | 910122-910180 | (none) |
| Heroic loot: Razorfen Kraul, Scarlet Monastery, Razorfen Downs, Uldaman | (heroic bosses: entry + 1000000) | 910181-910248 | (none) |
| Heroic loot: Zul'Farrak, Maraudon, Sunken Temple, Blackrock Depths | (heroic bosses: entry + 1000000) | 910249-910368 | (none) |
| Heroic loot: Blackrock Spire, Dire Maul, Scholomance, Stratholme | (heroic bosses: entry + 1000000) | 910369-910549 | (none) |
| Blackened Defias Garb set (item set 950) | (none) | 910112, 910115, 910118, 910119 | 9102, 9336 (set bonuses) |
| World boss Hrimthar the Frostbound (spawn guid 9190110) | 190110, adds 190111 | 911000-911005 | (none) |
| Shadowflame Ward chain (quests 921001-921012; spawn guids 9190206-9190209) | Kaelastrasz 190206; Vexathrax 190207, Pyraxis 190208, Azurathys 190209 | ward 912100, scales 912101-912108, unfinished ward 912109 | (none) |

Preview a heroic item on a GM account with `.additem <item id>` (for example `.additem 910118`).

World boss Hrimthar the Frostbound is on Lake Kel'Theril in Winterspring. GM shortcuts: `.go creature id 190110`
goes to him; `.respawn` next to his corpse brings him back early (for testing).

Bounty Wayfinder: stands beside each Bulletin Board (Stormwind, Orgrimmar) and drops you from 90 yards up
beside the board's open-world quests, outside aggro range, with Wayfinder's Descent (spell 200204, a slow fall
until you land). Move one with `.npc move` if it blocks the board.

Shadowflame Ward chain: Kaelastrasz stands at Thorium Point (Searing Gorge); `.go creature id 190206` goes to
him (`.npc move` to place him better). Elites: `.go creature id 190207` (Vexathrax, Burning Steppes), 190208
(Pyraxis, Grim Batol), 190209 (Azurathys, Azshara). Test the cloak with `.additem 912100`, skip ahead with
`.quest complete <id>` (921001-921012), and `.additem 15410` gives a Scale of Onyxia.

World boss announcements (whole server, in chat): 10 and 5 minutes before a world boss spawns, when it
spawns (with the location), when it dies (with who killed it), and when nobody killed it within 24 hours
(it then despawns, never mid-fight, and its 3-day respawn timer starts again). Settings:
`Unbound.WorldBoss.*` in `mod_unbound.conf`; the yells themselves are only heard in the boss's zone now.

## In-game features

- **Transmog:** cast Transmogrify or type `/transmog`; no NPC needed. (mod-transmog-plus's Warpweaver,
  `.npc add 190012`, opens the same window but isn't placed anywhere.)
- **Loot companions:** while the Loot Goblin or Arcane Loot Scanner is out, corpses within 55 yards are
  auto-looted, and opening a corpse also loots the corpses around it. That's the only way to AoE loot:
  `.aoeloot on/off` is disabled. The **Scavenger Imp** (85 Heroic Sigils from the Warden of Rare Wonders) is the
  smaller one: when you open a corpse, it also loots up to 4 of the nearest corpses within 27 yards
  (`Unbound.ScavengerImp.ExtraCorpses` and `.Range` in `mod_unbound.conf`).
- **Reset lockouts:** right-click your portrait, then **Reset all instances**. This resets raids and
  heroic and normal dungeons. You must be outside the instance, with no bots inside.
- **Classic heroics:** right-click your portrait, then Dungeon Difficulty > Heroic (or type `/heroic`;
  `/normal` switches back), and enter the dungeon (level 60+). Every classic dungeon has one (19), from the
  Stormwind Stockades to Stratholme; Blackrock Spire's is for up to 15 players like its normal mode. Heroic
  bosses drop level 60 loot (one item each, two from the final boss or each wing's last boss) in all of them
  except the Stockades and Ragefire Chasm. Needs the **Unbound** addon, which shows the menu from level 60
  instead of 65.
- **Solo dungeon finder:** queue alone or with bots, and you go straight in.
- **Onyxia's Lair:** a classic level 60 raid again (Dustwallow Marsh, the Wyrmbog), 10-player difficulty.
  Hand the Head of Onyxia to Thrall or King Varian Wrynn, then the follow-up to Overlord Runthak or Major
  Mattingly for the Rallying Cry of the Dragonslayer.
- **Classic Naxxramas:** the Necropolis floats above Plaguewood in the Eastern Plaguelands; use the "Teleport To
  Naxxramas" runestone below it (level 60-70). Needs "The Dread Citadel - Naxxramas" from Archmage Angela
  Dosantos at Light's Hope (cheaper with more Argent Dawn reputation). Your group within 30 yards comes along.
  Tier 3 quests are at Light's Hope; there are no exit portals inside (use your hearthstone).
- **Bulletin Board:** in Stormwind's Trade District (by the auction house) and Orgrimmar's Valley of Strength
  (both factions can use either). Level 60: two daily kill bounties, a daily quest for each of your
  professions, weekly dungeon and raid quests (Normal dungeon, Heroic dungeon, Normal raid, a different
  one each), and a weekly elite bounty (an elite camp, a different one each week). GMs: `.bulletinboard show` lists this week's picks, `.bulletinboard reroll` picks again. Move a
  board with `.gobject move` if it stands badly.
- **Raid Finder:** open the Dungeon Finder (or type `/raidfinder`) and choose **Raids** in its dropdown (under
  the random dungeons and Specific Dungeons). Tick a raid and press **Enter Raid**. In a group the leader picks; everyone else gets an "Enter the raid?"
  prompt. **Leave Raid** takes you back to where you joined from. Needs the **UnboundRaidFinder** addon.
- **Solo raids:** alone in a raid (no other players or bots; pets are fine), mechanics no single player can
  handle are changed. Blackwing Lair: in Razorgore's room, walk over (or click) the eggs to break them once
  Razorgore is pulled, and don't kill him before the last egg; his add waves come every 30 seconds instead of 15; Grethok, Vaelastrasz, Ebonroc, Chromaggus and
  Nefarius skip their solo-killing spells. Molten Core, Zul'Gurub and Ahn'Qiraj: no mind controls (Lucifron's
  adds, Jin'do's totem, Hakkar, Skeram, Qiraji Mindslayers), no Jin'do Banish, Hakkar Blood Siphon, Ayamiss
  Paralyze, Molten Core Firelords' silencing Soul Burn, Ossirian Curse of Tongues or Twin Emperors Heal Brother
  (and Ossirian's Enveloping Winds only every 40
  seconds); each hit on Viscidus counts 10 times towards freezing (frost) and
  shattering (melee) him. Naxxramas: Gothik doesn't reset when he teleports to the other side, and Stalagg and
  Feugen don't revive each other or overload their coils (the
  Four Horsemen need `Unbound.Naxx40.Doable.FourHorsemen = 1` to be beaten solo). Switch them off in
  `mod_unbound.conf` (`Unbound.SoloRaid.*`).
- **Perks:** type `/perks` or click the **Perks** side tab on the right edge of the character sheet (C) to open the Character Perks window (needs the **UnboundPerks** addon). Always on
  for everyone: No Resurrection Sickness, No Daze, and Rapid Recovery (ranked by level: up to 8% health
  and mana per second, 4 seconds after combat). Switch on up to 5 Offensive perks (about +10% each) and one class perk (so far: Paladin
  **Crusader's Oath**, Retribution, **Bulwark's Oath**, Protection, or **Lightbringer's Oath**, Holy). Perks can't be changed in combat; save favourite sets as loadouts.
- **Lightbringer's Oath** (Paladin): Judgement, Exorcism and Holy Shock build **Holy Power**; the perk teaches
  **Light of Dawn** (a Holy blast that heals you) and **Atonement** (for up to 30 seconds part of all your
  healing also hits the enemy you're fighting, so healing yourself kills the boss). From level 30 choose an oath:
  **the Dawn** (more Holy Power, a bigger Light of Dawn low on health) or **Mercy** (more self-healing). At 60:
  **Naaru's Blessing** (2 min, a small Naaru smites and heals your group within 10 yards for 15 seconds). In groups only a quarter of
  overhealing counts (`Unbound.Perks.LightbringersOath.GroupOverheal`). Perk 1003; spells 200229-200231;
  creature 190222.
- **Bulwark's Oath** (Paladin): Hammer of the Righteous, Judgement and Avenger's Shield build **Holy Power**; the
  perk teaches **Aegis Strike** (a shield strike) and **Word of Glory** (a self heal), which spend it all. From
  level 30 choose an oath: **the Bulwark** (Bastion: less damage taken, more block, a full Word of Glory) or
  **Retaliation** (blocks hit back, stronger Consecration). At 60: **Guardian of the Light** (3 min, 30% less
  damage taken for 15 seconds). Perk 1002; spells 200224-200228; guardian creature 190221.
- **Crusader's Oath** (Paladin): Crusader Strike, Judgement and Hammer of Wrath build **Holy Power** (up to 3,
  icons under the player frame); the perk teaches **Templar's Verdict** (a Holy strike) and **Inquisition** (more
  Holy damage), which spend it all. From level 30 choose an oath in the perk window: **Vengeance** (bigger
  Verdicts, on crits and below 35% health) or **the Crusade** (Divine Storm builds and spends Holy Power). At 60:
  **Ashbringer's Call** (2 min, a spirit fights for 15 seconds). To switch back to the original Retribution perk:
  `Unbound.Perks.Retribution.Classic = 1` in `mod_unbound.conf`, then restart.

## Gear infusion (GM commands for testing)

Infused items permanently give the character 20% of their stats, even after the item is gone. **Infusing:**
wear the item and kill creatures that give experience (not grey ones): 50 kills for a green, 100 for a blue,
200 for an epic (an elite counts as 2, a boss as 10). Every equipped item that counts progresses at once, and
chat shows 25%, 50%, 75% and "fully infused". **Any player** can type `.infuse progress` to see their
equipped items' progress. **Tribute:** talk to the **Altar of Tribute** to pick an item from your bags; it is destroyed and
infused at once for 2 / 10 / 50 / 250 gold (green / blue / epic / legendary), double for gear you could infuse
by wearing it. **Item tooltips** show each piece's infusion (infused, % and kills, tribute only, or why it
doesn't count), and the **Infusion** side tab on the right edge of the character sheet (C), under Perks, or `/infusion` opens the collection window:
your infused items and items in progress (60 a page: the arrows or the mouse wheel turn pages), the stats they give
and how far along the diminishing returns you are.
Needs the **UnboundAttunement** addon. GM commands (they act on the selected
player, else yourself; the old `.attune` still works):

| Command | What it does |
|---|---|
| `.infuse check <item>` | Does the item count, and what would it give (shift-click the item, or type its id) |
| `.infuse add <item>` | Infuse the item (it must count) |
| `.infuse remove <item>` | Take it out of the collection |
| `.infuse info` | Items infused, % of a full set collected, and the stats it gives |
| `.infuse reset` | Remove the whole collection |
| `.infuse fill 100` | (testing) Infuse items until the bonus is +100% of a full set's stats after diminishing returns |
| `.infuse fill 200` | (testing) The same up to +200% |
| `.infuse fill full` | (testing) Infuse every item that counts: the most a character can collect |
| `.infuse progress` | (any player) Your equipped items' infusion progress |

`.infuse fill` picks real items, gear the target can use first, best first, so the stats look like a real
collection. `.infuse reset` undoes it.

Only green or better weapons and armour with required level 50-60 from classic content count (TBC and Wrath
items count once those expansions are released). Settings: `Unbound.Attunement.*` in `mod_unbound.conf`.

## Perk ranks

The 4 pet-only perks (Pet Encouragement, Pet's Blessing, Pets replenishment, Pets Roar) only show for
Hunters, Warlocks, Death Knights and Mages.

All 63 perks but No Daze and No Resurrection Sickness have ranks (the three Paladin class perks have 3, at levels 1 / 30 / 60,
each unlocking more; the original Retribution perk has none). A character's
rank comes from its level; values in `mod_unbound.conf` (`Unbound.Perks.<Name>.*`). Test any rank with
`.perk rank <perk id> <rank>`; `.perk rank <perk id>` goes back to the level's rank.

**Offensive, Defensive and Utility perks** have 5 ranks: Ranks 1-3 at levels 1 / 30 / 60 (Rank 3 is the
value from before Ranks 4-5 existed), Ranks 4-5 (about 1.3x / 1.5x of Rank 3) for the endgame, GM-only for now
(they unlock at level 255 until a way to earn them is built). The Defensive and Utility tables below show
Ranks 1-3; Ranks 4-5 are in `mod_unbound.conf` (e.g. Iron Will 35 / 40%, Juggernaut's cap 27 / 25%, Steady
Hands' pushback 80 / 90%). Thresholds, durations and drawbacks stay the same at every rank. A +10% perk is 4 / 7 / 10 / 13 / 15%, a +15% one (Pet Encouragement, Merciless) 6 / 10 / 15 / 19 / 22%;
Cyclic Power's high point 10 / 15 / 20 / 25 / 30%, Critical Understanding's cap 8 / 14 / 20 / 26 / 30%, Pressure's
stacks 4 / 7 / 10 / 13 / 15, Chaos's chance 4 / 7 / 10 / 13 / 15%. Drawbacks and caps don't change with the rank.

Rapid Recovery and Iron Will:

| Rank | Level | Rapid Recovery: delay after combat | Rapid Recovery: health and mana per second | Iron Will: crowd control shorter by |
|---|---|---|---|---|
| 1 | 1 | 6 seconds | 4% | 10% |
| 2 | 30 | 5 seconds | 6% | 20% |
| 3 | 60 | 4 seconds | 8% | 30% |

Iron Will is a Utility perk (turn it on in `/perks`). It shortens enemy stuns, fears, roots, silences,
sleeps, polymorphs, charms, disorients and saps on you and your pets, on top of racials, talents and
diminishing returns.

**Defensive perks** (at most 3 active; Rank 1 / 2 / 3 at levels 1 / 30 / 60, values in `mod_unbound.conf`):

| Id | Perk | Rank 1 / 2 / 3 |
|---|---|---|
| 204 | Greater Bulwark | Dodge + Parry become Block at 100 / 110 / 120% (needs a shield) |
| 205 | Evasive Maneuvers | Block + Parry become Dodge at 100 / 110 / 120% |
| 206 | Parry King | Block + Dodge become Parry at 100 / 110 / 120% (only one of 204-206) |
| 207 | Reinforced Armor | physical damage taken -4 / 7 / 10% |
| 208 | Spellwarded | magic damage taken -4 / 7 / 10% |
| 209 | Stoicism | damage-over-time taken -8 / 14 / 20% (you and pet) |
| 210 | Defensive Momentum | up to 5 / 7.5 / 10% damage reduction built by moving, lost after 2 s still |
| 211 | Fortress | up to 5 / 7.5 / 10% built by standing still, lost after 3 s moving (not with 210) |
| 212 | Juggernaut | no hit takes more than 40 / 35 / 30% of maximum health, once every 3 s |
| 213 | Counterweight | after a dodge, parry or block, next hit taken -10 / 15 / 20% |
| 214 | Titan's Resolve | up to 5 / 7.5 / 10% damage reduction, the more health missing the more |
| 215 | Second Wind | a hit over 15% of maximum health: heal 1 / 1.5 / 2% a second for 5 s |
| 216 | Hardened Flesh | the part of a hit over 10% of maximum health -10 / 15 / 20% |
| 217 | Pet's Blessing | pet damage taken -10 / 15 / 20% |
| 218 | Shield Wall Training | each block: +0.5 / 0.75 / 1% block chance for 5 s, up to 5 stacks |
| 219 | Survival Instinct | below 30% health: damage taken -8 / 12 / 15% |
| 220 | Vital Reserve | maximum health +4 / 7 / 10% |
| 221 | Enduring | healing received +4 / 7 / 10% |
| 222 | Thornmail | melee attackers take 10 / 20 / 30% of the damage they deal back |
| 223 | Heavy Frame | armor +5 / 10 / 15% |

The avoidance conversions work on melee attacks; the character sheet still shows the unconverted chances.

**Utility perks** (at most 3 active; Rank 1 / 2 / 3 at levels 1 / 30 / 60, values in `mod_unbound.conf`):

| Id | Perk | Rank 1 / 2 / 3 |
|---|---|---|
| 303 | Iron Will | enemy crowd control 10 / 20 / 30% shorter (you and pet) |
| 304 | Longer Legs | run and mount speed +4 / 7 / 10%, swim +20 / 35 / 50%, fall damage -20 / 35 / 50% |
| 305 | Planting your legs | after 3 s standing still: 0.5 / 0.75 / 1% health, 0.25 / 0.4 / 0.5% mana per second |
| 306 | Relentless Pursuit | +15 / 25 / 35% speed for 10 s after you or your pet kill something |
| 307 | Vampirism | heal 3 / 4 / 5% of damage dealt (not with Soul Drain) |
| 308 | Soul Drain | heal 6 / 8 / 10% of damage dealt, pet too; direct healing taken -20% (not with Vampirism) |
| 309 | Pets replenishment | pet healing taken +20 / 35 / 50% |
| 310 | Pets Roar | pet threat +100 / 200 / 300% |
| 311 | Silent Killer | your threat -20 / 35 / 50% (not with Unbreakable Presence) |
| 312 | Unbreakable Presence | your threat +50 / 100 / 150% (not with Silent Killer) |
| 313 | Spell-Protected Steady Hands | pushback -30 / 50 / 70%, interrupt lockouts and silences -10 / 20 / 30% |
| 314 | Mana Leech | 1 / 1.5 / 2% of damage dealt as mana (mana users only) |
| 315 | Endless Rage | +8 / 14 / 20% rage from damage dealt and taken (Warriors and Druids only) |
| 316 | Focused Mind | energy regenerates 8 / 14 / 20% faster (Rogues and Druids only) |

GM testing: target a player (or nobody, for yourself) and type `.perk rank 3 2` for Rank 2;
`.perk rank 3` goes back to the rank the level gives. The perk window shows the rank as "2/3".
Next: give other perks ranks (for example Masteries: Rank 1 +4% ... Rank 4 +10%) and decide how ranks
are earned (levels, Heroic currency, quests, ...). No Daze and No Resurrection Sickness stay on/off.

## Expansion lock (classic only for now)

The Burning Crusade and Wrath of the Lich King are locked: level cap 60, no Outland or Northrend, no
expansion dungeons or raids, and no new Death Knights for regular accounts (GM accounts can still create
them, and Ebon Hold stays open for Death Knights). The Blood Elf and Draenei starting zones stay
open. GMs with GM mode on (`.gm on`) can go anywhere.

To release an expansion (stop the servers first):

| Release | Change |
|---|---|
| The Burning Crusade | `Unbound.ExpansionUnlocked = 1` in `server\configs\modules\mod_unbound.conf`, `MaxPlayerLevel = 70` in `worldserver.conf`, and in `playerbots.conf` set `RandomBotMaxLevel = 70` and add 530 to `RandomBotMaps` |
| Wrath of the Lich King | `Unbound.ExpansionUnlocked = 2`, `MaxPlayerLevel = 80`, `CharacterCreating.Disabled.ClassMask = 0` (Death Knights), and in `playerbots.conf` set `RandomBotMaxLevel = 80`, add 571 to `RandomBotMaps`, and `DisableDeathKnightLogin = 0` |

