# Server Cheat Sheet

## Tips

- **Preview a creature's size without restarting:** summon or spawn it, target it, and type
  `.modify scale <number>` on a GM account (for example `.modify scale 0.08`). The change only lasts
  until the creature despawns or is dismissed. When you find the size you like, ask Claude to make it
  permanent. Permanent size changes need a server restart.

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

## In-game features

- **Transmog:** cast Transmogrify, type `/transmog`, or talk to the Warpweaver.
- **Loot companions:** while the Loot Goblin or Arcane Loot Scanner is out, corpses within 55 yards are
  auto-looted, and opening a corpse also loots the corpses around it.
- **Reset lockouts:** right-click your portrait, then **Reset all instances**. This resets raids and
  heroic and normal dungeons. You must be outside the instance, with no bots inside.
- **Classic heroics:** right-click your portrait, then Dungeon Difficulty > Heroic (or type `/heroic`;
  `/normal` switches back), and enter the dungeon (level 60+). Available so far: Stormwind Stockades.
  Needs the **Unbound** addon, which shows the menu from level 60 instead of 65.
- **Solo dungeon finder:** queue alone or with bots, and you go straight in.

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

