# In-game test checklist

Everything below compiles and the server starts cleanly, but none of it has been checked in the game client
yet. Tick each box as you check it. If something fails, write down what you saw next to the box (chat message,
what the boss did, a Lua error) so it can be fixed.

Most checks are quickest on a GM account (`.gm on` for travel, then `.gm off` before fighting: GMs don't
count as players for the solo raid changes). Use a level 60 character unless a check says otherwise.

## 0. Before you start

- [ ] Pull the branch, run **Rebuild Server.bat**, then `apply-unbound-settings.ps1`.
- [ ] Copy the addons again: `addon\UnboundPerks`, `addon\UnboundAttunement`, `addon\UnboundRaidFinder`
      (new) into the client's `Interface\AddOns`.
- [ ] On the character select screen, AddOns: **Unbound Infusion** and **Unbound Raid Finder** are listed and
      enabled.
- [ ] The worldserver console shows no new errors from mod-unbound while it starts (the database updater
      applies the new SQL files the first time).

## 1. Infusion (renamed from attunement)

- [ ] Hover a level 50+ green or better item you can wear: the tooltip says **"Infusion: x% (n/m kills)"** or
      **"Wear it and slay foes to infuse it"**. An infused item says **"Infused: its stats are yours for good"**.
- [ ] Hover gear you can't wear (wrong armour type): **"Infusion: tribute only (you can't wear it)"**.
- [ ] Kill creatures with gear on: chat shows **[Infusion]** messages at 25%, 50% and 75%, then
      **"… is fully infused!"**.
- [ ] The character sheet (C) has two side tabs on its right edge, Perks and Infusion below it; Infusion's tooltip says
      "Gear Infusion". Opening one window closes the other.
- [ ] The window opens with the button, `/infusion`, `/infuse`, and the old `/attunement` and `/attune`.
      The title is **Gear Infusion**, with an **Infused (n)** tab and **Infusion stats** on the left.
- [ ] `.infuse progress` works as a normal player, and `.attune progress` still works too.
- [ ] As a GM: `.infuse check <item>`, `.infuse add <item>`, `.infuse info`, `.infuse remove <item>` and
      `.infuse reset` all answer with the new wording.
- [ ] Nowhere in the gear system still says "attune", "attunement" or "attuned" (classic Naxxramas is supposed
      to, see section 7).

## 2. Altar of Tribute (renamed from Altar of Sacrifice)

- [ ] `.npc add 190103`: the altar is named **Altar of Tribute**, with **<Infusion>** under its name.
- [ ] Its greeting talks about tribute and infusing (no "sacrifice" or "attune").
- [ ] Its list shows bag items that count; each says "(x% infused)" or "- you could infuse it by wearing it".
- [ ] Choosing one shows **"Offer <item> as tribute?"** with the gold price (2 / 10 / 50 / 250 gold for green /
      blue / epic / legendary, double for gear you could wear).
- [ ] Accepting takes the gold, destroys the item, and chat says **"… was offered as tribute and is fully
      infused!"**. The item shows in the window's Infused tab.
- [ ] With too little gold you get "You need … gold to offer … as tribute." and keep the item.
- [ ] With nothing that counts in your bags, the altar says so.
- [ ] Don't delete the old altars you placed before. Their spawns keep working with the new name.

## 3. Bulletin Board

Boards: Stormwind Trade District (`.go xyz -8812.4 651.6 94.9 0`) and Orgrimmar Valley of Strength
(`.go xyz 1609.8 -4376.9 9.77 1`).

- [ ] Both boards are there, upright and facing the right way. They're clickable by both factions.
- [ ] Level 60 only: a level 59 character gets no quests from it.
- [ ] **Kill dailies:** exactly 2 bounties are offered. Take one, kill the creatures, and the quest **does not**
      complete before the kills are done (this was the auto-complete bug). Turn it in for 15 gold.
- [ ] The next day (or after a daily reset) a different pair of bounties shows up.
- [ ] **Profession dailies:** a character with a gathering profession sees its gathering quest (12 gold).
      A character with a crafting profession sees its crafting quest (15 gold). A profession you don't have
      isn't offered.
- [ ] Gather or craft the items and turn them in: the items are taken and the gold is given.
- [ ] **Weeklies:** `.bulletinboard show` lists this week's picks. The board offers the Normal dungeon,
      Heroic dungeon and Normal raid weekly, and they match `.bulletinboard show`. No two tiers have the same
      dungeon.
