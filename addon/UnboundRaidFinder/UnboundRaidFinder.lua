-- Unbound Raid Finder: "Dungeons" and "Raids" tabs under the Dungeon Finder window (LFDParentFrame).
-- The Raids tab lists every raid with its level and whether you can enter it; the server
-- (src/unbound_raid_finder.cpp) does the checks and the teleport. Solo you go straight in. In a group
-- only the leader picks a raid: the leader goes in first and everyone else gets a prompt to follow
-- (the game's summon prompt, titled "Enter Raid" by this addon). "Leave Raid" sends you back to where
-- you joined from.
--
-- Messages: the addon whispers its own character with prefix UBRAID (LIST, ENTER:<id>, LEAVE); the server
-- answers R:<id>:<status>:<min>:<max>:<players>:<expansion>:<name> per raid, then END:<current>:<may pick>,
-- and sends INVITE:<raid>, MSG:<text>, ERR:<text>.

local PREFIX = "UBRAID"
local ROW_HEIGHT = 18
local NUM_ROWS = 15

local EXPANSIONS = { [0] = "Classic", [1] = "The Burning Crusade", [2] = "Wrath of the Lich King" }
local STATUS = {
    A = { "Available", 0.25, 1, 0.25 },
    L = { "Level", 0.6, 0.6, 0.6 },
    Q = { "Attunement", 1, 0.5, 0.25 },
    E = { "Not released", 0.5, 0.5, 0.5 },
}

local raids, incoming = {}, nil      -- incoming: the list being received
local currentRaid, mayPick = 0, true
local selectedId
local panel, scroll, rows, enterButton, statusText
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
    if raid.max > 0 then return raid.min .. "-" .. raid.max end
    return raid.min > 0 and tostring(raid.min) or ""
end

-- ------------------------------------------------------------------ list
local function buildDisplay()
    wipe(display)
    local lastExpansion
    for _, raid in ipairs(raids) do
        if raid.expansion ~= lastExpansion then
            display[#display + 1] = { header = EXPANSIONS[raid.expansion] or "" }
            lastExpansion = raid.expansion
        end
        display[#display + 1] = raid
    end
end

local function selectedRaid()
    for _, raid in ipairs(raids) do
        if raid.id == selectedId then return raid end
    end
end

local function updateButtons()
    if not enterButton then return end
    if currentRaid ~= 0 then
        enterButton:SetText("Leave Raid")
        enterButton:Enable()
        return
    end
    enterButton:SetText("Enter Raid")
    local raid = selectedRaid()
    if raid and raid.status == "A" and mayPick then enterButton:Enable() else enterButton:Disable() end
end

local function updateList()
    if not panel then return end
    local offset = FauxScrollFrame_GetOffset(scroll)
    for i = 1, NUM_ROWS do
        local row, entry = rows[i], display[offset + i]
        row.entry = entry
        if not entry then
            row:Hide()
        else
            row:Show()
            if entry.header then
                row.name:SetText(entry.header)
                row.name:SetFontObject(GameFontNormal)
                row.level:SetText("")
                row.state:SetText("")
                row.selected:Hide()
                row:Disable()
            else
                row:Enable()
                row.name:SetFontObject(GameFontHighlightSmall)
                row.name:SetText("   " .. entry.name)
                row.level:SetText(levelText(entry))
                local s = STATUS[entry.status] or STATUS.E
                if entry.id == currentRaid then
                    row.state:SetText("You are here")
                    row.state:SetTextColor(1, 0.82, 0)
                else
                    row.state:SetText(s[1])
                    row.state:SetTextColor(s[2], s[3], s[4])
                end
                local dim = entry.status ~= "A" and entry.id ~= currentRaid
                row.name:SetTextColor(dim and 0.6 or 1, dim and 0.6 or 1, dim and 0.6 or 1)
                if entry.id == selectedId then row.selected:Show() else row.selected:Hide() end
            end
        end
    end
    FauxScrollFrame_Update(scroll, #display, NUM_ROWS, ROW_HEIGHT)
    updateButtons()
end

local function requestList()
    incoming = {}
    send("LIST")
end

-- ------------------------------------------------------------------ panel
local function createRow(i)
    local row = CreateFrame("Button", "UnboundRaidFinderRow" .. i, panel)
    row:SetSize(300, ROW_HEIGHT)
    if i == 1 then
        row:SetPoint("TOPLEFT", panel, "TOPLEFT", 24, -112)
    else
        row:SetPoint("TOPLEFT", rows[i - 1], "BOTTOMLEFT", 0, 0)
    end
    row:SetHighlightTexture("Interface\\QuestFrame\\UI-QuestTitleHighlight", "ADD")

    row.selected = row:CreateTexture(nil, "BACKGROUND")
    row.selected:SetTexture("Interface\\QuestFrame\\UI-QuestLogTitleHighlight")
    row.selected:SetBlendMode("ADD")
    row.selected:SetVertexColor(1, 0.82, 0, 0.5)
    row.selected:SetAllPoints()
    row.selected:Hide()

    row.name = row:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    row.name:SetPoint("LEFT", 4, 0)
    row.name:SetWidth(170)
    row.name:SetJustifyH("LEFT")

    row.level = row:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    row.level:SetPoint("LEFT", 176, 0)
    row.level:SetWidth(44)
    row.level:SetJustifyH("CENTER")

    row.state = row:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    row.state:SetPoint("RIGHT", -4, 0)
    row.state:SetWidth(78)
    row.state:SetJustifyH("RIGHT")

    row:SetScript("OnClick", function(self)
        if self.entry and not self.entry.header then
            selectedId = self.entry.id
            updateList()
        end
    end)
    row:SetScript("OnEnter", function(self)
        local raid = self.entry
        if not raid or raid.header then return end
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:SetText(raid.name, 1, 1, 1)
        if raid.players > 0 then GameTooltip:AddLine(raid.players .. " players", 1, 0.82, 0) end
        if levelText(raid) ~= "" then GameTooltip:AddLine("Level " .. levelText(raid), 1, 0.82, 0) end
        if raid.status == "Q" then
            GameTooltip:AddLine("Needs \"The Dread Citadel - Naxxramas\" from Archmage Angela Dosantos at Light's Hope Chapel.", 1, 0.5, 0.25, true)
        elseif raid.status == "E" then
            GameTooltip:AddLine("This expansion has not been released yet.", 0.6, 0.6, 0.6, true)
        elseif raid.status == "L" then
            GameTooltip:AddLine("Your level doesn't fit this raid.", 0.6, 0.6, 0.6, true)
        end
        GameTooltip:Show()
    end)
    row:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return row
end

local function createPanel()
    panel = CreateFrame("Frame", "UnboundRaidFinderFrame", LFDParentFrame)
    panel:SetAllPoints(LFDParentFrame)
    panel:Hide()

    -- the same art as the Dungeons page, unless ElvUI has replaced it with its own backdrop
    local layout = _G["LFDQueueFrameLayout"]
    if layout and layout:IsShown() and layout:GetTexture() then
        local art = panel:CreateTexture(nil, "BACKGROUND")
        art:SetTexture("Interface\\LFGFrame\\UI-LFG-FRAME")
        art:SetSize(512, 512)
        art:SetPoint("TOPLEFT")
        local paper = panel:CreateTexture(nil, "BORDER")
        paper:SetTexture("Interface\\LFGFrame\\UI-LFG-BACKGROUND-QUESTPAPER")
        paper:SetSize(512, 256)
        paper:SetPoint("LEFT", 21, -64)
    end

    local title = panel:CreateFontString(nil, "ARTWORK", "GameFontNormal")
    title:SetPoint("TOP", 12, -17)
    title:SetText("Raid Finder")

    local intro = panel:CreateFontString(nil, "ARTWORK", "GameFontHighlightSmall")
    intro:SetPoint("TOPLEFT", 26, -62)
    intro:SetWidth(300)
    intro:SetJustifyH("LEFT")
    intro:SetText("Choose a raid and press Enter Raid. In a group, the leader chooses: the leader goes in " ..
                  "first, then everyone else is asked to follow.")

    local head = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
    head:SetPoint("TOPLEFT", 28, -98)
    head:SetText("Raid")
    local headLevel = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
    headLevel:SetPoint("TOPLEFT", 200, -98)
    headLevel:SetText("Level")

    scroll = CreateFrame("ScrollFrame", "UnboundRaidFinderScrollFrame", panel, "FauxScrollFrameTemplate")
    scroll:SetPoint("TOPLEFT", 24, -112)
    scroll:SetSize(300, ROW_HEIGHT * NUM_ROWS)
    scroll:SetScript("OnVerticalScroll", function(self, offset)
        FauxScrollFrame_OnVerticalScroll(self, offset, ROW_HEIGHT, updateList)
    end)
    skin("HandleScrollBar", _G["UnboundRaidFinderScrollFrameScrollBar"])

    rows = {}
    for i = 1, NUM_ROWS do rows[i] = createRow(i) end

    statusText = panel:CreateFontString(nil, "ARTWORK", "GameFontNormalSmall")
    statusText:SetPoint("BOTTOMLEFT", 22, 34)
    statusText:SetWidth(310)
    statusText:SetJustifyH("LEFT")

    enterButton = CreateFrame("Button", "UnboundRaidFinderEnterButton", panel, "UIPanelButtonTemplate2")
    enterButton:SetSize(135, 22)
    enterButton:SetPoint("BOTTOMLEFT", 18, 6)
    enterButton:SetText("Enter Raid")
    enterButton:SetScript("OnClick", function()
        if currentRaid ~= 0 then
            send("LEAVE")
        elseif selectedId then
            send("ENTER:" .. selectedId)
        end
    end)
    skin("HandleButton", enterButton)

    local close = CreateFrame("Button", "UnboundRaidFinderCloseButton", panel, "UIPanelButtonTemplate2")
    close:SetSize(112, 22)
    close:SetPoint("BOTTOMRIGHT", -7, 6)
    close:SetText(CLOSE)
    close:SetScript("OnClick", function() HideUIPanel(LFDParentFrame) end)
    skin("HandleButton", close)

    panel:SetScript("OnShow", function()
        setStatus("")
        requestList()
        updateList()
    end)
end

-- ------------------------------------------------------------------ tabs
local function selectTab(id)
    PanelTemplates_SetTab(LFDParentFrame, id)
    if id == 2 then
        LFDQueueFrame:Hide()
        panel:Show()
    else
        panel:Hide()
        LFDQueueFrame:Show()
    end
end

local function createTabs()
    local tabs = {}
    for i, text in ipairs({ "Dungeons", "Raids" }) do
        local tab = CreateFrame("Button", "LFDParentFrameTab" .. i, LFDParentFrame, "CharacterFrameTabButtonTemplate")
        tab:SetID(i)
        tab:SetText(text)
        tab:SetScript("OnShow", function(self) PanelTemplates_TabResize(self, 0) end)
        tab:SetScript("OnClick", function(self)
            PlaySound("igCharacterInfoTab")
            selectTab(self:GetID())
        end)
        PanelTemplates_TabResize(tab, 0)
        tabs[i] = tab
        skin("HandleTab", tab)
    end
    local skinned = elvSkins() ~= nil
    tabs[1]:SetPoint("TOPLEFT", LFDParentFrame, "BOTTOMLEFT", 14, skinned and -2 or 4)
    tabs[2]:SetPoint("LEFT", tabs[1], "RIGHT", skinned and -15 or -16, 0)
    PanelTemplates_SetNumTabs(LFDParentFrame, 2)
    LFDParentFrame.selectedTab = 1
    PanelTemplates_UpdateTabs(LFDParentFrame)
    LFDParentFrame:HookScript("OnShow", function(self) selectTab(self.selectedTab or 1) end)
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
        if LFDParentFrame and LFDQueueFrame then
            createPanel()
            createTabs()
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
    selectTab(2)
end
