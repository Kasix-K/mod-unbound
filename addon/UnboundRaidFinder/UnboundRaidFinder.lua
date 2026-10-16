-- Unbound Raid Finder: a "Raids" choice in the Dungeon Finder's type dropdown (with the random dungeons and
-- "Specific Dungeons"). Choosing it swaps the dungeon list for every raid, drawn with the Dungeon Finder's own
-- list rows (checkbox, lock icon, level range, expansion headers), and "Find Group" becomes "Enter Raid". The
-- server (src/unbound_raid_finder.cpp) does the checks and the teleport. Solo you go straight in. In a group
-- only the leader picks a raid: the leader goes in first and everyone else gets a prompt to follow (the
-- game's summon prompt, titled "Enter Raid" by this addon). "Leave Raid" sends you back to where you joined
-- from. /raidfinder (or /rf) opens the Dungeon Finder on Raids.
--
-- Messages: the addon whispers its own character with prefix UBRAID (LIST, ENTER:<id>, LEAVE); the server
-- answers R:<id>:<status>:<min>:<max>:<players>:<expansion>:<name> per raid, then END:<current>:<may pick>,
-- and sends INVITE:<raid>, MSG:<text>, ERR:<text>.

local PREFIX = "UBRAID"
local RAIDS = "unbound_raids"        -- the dropdown value (the game's are "specific" and random dungeon ids)
local RAIDS_TEXT = "Raids"
local ROW_HEIGHT = 16                 -- the Dungeon Finder's list: 15 rows of 16 from (25, -165)
local NUM_ROWS = 15

local EXPANSIONS = { [0] = "Classic Raids", [1] = "Burning Crusade Raids", [2] = "Wrath of the Lich King Raids" }

local raids, incoming = {}, nil      -- incoming: the list being received
local currentRaid, mayPick = 0, true
local selectedId
local panel, scroll, rows, statusText
local findGroupButton                 -- the Dungeon Finder's own Find Group button, Enter / Leave Raid on Raids
local display = {}                    -- rows to show: { header = text } or a raid

local function send(text)
    SendAddonMessage(PREFIX, text, "WHISPER", UnitName("player"))
end

local function elvSkins()
    if not ElvUI then return nil end
    local ok, E = pcall(function() return unpack(ElvUI) end)
    if not ok or not E or not E.private or not E.private.skins then return nil end
    local blizzard = E.private.skins.blizzard
    if not (blizzard and blizzard.enable) then return nil end
    return E:GetModule("Skins", true)
end

local function skin(method, ...)
    local skins = elvSkins()
    if skins and skins[method] then pcall(skins[method], skins, ...) end
end

local function setStatus(text, r, g, b)
    if statusText then
        statusText:SetText(text or "")
        statusText:SetTextColor(r or 1, g or 0.82, b or 0)
    end
end

local function levelText(raid)
    if raid.max > 0 and raid.max ~= raid.min then return format(LFD_LEVEL_FORMAT_RANGE, raid.min, raid.max) end
    return raid.min > 0 and format(LFD_LEVEL_FORMAT_SINGLE, raid.min) or ""
end

local function isRaidMode()
    return LFDQueueFrame and LFDQueueFrame.type == RAIDS
end

-- ------------------------------------------------------------------ list
local function buildDisplay()
    wipe(display)
    local lastExpansion
    for _, raid in ipairs(raids) do
        -- raids of an expansion the server's content lock keeps closed aren't listed at all (like the Dungeon
        -- Finder's dungeons); they appear once that expansion is released (Unbound.ExpansionUnlocked)
        if raid.status ~= "E" then
            if raid.expansion ~= lastExpansion then
                display[#display + 1] = { header = EXPANSIONS[raid.expansion] or "" }
                lastExpansion = raid.expansion
            end
            display[#display + 1] = raid
        end
    end
end

local function selectedRaid()
    for _, raid in ipairs(raids) do
        if raid.id == selectedId then return raid end
    end
end

-- On Raids the Find Group button is the Enter Raid / Leave Raid button (the same button, so it looks exactly
-- like Find Group with or without ElvUI). The game resets its text whenever it updates it.
local function updateButtons()
    if not findGroupButton or not isRaidMode() then return end
    if currentRaid ~= 0 then
        findGroupButton:SetText("Leave Raid")
        findGroupButton:Enable()
        return
    end
    findGroupButton:SetText("Enter Raid")
    local raid = selectedRaid()
    if raid and raid.status == "A" and mayPick then findGroupButton:Enable() else findGroupButton:Disable() end
end

-- one row, the way LFDQueueFrameSpecificListButton_SetDungeon draws a dungeon or a header
local function setRow(row, entry)
    row.entry = entry
    row.expandOrCollapseButton:Hide()
    row.heroicIcon:Hide()
    if entry.header then
        row.instanceName:SetText(entry.header)
        row.instanceName:SetFontObject(QuestDifficulty_Header)
        row.instanceName:SetPoint("LEFT", 40, 0)
        row.instanceName:SetPoint("RIGHT", row, "RIGHT", 0, 0)
        row.level:Hide()
        row.enableButton:Hide()
        row.lockedIndicator:Hide()
        return
    end

    local name = entry.name
    if entry.id == currentRaid then name = name .. " (you are here)" end
    row.instanceName:SetText(name)
    row.instanceName:SetPoint("LEFT", 40, 0)
    row.instanceName:SetPoint("RIGHT", row.level, "LEFT", -10, 0)
    row.level:SetText(levelText(entry))
    row.level:Show()

    local color = GetQuestDifficultyColor(entry.max > 0 and entry.max or entry.min)
    row.level:SetFontObject(color.font)
    if entry.status == "A" or entry.id == currentRaid then
        row.instanceName:SetFontObject(color.font)
        row.lockedIndicator:Hide()
        row.enableButton:Show()
        row.enableButton:SetChecked(entry.id == selectedId)
        if mayPick and currentRaid == 0 then row.enableButton:Enable() else row.enableButton:Disable() end
    else
        row.instanceName:SetFontObject(QuestDifficulty_Header)
        row.instanceName:SetTextColor(0.5, 0.5, 0.5)
        row.enableButton:Hide()
        row.lockedIndicator:Show()
    end
end

local function updateList()
    if not panel then return end
    local offset = FauxScrollFrame_GetOffset(scroll)
    for i = 1, NUM_ROWS do
        local row, entry = rows[i], display[offset + i]
        if entry then
            setRow(row, entry)
            row:Show()
        else
            row.entry = nil
            row:Hide()
        end
    end
    FauxScrollFrame_Update(scroll, #display, NUM_ROWS, ROW_HEIGHT)
    updateButtons()
end

local function requestList()
    incoming = {}
    send("LIST")
end

-- ------------------------------------------------------------------ raid view
local function createRow(i)
    local row = CreateFrame("Frame", "UnboundRaidFinderRow" .. i, panel, "LFGSpecificChoiceTemplate")
    if i == 1 then
        -- where the dungeon list starts (ElvUI moves it)
        row:SetPoint("TOPLEFT", LFDQueueFrameSpecificListButton1 or panel, "TOPLEFT", 0, 0)
    else
        row:SetPoint("TOPLEFT", rows[i - 1], "BOTTOMLEFT", 0, 0)
    end
    row:EnableMouse(true)

    -- the checkbox picks the raid (one at a time, like a radio button)
    row.enableButton:SetScript("OnClick", function(self)
        local entry = row.entry
        if entry and not entry.header then
            selectedId = entry.id
            PlaySound("igMainMenuOptionCheckBoxOn")
        end
        updateList()
    end)
    row:SetScript("OnMouseUp", function(self)
        if self.entry and not self.entry.header and self.enableButton:IsShown() and self.enableButton:IsEnabled() == 1 then
            self.enableButton:Click()
        end
    end)
    skin("HandleCheckBox", row.enableButton)
    return row
end

local function createRaidView()
    -- the raid list takes the place of LFDQueueFrameSpecific (the same area of the Dungeon Finder)
    panel = CreateFrame("Frame", "UnboundRaidFinderFrame", LFDQueueFrame)
    panel:SetAllPoints(LFDQueueFrame)
    panel:Hide()

    rows = {}
    for i = 1, NUM_ROWS do rows[i] = createRow(i) end

    scroll = CreateFrame("ScrollFrame", "UnboundRaidFinderScrollFrame", panel, "FauxScrollFrameTemplate")
    scroll:SetPoint("TOPLEFT", rows[1], "TOPLEFT", 0, 7)
    scroll:SetPoint("BOTTOMRIGHT", rows[NUM_ROWS], "BOTTOMRIGHT", 1, -7)
    scroll:SetScript("OnVerticalScroll", function(self, offset)
        FauxScrollFrame_OnVerticalScroll(self, offset, ROW_HEIGHT, updateList)
    end)
    skin("HandleScrollBar", _G["UnboundRaidFinderScrollFrameScrollBar"])

    statusText = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
    statusText:SetPoint("BOTTOMLEFT", 25, 34)
    statusText:SetWidth(300)
    statusText:SetJustifyH("LEFT")

    -- Find Group does Enter Raid / Leave Raid on Raids, and the game's join everywhere else
    findGroupButton = LFDQueueFrameFindGroupButton
    local findGroup = findGroupButton:GetScript("OnClick")
    findGroupButton:SetScript("OnClick", function(self, ...)
        if not isRaidMode() then
            return findGroup(self, ...)
        end
        if currentRaid ~= 0 then
            send("LEAVE")
        elseif selectedId then
            send("ENTER:" .. selectedId)
        end
    end)
    hooksecurefunc("LFDQueueFrameFindGroupButton_Update", updateButtons)

    panel:SetScript("OnShow", function()
        setStatus("")
        requestList()
        updateList()
    end)
end

local function setRaidView(on)
    if not panel then return end
    if on then
        LFDQueueFrameSpecific:Hide()
        LFDQueueFrameRandom:Hide()
        if LFDQueueFrameBackground then
            LFDQueueFrameBackground:SetTexture("Interface\\LFGFrame\\UI-LFG-BACKGROUND-DUNGEONWALL")
        end
        panel:Show()
        updateButtons()
    else
        panel:Hide()
        LFDQueueFrameFindGroupButton_Update()   -- back to Find Group
    end
end

-- ------------------------------------------------------------------ the dropdown
local function hookDungeonFinder()
    -- "Raids" at the end of the type dropdown. The dropdown is set up again every time the Dungeon Finder
    -- opens (LFDQueueFrameTypeDropDown_SetUp, OnShow), which looks up LFDQueueFrameTypeDropDown_Initialize by
    -- name: so that is the function to extend.
    local dropDown = LFDQueueFrameTypeDropDown
    local initialize = LFDQueueFrameTypeDropDown_Initialize
    LFDQueueFrameTypeDropDown_Initialize = function(...)
        initialize(...)
        if (UIDROPDOWNMENU_MENU_LEVEL or 1) ~= 1 then return end
        local info = UIDropDownMenu_CreateInfo()
        info.text = RAIDS_TEXT
        info.value = RAIDS
        info.func = function() LFDQueueFrame_SetType(RAIDS) end
        info.checked = isRaidMode()
        UIDropDownMenu_AddButton(info)
    end
    if dropDown.initialize == initialize then dropDown.initialize = LFDQueueFrameTypeDropDown_Initialize end
    dropDown:HookScript("OnShow", function()
        if isRaidMode() then
            UIDropDownMenu_SetSelectedValue(dropDown, RAIDS)
            UIDropDownMenu_SetText(dropDown, RAIDS_TEXT)
        end
    end)

    -- choosing it: the game's LFDQueueFrame_SetType only knows "specific" and random dungeon ids
    local setType = LFDQueueFrame_SetType
    LFDQueueFrame_SetType = function(value, ...)
        if value == RAIDS then
            LFDQueueFrame.type = RAIDS
            UIDropDownMenu_SetSelectedValue(dropDown, RAIDS)
            UIDropDownMenu_SetText(dropDown, RAIDS_TEXT)
            setRaidView(true)
            return
        end
        -- the game's function first (it sets the type), then the raid view goes and Find Group is reset
        setType(value, ...)
        setRaidView(false)
    end
end

-- ------------------------------------------------------------------ "Enter Raid" prompt
-- The server sends INVITE just before the summon prompt; the prompt then reads as an invitation to
-- the raid. Its text keeps the game's four values (who, where, time, unit).
local summon = StaticPopupDialogs["CONFIRM_SUMMON"]
local original = summon and { text = summon.text, button1 = summon.button1, button2 = summon.button2 }
local inviteUntil = 0

local function restorePrompt()
    if not summon or not original then return end
    summon.text, summon.button1, summon.button2 = original.text, original.button1, original.button2
    inviteUntil = 0
end

if summon then
    local onHide = summon.OnHide
    summon.OnHide = function(...)
        restorePrompt()
        if onHide then return onHide(...) end
    end
end

local function prepareInvite()
    if not summon then return end
    summon.text = "%s's group is entering %s.  Enter the raid?  The offer ends in %d %s."
    summon.button1 = "Enter Raid"
    summon.button2 = DECLINE
    inviteUntil = GetTime() + 125
end

local timer = CreateFrame("Frame")
timer:SetScript("OnUpdate", function()
    if inviteUntil > 0 and GetTime() > inviteUntil and not StaticPopup_Visible("CONFIRM_SUMMON") then
        restorePrompt()
    end
end)

-- ------------------------------------------------------------------ server messages
local events = CreateFrame("Frame")
events:RegisterEvent("PLAYER_LOGIN")
events:RegisterEvent("CHAT_MSG_ADDON")
events:RegisterEvent("PARTY_MEMBERS_CHANGED")
events:RegisterEvent("PARTY_LEADER_CHANGED")
events:RegisterEvent("PLAYER_LEVEL_UP")
events:RegisterEvent("PLAYER_ENTERING_WORLD")
events:SetScript("OnEvent", function(_, event, prefix, message, channel, sender)
    if event == "PLAYER_LOGIN" then
        if LFDParentFrame and LFDQueueFrame and LFDQueueFrameTypeDropDown and LFDQueueFrame_SetType then
            createRaidView()
            hookDungeonFinder()
        end
        return
    end
    if event ~= "CHAT_MSG_ADDON" then
        if panel and panel:IsShown() then requestList() end
        return
    end
    if prefix ~= PREFIX or channel ~= "WHISPER" or sender ~= UnitName("player") then return end

    local kind, rest = string.match(message, "^(%u+):(.*)$")
    if kind == "R" then
        local id, status, minLevel, maxLevel, players, expansion, name =
            string.match(rest, "^(%d+):(%u):(%d+):(%d+):(%d+):(%d+):(.*)$")
        if id and incoming then
            incoming[#incoming + 1] = { id = tonumber(id), status = status, min = tonumber(minLevel),
                max = tonumber(maxLevel), players = tonumber(players), expansion = tonumber(expansion), name = name }
        end
    elseif kind == "END" then
        local current, pick = string.match(rest, "^(%d+):(%d)$")
        if incoming then raids = incoming end
        incoming = nil
        currentRaid = tonumber(current) or 0
        mayPick = pick == "1"
        buildDisplay()
        if not selectedId or not selectedRaid() then
            for _, raid in ipairs(raids) do
                if raid.status == "A" then selectedId = raid.id break end
            end
        end
        if not mayPick and currentRaid == 0 then
            setStatus("Only your group leader can choose a raid.", 0.7, 0.7, 0.7)
        end
        updateList()
    elseif kind == "INVITE" then
        prepareInvite()
    elseif kind == "MSG" then
        setStatus(rest, 1, 0.82, 0)
    elseif kind == "ERR" then
        UIErrorsFrame:AddMessage(rest, 1, 0.3, 0.3)
        setStatus(rest, 1, 0.3, 0.3)
    end
end)

SLASH_UNBOUNDRAIDFINDER1 = "/raidfinder"
SLASH_UNBOUNDRAIDFINDER2 = "/rf"
SlashCmdList["UNBOUNDRAIDFINDER"] = function()
    if not panel then return end
    if not LFDParentFrame:IsShown() then ShowUIPanel(LFDParentFrame) end
    LFDQueueFrame_SetType(RAIDS)
end
