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

-- Dungeon Finder: hide dungeons the server reports as locked for "insufficient expansion". The client lists
-- every dungeon that fits the player's level and the account's expansion (Wrath), so at level 60 it showed
-- Hellfire Ramparts, The Blood Furnace and The Slave Pens under "Burning Crusade Normal". The server's content
-- lock (src/unbound_content_lock.cpp) reports an unreleased expansion's dungeons with this reason, so they
-- come back by themselves once that expansion is released. A header with nothing left under it is removed
-- by the game's own list code.
local LOCKED_INSUFFICIENT_EXPANSION = 1

if LFD_CURRENT_FILTER then
    local defaultFilter = LFD_CURRENT_FILTER
    LFD_CURRENT_FILTER = function(dungeonID)
        local _, reason = GetLFDLockInfo(dungeonID, 1)
        if reason == LOCKED_INSUFFICIENT_EXPANSION then
            return false
        end
        return defaultFilter(dungeonID)
    end
end
