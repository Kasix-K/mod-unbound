-- Unbound Perks: perk definitions.
-- Permanent and Offensive perks are the real designs. Defensive, Utility and the class perk are still
-- placeholders. Perks don't do anything yet: the server side comes later and uses the same ids.
--
-- Fields:
--   id         unique number, never reuse one (saved loadouts store ids)
--   name, category, icon
--   desc       the EFFECT text (colour codes: G() good/green, B() bad/red)
--   live       optional function returning an extra line computed from your current stats
--   pets       true = shows "This perk also works for your pets."
--   note       optional grey line under the effect
--   permanent  always on, can't be toggled
--   works      the server implements it (src/unbound_perks.cpp); others are listed but do nothing yet
--   class      only shown to that class, e.g. "PALADIN"

UnboundPerks = UnboundPerks or {}

UnboundPerks.CATEGORIES = {
    { key = "PERMANENT", name = "Permanent", color = { 1.00, 0.82, 0.30 } },
    { key = "OFFENSIVE", name = "Offensive", color = { 0.92, 0.38, 0.32 } },
    { key = "DEFENSIVE", name = "Defensive", color = { 0.38, 0.62, 0.98 } },
    { key = "UTILITY",   name = "Utility",   color = { 0.72, 0.52, 0.98 } },
    { key = "CLASS",     name = nil,         color = nil },  -- name and colour come from the player's class
}

local function G(s) return "|cff33ff33" .. s .. "|r" end  -- good (green)
local function B(s) return "|cffff4040" .. s .. "|r" end  -- bad (red)

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

-- "every <step>% above <floor>% grants +1%, up to +200%"
local function overCap(value, floor, step)
    return math.min(200, math.floor(math.max(0, value - floor) / step))
end

local function capLine(label, value)
    return string.format("You have %d%% %s -> %s damage.", math.floor(value), label, G("+" .. overCap(value, 60, 200) .. "%"))
end

