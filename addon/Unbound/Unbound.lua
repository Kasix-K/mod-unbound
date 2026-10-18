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

-- The same for the random dungeons in the Dungeon Finder's dropdown: the client lists every random dungeon
-- that fits the player's level and the account's expansion (Random Burning Crusade Dungeon at level 60) and
-- only greys out the locked ones. While the dropdown is built, the random dungeons the server reports as
-- locked for "insufficient expansion" are left out of what the game's dropdown code sees.
if LFDQueueFrameTypeDropDown_Initialize and GetNumRandomDungeons and GetLFGRandomDungeonInfo then
    local initialize = LFDQueueFrameTypeDropDown_Initialize
    LFDQueueFrameTypeDropDown_Initialize = function(...)
        local getNum, getInfo = GetNumRandomDungeons, GetLFGRandomDungeonInfo
        local shown = {}
        for i = 1, getNum() do
            local id = getInfo(i)
            local _, reason = GetLFDLockInfo(id, 1)
            if reason ~= LOCKED_INSUFFICIENT_EXPANSION then
                shown[#shown + 1] = i
            end
        end
        GetNumRandomDungeons = function() return #shown end
        GetLFGRandomDungeonInfo = function(i) return getInfo(shown[i]) end
        local ok, err = pcall(initialize, ...)
        GetNumRandomDungeons, GetLFGRandomDungeonInfo = getNum, getInfo
        if not ok then error(err, 0) end
    end
    -- the dropdown keeps the function it was first set up with until the Dungeon Finder opens again
    if LFDQueueFrameTypeDropDown and LFDQueueFrameTypeDropDown.initialize == initialize then
        LFDQueueFrameTypeDropDown.initialize = LFDQueueFrameTypeDropDown_Initialize
    end
end

-- Transmog window (mod-transmog-plus's Transmog addon): its Sets tab lists the sets of every expansion. Hide the
-- sets of expansions the server hasn't released (Unbound.ExpansionUnlocked), and their Category choices, so they
-- come back by themselves once an expansion is released. Each set's expansion is in TransmogSetExpansions.lua
-- (tools/transmog_set_expansions.py); the server tells which are released when asked (prefix UBLOCK,
-- src/unbound_content_lock.cpp). Until it answers, only classic sets show.
local LOCK_PREFIX = "UBLOCK"
local releasedExpansion = 0
local setExpansion = UnboundTransmogSetExpansion or {}
local categoryExpansion = { TBC = 1, WOTLK = 2 }

local function IsReleased(expansion)
    return (expansion or 0) <= releasedExpansion
end

local transmog = Transmog
if transmog and transmog.UpdateSetList and transmog.InitSetsView then
    -- The Sets tab builds its list from Transmog.SetData: let it see only the released sets while it does.
    local updateSetList = transmog.UpdateSetList
    transmog.UpdateSetList = function(self, ...)
        if not IsReleased(categoryExpansion[self.selectedSetCategory]) then
            self.selectedSetCategory = "ALL"
            if self.categoryDropDown then
                UIDropDownMenu_SetText(self.categoryDropDown, "All Categories")
            end
        end

        local all = self.SetData
        if all then
            local shown = {}
            for _, set in ipairs(all) do
                if IsReleased(setExpansion[set.id]) then
                    shown[#shown + 1] = set
                end
            end
            self.SetData = shown
        end
        local ok, err = pcall(updateSetList, self, ...)
        self.SetData = all
        if not ok then error(err, 0) end
    end

    -- The Category dropdown: leave out a locked expansion's choice while the menu is built.
    hooksecurefunc(transmog, "InitSetsView", function(self)
        local dropDown = self.categoryDropDown
        if not dropDown or dropDown.unboundFiltered or not dropDown.initialize then return end
        local initialize = dropDown.initialize
        dropDown.initialize = function(...)
            local addButton = UIDropDownMenu_AddButton
            UIDropDownMenu_AddButton = function(info, ...)
                if info and not IsReleased(categoryExpansion[info.value]) then return end
                return addButton(info, ...)
            end
            local ok, err = pcall(initialize, ...)
            UIDropDownMenu_AddButton = addButton
            if not ok then error(err, 0) end
        end
        dropDown.unboundFiltered = true
    end)

    local events = CreateFrame("Frame")
    events:RegisterEvent("PLAYER_ENTERING_WORLD")
    events:RegisterEvent("CHAT_MSG_ADDON")
    events:SetScript("OnEvent", function(self, event, prefix, message, channel, sender)
        if event == "PLAYER_ENTERING_WORLD" then
            self:UnregisterEvent("PLAYER_ENTERING_WORLD")
            SendAddonMessage(LOCK_PREFIX, "EXPANSION", "WHISPER", UnitName("player"))
            return
        end
        if prefix ~= LOCK_PREFIX or channel ~= "WHISPER" or sender ~= UnitName("player") then return end
        local expansion = tonumber(string.match(message, "^EXPANSION:(%d+)$"))
        if not expansion or expansion == releasedExpansion then return end
        releasedExpansion = expansion
        if TransmogSetsFrame and TransmogSetsFrame:IsVisible() then
            transmog:UpdateSetList(false)
        end
    end)
end
