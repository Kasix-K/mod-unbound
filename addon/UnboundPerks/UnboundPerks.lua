-- Unbound Perks: the Character Perks window (/perks).
-- Toggles go to the server (src/unbound_perks.cpp), which keeps them; loadouts are saved per character
-- in UnboundPerksDB. The window uses the game's own (Blizzard) frame art: dialog border and header,
-- red panel buttons, check boxes and quest-log highlights.

local P = UnboundPerks

-- ------------------------------------------------------------------ colours (Blizzard style)
local C = {
    panel     = { 0, 0, 0, 0.55 },          -- inner panels (tinted tooltip background)
    border    = { 0.60, 0.60, 0.60, 1 },    -- inner panel borders (tooltip border, grey)
    gold      = { 1.00, 0.82, 0.00 },       -- NORMAL_FONT_COLOR
    text      = { 1.00, 1.00, 1.00 },
    muted     = { 0.60, 0.60, 0.60 },
    selected  = { 1.00, 0.82, 0.00, 0.45 }, -- selected row highlight (gold)
    active    = { 0.10, 1.00, 0.10 },       -- GREEN_FONT_COLOR
}

local WHITE = "Interface\\Buttons\\WHITE8X8"
local CAT_H = 26
-- talent-tree grid: perk icons in rows of GRID_COLS
local GRID_COLS, ICON, ROW_PITCH = 5, 40, 64
local GRID_W = 318         -- inside the middle panel, left of its scroll bar
local FRAME_W, FRAME_H = 880, 620
local DETAIL_W = 300
local PANELS_TOP, PANELS_BOTTOM = -96, 34  -- the three panels, relative to the window
local HIGHLIGHT = "Interface\\QuestFrame\\UI-QuestTitleHighlight"
local SELECTED = "Interface\\QuestFrame\\UI-QuestLogTitleHighlight"

-- The game's dialog window: parchment-dark background with the stone border.
local function dialogBackdrop(f)
    f:SetBackdrop({
        bgFile = "Interface\\DialogFrame\\UI-DialogBox-Background", tile = true, tileSize = 32,
        edgeFile = "Interface\\DialogFrame\\UI-DialogBox-Border", edgeSize = 32,
        insets = { left = 11, right = 12, top = 12, bottom = 11 },
    })
end

-- Inner panels: the tooltip border on a darkened background.
local function backdrop(f, bg, border)
    f:SetBackdrop({
        bgFile = "Interface\\Tooltips\\UI-Tooltip-Background", edgeFile = "Interface\\Tooltips\\UI-Tooltip-Border",
        tile = true, tileSize = 16, edgeSize = 16, insets = { left = 4, right = 4, top = 4, bottom = 4 },
    })
    f:SetBackdropColor(unpack(bg))
    f:SetBackdropBorderColor(unpack(border or C.border))
end

-- A row's selected highlight (under the hover highlight).
local function selectedTexture(row)
    local t = row:CreateTexture(nil, "BACKGROUND")
    t:SetTexture(SELECTED)
    t:SetBlendMode("ADD")
    t:SetVertexColor(unpack(C.selected))
    t:SetAllPoints()
    t:Hide()
    return t
end

local function text(parent, font, r, g, b)
    local fs = parent:CreateFontString(nil, "OVERLAY", font or "GameFontHighlightSmall")
    if r then fs:SetTextColor(r, g, b) end
    return fs
end

-- Region:SetShown doesn't exist in 3.3.5
local function setShown(region, show)
    if show then region:Show() else region:Hide() end
end

-- ------------------------------------------------------------------ state
local db                 -- UnboundPerksDB (per character)
local frame              -- main window
local perksByCat = {}    -- category key -> { perk, ... } visible to this character
local categories = {}    -- visible categories in order
local selectedCat, selectedPerk
local filtered = {}      -- perks shown in the middle grid
local catRows, perkButtons = {}, {}
local ui = {}

local function playerClass()
    local _, cls = UnitClass("player")
    return cls
end

local function isOn(perk)
    return perk.permanent or db.active[perk.id] == true
end

local function activeCount(catKey)
    local n = 0
    for _, perk in ipairs(perksByCat[catKey] or {}) do
        if isOn(perk) then n = n + 1 end
    end
    return n
end

