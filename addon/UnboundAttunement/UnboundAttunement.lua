-- Unbound Attunement: gear infusion (called attunement in the code) on item tooltips, and the collection window
-- (/infusion, or the Infusion button in the micro menu). The server (src/unbound_attunement.cpp) knows everything: the addon
-- asks it about items and the collection with whispered addon messages (prefix UBATT) and keeps the answers.
-- The window uses the same Blizzard frame art and talent-tree grid as the perk window.

-- ------------------------------------------------------------------ server messages
local PREFIX = "UBATT"
local cache = {}        -- item id -> { code, done, needed, price, reason }  (code: A, W, S, N)
local queued = {}       -- item ids waiting to be asked about
local asked = {}        -- item ids asked about, no answer yet
local collection        -- the last collection the server sent (window)
local incoming          -- the collection being received
local refresh           -- forward (window)

local function send(text)
    SendAddonMessage(PREFIX, text, "WHISPER", UnitName("player"))
end

-- Ask about queued items a few times a second, up to 40 per message.
local asker = CreateFrame("Frame")
local askTimer = 0
asker:SetScript("OnUpdate", function(_, elapsed)
    askTimer = askTimer + elapsed
    if askTimer < 0.2 then return end
    askTimer = 0
    local ids = {}
    for id in pairs(queued) do
        if #ids >= 40 then break end
        table.insert(ids, id)
    end
    if #ids == 0 then return end
    for _, id in ipairs(ids) do queued[id] = nil; asked[id] = true end
    send("Q:" .. table.concat(ids, ","))
end)

local function ask(id)
    if not cache[id] and not asked[id] then queued[id] = true end
end

-- ------------------------------------------------------------------ tooltips
local LIGHT_BLUE = { 0.30, 0.76, 1.00 }
local GREEN = { 0.10, 1.00, 0.10 }
local GREY = { 0.60, 0.60, 0.60 }
local NOT_GEAR = { INVTYPE_BAG = true, INVTYPE_AMMO = true, INVTYPE_QUIVER = true, INVTYPE_BODY = true,
                   INVTYPE_TABARD = true }

local function money(copper)
    if GetCoinTextureString then return GetCoinTextureString(copper) end
    return math.floor(copper / 10000) .. "g"
end

local function addLines(tooltip, info)
    if info.code == "A" then
        tooltip:AddLine("Infused: its stats are yours for good", unpack(GREEN))
    elseif info.code == "W" then
        local percent = info.needed > 0 and math.floor(info.done * 100 / info.needed) or 0
        tooltip:AddLine(string.format("Infusion: %d%% (%d/%d kills)", percent, info.done, info.needed), unpack(LIGHT_BLUE))
        if info.done == 0 then
            tooltip:AddLine("Wear it and slay foes to infuse it", unpack(GREY))
        end
        tooltip:AddLine("Or offer it as tribute at an Altar of Tribute: " .. money(info.price), unpack(GREY))
    elseif info.code == "S" then
        tooltip:AddLine("Infusion: tribute only (you can't wear it)", unpack(LIGHT_BLUE))
        tooltip:AddLine("At an Altar of Tribute: " .. money(info.price), unpack(GREY))
    elseif info.reason and info.reason ~= "" then
        tooltip:AddLine("Infusion: " .. info.reason, unpack(GREY))
    end
end

local tooltips = {}

local function itemIdFromLink(link)
    return link and tonumber(link:match("item:(%d+)"))
end

local function showOn(tooltip, id)
    local info = cache[id]
    if not info or tooltip.ubattAdded == id then return end
    tooltip.ubattAdded = id
    addLines(tooltip, info)
    tooltip:Show()
end

local function onTooltipSetItem(tooltip)
    local _, link = tooltip:GetItem()
    local id = itemIdFromLink(link)
    if not id then return end
    local _, _, quality, _, _, _, _, _, equipLoc = GetItemInfo(link)
    if not quality or quality < 2 or not equipLoc or equipLoc == "" or NOT_GEAR[equipLoc] then return end
    tooltip.ubattId = id
    if cache[id] then showOn(tooltip, id) else ask(id) end
end

for _, name in ipairs({ "GameTooltip", "ItemRefTooltip", "ShoppingTooltip1", "ShoppingTooltip2" }) do
    local tooltip = _G[name]
    if tooltip then
        tooltip:HookScript("OnTooltipSetItem", onTooltipSetItem)
        tooltip:HookScript("OnTooltipCleared", function(self) self.ubattId = nil; self.ubattAdded = nil end)
        table.insert(tooltips, tooltip)
    end