- [ ] Kill the final boss of the weekly dungeon. The quest completes; turn it in (Normal 50 gold, Heroic
      100 gold). Do the same for the raid (100 gold).
- [ ] **Elite bounty:** one elite bounty weekly (75 gold), listed in `.bulletinboard show`. Kill the elites and
      turn it in.
- [ ] `.bulletinboard reroll` changes the weeklies on the board (you may need to close and reopen it). The elite
      bounty is never the same as the one before.
- [ ] Rewards are gold only: no infusion progress from turning in.
- [ ] Each weekly can be done once per week, and each daily once per day.

## 4. Raid Finder

- [ ] Open the Dungeon Finder (I key or the micro menu): its type dropdown (random dungeons, Specific Dungeons)
      ends with **Raids**. `/raidfinder` opens the Dungeon Finder on Raids.
- [ ] Choosing Raids replaces the dungeon list with the raids, in the same style (checkbox, lock icon, level,
      "Classic Raids" header), and Find Group becomes **Enter Raid**. Choosing a random dungeon or Specific
      Dungeons again brings the normal Dungeon Finder back, and queueing for a dungeon still works.
- [ ] Close and reopen the Dungeon Finder while on Raids: the dropdown still says Raids and has the Raids entry.
- [ ] Raids you can't enter show a lock icon (level, Naxxramas attunement); hovering a raid shows no tooltip. Ticking a raid unticks the one before (one raid at a time).
- [ ] Only the classic raids are listed (no Burning Crusade or Wrath raids while those expansions are locked).
- [ ] **Solo:** pick Molten Core and Enter. You're teleported **inside** the raid near its entrance.
- [ ] **Leave Raid** takes you back to where you joined from. Also try it after logging out and back in inside
      the raid.
- [ ] **Group:** a non-leader can't pick a raid. The leader enters and goes in first. Each other member gets the
      summon-style prompt ("<leader>'s group is entering <raid>. Enter the raid?"). Accepting teleports them
      next to the leader, declining (or 2 minutes passing) leaves them where they are.
- [ ] A member below the level or without the Naxxramas attunement is told why and isn't teleported.
- [ ] Playerbots in the group come along.
- [ ] Set `Unbound.RaidFinder.Enable = 0`, restart, and choose Raids: chat says "The Raid Finder is turned off
      on this server." Set it back to 1 afterwards.

## 5. Onyxia's Lair (classic level 60)

- [ ] A level 60 character can enter the lair (10-player difficulty). A level 59 character can't. 25-player
      difficulty can't be entered.
- [ ] Onyxia is **level 63** with about **1.1 million** health (scaled down when solo).
- [ ] No Onyxian Lair Guards. Whelps and Warders are level 60 classic.
- [ ] Her damage is classic: Flame Breath around 3,000-4,000 (not 19,000-21,000), and Deep Breath, Fireball,
      Wing Buffet, Tail Sweep, Eruption and Fire Nova are survivable at level 60.
