# Roadmap

Work-on list for the Unbound server. Tick a box (`- [x]`) when a feature is done and add it to the
[CHANGELOG.md](CHANGELOG.md) under that day's date. Effort is a rough guess: **easy** (a config or ready-made
module), **moderate** (custom code or data), **large** (several parts, client changes).

Guiding idea: inspired by Peloria, not a copy. No Peloria-sized numbers (billions): a fully progressed
player is at most several times a normal level 60, and every number stays far below the 32-bit limits.

## Power budget

The endgame goal: **one player can solo a full Mythic raid** (the player count will be low). Raids are
scaled down to one player, and **gear attunement is the main lever** that lets a player climb Mythic
levels; perks and perk ranks add on top. Design every power system against these targets, and change the
numbers here first if testing says so. Every number below is meant to be a config setting.

### Content

| Lever | Target |
|---|---|
| Classic raids solo (mod-autobalance) | A solo player faces **about 3 players' worth** of a raid; a full raid is unchanged. 20-player raids: `AutoBalance.InflectionPointRaid20M.CurveFloor = 0.1` (2.9 players' worth); 40-player raids: `AutoBalance.InflectionPointRaid40M.CurveFloor = 0.03` (2.8). Set 2026-10-14. |
| Mythic scaling | **+10% per level, added** (not multiplied): Mythic +10 = 2x, +20 = 3x the solo raid |
| Mythic capstone | **Mythic +10** is the first goal for a fully attuned player |
| Mythic maximum | Configurable, start at **Mythic +30** (the long climb past the capstone); raise it as players progress |
| Safety clamp | No creature health or damage above **2 billion**, whatever the settings (the 3.3.5 client shows numbers above about 2.1 billion wrongly). With added scaling this is never reached in practice: the biggest classic boss (Vaelastrasz, 3.3 million health) would pass it only around Mythic +90,000 solo |

### Player power needed

| Raid | Player power needed (x a normal level 60) |
|---|---|
| Base solo raid | about 2.8x |
| Mythic +5 | about 4.2x |
| Mythic +10 (capstone) | about 5.6x |
| Mythic +20 | about 8.4x |

### Player

| Lever | Target |
|---|---|
| Gear | Normal level 60 gear: the baseline (1x) |
| Perks | About **x1.55** with five Offensive perks (about +10% per perk) |
| Perk ranks | Up to about **x1.3** more on top of perks (together about x2) |
| Class perk | About **x1.25-1.35**: each spec's class perk is worth about **+25-35% to that spec's single-target damage** (a lone raid boss is what a solo Mythic raid is about). Extra area damage on trash is fine on top. Every class perk is held to this target, so no spec pulls ahead. Measure with a damage meter on a training dummy, perk off vs on. Paladin **Retribution** is estimated at about +35-40% (Holy +15% / Physical +10% about +12%, a free Crusader Strike per Divine Storm about +10-15%, a free Exorcism per Judgement about +5-10%, stronger Exorcism a few %), the top of the range: if testing confirms it, lower Holy to +10% |
| Gear attunement / sacrifice | About **+200% of gear stats** when well collected (about x3), the main lever: |
| - per item | **20%** of the item's fixed stats (tune 15-25% in testing); fixed stats only (no procs, set bonuses, weapon damage) |
| - which items count | **Every unique item** counts once (a second copy adds nothing); **green or better** |
| - minimum item level | Only items whose **required level is within 10 of the level cap** count (level 50+ while the cap is 60; it moves up with each expansion), so every attuned item matters and nobody grinds low-level items |
| - diminishing returns | Full value up to **+100%** of gear stats, half value up to **+200%**, a quarter beyond: early collecting feels strong, the long tail is the endgame grind (no hard cap) |
| - the grind | About **255 level 60 blue/epic items** for +200% with the diminishing returns (about 170 items give +150%); 20% of an item is about 7 stat points, a full set is about 600 (`ReferenceSetStats`). Tune `Percent` or the diminishing returns after testing |
| **Total** | About **6x** a normal level 60 when fully progressed, before the class perk: Mythic +10. With the class perk about **7.5-8x** (about Mythic +16-18). Each further Mythic level needs more collected gear and higher perk ranks |