end

-- An answer arrived: show it on any tooltip still waiting for that item.
local function answered(id)
    for _, tooltip in ipairs(tooltips) do
        if tooltip:IsShown() and tooltip.ubattId == id then showOn(tooltip, id) end
    end
end

-- ------------------------------------------------------------------ messages from the server
local function split(s, sep)
    local parts = {}
    for part in string.gmatch(s, "([^" .. sep .. "]+)") do table.insert(parts, part) end
    return parts
end

local function onProgress(list)
    for _, entry in ipairs(split(list, ",")) do
        local id, done, needed = entry:match("^(%d+)=(%d+)=(%d+)$")
        id = tonumber(id)
        if id then
            local info = cache[id]
            if info then
                info.done, info.needed = tonumber(done), tonumber(needed)
            end
        end
    end
end

local function onMessage(message)
    local kind, rest = message:match("^(%u+):?(.*)$")
    if kind == "I" then
        -- I:<id>:<code>:<done>:<needed>:<price>:<reason>
        local id, code, done, needed, price, reason = rest:match("^(%d+):(%a):(%d+):(%d+):(%d+):(.*)$")
        id = tonumber(id)
        if not id then return end
        cache[id] = { code = code, done = tonumber(done), needed = tonumber(needed), price = tonumber(price),
                      reason = reason }
        asked[id] = nil
        answered(id)
    elseif kind == "P" then
        onProgress(rest)
        if refresh then refresh(true) end
    elseif kind == "A" then
        local id = tonumber(rest)
        if id and cache[id] then cache[id].code = "A" end
        if refresh then refresh(true) end
    elseif kind == "RESET" then
        wipe(cache); wipe(asked)
        if refresh then refresh(true) end
    elseif kind == "C" then
        local what, data = rest:match("^(%u+):?(.*)$")
        if what == "BEGIN" then
            incoming = { attuned = {}, progress = {}, stats = {}, items = 0, raw = 0, effective = 0,
                         full = 100, half = 200 }
        elseif incoming and what == "A" then
            for _, id in ipairs(split(data, ",")) do table.insert(incoming.attuned, tonumber(id)) end
        elseif incoming and what == "P" then
            for _, entry in ipairs(split(data, ",")) do
                local id, done, needed = entry:match("^(%d+)=(%d+)=(%d+)$")
                if id then
                    table.insert(incoming.progress, { id = tonumber(id), done = tonumber(done), needed = tonumber(needed) })
                end
            end
        elseif incoming and what == "S" then
            local items, raw, effective, full, half = data:match("^(%d+):([%d%.]+):([%d%.]+):([%d%.]+):([%d%.]+)$")
            incoming.items = tonumber(items) or 0
            incoming.raw, incoming.effective = tonumber(raw) or 0, tonumber(effective) or 0
            incoming.full, incoming.half = tonumber(full) or 100, tonumber(half) or 200
        elseif incoming and what == "T" then
            for _, entry in ipairs(split(data, ";")) do
                local name, value = entry:match("^(.+)=(%-?%d+)$")
                if name then table.insert(incoming.stats, { name = name, value = tonumber(value) }) end
            end
        elseif incoming and what == "END" then
            collection = incoming
            incoming = nil
            table.sort(collection.attuned)
            table.sort(collection.progress, function(a, b) return a.done / a.needed > b.done / b.needed end)
            if refresh then refresh(false) end
        end
    end
end

local comm = CreateFrame("Frame")
comm:RegisterEvent("CHAT_MSG_ADDON")
comm:SetScript("OnEvent", function(_, _, prefix, message, channel, sender)
    if prefix == PREFIX and channel == "WHISPER" and sender == UnitName("player") then onMessage(message) end
end)

-- ------------------------------------------------------------------ window (perk window style)
local C = {
    panel  = { 0, 0, 0, 0.55 },
    border = { 0.60, 0.60, 0.60, 1 },
    gold   = { 1.00, 0.82, 0.00 },
    muted  = { 0.60, 0.60, 0.60 },
}
local WHITE = "Interface\\Buttons\\WHITE8X8"
local FRAME_W, FRAME_H = 780, 560
local COLS, ICON, PITCH_X, PITCH_Y = 8, 36, 54, 56
local GRID_W = COLS * PITCH_X + 6
local BAR_W = FRAME_W - 36 - 28    -- the summary bar: window minus the panel and bar insets

