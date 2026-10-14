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

-- While the UI loads (login, /reload), the chat code can ask which side of the screen a chat window is on
-- before that window has a position, which errors in FloatingChatFrame.lua ("attempt to perform
-- arithmetic on a nil value" in FCF_UpdateButtonSide; seen with ElvUI's chat). Skip it for a window
-- without a position; the game runs it again once the window is placed.
if FCF_UpdateButtonSide then
    local updateButtonSide = FCF_UpdateButtonSide
    FCF_UpdateButtonSide = function(chatFrame, ...)
        if not chatFrame or not chatFrame:GetLeft() or not chatFrame:GetRight() then
            return
        end
        return updateButtonSide(chatFrame, ...)
    end
end