local function buildPerkLists()
    local cls = playerClass()
    wipe(perksByCat); wipe(categories)
    for _, perk in ipairs(P.PERKS) do
        if not perk.class or perk.class == cls then
            perksByCat[perk.category] = perksByCat[perk.category] or {}
            table.insert(perksByCat[perk.category], perk)
        end
    end
    for _, cat in ipairs(P.CATEGORIES) do
        if perksByCat[cat.key] then
            local c = { key = cat.key, name = cat.name, color = cat.color, limit = cat.limit }
            if cat.key == "CLASS" then
                local localized, token = UnitClass("player")
                local cc = RAID_CLASS_COLORS[token]
                c.name = localized
                c.color = cc and { cc.r, cc.g, cc.b } or C.gold
            end
            table.insert(categories, c)
        end
    end
end

local function categoryOf(perk)
    for _, c in ipairs(categories) do
        if c.key == perk.category then return c end
    end
end

-- ------------------------------------------------------------------ loadouts
local function currentLoadout()
    return db.loadouts[db.loadout]
end

local function savedCount(loadout)
    local n = 0
    for _ in pairs(loadout.perks) do n = n + 1 end
    return n
end

local refresh -- forward
local sendServer, serverIds -- forward (server sync, below)

local function setStatus(msg)
    ui.status:SetText(msg or "")
end

local function loadoutStatus()
    local lo = currentLoadout()
    local n = savedCount(lo)
    setStatus(n == 1 and "1 perk saved" or (n .. " perks saved"))
end

local function doSave()
    local lo = currentLoadout()
    wipe(lo.perks)
    for id, on in pairs(db.active) do
        if on then lo.perks[id] = true end
    end
    loadoutStatus()
end

local function doApply()
    local lo = currentLoadout()
    wipe(db.active)
    for id in pairs(lo.perks) do db.active[id] = true end
    sendServer("LOAD:" .. serverIds())
    refresh()
    setStatus("Applied " .. lo.name)
end

local function doRename()
    local name = strtrim(ui.nameBox:GetText() or "")
    if name == "" then return end
    currentLoadout().name = name
    ui.nameBox:ClearFocus()
    refresh()
end

local function doDelete()
    if #db.loadouts <= 1 then
        setStatus("Keep at least one loadout")
        return
    end
    table.remove(db.loadouts, db.loadout)
    db.loadout = math.max(1, db.loadout - 1)
    refresh()
end

