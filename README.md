# mod-unbound

Custom features for the WoW 3.3.5a Unbound server.

## Roadmap and changelog

| [Roadmap](ROADMAP.md) | [Changelog](CHANGELOG.md) | [Technical notes](TECHNICAL_NOTES.md) |
|---|---|---|
| What's planned next, with rough effort | Every feature, with the date it was added and last changed | How each system is built and what to run after changing it |

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

**Setting up the client by hand** (if you skipped the script's last step): copy `addon\Unbound`,
`addon\UnboundPerks`, `addon\UnboundAttunement` and `addon\UnboundRaidFinder` from this repository and `addon\Transmog` from `azerothcore\modules\mod-transmog-plus` into the client's
`Interface\AddOns`, then build the client patch (with the game closed):

```bash
python tools/custom_dbc.py --client "D:\WoW 3.3.5a Unbound" --dbc "D:\WoW Solo Server\data\dbc"
```

**ElvUI: use the official 6.09.** The Unbound client first came with Synastria's build of ElvUI, which
changes 36 files (attunement icons that call Synastria-only client functions, plus changes to movers,
config, media, bars and skins). On this server it errors, e.g. with the character skin on:
`Interface\AddOns\ElvUI\Core\Attune.lua:91: attempt to call global 'ItemLocIsLoaded' (a nil value)`.
The fix is to replace `ElvUI` and `ElvUI_OptionsUI` in the client's `Interface\AddOns` with the official
ElvUI 6.09 for 3.3.5a (the version the Synastria build is based on), with the game closed:

```bash
git clone --depth 1 --branch 6.09 https://github.com/ElvUI-WotLK/ElvUI.git ElvUI-6.09
```

Then copy its `ElvUI` and `ElvUI_OptionsUI` folders over the client's (delete the old ones first). Keep
`ElvUI_AddOnSkins` (it has no Synastria code). ElvUI settings carry over (same save files). A client with
`Interface\AddOns\ElvUI\Core\Attune.lua` still has the Synastria build.

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
- Keep `server-setup/Server Cheat Sheet.md` and `ROADMAP.md` up to date with your changes, and add every
  new or changed feature to `CHANGELOG.md` under today's date (and update its row in the feature index).
- New features go in their own `src/unbound_<feature>.cpp`, registered in `src/unbound_loader.cpp`, and get
  an entry in `CHANGELOG.md` (plus `TECHNICAL_NOTES.md` if others need to know how it works).
- Custom IDs are shared, so pick new ones next to the existing ones and say so in the commit: spells
  2002xx, items 9100xx (heroic loot 910100-910999, world boss loot 911000-911999), item sets 950-999,
  creatures 1901xx (world bosses 190110-190199, spawn guids 9190110-9190199),
  SkillLineAbility 9000xx, loot references 9100100-9100199, Bulletin Board
  (gameobject 920000, spawn guids 9920000-9920009, quests 920001-920999, pools 920000-920099, world states
  920001-920009). Classic Naxxramas (from mod-individual-progression)
  uses creatures 351000-351099, creature guids 361000-362999, gameobjects and their guids 361000-361003 and spells
  90001-90008.

## Credits

Classic Naxxramas (`src/naxx40`, `data/sql/db-world/unbound_naxx40*.sql`) comes from
[mod-individual-progression](https://github.com/ZhengPeiRu21/mod-individual-progression) by ZhengPeiRu21 (Naxx
40 scripts and data by Sogladev), MIT license (`src/naxx40/LICENSE-mod-individual-progression`).