local PETS_TOO = true
local ALWAYS = "Always active - cannot be turned off."

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
      desc = "After leaving combat for " .. G("3 seconds") .. ", you rapidly regenerate " ..
             G("15% of your maximum health and mana every second") .. " until full.",
      note = ALWAYS },

    -- Offensive -------------------------------------------------------------------------------------
    { id = 101, name = "Cyclic Power", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_TimeStop",
      desc = "Your damage output continuously cycles between " .. B("-50%") .. " and " .. G("+100%") .. " over 25 seconds." },
    { id = 102, name = "Critical Understanding", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_CriticalStrike",
      desc = "Every 300% critical strike chance above 100% grants " .. G("+1%") ..
             " critical strike damage, up to " .. G("+200%") .. ".",
      live = function()
          local crit = critChance()
          return string.format("You have %d%% crit -> %s critical strike damage.", math.floor(crit), G("+" .. overCap(crit, 100, 300) .. "%"))
      end },
    { id = 103, name = "Defensive Sacrifice", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_BattleShout",
      desc = "Take " .. B("30% more damage") .. " in exchange for:",
      live = function()
          return string.format(" %s attack power  |cffaaaaaa(10%% of current)|r\n %s spell power  |cffaaaaaa(10%% of current)|r",
              G("+" .. math.floor(attackPower() * 0.1)), G("+" .. math.floor(spellPower() * 0.1)))
      end,
      liveInline = true },
    { id = 104, name = "Desperate Power", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_UnholyFrenzy",
      desc = "Sacrifice " .. B("75%") .. " of your magic resistances for " .. G("+50%") .. " damage dealt." },
    { id = 105, name = "Block Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\INV_Shield_05",
      desc = "Your Block caps at 60%; every 200% of Block above the cap grants " .. G("+1%") ..
             " damage dealt, up to " .. G("+200%") .. ".",
      live = function() return capLine("Block", GetBlockChance() or 0) end },
    { id = 106, name = "Dodge Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Rogue_Feint",
      desc = "Your Dodge caps at 60%; every 200% of Dodge above the cap grants " .. G("+1%") ..
             " damage dealt, up to " .. G("+200%") .. ".",
      live = function() return capLine("Dodge", GetDodgeChance() or 0) end },
    { id = 107, name = "Parry Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Parry",
      desc = "Your Parry caps at 60%; every 200% of Parry above the cap grants " .. G("+1%") ..
             " damage dealt, up to " .. G("+200%") .. ".",
      live = function() return capLine("Parry", GetParryChance() or 0) end },
    { id = 108, name = "Haste Capping", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_Bloodlust",
      desc = "Every 200% Haste above 60% grants " .. G("+1%") .. " damage dealt, up to " .. G("+200%") ..
             ". Your Haste is not capped; instead you take " .. B("10% more damage") .. ".",
      live = function() return capLine("Haste", hastePercent()) end },
    { id = 109, name = "Pet Encouragement", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Hunter_BeastWithin",
      desc = "Your controlled units deal " .. G("40%") .. " increased damage." },
    { id = 110, name = "Rolling Momentum", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Charge",
      desc = "For every second you spend in combat you deal " .. G("+2%") .. " damage, stacking up to " .. G("+50%") ..
             ". While out of combat the bonus bleeds away at " .. B("-2%") .. " per second." },
    { id = 111, name = "Tunnel Vision", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Hunter_SniperShot",
      desc = "Your single-target damage is increased by " .. G("40%") ..
             ", but your area-of-effect damage is reduced by " .. B("30%") .. "." },
    { id = 112, name = "Collateral Damage", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Fire_SelfDestruct",
      desc = "Your area-of-effect damage is increased by " .. G("40%") ..
             ", but your single-target damage is reduced by " .. B("30%") .. "." },
    { id = 113, name = "Giant Slayer", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Decisivestrike",
      desc = "Deal " .. G("25%") .. " increased damage to " .. B("bosses") .. "." },
    { id = 114, name = "Merciless", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_CurseOfSargeras",
      desc = "Your damage-over-time effects deal " .. G("50%") .. " more damage." },
    { id = 115, name = "Pressure", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_Warrior_Sunder",
      desc = "Each hit on the same target grants " .. G("+8%") .. " damage, stacking up to " .. G("10") ..
             " times (" .. G("+80%") .. "). Resets when you switch targets." },
    { id = 116, name = "Chaos", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_ChillTouch",
      desc = "Every damaging ability has a " .. G("10%") .. " chance to deal " .. G("double") .. " damage." },
    { id = 117, name = "Power Conversion", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Arcane_ArcanePotency",
      desc = "Every 30000 of your highest primary stat grants " .. G("+0.5%") .. " damage, up to " .. G("+200%") .. ".",
      live = function()
          local stat = highestPrimaryStat()
          local bonus = math.min(200, math.floor(stat / 30000) * 0.5)
          return string.format("Highest stat %d  ->  %s damage.", math.floor(stat), G(string.format("+%.1f%%", bonus)))
      end },
    { id = 118, name = "Healing Powah", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Holy_FlashHeal",
      desc = "Increases your healing done by " .. G("25%") .. "." },
    { id = 119, name = "Shadow Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Shadow_ShadowBolt",
      desc = "Increases all |cff8c8cffShadow|r damage you deal by " .. G("30%") .. "." },
    { id = 120, name = "Holy Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Holy_HolyBolt",
      desc = "Increases all |cffffe680Holy|r damage you deal by " .. G("30%") .. "." },
    { id = 121, name = "Arcane Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_StarFall",
      desc = "Increases all |cffff80ffArcane|r damage you deal by " .. G("30%") .. "." },
    { id = 122, name = "Nature Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Nature_Lightning",
      desc = "Increases all |cff4dff4dNature|r damage you deal by " .. G("30%") .. "." },
    { id = 123, name = "Fire Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Fire_FlameBolt",
      desc = "Increases all |cffff8040Fire|r damage you deal by " .. G("30%") .. "." },
    { id = 124, name = "Frost Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Spell_Frost_FrostBolt02",
      desc = "Increases all |cff80ffffFrost|r damage you deal by " .. G("30%") .. "." },
    { id = 125, name = "Physical Mastery", category = "OFFENSIVE", pets = PETS_TOO, works = true,
      icon = "Interface\\Icons\\Ability_MeleeDamage",
      desc = "Increases all Physical damage you deal by " .. G("30%") .. ".\nYour pet gains this too." },

    -- Defensive (placeholders) -----------------------------------------------------------------------
    { id = 201, name = "Thick Skin", category = "DEFENSIVE", icon = "Interface\\Icons\\INV_Misc_LeatherScrap_08",
      desc = "Placeholder: +5% armor." },
    { id = 202, name = "Second Wind", category = "DEFENSIVE", icon = "Interface\\Icons\\Ability_Warrior_DefensiveStance",
      desc = "Placeholder: heal 10% of your health when you drop below 20% (once per minute)." },
    { id = 203, name = "Steadfast", category = "DEFENSIVE", icon = "Interface\\Icons\\Ability_Defend",
      desc = "Placeholder: +1% dodge chance." },

    -- Utility (placeholders) -------------------------------------------------------------------------
    { id = 301, name = "Fleet Foot", category = "UTILITY", icon = "Interface\\Icons\\Ability_Rogue_Sprint",
      desc = "Placeholder: +5% run speed out of combat." },
    { id = 302, name = "Treasure Sense", category = "UTILITY", icon = "Interface\\Icons\\INV_Misc_Coin_02",
      desc = "Placeholder: creatures drop 10% more gold." },

    -- Class (placeholder until the real Paladin perks are added) --------------------------------------
    { id = 1001, name = "Paladin Perk (coming soon)", category = "CLASS", class = "PALADIN",
      icon = "Interface\\Icons\\Spell_Holy_HolyBolt",
      desc = "Placeholder: the real Paladin perks will be listed here." },
}
