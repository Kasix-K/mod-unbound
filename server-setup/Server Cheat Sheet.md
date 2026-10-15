# Server Cheat Sheet

## Tips

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
| Warpweaver (transmogrifier) | `.npc add 190010` |
| Grizzle Lootsnatch (companion vendor) | `.npc add 190101` |

## Custom IDs

| Thing | Creature | Item | Spell |
|---|---|---|---|
| Transmogrify spell | (none) | (none) | 200200 |
| Loot Goblin companion | 190100 | 910001 | 200201 |
| Arcane Loot Scanner companion | 190102 (size 0.08) | 910002 | 200202 |
| Heroic Deadmines loot | (heroic bosses: entry + 1000000) | 910100-910121 | (none) |
| Blackened Defias Garb set (item set 950) | (none) | 910112, 910115, 910118, 910119 | 9102, 9336 (set bonuses) |
| World boss Hrimthar the Frostbound (spawn guid 9190110) | 190110, adds 190111 | 911000-911005 | (none) |

Preview a heroic item on a GM account with `.additem <item id>` (for example `.additem 910118`).

World boss Hrimthar the Frostbound is on Lake Kel'Theril in Winterspring. GM shortcuts: `.go creature id 190110`
goes to him; `.respawn` next to his corpse brings him back early (for testing).

## In-game features

- **Transmog:** cast Transmogrify, type `/transmog`, or talk to the Warpweaver.
- **Loot companions:** while the Loot Goblin or Arcane Loot Scanner is out, corpses within 55 yards are
  auto-looted, and opening a corpse also loots the corpses around it.
- **Reset lockouts:** right-click your portrait, then **Reset all instances**. This resets raids and
  heroic and normal dungeons. You must be outside the instance, with no bots inside.
- **Classic heroics:** right-click your portrait, then Dungeon Difficulty > Heroic (or type `/heroic`;
  `/normal` switches back), and enter the dungeon (level 60+). Available so far: Stormwind Stockades,
  The Deadmines, Ragefire Chasm. Heroic Deadmines bosses drop level 60 loot (see Custom IDs).
  Needs the **Unbound** addon, which shows the menu from level 60 instead of 65.
- **Solo dungeon finder:** queue alone or with bots, and you go straight in.
- **Perks:** type `/perks` or click the **Perks** tab at the bottom of the character sheet (C) to open the Character Perks window (needs the **UnboundPerks** addon). Always on
  for everyone: No Resurrection Sickness, No Daze, and Rapid Recovery (ranked by level: up to 8% health
  and mana per second, 4 seconds after combat). Switch on up to 5 Offensive perks (about +10% each) and your class perk (so far: Paladin
  Retribution). Perks can't be changed in combat; save favourite sets as loadouts.

<<<<<<< Updated upstream
## Gear attunement (GM commands for testing)

Attuned items permanently give the character 20% of their stats, even after the item is gone. **Attuning:**
wear the item and kill creatures that give experience (not grey ones): 50 kills for a green, 100 for a blue,
200 for an epic (an elite counts as 2, a boss as 10). Every equipped item that counts progresses at once, and
chat shows 25%, 50%, 75% and "fully attuned". **Any player** can type `.attune progress` to see their
equipped items' progress. The sacrifice altar and tooltips come next. GM commands (they act on the selected
player, else yourself):

| Command | What it does |
|---|---|
| `.attune check <item>` | Does the item count, and what would it give (shift-click the item, or type its id) |
| `.attune add <item>` | Attune the item (it must count) |
| `.attune remove <item>` | Take it out of the collection |
| `.attune info` | Items attuned, % of a full set collected, and the stats it gives |
| `.attune reset` | Remove the whole collection |
| `.attune progress` | (any player) Your equipped items' attunement progress |

Only green or better weapons and armour with required level 50-60 from classic content count (TBC and Wrath
items count once those expansions are released). Settings: `Unbound.Attunement.*` in `mod_unbound.conf`.

## Perk ranks

Rank support is built; so far **Rapid Recovery** (perk 3) and **Iron Will** (perk 303) have ranks. A
character's rank comes from its level, values in `mod_unbound.conf`:

| Rank | Level | Rapid Recovery: delay after combat | Rapid Recovery: health and mana per second | Iron Will: crowd control shorter by |
|---|---|---|---|---|
| 1 | 1 | 6 seconds | 4% | 10% |
| 2 | 30 | 5 seconds | 6% | 20% |
| 3 | 60 | 4 seconds | 8% | 30% |

Iron Will is a Utility perk (turn it on in `/perks`). It shortens enemy stuns, fears, roots, silences,
sleeps, polymorphs, charms, disorients and saps on you and your pets, on top of racials, talents and
diminishing returns.

=======
## Perk ranks

Rank support is built; so far only **Rapid Recovery** (perk 3) has ranks. A character's rank comes from
its level, values in `mod_unbound.conf`:

| Rank | Level | Delay after combat | Health and mana per second |
|---|---|---|---|
| 1 | 1 | 6 seconds | 4% |
| 2 | 30 | 5 seconds | 6% |
| 3 | 60 | 4 seconds | 8% |

>>>>>>> Stashed changes
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