local frame
local ui = { buttons = {} }
local showing = "attuned"  -- or "progress"

local function dialogBackdrop(f)
    f:SetBackdrop({
        bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background", tile = true, tileSize = 32,
        edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border", edgeSize = 32,
        insets = { left = 11, right = 12, top = 12, bottom = 11 },
    })
end

local function panel(parent)
    local p = CreateFrame("Frame", nil, parent)
    p:SetBackdrop({
        bgFile = "Interface\\Tooltips\\UI-Tooltip-Background", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
        tile = true, tileSize = 16, edgeSize = 16, insets = { left = 4, right = 4, top = 4, bottom = 4 },
    })
    p:SetBackdropColor(unpack(C.panel))
    p:SetBackdropBorderColor(unpack(C.border))
    return p
end

local function text(parent, font)
    return parent:CreateFontString(nil, "OVERLAY", font or "GameFontHighlightSmall")
end

local function separator(parent, y)
    local t = parent:CreateTexture(nil, "ARTWORK")
    t:SetTexture(WHITE)
    t:SetHeight(1)
    t:SetPoint("TOPLEFT", 8, y)
    t:SetPoint("TOPRIGHT", -8, y)
    t:SetGradientAlpha("HORIZONTAL", C.gold[1], C.gold[2], C.gold[3], 0.7, C.gold[1], C.gold[2], C.gold[3], 0)
end

local buttonCount = 0
local function makeItemButton(parent)
    buttonCount = buttonCount + 1
    local b = CreateFrame("Button", "UnboundAttunementItem" .. buttonCount, parent)
    b:SetSize(ICON, ICON)
    b.icon = b:CreateTexture(nil, "BORDER")
    b.icon:SetAllPoints()
    b.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    b.frame = b:CreateTexture(nil, "ARTWORK")
    b.frame:SetTexture("Interface\\Buttons\\UI-Quickslot2")
    b.frame:SetSize(ICON * 1.75, ICON * 1.75); b.frame:SetPoint("CENTER", 0, -1)
    b.glow = b:CreateTexture(nil, "OVERLAY")
    b.glow:SetTexture("Interface\\Buttons\\UI-ActionButton-Border")
    b.glow:SetBlendMode("ADD")
    b.glow:SetSize(ICON * 1.8, ICON * 1.8); b.glow:SetPoint("CENTER")
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b.badgeBorder = b:CreateTexture(nil, "OVERLAY")
    b.badgeBorder:SetTexture("Interface\\TalentFrame\\TalentFrame-RankBorder")
    b.badgeBorder:SetSize(36, 32); b.badgeBorder:SetPoint("CENTER", b, "BOTTOMRIGHT", 0, 0)
    b.badge = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    b.badge:SetPoint("CENTER", b.badgeBorder, "CENTER", 0, 0)
    b:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:SetHyperlink("item:" .. self.itemId)
        GameTooltip:Show()
    end)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    b:SetScript("OnClick", function(self)
        if IsModifiedClick("CHATLINK") then
            local _, link = GetItemInfo(self.itemId)
            if link then ChatEdit_InsertLink(link) end
        end
    end)
    return b
end