local function newLoadout()
    table.insert(db.loadouts, { name = "Loadout " .. (#db.loadouts + 1), perks = {} })
    db.loadout = #db.loadouts
    refresh()
end

-- ------------------------------------------------------------------ widgets
-- The game's templates name their parts after the frame ("$parentText"), so every frame built from one
-- gets a unique name.
local frameCount = 0
local function uniqueName(kind)
    frameCount = frameCount + 1
    return "UnboundPerks" .. kind .. frameCount
end

-- The game's red panel button (UIPanelButtonTemplate).
local function makeButton(parent, label, width, onClick)
    local b = CreateFrame("Button", uniqueName("Button"), parent, "UIPanelButtonTemplate")
    b:SetSize(width, 22)
    b:SetText(label)
    b:SetScript("OnClick", function() PlaySound("igMainMenuOptionCheckBoxOn"); onClick() end)
    return b
end

-- The game's text box (InputBoxTemplate; it needs a frame name for its border textures).
local function makeEditBox(parent, name, width)
    local e = CreateFrame("EditBox", name, parent, "InputBoxTemplate")
    e:SetSize(width, 20)
    e:SetAutoFocus(false)
    e:SetFontObject(ChatFontNormal)
    e:SetTextColor(unpack(C.text))
    e:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
    return e
end

local function makePanel(parent)
    local p = CreateFrame("Frame", nil, parent)
    backdrop(p, C.panel)
    return p
end

local function separator(parent, y, left, right)
    local t = parent:CreateTexture(nil, "ARTWORK")
    t:SetTexture(WHITE)
    t:SetHeight(1)
    t:SetPoint("TOPLEFT", left or 8, y)
    t:SetPoint("TOPRIGHT", -(right or 8), y)
    t:SetGradientAlpha("HORIZONTAL", C.gold[1], C.gold[2], C.gold[3], 0.7, C.gold[1], C.gold[2], C.gold[3], 0)
    return t
end

-- ------------------------------------------------------------------ perk toggling
-- ------------------------------------------------------------------ server sync
-- Perks marked works = true are kept by the server (src/unbound_perks.cpp); it answers every change
-- with STATE:<ids>, which is the truth for those perks. Other perks are only saved in this addon.
local PREFIX = "UBPERK"

sendServer = function(text)
    SendAddonMessage(PREFIX, text, "WHISPER", UnitName("player"))
end

serverIds = function()
    local ids = {}
    for _, perk in ipairs(P.PERKS) do
        if perk.works and not perk.permanent and db.active[perk.id] then table.insert(ids, perk.id) end
    end
    return table.concat(ids, ",")
end

-- Perk ranks from the server: RANK:<perk>:<rank>:<max>:<values> (values: "a,b,c;a,b,c" per rank)
local ranks = {}

local function onServerRank(rest)
    local id, rank, maxRank, values = string.match(rest, "^(%d+):(%d+):(%d+):(.*)$")
    id, rank, maxRank = tonumber(id), tonumber(rank), tonumber(maxRank)
    if not id then return end
    local parsed = {}
    for entry in string.gmatch(values or "", "[^;]+") do
        local nums = {}
        for n in string.gmatch(entry, "[%d%.]+") do table.insert(nums, tonumber(n)) end
        table.insert(parsed, nums)
    end
    ranks[id] = { rank = rank, max = maxRank }
    for _, perk in ipairs(P.PERKS) do
        if perk.id == id and perk.applyRank then perk.applyRank(perk, rank, maxRank, parsed) end
    end
    if refresh then refresh() end
end

local function onServerState(list)
    local on = {}
    for id in string.gmatch(list, "%d+") do on[tonumber(id)] = true end
    for _, perk in ipairs(P.PERKS) do
        if perk.works and not perk.permanent then db.active[perk.id] = on[perk.id] end
    end
    if refresh then refresh() end
end

-- The perk this one is exclusive with, if that one is on (turning this one on swaps them).
local function activePartner(perk)
    return perk.excludes and db.active[perk.excludes] and perk.excludes or nil
end

local function togglePerk(perk)
    if perk.permanent then return end
    if not db.active[perk.id] then
        local cat = categoryOf(perk)
        local partner = activePartner(perk)
        if partner then
            db.active[partner] = nil  -- the server turns it off too
        elseif cat and cat.limit and activeCount(cat.key) >= cat.limit then
            local msg = "You can only have " .. cat.limit .. " " .. cat.name .. " perks active. Turn one off first."
            UIErrorsFrame:AddMessage(msg, 1, 0.3, 0.3)
            setStatus(msg)
            PlaySound("igQuestFailed")
            return
        end
    end
    db.active[perk.id] = not db.active[perk.id] or nil
    PlaySound(db.active[perk.id] and "igMainMenuOptionCheckBoxOn" or "igMainMenuOptionCheckBoxOff")
    if perk.works then sendServer("SET:" .. perk.id .. ":" .. (db.active[perk.id] and "1" or "0")) end
    refresh()
end

-- ------------------------------------------------------------------ refresh
local function updateFilter()
    wipe(filtered)
    local q = strlower(strtrim(ui.search:GetText() or ""))
    if q ~= "" then
        -- searching looks through every category
        for _, c in ipairs(categories) do
            for _, perk in ipairs(perksByCat[c.key]) do
                if strfind(strlower(perk.name), q, 1, true) then table.insert(filtered, perk) end
            end
        end
    else
        for _, perk in ipairs(perksByCat[selectedCat] or {}) do table.insert(filtered, perk) end
    end
end

local function updateCategories()
    for i, row in ipairs(catRows) do
        local c = categories[i]
        if c then
            row.cat = c
            row.name:SetText(c.name)
            row.name:SetTextColor(unpack(c.color))
            row.count:SetText(activeCount(c.key) .. "/" .. (c.limit or #perksByCat[c.key]))
            setShown(row.sel, c.key == selectedCat)
            row:Show()
        else
            row:Hide()
        end
    end
end

-- ------------------------------------------------------------------ talent-tree grid
-- A perk can be turned on now: not on yet, implemented, and its category isn't full.
local function canTurnOn(perk)
    if isOn(perk) or perk.permanent or not perk.works then return false end
    local cat = categoryOf(perk)
    return activePartner(perk) ~= nil or not (cat and cat.limit and activeCount(cat.key) >= cat.limit)
end

local function showPerkTooltip(button)
    local perk = button.perk
    if not perk then return end
    local cat = categoryOf(perk) or { name = "", color = C.gold }
    GameTooltip:SetOwner(button, "ANCHOR_RIGHT")
    GameTooltip:AddLine(perk.name, 1, 1, 1)
    GameTooltip:AddLine((perk.permanent and "Permanent" or cat.name) .. " Perk", unpack(cat.color))
    if perk.permanent then
        GameTooltip:AddLine("Always active", unpack(C.active))
    elseif isOn(perk) then
        GameTooltip:AddLine("Active", unpack(C.active))
    end
    GameTooltip:AddLine(perk.desc or "", 1, 0.82, 0, true)
    if not perk.works and not perk.permanent then
        GameTooltip:AddLine("Not active on the server yet.", 1, 0.6, 0.2, true)
    elseif not perk.permanent then
        GameTooltip:AddLine(isOn(perk) and "Right-click to turn off." or "Right-click to turn on.", 0.1, 1, 0.1)
    end
    GameTooltip:Show()
end

-- One perk icon in the grid: the action-button frame, a talent-style rank badge (0/1, 1/1), a gold
-- glow while active.
local function makePerkButton(parent)
    local b = CreateFrame("Button", uniqueName("Perk"), parent)
    b:SetSize(ICON, ICON)
    b:RegisterForClicks("LeftButtonUp", "RightButtonUp")
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
    b.sel = b:CreateTexture(nil, "OVERLAY")
    b.sel:SetTexture("Interface\\Buttons\\CheckButtonHilight")
    b.sel:SetBlendMode("ADD")
    b.sel:SetAllPoints()
    b:SetHighlightTexture("Interface\\Buttons\\ButtonHilight-Square", "ADD")
    b.rankBorder = b:CreateTexture(nil, "OVERLAY")
    b.rankBorder:SetTexture("Interface\\TalentFrame\\TalentFrame-RankBorder")
    b.rankBorder:SetSize(32, 32); b.rankBorder:SetPoint("CENTER", b, "BOTTOMRIGHT", 0, 0)
    b.rank = b:CreateFontString(nil, "OVERLAY", "GameFontNormalSmall")
    b.rank:SetPoint("CENTER", b.rankBorder, "CENTER", 0, 0)
    b:SetScript("OnClick", function(self, button)
        if button == "RightButton" then
            togglePerk(self.perk)
        else
            PlaySound("igMainMenuOptionCheckBoxOn")
            selectedPerk = self.perk
        end
        refresh()
        showPerkTooltip(self)
    end)
    b:SetScript("OnDoubleClick", function(self) togglePerk(self.perk); refresh(); showPerkTooltip(self) end)
    b:SetScript("OnEnter", showPerkTooltip)
    b:SetScript("OnLeave", function() GameTooltip:Hide() end)
    return b
end

local function updateGrid()
    local colGap = (GRID_W - GRID_COLS * ICON) / (GRID_COLS + 1)
    for i, perk in ipairs(filtered) do
        local b = perkButtons[i]
        if not b then
            b = makePerkButton(ui.gridChild)
            perkButtons[i] = b
        end
        local col, row = (i - 1) % GRID_COLS, math.floor((i - 1) / GRID_COLS)
        b:ClearAllPoints()
        b:SetPoint("TOPLEFT", colGap + col * (ICON + colGap), -(14 + row * ROW_PITCH))
        b.perk = perk
        b.icon:SetTexture(perk.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
        local on, available = isOn(perk), canTurnOn(perk)
        b.icon:SetDesaturated(not on and not available)
        b.icon:SetVertexColor(1, 1, 1)
        if not on and not available then b.icon:SetVertexColor(0.6, 0.6, 0.6) end
        setShown(b.glow, on)
        setShown(b.sel, perk == selectedPerk)
        local r = ranks[perk.id]
        if r then
            b.rank:SetText((on and r.rank or 0) .. "/" .. r.max)
        else
            b.rank:SetText(on and "1/1" or "0/1")
        end
        if on then
            b.rank:SetTextColor(unpack(C.gold))          -- learned (talent: yellow)
        elseif available then
            b.rank:SetTextColor(unpack(C.active))        -- can be turned on (talent: green)
        else
            b.rank:SetTextColor(unpack(C.muted))         -- locked (talent: grey)
        end
        b:Show()
    end
    for i = #filtered + 1, #perkButtons do perkButtons[i]:Hide() end
    local rows = math.max(1, math.ceil(#filtered / GRID_COLS))
    local height = 14 + rows * ROW_PITCH
    ui.gridChild:SetHeight(height)
    ui.scroll:UpdateScrollChildRect()
    -- only show the scroll bar when the tree is taller than the panel
    if ui.scrollBar then setShown(ui.scrollBar, height > ui.scroll:GetHeight() + 1) end
    setShown(ui.empty, #filtered == 0)

    -- tree header: the category (or search) and how many of its perks are on
    local q = strtrim(ui.search:GetText() or "")
    local cat = categoryOf({ category = selectedCat })
    if q ~= "" then
        ui.treeTitle:SetText("Search results"); ui.treeTitle:SetTextColor(unpack(C.gold))
        ui.treeCount:SetText(#filtered .. (#filtered == 1 and " perk" or " perks"))
        ui.treeTint:SetGradientAlpha("VERTICAL", 1, 0.82, 0, 0, 1, 0.82, 0, 0.12)
    elseif cat then
        ui.treeTitle:SetText(cat.name .. " Perks"); ui.treeTitle:SetTextColor(unpack(cat.color))
        ui.treeCount:SetText("Active: " .. activeCount(cat.key) .. "/" .. (cat.limit or #perksByCat[cat.key]))
        local r, g, b = unpack(cat.color)
        ui.treeTint:SetGradientAlpha("VERTICAL", r, g, b, 0, r, g, b, 0.18)
    end
end

local function updateDetails()
    local d = ui.details
    local perk = selectedPerk
    if not perk then
        d.content:Hide(); d.none:Show()
        return
    end
    d.none:Hide(); d.content:Show()
    local c = categoryOf(perk) or { name = "", color = C.gold }
    d.icon:SetTexture(perk.icon or "Interface\\Icons\\INV_Misc_QuestionMark")
    d.name:SetText(perk.name)
    d.cat:SetText((perk.permanent and "Permanent" or c.name) .. " Perk")
    d.cat:SetTextColor(unpack(c.color))
    d.icon:SetDesaturated(not isOn(perk))
    if perk.permanent then
        d.state:SetText("Always Active"); d.state:SetTextColor(unpack(C.active)); d.check:Show()
        d.toggle:Hide()
    elseif isOn(perk) then
        d.state:SetText("Active"); d.state:SetTextColor(unpack(C.active)); d.check:Show()
        d.toggle:SetText("Turn Off"); d.toggle:Show()
    else
        d.state:SetText("Inactive"); d.state:SetTextColor(unpack(C.muted)); d.check:Hide()
        d.toggle:SetText("Turn On"); d.toggle:Show()
    end
    local body = perk.desc or ""
    if perk.live then
        local ok, line = pcall(perk.live)
        if ok and line then body = body .. (perk.liveInline and "\n" or "\n\n") .. line end
    end
    if perk.pets then
        body = body .. "\n\n|cff999999This perk also works for your pets.|r"
    end
    if not perk.works and not perk.permanent then
        body = body .. "\n\n|cffff9933Not active on the server yet.|r"
    end
    d.desc:SetText(body)
    d.note:SetText(perk.note or "")
end

local function updateLoadoutBar()
    local lo = currentLoadout()
    UIDropDownMenu_SetText(ui.drop, db.loadout .. ". " .. lo.name)
    if not ui.nameBox:HasFocus() then ui.nameBox:SetText(lo.name) end
end

refresh = function()
    if not frame then return end
    updateFilter()
    updateCategories()
    updateGrid()
    updateDetails()
    updateLoadoutBar()
    loadoutStatus()
end

local function selectCategory(key)
    selectedCat = key
    ui.search:SetText("")
    ui.scroll:SetVerticalScroll(0)
    selectedPerk = perksByCat[key] and perksByCat[key][1]
    refresh()
end

-- ------------------------------------------------------------------ build the window
local function build()
    frame = CreateFrame("Frame", "UnboundPerksFrame", UIParent)
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
    tinsert(UISpecialFrames, "UnboundPerksFrame") -- Escape closes it

    -- title banner (the game's dialog header)
    local header = frame:CreateTexture(nil, "ARTWORK")
    header:SetTexture("Interface\\DialogFrame\\UI-DialogBox-Header")
    header:SetSize(340, 64)
    header:SetPoint("TOP", 0, 12)
    local title = text(frame, "GameFontNormal")
    title:SetPoint("TOP", header, "TOP", 0, -14)
    title:SetText("Character Perks")
    local sub = text(frame, "GameFontHighlightSmall")
    sub:SetPoint("TOP", 0, -26)
    sub:SetText("Toggle perks on to gain their power")
    sub:SetTextColor(unpack(C.muted))

    local close = CreateFrame("Button", "UnboundPerksCloseButton", frame, "UIPanelCloseButton")
    close:SetPoint("TOPRIGHT", -6, -6)

    -- loadout bar
    local bar = CreateFrame("Frame", nil, frame)
    bar:SetPoint("TOPLEFT", 18, -46); bar:SetPoint("TOPRIGHT", -18, -46); bar:SetHeight(40)
    backdrop(bar, C.panel)
    local lbl = text(bar, "GameFontNormal")
    lbl:SetPoint("LEFT", 12, 0); lbl:SetText("Loadout:")

    ui.drop = CreateFrame("Frame", "UnboundPerksLoadoutDropDown", bar, "UIDropDownMenuTemplate")
    ui.drop:SetPoint("LEFT", lbl, "RIGHT", -10, -2)
    UIDropDownMenu_SetWidth(ui.drop, 130)
    UIDropDownMenu_Initialize(ui.drop, function()
        for i, lo in ipairs(db.loadouts) do
            local info = UIDropDownMenu_CreateInfo()
            info.text = i .. ". " .. lo.name
            info.checked = (i == db.loadout)
            info.func = function() db.loadout = i; refresh() end
            UIDropDownMenu_AddButton(info)
        end
        local info = UIDropDownMenu_CreateInfo()
        info.text = "|cff7fb2ff+ New loadout|r"
        info.notCheckable = true
        info.func = newLoadout
        UIDropDownMenu_AddButton(info)
    end)

    ui.nameBox = makeEditBox(bar, "UnboundPerksLoadoutName", 150)
    ui.nameBox:SetPoint("LEFT", ui.drop, "RIGHT", -4, 2)
    ui.nameBox:SetScript("OnEnterPressed", doRename)

    local apply = makeButton(bar, "Apply", 76, doApply)
    apply:SetPoint("LEFT", ui.nameBox, "RIGHT", 10, 0)
    local save = makeButton(bar, "Save", 76, doSave)
    save:SetPoint("LEFT", apply, "RIGHT", 4, 0)
    local rename = makeButton(bar, "Rename", 76, doRename)
    rename:SetPoint("LEFT", save, "RIGHT", 4, 0)
    local delete = makeButton(bar, "Delete", 76, doDelete)
    delete:SetPoint("LEFT", rename, "RIGHT", 4, 0)

    ui.status = text(bar, "GameFontHighlightSmall")
    ui.status:SetPoint("RIGHT", -12, 0)
    ui.status:SetTextColor(unpack(C.muted))

    -- three panels
    local left = makePanel(frame)
    left:SetPoint("TOPLEFT", 18, PANELS_TOP); left:SetPoint("BOTTOMLEFT", 18, PANELS_BOTTOM); left:SetWidth(176)
    local right = makePanel(frame)
    right:SetPoint("TOPRIGHT", -18, PANELS_TOP); right:SetPoint("BOTTOMRIGHT", -18, PANELS_BOTTOM)
    right:SetWidth(DETAIL_W)
    local mid = makePanel(frame)
    mid:SetPoint("TOPLEFT", left, "TOPRIGHT", 6, 0); mid:SetPoint("BOTTOMRIGHT", right, "BOTTOMLEFT", -6, 0)

    -- categories
    local ch = text(left, "GameFontNormal")
    ch:SetPoint("TOPLEFT", 12, -12); ch:SetText("Categories")
    separator(left, -30)
    for i = 1, #P.CATEGORIES do
        local row = CreateFrame("Button", nil, left)
        row:SetHeight(CAT_H)
        row:SetPoint("TOPLEFT", 6, -36 - (i - 1) * (CAT_H + 2))
        row:SetPoint("TOPRIGHT", -6, -36 - (i - 1) * (CAT_H + 2))
        row:SetHighlightTexture(HIGHLIGHT, "ADD")
        row.sel = selectedTexture(row)
        row.name = text(row, "GameFontNormal"); row.name:SetPoint("LEFT", 10, 0)
        row.count = text(row, "GameFontHighlightSmall"); row.count:SetPoint("RIGHT", -8, 0)
        row:SetScript("OnClick", function(self)
            PlaySound("igMainMenuOptionCheckBoxOn")
            selectCategory(self.cat.key)
        end)
        catRows[i] = row
    end

    -- search
    ui.search = makeEditBox(mid, "UnboundPerksSearch", 10)
    ui.search:SetPoint("TOPLEFT", 16, -12); ui.search:SetPoint("TOPRIGHT", -12, -12)
    local hint = text(ui.search, "GameFontDisableSmall")
    hint:SetPoint("LEFT", 2, 0); hint:SetText("Search all perks...")
    ui.search:SetScript("OnTextChanged", function(self)
        setShown(hint, self:GetText() == "" and not self:HasFocus())
        ui.scroll:SetVerticalScroll(0)
        if frame:IsShown() then refresh() end
    end)
    ui.search:HookScript("OnEditFocusGained", function() hint:Hide() end)
    ui.search:HookScript("OnEditFocusLost", function(self) setShown(hint, self:GetText() == "") end)

    -- talent tree: a header (category, active count), a tint in the category's colour, the icon grid
    ui.treeTitle = text(mid, "GameFontNormal")
    ui.treeTitle:SetPoint("TOPLEFT", 14, -40)
    ui.treeCount = text(mid, "GameFontHighlightSmall")
    ui.treeCount:SetPoint("TOPRIGHT", -14, -42)
    separator(mid, -56)
    ui.treeTint = mid:CreateTexture(nil, "BACKGROUND")
    ui.treeTint:SetTexture(WHITE)
    ui.treeTint:SetPoint("TOPLEFT", 4, -58); ui.treeTint:SetPoint("BOTTOMRIGHT", -4, 4)

    local gridTop = -62
    ui.scroll = CreateFrame("ScrollFrame", "UnboundPerksGrid", mid, "UIPanelScrollFrameTemplate")
    ui.scroll:SetPoint("TOPLEFT", 8, gridTop); ui.scroll:SetPoint("BOTTOMRIGHT", -30, 8)
    ui.scrollBar = _G["UnboundPerksGridScrollBar"]
    ui.gridChild = CreateFrame("Frame", nil, ui.scroll)
    ui.gridChild:SetSize(GRID_W, 10)
    ui.scroll:SetScrollChild(ui.gridChild)
    ui.empty = text(mid, "GameFontDisableSmall")
    ui.empty:SetPoint("TOP", 0, gridTop - 20)
    ui.empty:SetText("No perks match your search.")

    -- details
    local d = {}
    ui.details = d
    d.none = text(right, "GameFontDisableSmall")
    d.none:SetPoint("TOP", 0, -30); d.none:SetText("Select a perk to see what it does.")
    d.content = CreateFrame("Frame", nil, right)
    d.content:SetAllPoints()
    local cnt = d.content
    d.icon = cnt:CreateTexture(nil, "ARTWORK")
    d.icon:SetSize(40, 40); d.icon:SetPoint("TOPLEFT", 18, -16)
    -- the action button frame around the icon
    local iconFrame = cnt:CreateTexture(nil, "OVERLAY")
    iconFrame:SetTexture("Interface\\Buttons\\UI-Quickslot2")
    iconFrame:SetSize(70, 70); iconFrame:SetPoint("CENTER", d.icon, "CENTER", 0, 0)
    d.name = text(cnt, "GameFontNormalLarge")
    d.name:SetPoint("TOPLEFT", d.icon, "TOPRIGHT", 12, -1); d.name:SetWidth(DETAIL_W - 76)
    d.name:SetJustifyH("LEFT")
    d.cat = text(cnt, "GameFontHighlightSmall")
    d.cat:SetPoint("TOPLEFT", d.name, "BOTTOMLEFT", 0, -3)
    d.check = cnt:CreateTexture(nil, "ARTWORK")
    d.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
    d.check:SetSize(14, 14); d.check:SetPoint("TOPLEFT", d.cat, "BOTTOMLEFT", -2, -1)
    d.state = text(cnt, "GameFontHighlightSmall")
    d.state:SetPoint("TOPLEFT", d.cat, "BOTTOMLEFT", 14, -3)

    separator(cnt, -72)
    local eh = text(cnt, "GameFontNormal")
    eh:SetPoint("TOPLEFT", 14, -82); eh:SetText("Effect")
    d.desc = text(cnt, "GameFontHighlightSmall")
    -- 3.3.5 font strings only wrap with an explicit width (two side anchors keep them on one line)
    d.desc:SetPoint("TOPLEFT", eh, "BOTTOMLEFT", 0, -6); d.desc:SetWidth(DETAIL_W - 28)
    d.desc:SetJustifyH("LEFT"); d.desc:SetJustifyV("TOP")
    d.desc:SetTextColor(unpack(C.text))
    d.note = text(cnt, "GameFontHighlightSmall")
    d.note:SetPoint("TOPLEFT", d.desc, "BOTTOMLEFT", 0, -6); d.note:SetWidth(DETAIL_W - 28)
    d.note:SetJustifyH("LEFT")
    d.note:SetTextColor(unpack(C.muted))
    d.toggle = makeButton(cnt, "Turn On", 130, function() if selectedPerk then togglePerk(selectedPerk) end end)
    d.toggle:SetHeight(24)
    d.toggle:SetPoint("BOTTOM", 0, 14)

    -- footer
    local foot = text(frame, "GameFontDisableSmall")
    foot:SetPoint("BOTTOMLEFT", 22, 16)
    foot:SetText("Up to 5 Offensive perks at a time.  Perks can't be changed in combat.  Click a perk for details; right-click or double-click to toggle it.")

    frame:SetScript("OnShow", function() PlaySound("igCharacterInfoOpen"); refresh() end)
    frame:SetScript("OnHide", function() PlaySound("igCharacterInfoClose") end)
end

-- ------------------------------------------------------------------ character sheet tab
-- A "Perks" tab after the character sheet's own tabs (Character, Pet, Reputation, Skills, Currency),
-- built from the same template. It opens the perk window beside the character sheet instead of
-- switching the sheet's page. With ElvUI's character skin on, ElvUI skins it like the other tabs.
local function elvSkins()
    if not ElvUI then return nil end
    local ok, E = pcall(function() return unpack(ElvUI) end)
    if not ok or not E or not E.private or not E.private.skins then return nil end
    local blizzard = E.private.skins.blizzard
    if not (blizzard and blizzard.enable and blizzard.character) then return nil end
    return E:GetModule("Skins", true)
end

local function addCharacterTab()
    if not CharacterFrame or _G["UnboundPerksCharacterTab"] then return end
    local tab = CreateFrame("Button", "UnboundPerksCharacterTab", CharacterFrame, "CharacterFrameTabButtonTemplate")
    tab:SetText("Perks")
    PanelTemplates_TabResize(tab, 0)
    PanelTemplates_DeselectTab(tab)

    local skins = elvSkins()
    if skins and skins.HandleTab then pcall(skins.HandleTab, skins, tab) end
    local gap = skins and -15 or -16   -- ElvUI spaces its tabs one pixel closer

    -- follow the right-most visible tab (the Pet and Currency tabs come and go)
    local function anchor()
        local last
        for i = 1, 5 do
            local t = _G["CharacterFrameTab" .. i]
            if t and t:IsShown() then last = t end
        end
        tab:ClearAllPoints()
        if last then tab:SetPoint("LEFT", last, "RIGHT", gap, 0) end
    end
    for i = 1, 5 do
        local t = _G["CharacterFrameTab" .. i]
        if t then t:HookScript("OnShow", anchor); t:HookScript("OnHide", anchor) end
    end
    CharacterFrame:HookScript("OnShow", anchor)
    anchor()

    tab:SetScript("OnClick", function()
        PlaySound("igCharacterInfoTab")
        if frame:IsShown() then
            frame:Hide()
        else
            -- open next to the character sheet
            frame:ClearAllPoints()
            frame:SetPoint("TOPLEFT", CharacterFrame, "TOPRIGHT", -28, -10)
            frame:Show()
        end
    end)
    tab:SetScript("OnEnter", function(self)
        GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
        GameTooltip:SetText("Character Perks", 1, 1, 1)
        GameTooltip:AddLine("Open or close your perks (/perks).", 1, 0.82, 0)
        GameTooltip:Show()
    end)
    tab:SetScript("OnLeave", function() GameTooltip:Hide() end)
end

-- ------------------------------------------------------------------ startup
-- Keep the live stat lines current while the window is open.
local statWatch = CreateFrame("Frame")
for _, ev in ipairs({ "UNIT_STATS", "UNIT_AURA", "UNIT_ATTACK_POWER", "COMBAT_RATING_UPDATE",
                      "PLAYER_DAMAGE_DONE_MODS", "PLAYER_EQUIPMENT_CHANGED" }) do
    statWatch:RegisterEvent(ev)
end
statWatch:SetScript("OnEvent", function(_, _, unit)
    if unit and unit ~= "player" then return end
    if frame and frame:IsShown() and selectedPerk and selectedPerk.live then updateDetails() end
end)

local loader = CreateFrame("Frame")
loader:RegisterEvent("PLAYER_LOGIN")
loader:SetScript("OnEvent", function()
    UnboundPerksDB = UnboundPerksDB or {}
    db = UnboundPerksDB
    db.active = db.active or {}
    db.loadouts = db.loadouts or { { name = "Loadout 1", perks = {} } }
    if not db.loadouts[1] then db.loadouts[1] = { name = "Loadout 1", perks = {} } end
    db.loadout = math.min(db.loadout or 1, #db.loadouts)

    buildPerkLists()
    build()
    selectCategory(categories[1] and categories[1].key)
    addCharacterTab()
    sendServer("SYNC")
end)

local comm = CreateFrame("Frame")
comm:RegisterEvent("CHAT_MSG_ADDON")
comm:SetScript("OnEvent", function(_, _, prefix, message, channel, sender)
    if prefix ~= PREFIX or channel ~= "WHISPER" or sender ~= UnitName("player") or not db then return end
    local kind, rest = string.match(message, "^(%u+):(.*)$")
    if kind == "STATE" then
        onServerState(rest)
    elseif kind == "RANK" then
        onServerRank(rest)
    elseif kind == "ERR" then
        UIErrorsFrame:AddMessage(rest, 1, 0.3, 0.3)
        if frame then setStatus(rest) end
    end
end)

SLASH_UNBOUNDPERKS1 = "/perks"
SLASH_UNBOUNDPERKS2 = "/perk"
SlashCmdList["UNBOUNDPERKS"] = function()
    if frame then setShown(frame, not frame:IsShown()) end
end
