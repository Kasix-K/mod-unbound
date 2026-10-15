-- Unbound Perks: perk definitions.
-- The numbers here must match src/unbound_perks.cpp (the server applies the effects; this file only
-- describes them). Numbers stay in normal WoW ranges: one perk is worth about +10%.
--
-- Fields:
--   id         unique number, never reuse one (saved loadouts store ids)
--   name, category, icon
--   desc       the EFFECT text (colour codes: G() good/green, B() bad/red)
--   live       optional function returning an extra line computed from your current stats
--   pets       true = shows "This perk also works for your pets."
--   note       optional grey line under the effect
--   permanent  always on, can't be toggled
--   works      the server implements it (src/unbound_perks.cpp); every perk listed here should have it
--   class      only shown to that class, e.g. "PALADIN"
--   excludes   id (or list of ids) of perks that can't be active together with this one (turning this on
--              turns them off)
--   applyRank  ranked perks: rewrites desc/note from the rank numbers the server sends

UnboundPerks = UnboundPerks or {}

UnboundPerks.CATEGORIES = {
    { key = "PERMANENT", name = "Permanent", color = { 1.00, 0.82, 0.30 } },
    { key = "OFFENSIVE", name = "Offensive", color = { 0.92, 0.38, 0.32 }, limit = 5 },  -- same limit as the server
    { key = "DEFENSIVE", name = "Defensive", color = { 0.38, 0.62, 0.98 }, limit = 3 },  -- same limit as the server
    { key = "UTILITY",   name = "Utility",   color = { 0.72, 0.52, 0.98 }, limit = 3 },  -- same limit as the server
    { key = "CLASS",     name = nil,         color = nil },  -- name and colour come from the player's class
}

local function G(s) return "|cff33ff33" .. s .. "|r" end  -- good (green)
local function B(s) return "|cffff4040" .. s .. "|r" end  -- bad (red)
local function H(s) return "|cffffd200" .. s .. "|r" end  -- section heading (gold)
local function S(s) return "|cff4dc3ff" .. s .. "|r" end  -- spell name (blue)

-- ------------------------------------------------------------------ current stats (for the live lines)
local function maxSpellCrit()
    local best = 0
    for school = 2, 7 do best = math.max(best, GetSpellCritChance(school) or 0) end
    return best
end

local function critChance()
    return math.max(GetCritChance() or 0, GetRangedCritChance() or 0, maxSpellCrit())
end

local function hastePercent()
    -- CR_HASTE_MELEE = 18, CR_HASTE_RANGED = 19, CR_HASTE_SPELL = 20
    return math.max(GetCombatRatingBonus(18) or 0, GetCombatRatingBonus(19) or 0, GetCombatRatingBonus(20) or 0)
end

local function attackPower()
    local base, pos, neg = UnitAttackPower("player")
    return (base or 0) + (pos or 0) + (neg or 0)
end

local function spellPower()
    local best = GetSpellBonusHealing() or 0
    for school = 2, 7 do best = math.max(best, GetSpellBonusDamage(school) or 0) end
    return best
end

local function highestPrimaryStat()
    local best = 0
    for stat = 1, 5 do  -- Strength, Agility, Stamina, Intellect, Spirit
        local _, effective = UnitStat("player", stat)
        best = math.max(best, effective or 0)
    end
    return best
end

-- "every 1% above <floor>% grants +1%, up to +<max>%"
local function overCap(value, floor, max)
    return math.min(max, math.floor(math.max(0, value - floor)))
end

local function capLine(label, value, floor)
    return string.format("You have %d%% %s -> %s damage.", math.floor(value), label, G("+" .. overCap(value, floor, 10) .. "%"))
end

local PETS_TOO = true
local ALWAYS = "Always active - cannot be turned off."

local function pct(n) return string.format("%g%%", n) end

