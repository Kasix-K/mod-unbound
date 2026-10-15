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
--   works      the server implements it (src/unbound_perks.cpp); others are listed but do nothing yet
--   class      only shown to that class, e.g. "PALADIN"

UnboundPerks = UnboundPerks or {}

UnboundPerks.CATEGORIES = {
    { key = "PERMANENT", name = "Permanent", color = { 1.00, 0.82, 0.30 } },
    { key = "OFFENSIVE", name = "Offensive", color = { 0.92, 0.38, 0.32 }, limit = 5 },  -- same limit as the server
    { key = "DEFENSIVE", name = "Defensive", color = { 0.38, 0.62, 0.98 } },
    { key = "UTILITY",   name = "Utility",   color = { 0.72, 0.52, 0.98 } },
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