local function updateGrid()
    local list = {}
    if collection then
        if showing == "attuned" then
            for _, id in ipairs(collection.attuned) do table.insert(list, { id = id }) end
        else
            for _, p in ipairs(collection.progress) do table.insert(list, p) end
        end
    end
    local gap = (GRID_W - COLS * ICON) / (COLS + 1)
    for i, entry in ipairs(list) do
        local b = ui.buttons[i]
        if not b then
            b = makeItemButton(ui.gridChild)
            ui.buttons[i] = b
        end
        local col, row = (i - 1) % COLS, math.floor((i - 1) / COLS)
        b:ClearAllPoints()
        b:SetPoint("TOPLEFT", gap + col * PITCH_X, -(10 + row * PITCH_Y))
        b.itemId = entry.id
        b.icon:SetTexture(GetItemIcon(entry.id) or "Interface\\Icons\\INV_Misc_QuestionMark")
        if entry.needed then
            b.icon:SetDesaturated(true)
            b.glow:Hide()
            b.badge:SetText(math.floor(entry.done * 100 / entry.needed) .. "%")
            b.badge:SetTextColor(unpack(LIGHT_BLUE))
            b.badge:Show(); b.badgeBorder:Show()
        else
            b.icon:SetDesaturated(false)
            b.glow:Show()
            b.badge:Hide(); b.badgeBorder:Hide()
        end
        b:Show()
    end
    for i = #list + 1, #ui.buttons do ui.buttons[i]:Hide() end
    local rows = math.max(1, math.ceil(#list / COLS))
    local height = 10 + rows * PITCH_Y
    ui.gridChild:SetHeight(height)
    ui.scroll:UpdateScrollChildRect()
    if ui.scrollBar then
        if height > ui.scroll:GetHeight() + 1 then ui.scrollBar:Show() else ui.scrollBar:Hide() end
    end
    if #list == 0 then
        ui.empty:SetText(showing == "attuned" and "Nothing infused yet. Wear gear and slay foes, or offer it as tribute at an Altar of Tribute."
                                             or "No items in progress. Equip gear that counts and slay foes.")
        ui.empty:Show()
    else
        ui.empty:Hide()
    end
end

local function updateSummary()
    local c = collection or { items = 0, raw = 0, effective = 0, full = 100, half = 200, stats = {}, progress = {} }
    ui.count:SetText(string.format("%d items infused", c.items))
    ui.percent:SetText(string.format("%.0f%% of a full set of gear's stats", c.effective))
    ui.raw:SetText(string.format("collected %.0f%% before diminishing returns: full value until %d%%, half until %d%%, a quarter beyond",
        c.raw, c.full, c.half))
    local scaleMax = c.half * 1.5
    local width = BAR_W - 10
    ui.fill:SetWidth(math.max(1, width * math.min(c.effective, scaleMax) / scaleMax))
    ui.markFull:SetPoint("LEFT", ui.bar, "LEFT", 5 + width * c.full / scaleMax, 0)
    ui.markHalf:SetPoint("LEFT", ui.bar, "LEFT", 5 + width * c.half / scaleMax, 0)

    local lines = {}
    for _, s in ipairs(c.stats) do
        table.insert(lines, string.format("|cff1eff00%+d|r %s", s.value, s.name))
    end
    ui.stats:SetText(#lines > 0 and table.concat(lines, "\n") or "|cff999999No infusion stats yet.|r")
    ui.tabAttuned:SetText(string.format("Infused (%d)", #((collection and collection.attuned) or {})))
    ui.tabProgress:SetText(string.format("In progress (%d)", #((collection and collection.progress) or {})))
    if showing == "attuned" then ui.tabAttuned:LockHighlight(); ui.tabProgress:UnlockHighlight()
    else ui.tabProgress:LockHighlight(); ui.tabAttuned:UnlockHighlight() end
end

-- refresh(true): the server says something changed, ask for the collection again (once per half second);
-- refresh(false): a new collection arrived, redraw.
local pending, pendingTimer = false, 0
local ticker = CreateFrame("Frame")
ticker:SetScript("OnUpdate", function(_, elapsed)
    if not pending then return end
    pendingTimer = pendingTimer + elapsed
    if pendingTimer >= 0.5 then pending = false; send("COLL") end
end)

refresh = function(fromServer)
    if not frame or not frame:IsShown() then return end
    if fromServer then
        pending, pendingTimer = true, 0
        return
    end
    updateSummary()
    updateGrid()
end

local function build()
    frame = CreateFrame("Frame", "UnboundAttunementFrame", UIParent)
    frame:SetSize(FRAME_W, FRAME_H)
    frame:SetPoint("CENTER")
    frame:SetFrameStrata("HIGH")
    frame:SetToplevel(true)
    frame:EnableMouse(true)
    frame:SetMovable(true)
    frame:SetClampedToScreen(true)
    frame:RegisterForDrag("LeftButton")
    frame:SetScript("OnDragStart", frame.StartMoving)
    frame:SetScript("OnDragStop", frame.StopMovingOrSizing)
    dialogBackdrop(frame)
    frame:Hide()
    tinsert(UISpecialFrames, "UnboundAttunementFrame")

    local header = frame:CreateTexture(nil, "ARTWORK")
    header:SetTexture("Interface\\DialogFrame\\UI-DialogBox-Header")
    header:SetSize(340, 64)
    header:SetPoint("TOP", 0, 12)
    local title = text(frame, "GameFontNormal")
    title:SetPoint("TOP", header, "TOP", 0, -14)
    title:SetText("Gear Infusion")
    local sub = text(frame)
    sub:SetPoint("TOP", 0, -26)
    sub:SetText("Gear whose stats are yours for good")
    sub:SetTextColor(unpack(C.muted))
    local close = CreateFrame("Button", "UnboundAttunementCloseButton", frame, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -6, -6)

    -- summary: count, % of a full set, the diminishing-returns bar
    local top = panel(frame)
    top:SetPoint("TOPLEFT", 18, -46); top:SetPoint("TOPRIGHT", -18, -46); top:SetHeight(86)
    ui.count = text(top, "GameFontNormalLarge")
    ui.count:SetPoint("TOPLEFT", 14, -12)
    ui.percent = text(top, "GameFontHighlight")
    ui.percent:SetPoint("LEFT", ui.count, "RIGHT", 16, 0)
    ui.bar = CreateFrame("Frame", nil, top)
    ui.bar:SetPoint("TOPLEFT", 14, -36); ui.bar:SetPoint("TOPRIGHT", -14, -36); ui.bar:SetHeight(18)
    ui.bar:SetBackdrop({ bgFile = WHITE, edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border", edgeSize = 10,
                         insets = { left = 2, right = 2, top = 2, bottom = 2 } })
    ui.bar:SetBackdropColor(0, 0, 0, 0.6)
    ui.bar:SetBackdropBorderColor(unpack(C.border))
    ui.fill = ui.bar:CreateTexture(nil, "ARTWORK")
    ui.fill:SetTexture("Interface\\TargetingFrame\\UI-StatusBar")
    ui.fill:SetVertexColor(LIGHT_BLUE[1], LIGHT_BLUE[2], LIGHT_BLUE[3])
    ui.fill:SetPoint("TOPLEFT", 5, -4); ui.fill:SetPoint("BOTTOMLEFT", 5, 4)
    ui.markFull = ui.bar:CreateTexture(nil, "OVERLAY")
    ui.markFull:SetTexture(WHITE); ui.markFull:SetVertexColor(unpack(C.gold)); ui.markFull:SetSize(2, 18)
    ui.markHalf = ui.bar:CreateTexture(nil, "OVERLAY")
    ui.markHalf:SetTexture(WHITE); ui.markHalf:SetVertexColor(unpack(C.gold)); ui.markHalf:SetSize(2, 18)
    ui.raw = text(top)
    ui.raw:SetPoint("TOPLEFT", ui.bar, "BOTTOMLEFT", 0, -6)
    ui.raw:SetTextColor(unpack(C.muted))

    -- left: the infusion stats
    local left = panel(frame)
    left:SetPoint("TOPLEFT", top, "BOTTOMLEFT", 0, -6); left:SetPoint("BOTTOMLEFT", 18, 34); left:SetWidth(240)
    local statsHead = text(left, "GameFontNormal")
    statsHead:SetPoint("TOPLEFT", 12, -12); statsHead:SetText("Infusion stats")
    separator(left, -30)
    ui.stats = text(left)
    ui.stats:SetPoint("TOPLEFT", 14, -38); ui.stats:SetWidth(212)
    ui.stats:SetJustifyH("LEFT"); ui.stats:SetJustifyV("TOP")

    -- right: tabs and the item grid
    local right = panel(frame)
    right:SetPoint("TOPLEFT", left, "TOPRIGHT", 6, 0); right:SetPoint("BOTTOMRIGHT", -18, 34)
    ui.tabAttuned = CreateFrame("Button", "UnboundAttunementTabAttuned", right, "UIPanelButtonTemplate")
    ui.tabAttuned:SetSize(140, 22); ui.tabAttuned:SetPoint("TOPLEFT", 12, -10)
    ui.tabAttuned:SetScript("OnClick", function() showing = "attuned"; PlaySound("igMainMenuOptionCheckBoxOn"); refresh(false) end)
    ui.tabProgress = CreateFrame("Button", "UnboundAttunementTabProgress", right, "UIPanelButtonTemplate")
    ui.tabProgress:SetSize(140, 22); ui.tabProgress:SetPoint("LEFT", ui.tabAttuned, "RIGHT", 6, 0)
    ui.tabProgress:SetScript("OnClick", function() showing = "progress"; PlaySound("igMainMenuOptionCheckBoxOn"); refresh(false) end)
    separator(right, -38)
    ui.scroll = CreateFrame("ScrollFrame", "UnboundAttunementGrid", right, "UIPanelScrollFrameTemplate")
    ui.scroll:SetPoint("TOPLEFT", 8, -44); ui.scroll:SetPoint("BOTTOMRIGHT", -30, 8)
    ui.scrollBar = _G["UnboundAttunementGridScrollBar"]
    ui.gridChild = CreateFrame("Frame", nil, ui.scroll)
    ui.gridChild:SetSize(GRID_W, 10)
    ui.scroll:SetScrollChild(ui.gridChild)
    ui.empty = text(right, "GameFontDisableSmall")
    ui.empty:SetPoint("TOP", 0, -64); ui.empty:SetWidth(380)

    local foot = text(frame, "GameFontDisableSmall")
    foot:SetPoint("BOTTOMLEFT", 22, 16)
    foot:SetText("Wear gear and slay foes to infuse it, or offer it as tribute at an Altar of Tribute. Hover an item for details; shift-click links it.")

    frame:SetScript("OnShow", function()
        PlaySound("igCharacterInfoOpen")
        refresh(false)
        send("COLL")
    end)
    frame:SetScript("OnHide", function() PlaySound("igCharacterInfoClose") end)
end

local function toggle()
    if not frame then return end
    if frame:IsShown() then frame:Hide() else frame:Show() end
end

-- ------------------------------------------------------------------ micro menu button
-- An "Infusion" button in the micro menu, between Talents and Achievements. ElvUI keeps its own fixed list of micro
-- buttons, so with ElvUI's micro bar the button styles itself like ElvUI's and follows the bar's layout;
-- with the default UI it uses the game's micro button art.
local MICRO_ICON = "Interface\\Icons\\INV_Enchant_EssenceEternalLarge"

local function elvActionBars()
    if not ElvUI or not ElvUI_MicroBar then return nil end
    local ok, E = pcall(function() return unpack(ElvUI) end)
    if not ok or not E then return nil end
    local AB = E:GetModule("ActionBars", true)
    if not AB or not AB.db or not AB.db.microbar then return nil end
    return E, AB
end

local function addMicroButton()
    if _G["UnboundAttunementMicroButton"] or not HelpMicroButton then return end
    local button = CreateFrame("Button", "UnboundAttunementMicroButton", HelpMicroButton:GetParent())

    local E, AB = elvActionBars()
    if E then
        -- ElvUI: a bordered square like its other micro buttons, the icon filling it. The icon and the pressed
        -- shade are drawn on the square's own frame: re-parenting the button (place() below) moves child frames
        -- back above it, so an icon on the button itself would end up hidden behind the square's background.
        local f = CreateFrame("Frame", nil, button)
        f:SetFrameLevel(button:GetFrameLevel() - 1)
        f:SetTemplate("Default", true)
        f:SetOutside(button)
        button.backdrop = f
        button.icon = f:CreateTexture(nil, "ARTWORK")
        button.icon:SetTexture(MICRO_ICON)
        button.icon:SetInside(f)
        button.icon:SetTexCoord(0.1, 0.9, 0.1, 0.9)
        local pushed = f:CreateTexture(nil, "OVERLAY")
        pushed:SetTexture(1, 1, 1, 0.25)
        pushed:SetInside(f)
        pushed:Hide()
        button:HookScript("OnMouseDown", function() pushed:Show() end)
        button:HookScript("OnMouseUp", function() pushed:Hide() end)

        -- One row (the usual layout): between Talents and Achievements; ElvUI anchors each button to the one
        -- before it, so moving Achievements after this button shifts the rest along. Several rows: ElvUI's grid
        -- would break, so the button goes after the last one (Help) instead.
        local function place()
            button:SetParent(HelpMicroButton:GetParent())
            button:SetSize(CharacterMicroButton:GetWidth(), CharacterMicroButton:GetHeight())
            local spacing = E:Scale((E.PixelMode and 1 or 3) + (AB.db.microbar.buttonSpacing or 0))
            local oneRow = (AB.db.microbar.buttonsPerRow or 10) >= 10
            button:ClearAllPoints()
            if oneRow then
                button:SetPoint("LEFT", TalentMicroButton, "RIGHT", spacing, 0)
                AchievementMicroButton:ClearAllPoints()
                AchievementMicroButton:SetPoint("LEFT", button, "RIGHT", spacing, 0)
            else
                button:SetPoint("LEFT", HelpMicroButton, "RIGHT", spacing, 0)
            end
            -- one row: make the bar's background wide enough for the extra button
            if oneRow and HelpMicroButton:GetParent() == ElvUI_MicroBar and AB.MicroWidth then
                ElvUI_MicroBar:SetWidth(AB.MicroWidth + button:GetWidth() + spacing)
            end
            button:SetAlpha(1)
        end
        hooksecurefunc(AB, "UpdateMicroPositionDimensions", place)
        button:HookScript("OnEnter", function(self)
            if AB.db.microbar.mouseover then E:UIFrameFadeIn(ElvUI_MicroBar, 0.2, ElvUI_MicroBar:GetAlpha(), AB.db.microbar.alpha) end
            self.backdrop:SetBackdropBorderColor(unpack(E.media.rgbvaluecolor))
        end)
        button:HookScript("OnLeave", function(self)
            if AB.db.microbar.mouseover then E:UIFrameFadeOut(ElvUI_MicroBar, 0.2, ElvUI_MicroBar:GetAlpha(), 0) end
            self.backdrop:SetBackdropBorderColor(unpack(E.media.bordercolor))
        end)
        place()
    else
        -- default UI: the game's micro button frame with the icon where the character portrait goes
        button.icon = button:CreateTexture(nil, "ARTWORK")
        button.icon:SetTexture(MICRO_ICON)
        button:SetSize(28, 58)
        button:SetNormalTexture("Interface\\Buttons\\UI-MicroButtonCharacter-Up")
        button:SetPushedTexture("Interface\\Buttons\\UI-MicroButtonCharacter-Down")
        button:SetHighlightTexture("Interface\\Buttons\\UI-MicroButton-Hilight", "ADD")
        button.icon:SetSize(18, 25)
        button.icon:SetPoint("TOP", 0, -28)
        button.icon:SetTexCoord(0.2, 0.8, 0.0666, 0.9)
        -- between Talents (hidden below level 10: then after Spellbook) and Achievements
        local function place()
            button:SetParent(AchievementMicroButton:GetParent())
            local before = TalentMicroButton:IsShown() and TalentMicroButton or SpellbookMicroButton
            button:ClearAllPoints()
            button:SetPoint("BOTTOMLEFT", before, "BOTTOMRIGHT", -3, 0)
            AchievementMicroButton:ClearAllPoints()
            AchievementMicroButton:SetPoint("BOTTOMLEFT", button, "BOTTOMRIGHT", -3, 0)
        end
        -- the game re-anchors the micro buttons (talents unlocking, vehicles): put this one back each time
        if UpdateMicroButtons then hooksecurefunc("UpdateMicroButtons", place) end
        if VehicleMenuBar_MoveMicroButtons then hooksecurefunc("VehicleMenuBar_MoveMicroButtons", place) end
        place()
        button:SetScript("OnMouseDown", function(self) self.icon:SetPoint("TOP", 1, -29) end)
        button:SetScript("OnMouseUp", function(self) self.icon:SetPoint("TOP", 0, -28) end)
    end

    button:SetScript("OnClick", function()
        PlaySound("igMainMenuOptionCheckBoxOn")
        toggle()
    end)
    button:HookScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:SetText("Gear Infusion", 1, 1, 1)
        GameTooltip:AddLine("Your infused gear and the stats it gives (/infusion).", 1, 0.82, 0)
        GameTooltip:Show()
    end)
    button:HookScript("OnLeave", function() GameTooltip:Hide() end)
    button:Show()
end

-- ------------------------------------------------------------------ startup
local loader = CreateFrame("Frame")
loader:RegisterEvent("PLAYER_LOGIN")
loader:SetScript("OnEvent", function(self)
    build()
    -- add the micro button a moment later, after ElvUI (if any) has set up its micro bar
    local wait = 0
    self:SetScript("OnUpdate", function(s, elapsed)
        wait = wait + elapsed
        if wait < 1 then return end
        s:SetScript("OnUpdate", nil)
        addMicroButton()
    end)
end)

SLASH_UNBOUNDATTUNEMENT1 = "/infusion"
SLASH_UNBOUNDATTUNEMENT2 = "/infuse"
SLASH_UNBOUNDATTUNEMENT3 = "/attunement"   -- old names
SLASH_UNBOUNDATTUNEMENT4 = "/attune"
SlashCmdList["UNBOUNDATTUNEMENT"] = function() toggle() end