Numbers check: a 6x character has a few thousand of a primary stat and tens of thousands of health, well
above normal WoW but nowhere near Peloria's billions.

### Attunement and sacrifice rules

Both styles fill **one shared collection** per character, so the end result is the same: an item gives
its full 20% whichever way it was collected. Time versus cost is the whole trade-off.

| | Attune | Sacrifice |
|---|---|---|
| How | Equip the item and kill creatures until it reaches 100% | Destroy the item for its stats at once |
| Speed | Slow | Instant |
| The item | **Kept**: wear it, transmog it, sell it later | **Destroyed** |
| Which items | Only gear the character **can equip** (their armour type, their class's weapons) | **Any item** that counts (see the Player table), including gear the character could attune |
| Value | **Full 20%** | **Full 20%** (not reduced) |
| Cost | Free | A price scaled by quality: gold for now, Heroic Badges once they exist |
| Cost for gear the character could attune | (free) | **Double** the normal price, so attuning stays the main route for one's own gear |

- **Collected stats are permanent:** once an item is 100% attuned (or sacrificed), its 20% stays whatever
  happens to the item (unequipped, banked, sold, deleted). An upgrade never costs anything: attune it too
  and both count. (The level copies of one Mythic item are the exception: the highest attuned copy
  replaces the lower ones, see Mythic+ gear.)
- **Progress is saved per item:** unequipping a partly attuned item pauses it (60% stays 60%); equipping it
  again carries on from there.
- **Stats only at 100%:** a partly attuned item gives nothing yet; its full 20% arrives when it reaches 100%.
- **Kills needed** (config settings): about **50 kills** for a green, **100** for a blue, **200** for an epic.
  An elite counts as 2 kills, a boss as 10. Every eligible equipped item gets progress from each kill.
- **Which kills count:** only creatures that **would give experience** (not grey for the player's level,
  not a no-experience creature such as critters or training dummies). At the level cap players earn no
  experience, so the check is "would give", not "gave".
- **Released expansions only:** items from The Burning Crusade and Wrath of the Lich King don't count until
  that expansion is released. Every item is tagged with its expansion by a small tool (from where it comes
  from: classic or expansion zones, dungeons, quests, vendors), because the level rule alone isn't enough
  (some TBC items require level 58-60, and item levels overlap). Attunement only accepts items from
  expansions up to `Unbound.ExpansionUnlocked` (the content lock's setting), so releasing an expansion
  turns its items on with that one change.
- An item counts only once. Sacrificing a partly attuned item finishes it (the price still applies).
- Sacrifice always shows a confirmation (item and price) before destroying anything.
- Tooltips show "Attunement: 37%", "Attuned", or "Can't attune: sacrifice only".
- A collection window in the perks' talent-tree style shows every absorbed item and the stat totals.
- **Per character:** each character has its own collection (alts start their own).
- **Sacrifice at an altar NPC:** an altar in the capital cities (players of both factions can use any,
  as everything else is cross-faction). Talking to it opens the sacrifice window: pick an item from the bags,
  see its stats and the price, confirm.
- **Sacrifice prices** (gold, scaled by quality; config settings, Heroic Badges later):

  | Quality | Price | Gear the character could attune (double) |
  |---|---|---|
  | Green (uncommon) | 2 gold | 4 gold |
  | Blue (rare) | 10 gold | 20 gold |
  | Purple (epic) | 50 gold | 100 gold |
  | Orange (legendary) | 250 gold | 500 gold |

### Mythic+ gear

Mythic+ bosses drop **epic gear whose stats grow with the Mythic level it dropped at** (Option A, decided
2026-10-14): every Mythic item exists once per level as its own item, generated by a tool like the Heroic
loot, so a tooltip shows plain white stats ("+22 Stamina"), exactly like normal WoW gear. All numbers are
config settings (the item generator reads them).

| Lever | Target |
|---|---|
| The items | Epic remakes of each boss's drops (same names and looks as its Heroic blues), one per boss, two from the final boss, like Heroic |
| Mythic +1 stats | **Level 60 epic level**: about 1.3x the Heroic version |
| Per Mythic level | **+2% of the +1 stats, added**: +10 = about 1.2x, +30 = about 1.6x the +1 item (helm: 20 Stamina at +1, about 24 at +10, 32 at +30) |
| Drop level | An item drops at the level the run was cleared at (a +12 clear drops +12 gear) |
| Item count | About 450 dungeon items x the configured maximum level (about 13,500 entries at +30; the client patch grows about 0.4 MB). Raising the maximum = rerun the generator and send out a new client patch |
| Attunement percent | **20% + 2% per Mythic level** for Mythic items (+1: 22%, +10: 40%, +30: 80%), so attuning high is worth much more than wearing high: a +30 helm gives 32 Stamina worn, 25 attuned |
| Attunement: one item | All level copies of a Mythic item count as **one item**: attuning (or sacrificing) a higher copy **replaces** the lower copy's bonus, it never adds to it. Attuning early is never wasted, waiting for a higher copy pays more. (Heroic and Mythic versions of a piece are different items and both count.) |
| Attunement: kills | A higher copy needs its own kills (the normal epic count); an upgrade never changes what is already attuned |
| Diminishing returns | A fourth step for the much larger Mythic totals: full value up to +100%, half to +200%, a quarter to +400%, **an eighth beyond** |

**Upgrading** (an Upgrade NPC next to the Keystone NPC): raise a Mythic item you own to a higher level, up to
**your best clear of that dungeon or raid** (each instance is worth pushing; gold can never buy a level you
haven't cleared). The item keeps its enchant, stays soulbound and only goes up (behind the scenes it is
swapped for the higher level's copy). Each level gained costs **gold and Mythic currency** (starting values,
config settings):

| Level gained (to +N) | Gold | Mythic currency |
|---|---|---|
| +2 to +10 | 5 x N gold (to +5: 25 gold) | 1 |
| +11 to +20 | 5 x N gold | 2 |
| +21 and above | 5 x N gold | 3 |

e.g. +1 to +5 costs 70 gold and 4 currency; +10 to +20 costs 775 gold and 20 currency.

**Mythic currency** (new, name to be decided, e.g. "Mythic Shard"): a currency item from Mythic bosses,
more at higher levels (e.g. 1 per boss plus 1 per 5 Mythic levels, double from the final boss; config
settings). Used for upgrades; later also a vendor (cosmetics, perk ranks) like the Heroic currency.

**Effect on the climb** (estimates, to be checked in testing):

| Fully collected | Gear worn | Attuned | Player power (with perks, before class perk) | Clears about |
|---|---|---|---|---|
| Before Mythic gear (normal attunement only) | 1x | +200% | about 6x | Mythic +10 (the capstone) |
| Every Mythic item attuned at +10 | about 1.5x | about +380% | about 10.5x | Mythic +28 |
| Every Mythic item attuned at +30 | about 2.1x | about +720% | about 18.5x | Mythic +55 |

The capstone (+10) stays the first goal; Mythic gear makes the climb past it much longer. The configured
maximum (+30) is reached long before a full +30 collection: raise it towards +60 as players get there. If
Mythic gear makes the climb too fast, lower the attunement percent per level first (2% to 1%), then the gear
stats per level.

Mechanics are a separate problem: some bosses need more than one player whatever the numbers
(Razorgore's orb, the Twin Emperors' teleport tank swap, C'Thun's stomach phase). They need small script
changes, raid by raid (see Next up).

## Done

- [x] Transmogrify spell (mod-transmog-plus window from anywhere)
- [x] Loot Goblin and Arcane Loot Scanner companions (auto-loot within 55 yards, AoE loot)
- [x] Cross-faction grouping, raids, guilds, chat, trade and auction house (not battlegrounds)
- [x] Solo dungeon scaling (mod-autobalance, floor 0.4) and solo dungeon finder (mod-solo-lfg)
- [x] No raid-group requirement, no instances-per-hour limit, Reset all instances resets raids too
- [x] Classic Heroic dungeons: pilot with Stormwind Stockades (level 60, 1.5x health and damage)
- [x] Heroic The Deadmines and Ragefire Chasm
- [x] Heroic loot for The Deadmines: one item per boss from a tank/healer/damage pool, Blackened
      Defias Garb set, level 60 gold (`tools/heroic_loot.py`)
- [x] World boss: Hrimthar the Frostbound at Lake Kel'Theril, Winterspring (`tools/world_bosses.py`)
- [x] Expansion content lock (classic only; TBC and Wrath released later), Death Knights GM-only
- [x] Unbound Perks: `/perks` window, 3 Permanent perks, all 25 Offensive perks (5 active at once),
      Paladin Retribution class perk; numbers scaled to normal WoW ranges (about +10% per perk)

- [x] Gear attunement (all 4 stages, 2026-10-14): the collection and its stats (20% per item, diminishing
      returns), item expansion tags, attuning by kills, the Altar of Sacrifice, item tooltips and the collection
      window (Attunement micro menu button, `/attunement`)

- [x] Classic Heroic dungeons, batch 1 (2026-10-14): Wailing Caverns, Shadowfang Keep, Blackfathom Deeps,
      Gnomeregan, with their summoned creatures (Mutanus, Baron Aquanis, Grubbis, ...) and Heroic loot
      (59 level 60 blues, 910122-910180)

- [x] Classic Heroic dungeons, batch 2 (2026-10-14): Razorfen Kraul, Scarlet Monastery (all 4 wings), Razorfen
      Downs, Uldaman, with their summoned creatures (Tuten'kash, Plaguemaw, the Tomb Fiends, Scarlet Scryers,
      ...) and Heroic loot (68 level 60 blues, 910181-910248)

- [x] Classic Heroic dungeons, batch 3 (2026-10-14): Zul'Farrak, Maraudon, Sunken Temple, Blackrock Depths, with
      their summoned creatures (Gahz'rilla, the pyramid event, Avatar of Hakkar, the Ring of Law, ...) and Heroic
      loot (120 level 60 blues, 910249-910368)

- [x] Classic Heroic dungeons, batch 4 (2026-10-14): Blackrock Spire (Lower and Upper, 15 players), Dire Maul
      (East, West, North), Scholomance, Stratholme (Live and Undead), with their summoned creatures (Gyth, the
      Brazier of Beckoning bosses, Kirtonos, Balnazzar, Ramstein, ...) and Heroic loot (181 level 60 blues,
      910369-910549). All 19 classic dungeons now have a Heroic mode.
- [x] Heroic creatures summoned by spells or transformations (2026-10-14), in all 19 dungeons: Sneed, boss adds,
      totems and wards now come at Heroic level too

- [x] Defensive perks (2026-10-14): 20 working (Greater Bulwark to Heavy Frame, at most 3 active). The old
      placeholders (Thick Skin, Second Wind, Steadfast, Fleet Foot, Treasure Sense) were removed; their ids
      201-203 and 301-302 are not reused.

## Next up

- [ ] **Soloable raid mechanics** (moderate, per raid): script changes for bosses that need several
      players (Razorgore, Twin Emperors, C'Thun, ...).
- [ ] **Perk ranks** (moderate): rank support is built (rank table, per-rank values, "2/3" badges,
      `.perk rank`), so far for Rapid Recovery (3 ranks by level). Still to do: ranks for the other perks
      with a number (Masteries, Pressure, ...) and how ranks are earned (levels, Heroic currency, quests).
- [ ] **More class perks** (large, 1-3 hours each): one per spec, like Paladin Retribution, each worth about
      +25-35% to its spec's single-target damage (the class perk target in the Power budget).
- [ ] **Heroic currency and vendor** (moderate): a token (e.g. "Heroic Badge") from Heroic bosses,
      spent on companions, mounts, transmog or gear. Becomes the Loot Goblin's currency.
- [ ] **Heroic classic raids** (moderate): Molten Core, Blackwing Lair, Zul'Gurub, Ruins and Temple of
      Ahn'Qiraj. (In 3.3.5, Onyxia and Naxxramas only exist as their level-80 versions.)
- [ ] **Raid Finder** (moderate to large): raids in the dungeon finder in level brackets. Still to
      decide: strict brackets or every raid up to the player's level; an addon window plus a
      server hook.

## Endgame and rewards

- [ ] **More world bosses** (moderate, mostly data): one per continent and level range, added to
      `tools/world_bosses.py`. Later a weekly rotation (boss of the week) with a first-kill bonus.

- [ ] **Mythic+** (large): player-chosen +1, +2, ... levels on top of Heroic, through mod-autobalance's
      multiplier hook. Scaling and limits per the Power budget (+10% per level added, capstone +10,
      configurable maximum starting at +30, 2 billion clamp). Best after gear attunement (its rewards
      feed attunement). Design (inspired by Peloria's Mythic Keystone, adapted):
  - **Mythic Keystone NPC** just inside the entrance of every dungeon and raid. Spawned automatically when
    an instance is created, at the instance's entry point (from the game's area trigger data), so every
    current and future instance gets one without placing it by hand.
  - **Keystone window** (same style as the perk window), opened by talking to the NPC:
    - **Tier picker:** - and + buttons, a slider from +1 to the configured maximum, and quick buttons
      **+1**, **+5**, **Max** and **Last** (the level of the last run).
    - **Run preview:** enemy power (x(1 + 0.1 x level), e.g. +10 shows x2.0) and the attunement and gold
      reward at that level.
    - **Best cleared** and **Last run**, per character and per instance.
    - **Activate Mythic +N:** group leader only, before the first pull; the level is locked once anything
      is pulled.
    - **Missing Attunements:** every item that can drop in this instance and counts for attunement (green
      or better, within the level rule), built from the instance's loot tables, with a collected count
      (e.g. "12 / 42 attuned") and the items still missing highlighted.
  - **Rewards:** **Mythic epic gear** whose stats grow with the level cleared, and the Mythic currency (see
    Power budget, Mythic+ gear), plus **faster attunement** (each kill gives more attunement progress, about
    +10% per Mythic level) and **more gold** from bosses (config settings).
  - **Upgrade NPC** next to the Keystone NPC: raise an owned Mythic item up to your best clear of that
    instance, for gold and Mythic currency.
  - **Entry requirements** (proposed, to confirm before building the Keystone NPC): level cap (60); dungeons
    on Heroic, raids on normal; +1 needs one Heroic (dungeon) or normal (raid) clear of that instance; then
    up to your best clear there + 1, or your best clear anywhere - 5, whichever is higher; a group is
    limited by its lowest member (bots don't count); no item level gate; no keystone item and no timer to
    start with; a failed run costs nothing (the level just isn't recorded as cleared).
  - **Build order:** 1. scaling core (autobalance's `OnAfterDefaultMultiplier` hook, `.mythic set`);
    2. Keystone NPC with a plain menu, best/last per character; 3. Mythic gear generator, drops at the
    cleared level, attunement changes (one item per Mythic piece, percent per level, fourth diminishing
    step); 4. Mythic currency and the Upgrade NPC; 5. other rewards; 6. Keystone window; 7. Missing
    Attunements; 8. raids and tuning. About 8-11 sessions; 1-3 make it playable.
- [ ] **Heroic-only loot** (moderate, mostly data): better versions of drops, or extra drops, on Heroic.
- [ ] **Random item bonuses** (easy): drops sometimes roll an extra enchant (mod-random-enchants).
- [ ] **Daily "Heroic of the Day"** (moderate): one random Heroic gives bonus rewards each day.
- [ ] **Change the Loot Goblin's currency** (easy once the Heroic currency exists).

## Progression past 60

- [ ] **Paragon levels** (moderate to large): XP past 60 earns points for small bonuses (+1% steps).
- [ ] **Achievements for classic Heroics** (easy to moderate, needs a client patch), with titles or
      rewards.

## A living solo world

- [ ] **Auction House bot** (easy): fills the auction house with items (mod-ah-bot).
- [ ] **Bot dungeon groups** (configuration): playerbots fill the party as tank and healer.
- [ ] **Bot battlegrounds** (configuration): playerbots queue for battlegrounds.

## Quality of life

- [ ] **Teleporter NPC or spell** (easy): travel to dungeons, raids and cities.
- [ ] **Account-wide collections** (moderate): companions and mounts on every character.
- [ ] **Personal XP rates** (easy): each player sets their leveling speed (mod-individual-xp).
- [ ] **Challenge modes** (easy to moderate): optional Hardcore or Ironman runs with rewards
      (mod-challenge-modes).
- [ ] **Guild houses** (easy): a private area per guild (mod-guildhouse).

## Open questions

- [ ] Disable the `.aoeloot on/off` commands, so AoE loot only comes from the loot companions?
- [ ] Confirm the content lock and Death Knight block in game on a non-GM account.