-- Ranked perks: the server sends each rank's numbers (the stats of RANKED_PERKS in src/unbound_perks.cpp, in
-- that order, then the level). describe(v) gives the EFFECT text for one rank, summary(v) a short rank line.
local function ranked(describe, summary, extra)
    return function(perk, rank, maxRank, values)
        local cur = values[rank] or values[#values]
        if not cur then return end
        perk.desc = describe(cur)
        local lines = { "Rank " .. rank .. " / " .. maxRank }
        for i, v in ipairs(values) do
            local line = string.format("Rank %d: %s  (level %d)", i, summary(v), v[#v])
            table.insert(lines, i == rank and G(line) or line)
        end
        if extra then table.insert(lines, extra) end
        perk.note = table.concat(lines, "\n")
    end
end

local function longerLegs(v)
    return "Increases your and your pet's running speed by " .. G(pct(v[1])) .. ". Your mount speed is increased by " ..
           G(pct(v[2])) .. ", your swimming speed by " .. G(pct(v[3])) .. ", and your fall damage is reduced by " .. G(pct(v[4])) .. "."
end
local function plantedFeet(v)
    return "Standing still for " .. string.format("%g", v[3]) .. " seconds restores " .. G(pct(v[1])) ..
           " of your maximum health and " .. G(pct(v[2])) .. " of your maximum mana every second."
end
local function pursuit(v)
    return "You and your pet gain " .. G(pct(v[1])) .. " movement speed for " .. string.format("%g", v[2]) ..
           " seconds after you or your pet kill an enemy."
end
local function vampirism(v) return "Heal for " .. G(pct(v[1])) .. " of all damage you deal." end
local function soulDrain(v)
    return "Heal for " .. G(pct(v[1])) .. " of all damage you deal,\nbut direct healing received is reduced by " ..
           B(pct(v[2])) .. ".\n -  Your |cff4dc3ffpet|r leeches the same way from its own damage, healing |cff4dc3ffitself|r"
end
local function petHealing(v) return "Increases your pet's healing taken by " .. G(pct(v[1])) .. "." end
local function petThreat(v) return "Increases your pet's threat generation by " .. G(pct(v[1])) .. "." end
local function silentKiller(v) return "Reduces threat you generate by " .. G(pct(v[1])) .. ". Your pet's threat is unchanged." end
local function presence(v) return "Increases threat you generate by " .. G(pct(v[1])) .. "." end
local function steadyHands(v)
    return "Spell pushback reduced by " .. G(pct(v[1])) .. ".\nInterrupt lockouts and " .. G("silences") ..
           " on you last " .. G(pct(v[2])) .. " shorter."
end
local function manaLeech(v)
    return "Restore Mana equal to " .. G(pct(v[1])) .. " of all damage you deal."
end
-- Defensive
local function chance(kind)
    if kind == "Block" then return GetBlockChance() or 0 end
    if kind == "Dodge" then return GetDodgeChance() or 0 end
    return GetParryChance() or 0
end
-- Greater Bulwark / Evasive Maneuvers / Parry King: into = the chance that gets the other two.
local function conversion(into, a, b, extra)
    local efficiency = 120  -- the current rank's, once the server sends it
    local function describe(v)
        return "Converts all your " .. a .. " and " .. b .. " into " .. into .. " chance at " .. G(pct(v[1])) ..
               " efficiency (melee attacks)." .. (extra and ("\n" .. extra) or "")
    end
    local function live()
        local ca, cb = chance(a), chance(b)
        local total = (ca + cb) * efficiency / 100 + chance(into)
        return string.format("%s %.0f%% + %s %.0f%%  ->  %s %s.", a, ca, b, cb, G(string.format("%.0f%%", total)), into)
    end
    return describe, live, function(p, rank, maxRank, values)
        local cur = values[rank] or values[#values]
        if cur then efficiency = cur[1] end
        ranked(describe, function(v) return string.format("%g%% efficiency", v[1]) end,
            "Only one of Greater Bulwark, Evasive Maneuvers and Parry King can be active.")(p, rank, maxRank, values)
    end
end
local bulwarkDesc, bulwarkLive, bulwarkRank = conversion("Block", "Dodge", "Parry",
    B("Needs a shield") .. " (a block without one stops no damage).")
local evasiveDesc, evasiveLive, evasiveRank = conversion("Dodge", "Block", "Parry")
local parryDesc, parryLive, parryRank = conversion("Parry", "Block", "Dodge")

local function reinforced(v) return "Reduces |cffffffffphysical|r damage taken by " .. G(pct(v[1])) .. "." end
local function spellwarded(v) return "Reduces all |cff4dc3ffmagic|r damage taken by " .. G(pct(v[1])) .. "." end
local function stoicism(v)
    return "Damage-over-time effects deal " .. G(pct(v[1])) .. " less damage to you and your pet."
end
local function momentum(v)
    return "You and your pet each gain " .. G(pct(v[1] / 10)) .. " damage reduction for every second spent moving, up to " ..
           G(pct(v[1])) .. ". Standing still removes the bonus after " .. string.format("%g", v[2]) .. " seconds."
end
local function fortress(v)
    return "You and your pet each gain " .. G(pct(v[1] / 10)) .. " damage reduction for every second spent standing still, up to " ..
           G(pct(v[1])) .. " (10 stacks). Moving for over " .. string.format("%g", v[2]) .. " seconds removes the stacks."
end

local function sec(n) return string.format("%g second%s", n, n == 1 and "" or "s") end
local function juggernaut(v)
    return "You and your pet cannot lose more than " .. G(pct(v[1])) .. " of maximum health from a single hit. " ..
           "This can occur once every " .. sec(v[2]) .. " for each of you."
end
local function counterweight(v)
    return "Successfully dodging, parrying, or blocking reduces your next incoming hit by " .. G(pct(v[1])) .. "."
end
local function titansResolve(v)
    return "You and your pet gain " .. G(pct(v[1] / 100)) .. " damage reduction for every " .. G("1%") ..
           " of your own health missing (up to " .. G(pct(v[1])) .. ")."
end
local function secondWind(v)
    return "After you or your pet suffer a hit exceeding " .. G(pct(v[1])) .. " of maximum health, the one struck " ..
           "regenerates " .. G(pct(v[2])) .. " health per second for " .. sec(v[3]) .. "."
end
local function hardenedFlesh(v)
    return "Hits on you and your pet that exceed " .. G(pct(v[1])) .. " of maximum health have their excess damage " ..
           "reduced by " .. G(pct(v[2])) .. "."
end
local function petsBlessing(v) return "Your pet takes " .. G(pct(v[1])) .. " less damage." end
local function shieldWall(v)
    return "Blocking an attack increases your block chance by " .. G(pct(v[1])) .. " for " .. sec(v[3]) ..
           ", stacking up to " .. string.format("%g", v[2]) .. " times."
end
local function survivalInstinct(v)
    return "While below " .. G(pct(v[1])) .. " Health, all damage taken by you and your pet is reduced by " .. G(pct(v[2])) .. "."
end
local function vitalReserve(v) return "Increases your and your pet's maximum Health by " .. G(pct(v[1])) .. "." end
local function enduring(v) return "Increases your and your pet's healing received by " .. G(pct(v[1])) .. "." end
local function thornmail(v)
    return "Melee attackers suffer Physical damage equal to " .. G(pct(v[1])) .. " of the damage they hit you and your pet for."
end
local function heavyFrame(v) return "Increases your and your pet's Armor by " .. G(pct(v[1])) .. "." end
local function one(fmt) return function(v) return string.format(fmt, v[1]) end end

local MANA_ONLY = "Requires a mana bar. It does nothing while you use Rage, Energy, Runic Power or Focus, " ..
                  "including a druid in Cat, Bear or Dire Bear Form."

UnboundPerks.PERKS = {
    -- Permanent -------------------------------------------------------------------------------------
    { id = 1, name = "No Resurrection Sickness", category = "PERMANENT", permanent = true,
      icon = "Interface\\Icons\\Spell_Holy_Resurrection",
      desc = "You are permanently immune to " .. B("Resurrection Sickness") ..
             ". Resurrecting at a Spirit Healer no longer weakens you.",
      note = ALWAYS },
    { id = 2, name = "No Daze", category = "PERMANENT", permanent = true,
      icon = "Interface\\Icons\\Spell_Frost_Stun",
      desc = "Enemies can no longer " .. B("Daze") .. " you or your pet. Being struck from behind while moving never slows you.",
      note = ALWAYS },
    { id = 3, name = "Rapid Recovery", category = "PERMANENT", permanent = true,
      icon = "Interface\\Icons\\Spell_Nature_Rejuvenation",
      desc = "After leaving combat for " .. G("4 seconds") .. ", you rapidly regenerate " ..
             G("8% of your maximum health and mana every second") .. " until full.",
      note = ALWAYS,
      -- Ranked: the server sends the rank and each rank's "delay ms,percent,level" (mod_unbound.conf).
      applyRank = function(perk, rank, maxRank, values)
          local cur = values[rank] or values[#values]
          if not cur then return end
          perk.desc = "After leaving combat for " .. G(string.format("%g seconds", cur[1] / 1000)) .. ", you rapidly regenerate " ..
                      G(cur[2] .. "% of your maximum health and mana every second") .. " until full."
          local lines = { "Rank " .. rank .. " / " .. maxRank }
          for i, v in ipairs(values) do
              local line = string.format("Rank %d: %g sec, %d%%  (level %d)", i, v[1] / 1000, v[2], v[3])
              table.insert(lines, i == rank and G(line) or line)
          end
          table.insert(lines, ALWAYS)
          perk.note = table.concat(lines, "\n")
      end },

    -- Offensive -------------------------------------------------------------------------------------
    { id = 101, name = "Cyclic Power", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_TimeStop",
      desc = "Your damage output continuously cycles between " .. B("-10%") .. " and " .. G("+20%") .. " over 25 seconds." },
    { id = 102, name = "Critical Understanding", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_CriticalStrike",
      desc = "Every 1% critical strike chance above 25% grants " .. G("+1%") ..
             " critical strike damage, up to " .. G("+20%") .. ".",
      live = function()
          local crit = critChance()
          return string.format("You have %d%% crit -> %s critical strike damage.", math.floor(crit), G("+" .. overCap(crit, 25, 20) .. "%"))
      end },
    { id = 103, name = "Defensive Sacrifice", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_BattleShout",
      desc = "Take " .. B("10% more damage") .. " in exchange for:",
      live = function()
          return string.format(" %s attack power  |cffaaaaaa(10%% of current)|r\n %s spell power  |cffaaaaaa(10%% of current)|r",
              G("+" .. math.floor(attackPower() * 0.1)), G("+" .. math.floor(spellPower() * 0.1)))
      end,
      liveInline = true },
    { id = 104, name = "Desperate Power", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_UnholyFrenzy",
      desc = "Sacrifice " .. B("50%") .. " of your magic resistances for " .. G("+10%") .. " damage dealt." },
    { id = 105, name = "Block Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\INV_Shield_05",
      desc = "Your Block caps at " .. B("20%") .. "; every 1% of Block above the cap grants " .. G("+1%") ..
             " damage dealt, up to " .. G("+10%") .. ".",
      live = function() return capLine("Block", GetBlockChance() or 0, 20) end },
    { id = 106, name = "Dodge Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Rogue_Feint",
      desc = "Your Dodge caps at " .. B("20%") .. "; every 1% of Dodge above the cap grants " .. G("+1%") ..
             " damage dealt, up to " .. G("+10%") .. ".",
      live = function() return capLine("Dodge", GetDodgeChance() or 0, 20) end },
    { id = 107, name = "Parry Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Parry",
      desc = "Your Parry caps at " .. B("20%") .. "; every 1% of Parry above the cap grants " .. G("+1%") ..
             " damage dealt, up to " .. G("+10%") .. ".",
      live = function() return capLine("Parry", GetParryChance() or 0, 20) end },
    { id = 108, name = "Haste Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_Bloodlust",
      desc = "Every 1% Haste above 5% grants " .. G("+1%") .. " damage dealt, up to " .. G("+10%") ..
             ". Your Haste is not capped; instead you take " .. B("5% more damage") .. ".",
      live = function() return capLine("Haste", hastePercent(), 5) end },
    { id = 109, name = "Pet Encouragement", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Hunter_BeastWithin",
      desc = "Your controlled units deal " .. G("15%") .. " increased damage." },
    { id = 110, name = "Rolling Momentum", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Charge",
      desc = "For every second you spend in combat you deal " .. G("+1%") .. " damage, stacking up to " .. G("+10%") ..
             ". While out of combat the bonus bleeds away at " .. B("-1%") .. " per second." },
    { id = 111, name = "Tunnel Vision", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Hunter_SniperShot",
      desc = "Your single-target damage is increased by " .. G("10%") ..
             ", but your area-of-effect damage is reduced by " .. B("10%") .. "." },
    { id = 112, name = "Collateral Damage", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Fire_SelfDestruct",
      desc = "Your area-of-effect damage is increased by " .. G("10%") ..
             ", but your single-target damage is reduced by " .. B("10%") .. "." },
    { id = 113, name = "Giant Slayer", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Decisivestrike",
      desc = "Deal " .. G("10%") .. " increased damage to " .. B("bosses") .. "." },
    { id = 114, name = "Merciless", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_CurseOfSargeras",
      desc = "Your damage-over-time effects deal " .. G("15%") .. " more damage." },
    { id = 115, name = "Pressure", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Sunder",
      desc = "Each hit on the same target grants " .. G("+1%") .. " damage, stacking up to " .. G("10") ..
             " times (" .. G("+10%") .. "). Resets when you switch targets." },
    { id = 116, name = "Chaos", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_ChillTouch",
      desc = "Every damaging ability has a " .. G("10%") .. " chance to deal " .. G("50% more") .. " damage." },
    { id = 117, name = "Power Conversion", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Arcane_ArcanePotency",
      desc = "Every 100 of your highest primary stat grants " .. G("+1%") .. " damage, up to " .. G("+10%") .. ".",
      live = function()
          local stat = highestPrimaryStat()
          local bonus = math.min(10, math.floor(stat / 100))
          return string.format("Highest stat %d  ->  %s damage.", math.floor(stat), G(string.format("+%d%%", bonus)))
      end },
    { id = 118, name = "Healing Powah", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Holy_FlashHeal",
      desc = "Increases your healing done by " .. G("10%") .. "." },
    { id = 119, name = "Shadow Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_ShadowBolt",
      desc = "Increases all |cff8c8cffShadow|r damage you deal by " .. G("10%") .. "." },
    { id = 120, name = "Holy Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Holy_HolyBolt",
      desc = "Increases all |cffffe680Holy|r damage you deal by " .. G("10%") .. "." },
    { id = 121, name = "Arcane Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_StarFall",
      desc = "Increases all |cffff80ffArcane|r damage you deal by " .. G("10%") .. "." },
    { id = 122, name = "Nature Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_Lightning",
      desc = "Increases all |cff4dff4dNature|r damage you deal by " .. G("10%") .. "." },
    { id = 123, name = "Fire Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Fire_FlameBolt",
      desc = "Increases all |cffff8040Fire|r damage you deal by " .. G("10%") .. "." },
    { id = 124, name = "Frost Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Frost_FrostBolt02",
      desc = "Increases all |cff80ffffFrost|r damage you deal by " .. G("10%") .. "." },
    { id = 125, name = "Physical Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_MeleeDamage",
      desc = "Increases all Physical damage you deal by " .. G("10%") .. ".\nYour pet gains this too." },

    -- Defensive (ids 201-299, at most 3 active; 201-203 were placeholders, removed: never reuse them) --------
    { id = 204, name = "Greater Bulwark", category = "DEFENSIVE", works = true, excludes = { 205, 206 },
      icon = "Interface\\Icons\\Ability_Warrior_ShieldWall",
      desc = bulwarkDesc({ 120 }), live = bulwarkLive, applyRank = bulwarkRank },
    { id = 205, name = "Evasive Maneuvers", category = "DEFENSIVE", works = true, excludes = { 204, 206 },
      icon = "Interface\\Icons\\Spell_Shadow_ShadowWard",
      desc = evasiveDesc({ 120 }), live = evasiveLive, applyRank = evasiveRank },
    { id = 206, name = "Parry King", category = "DEFENSIVE", works = true, excludes = { 204, 205 },
      icon = "Interface\\Icons\\Ability_Warrior_Riposte",
      desc = parryDesc({ 120 }), live = parryLive, applyRank = parryRank },
    { id = 207, name = "Reinforced Armor", category = "DEFENSIVE", works = true,
      icon = "Interface\\Icons\\INV_Chest_Plate16",
      desc = reinforced({ 10 }),
      applyRank = ranked(reinforced, function(v) return string.format("-%g%% physical damage", v[1]) end) },
    { id = 208, name = "Spellwarded", category = "DEFENSIVE", works = true,
      icon = "Interface\\Icons\\Spell_Holy_SpellWarding",
      desc = spellwarded({ 10 }),
      applyRank = ranked(spellwarded, function(v) return string.format("-%g%% magic damage", v[1]) end) },
    { id = 209, name = "Stoicism", category = "DEFENSIVE", works = true,
      icon = "Interface\\Icons\\Spell_Holy_DevotionAura",
      desc = stoicism({ 20 }),
      applyRank = ranked(stoicism, function(v) return string.format("-%g%% damage-over-time damage", v[1]) end) },
    { id = 210, name = "Defensive Momentum", category = "DEFENSIVE", works = true, excludes = 211,
      icon = "Interface\\Icons\\Ability_Rogue_FleetFooted",
      desc = momentum({ 10, 2 }),
      note = "Can't be active together with Fortress.",
      applyRank = ranked(momentum, function(v) return string.format("up to %g%% damage reduction", v[1]) end,
          "Can't be active together with Fortress.") },
    { id = 211, name = "Fortress", category = "DEFENSIVE", works = true, excludes = 210,
      icon = "Interface\\Icons\\Ability_Warrior_DefensiveStance",
      desc = fortress({ 10, 3 }),
      note = "Can't be active together with Defensive Momentum.",
      applyRank = ranked(fortress, function(v) return string.format("up to %g%% damage reduction", v[1]) end,
          "Can't be active together with Defensive Momentum.") },
    { id = 212, name = "Juggernaut", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Ability_Warrior_EndlessRage",
      desc = juggernaut({ 30, 3 }), applyRank = ranked(juggernaut, one("hits capped at %g%% of health")) },
    { id = 213, name = "Counterweight", category = "DEFENSIVE", works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Revenge",
      desc = counterweight({ 20 }), applyRank = ranked(counterweight, one("next hit -%g%%")) },
    { id = 214, name = "Titan's Resolve", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Spell_Holy_AshesToAshes",
      desc = titansResolve({ 10 }), applyRank = ranked(titansResolve, one("up to %g%% damage reduction")) },
    { id = 215, name = "Second Wind", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\INV_Misc_Bandage_15",
      desc = secondWind({ 15, 2, 5 }),
      applyRank = ranked(secondWind, function(v) return string.format("%g%% health per second", v[2]) end) },
    { id = 216, name = "Hardened Flesh", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Spell_Nature_StoneClawTotem",
      desc = hardenedFlesh({ 10, 20 }),
      applyRank = ranked(hardenedFlesh, function(v) return string.format("excess -%g%%", v[2]) end) },
    { id = 217, name = "Pet's Blessing", category = "DEFENSIVE", works = true,
      icon = "Interface\\Icons\\Ability_Hunter_Pet_Turtle",
      desc = petsBlessing({ 20 }), applyRank = ranked(petsBlessing, one("pet damage taken -%g%%")) },
    { id = 218, name = "Shield Wall Training", category = "DEFENSIVE", works = true,
      icon = "Interface\\Icons\\Ability_Warrior_ShieldMastery",
      desc = shieldWall({ 1, 5, 5 }), note = "Needs a shield (block chance).",
      applyRank = ranked(shieldWall, one("+%g%% block per stack"), "Needs a shield (block chance).") },
    { id = 219, name = "Survival Instinct", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Ability_Druid_TigersRoar",
      desc = survivalInstinct({ 30, 15 }),
      applyRank = ranked(survivalInstinct, function(v) return string.format("-%g%% below %g%% health", v[2], v[1]) end) },
    { id = 220, name = "Vital Reserve", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Spell_Holy_WordFortitude",
      desc = vitalReserve({ 10 }), applyRank = ranked(vitalReserve, one("+%g%% maximum health")) },
    { id = 221, name = "Enduring", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Spell_Holy_Renew",
      desc = enduring({ 10 }), applyRank = ranked(enduring, one("+%g%% healing received")) },
    { id = 222, name = "Thornmail", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\Spell_Nature_Thorns",
      desc = thornmail({ 30 }), applyRank = ranked(thornmail, one("%g%% reflected")) },
    { id = 223, name = "Heavy Frame", category = "DEFENSIVE", works = true, pets = PETS_TOO,
      icon = "Interface\\Icons\\INV_Chest_Plate04",
      desc = heavyFrame({ 15 }), applyRank = ranked(heavyFrame, one("+%g%% armor")) },

    -- Utility (ids 301 and 302 were placeholders, removed: never reuse them) ------------------------------
    { id = 303, name = "Iron Will", category = "UTILITY", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Magic_MageArmor",
      desc = "Crowd-control effects on you (and your pets) have their duration reduced by " .. G("30%") .. ".",
      note = "Stuns, fears, roots, silences, sleeps, polymorphs, charms, disorients and saps.",
      -- Ranked: the server sends the rank and each rank's "percent,level" (mod_unbound.conf).
      applyRank = function(perk, rank, maxRank, values)
          local cur = values[rank] or values[#values]
          if not cur then return end
          perk.desc = "Crowd-control effects on you (and your pets) have their duration reduced by " ..
                      G(cur[1] .. "%") .. "."
          local lines = { "Rank " .. rank .. " / " .. maxRank }
          for i, v in ipairs(values) do
              local line = string.format("Rank %d: -%d%% duration  (level %d)", i, v[1], v[2])
              table.insert(lines, i == rank and G(line) or line)
          end
          table.insert(lines, "Stuns, fears, roots, silences, sleeps, polymorphs, charms, disorients and saps.")
          perk.note = table.concat(lines, "\n")
      end },
    { id = 304, name = "Longer Legs", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Spell_Nature_Swiftness",
      desc = longerLegs({ 10, 10, 50, 50 }),
      applyRank = ranked(longerLegs, function(v)
          return string.format("run +%g%%, mount +%g%%, swim +%g%%, fall -%g%%", v[1], v[2], v[3], v[4])
      end) },
    { id = 305, name = "Planting your legs", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Spell_Nature_StoneSkinTotem",
      desc = plantedFeet({ 1, 0.5, 3 }),
      note = "Works in and out of combat.",
      applyRank = ranked(plantedFeet, function(v)
          return string.format("%g%% health, %g%% mana per second", v[1], v[2])
      end, "Works in and out of combat.") },
    { id = 306, name = "Relentless Pursuit", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Ability_Rogue_Sprint",
      desc = pursuit({ 35, 10 }),
      applyRank = ranked(pursuit, function(v) return string.format("+%g%% for %g sec", v[1], v[2]) end) },
    { id = 307, name = "Vampirism", category = "UTILITY", works = true, excludes = 308,
      icon = "Interface\\Icons\\Spell_Shadow_LifeDrain02",
      desc = vampirism({ 5 }),
      note = "Can't be active together with Soul Drain.",
      applyRank = ranked(vampirism, function(v) return string.format("%g%% of damage", v[1]) end,
          "Can't be active together with Soul Drain.") },
    { id = 308, name = "Soul Drain", category = "UTILITY", works = true, excludes = 307,
      icon = "Interface\\Icons\\Spell_Shadow_LifeDrain",
      desc = soulDrain({ 10, 20 }),
      note = "Can't be active together with Vampirism.",
      applyRank = ranked(soulDrain, function(v)
          return string.format("%g%% of damage, healing received -%g%%", v[1], v[2])
      end, "Can't be active together with Vampirism.") },
    { id = 309, name = "Pets replenishment", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Ability_Hunter_MendPet",
      desc = petHealing({ 50 }),
      applyRank = ranked(petHealing, function(v) return string.format("+%g%% healing taken", v[1]) end) },
    { id = 310, name = "Pets Roar", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Ability_Physical_Taunt",
      desc = petThreat({ 300 }),
      applyRank = ranked(petThreat, function(v) return string.format("+%g%% pet threat", v[1]) end) },
    { id = 311, name = "Silent Killer", category = "UTILITY", works = true, excludes = 312,
      icon = "Interface\\Icons\\Ability_Stealth",
      desc = silentKiller({ 50 }),
      note = "Can't be active together with Unbreakable Presence.",
      applyRank = ranked(silentKiller, function(v) return string.format("-%g%% threat", v[1]) end,
          "Can't be active together with Unbreakable Presence.") },
    { id = 312, name = "Unbreakable Presence", category = "UTILITY", works = true, excludes = 311,
      icon = "Interface\\Icons\\Ability_Warrior_DefensiveStance",
      desc = presence({ 150 }),
      note = "Can't be active together with Silent Killer.",
      applyRank = ranked(presence, function(v) return string.format("+%g%% threat", v[1]) end,
          "Can't be active together with Silent Killer.") },
    { id = 313, name = "Spell-Protected Steady Hands", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Spell_Holy_MindSooth",
      desc = steadyHands({ 70, 30 }),
      applyRank = ranked(steadyHands, function(v)
          return string.format("pushback -%g%%, lockouts -%g%%", v[1], v[2])
      end) },
    { id = 314, name = "Mana Leech", category = "UTILITY", works = true,
      icon = "Interface\\Icons\\Spell_Shadow_SiphonMana",
      desc = manaLeech({ 2 }),
      note = MANA_ONLY,
      applyRank = ranked(manaLeech, function(v) return string.format("%g%% of damage as mana", v[1]) end, MANA_ONLY) },

    -- Class: Paladin ----------------------------------------------------------------------------------
    { id = 1001, name = "Retribution", category = "CLASS", class = "PALADIN", works = true,
      icon = "Interface\\Icons\\Spell_Holy_AuraOfLight",
      desc = "|cffff9933Retribution|r paladin mastery. While active:\n\n" ..
             H("Improved Divine Storm") .. "\n" ..
             " -  " .. S("Divine Storm") .. " hits up to 6 enemies (normally 4)\n" ..
             " -  Every enemy it hits also takes a " .. S("Crusader Strike") .. "\n\n" ..
             H("All Will Be Judged!") .. "\n" ..
             " -  Your " .. S("Judgement") .. " spreads to up to 4 more enemies within 10 yards of the target\n" ..
             " -  Every enemy it hits is also struck by a free " .. S("Exorcism") .. ", which does not put Exorcism on cooldown\n\n" ..
             H("Exorcist") .. "\n" ..
             " -  " .. S("Exorcism") .. " deals 30% of your attack power + 30% of your spell power\n\n" ..
             H("Righteous Explosion") .. "\n" ..
             B("Requires the ") .. S("Righteous Vengeance") .. B(" talent.") .. "\n" ..
             " -  An enemy dying with your " .. S("Righteous Vengeance") .. " explodes for all it had left, on up to 5 enemies within 8 yards\n\n" ..
             H("By Sword & Light") .. "\n" ..
             " -  All Holy damage you deal is increased by 15%\n" ..
             " -  All Physical damage you deal is increased by 10%\n" ..
             " -  Covers your weapon swings, " .. S("Divine Storm") .. " and " .. S("Crusader Strike") ..
             " as well as " .. S("Judgement") .. " and " .. S("Exorcism") },
}
