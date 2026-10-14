-- Unbound: client tweaks for the Unbound server.

-- The stock client only lists Dungeon/Raid Difficulty in your portrait menu from level 65 (when the
-- difficulty is still Normal). Classic heroics open at level 60, so show them from there.
local MIN_DIFFICULTY_LEVEL = 60

hooksecurefunc("UnitPopup_HideButtons", function()
    local dropdownMenu = UIDROPDOWNMENU_INIT_MENU
    if not dropdownMenu or dropdownMenu.which ~= "SELF" or UIDROPDOWNMENU_MENU_LEVEL ~= 1 then
        return
    end
    if UnitLevel("player") < MIN_DIFFICULTY_LEVEL then
        return
    end

    local shown = UnitPopupShown[UIDROPDOWNMENU_MENU_LEVEL]
    for index, value in ipairs(UnitPopupMenus["SELF"]) do
        if value == "DUNGEON_DIFFICULTY" or value == "RAID_DIFFICULTY" then
            shown[index] = 1
        end
    end
end)

-- /heroic and /normal set the dungeon difficulty directly (same as the portrait menu).
SLASH_UNBOUNDHEROIC1 = "/heroic"
SlashCmdList["UNBOUNDHEROIC"] = function()
    SetDungeonDifficulty(2)
end

SLASH_UNBOUNDNORMAL1 = "/normal"
SlashCmdList["UNBOUNDNORMAL"] = function()
    SetDungeonDifficulty(1)
end