- [ ] Solo kill is possible at level 60 in good gear (autobalance about 2.8 players' worth).
- [ ] Loot: two Tier 2 helms, one of Sapphiron Drape / Ring of Binding / Eskhandar's Collar / Ancient
      Cornerstone Grimoire, sometimes Deathbringer / Vis'kag / Shard of the Scale, the Onyxia Hide Backpack, and
      the Head of Onyxia for your faction. No emblems, level 80 gear or Onyxian Drake.
- [ ] She **can't be skinned**: no Scale of Onyxia.
- [ ] Horde: the Head starts **Victory for the Horde** (Thrall), then **For All To See** (Overlord Runthak). The
      head goes up in Orgrimmar and everyone nearby gets the **Rallying Cry of the Dragonslayer**.
- [ ] Alliance: **Victory for the Alliance** (King Varian Wrynn), then **Celebrating Good Times** (Major
      Mattingly). Same head and buff in Stormwind.
- [ ] Hover her loot: it counts for infusion.

## 6. Solo raid mechanics

Do these **alone** (pets are fine), with `.gm off`. To check that the changes switch off with two players,
bring one other player or a playerbot for at least one boss.

**Blackwing Lair**
- [ ] Razorgore: Grethok the Controller's Dominate Mind fails. Walking over or clicking the eggs breaks them.
      The Orb still works. Killing Razorgore before the last egg still blows up the room.
- [ ] Razorgore: the orcs and dragonkin in the room attack as normal and the fight is doable alone.
- [ ] Vaelastrasz: Burning Adrenaline fails (no bomb on you).
- [ ] Ebonroc: Shadow of Ebonroc fails (he doesn't heal from your hits).
- [ ] Chromaggus: Time Lapse and Chromatic Mutation fail.
- [ ] Nefarian: Lord Victor Nefarius' Shadow Command fails (you aren't mind controlled).
- [ ] Shadowflame still needs an Onyxia Scale Cloak (expected for now, until Shadowflame Ward exists).

**Molten Core**
- [ ] Lucifron: his Flamewaker Protectors' Dominate Mind fails.

**Zul'Gurub**
- [ ] Jin'do: the Brain Wash Totem and Banish fail.
- [ ] Hakkar: Cause Insanity and Blood Siphon fail.

**Ruins of Ahn'Qiraj**
- [ ] Ayamiss: Paralyze and the larva's Feed fail.

**Temple of Ahn'Qiraj**
- [ ] Skeram: True Fulfillment fails.
- [ ] Twin Emperors: Heal Brother fails.
- [ ] Qiraji Mindslayers: Cause Insanity fails.
- [ ] Viscidus: freezes after about 20 frost hits and shatters after about 15 melee hits (each hit counts 10
      times).

**Naxxramas (classic)**
- [ ] Thaddius: alone, Stalagg and Feugen don't revive each other, and their Tesla Coils don't overload when
      they follow you off their platforms.
- [ ] Gothik: alone, the gate opens at about 2 minutes and his adds from both sides come at you; in phase two
      he keeps attacking you after each teleport to the other side (no reset), and comes through the gate.
- [ ] Sapphiron: alone, his Ice Bolt in the air phase freezes you and his Frost Breath doesn't kill you. A pet
      dies to the breath unless it stands behind your ice block.

**With two players**
- [ ] For one boss above, the normal mechanic happens again with a second player in the raid.

## 7. Classic Naxxramas (40-player, level 60)

- [ ] The floating Necropolis is visible above Plaguewood in the Eastern Plaguelands.
- [ ] The **Teleport To Naxxramas** runestone is below it (`.go xyz 3123.26 -3869.36 138.34 0`), with a
      Meeting Stone nearby.
- [ ] Without the attunement, the runestone refuses: "You are not attuned to Naxxramas." **This wording should still say
      attuned** (it was kept on purpose).
- [ ] Get **The Dread Citadel - Naxxramas** from Archmage Angela Dosantos at Light's Hope Chapel, finish it, and
      the runestone takes you in. Your group comes along.
- [ ] Inside: classic creatures and models, level 60 trash and bosses, 40-player difficulty. The level 80
      10/25-player versions can't be entered.
- [ ] The Stratholme back entrance doesn't lead in.
- [ ] Bosses use their classic scripts. Kill at least one boss per wing.
- [ ] Loot is classic: Tier 3 tokens and classic items, and the Four Horsemen chest appears.
- [ ] The Light's Hope Tier 3 quests, Master Craftsman Omarion, Archmage Tarsis Kir-Moldir and Frozen Runes
      are there and work.
- [ ] Solo scaling is about 2.8 players' worth.
- [ ] The optional `Unbound.Naxx40.Doable.*` settings (Four Horsemen, Gluth, Patchwerk, Razuvious) make those
      fights easier when turned on.
- [ ] In the Raid Finder, Naxxramas shows **"Attunement"** as the reason when you don't have it (kept on
      purpose).

## 8. Perk ranks

- [ ] The perk window shows **"x/5"** badges, and the tooltips list every rank (Ranks 4-5 say "endgame, coming
      later").
- [ ] At level 1, 30 and 60 the perk is at Rank 1, 2 and 3. A level 60 character has the same values as
      before ranks existed.
- [ ] As a GM, `.perk rank` can set Rank 4 or 5 and the stronger value applies (for example Reinforced Armor
      13% / 15%).

## 9. AoE loot only from loot companions

- [ ] `.aoeloot on`, `.aoeloot off` and the short form `.aoe on` answer "AoE looting comes from loot
      companions…" and change nothing (on a normal player and on a GM).
- [ ] Without a companion out, opening a corpse loots only that corpse.
- [ ] With the Loot Goblin or Arcane Loot Scanner out, corpses within 55 yards are auto-looted and opening one
      corpse loots the ones around it. Dismissing the companion turns it off again.

## 10. Report back

Note anything that failed or felt wrong (too hard, too easy, wrong text) and paste it into the chat with
Claude, with the section number.
