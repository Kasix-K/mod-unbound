-- Unbound Perks: the Character Perks window (/perks).
-- UI only for now: toggles and loadouts are saved per character in UnboundPerksDB. The server side
-- (perks actually doing something) is added later and will read the same perk ids.

local P = UnboundPerks

-- ------------------------------------------------------------------ colours (navy + gold theme)
local C = {
    bg        = { 0.035, 0.045, 0.075, 0.97 },
    panel     = { 0.055, 0.070, 0.110, 0.96 },
    border    = { 0.20, 0.30, 0.46, 1 },
    borderHi  = { 0.42, 0.58, 0.85, 1 },
    gold      = { 1.00, 0.82, 0.30 },
    text      = { 0.90, 0.92, 0.96 },
    muted     = { 0.52, 0.58, 0.68 },
    rowHover  = { 0.11, 0.15, 0.23, 0.85 },
    rowSel    = { 0.15, 0.23, 0.37, 0.95 },
    btn       = { 0.09, 0.13, 0.21, 1 },
    btnHover  = { 0.14, 0.21, 0.34, 1 },
    on        = { 1.00, 0.82, 0.30 },
    off       = { 0.22, 0.25, 0.31 },
    active    = { 0.35, 0.85, 0.45 },
}

local WHITE = "Interface\\Buttons\\WHITE8X8"
local ROW_H, CAT_H = 22, 26
local FRAME_W, FRAME_H = 880, 620
local DETAIL_W = 300

local function backdrop(f, bg, border)
    f:SetBackdrop({ bgFile = WHITE, edgeFile = WHITE, edgeSize = 1, insets = { left = 1, right = 1, top = 1, bottom = 1 } })
    f:SetBackdropColor(unpack(bg))
    f:SetBackdropBorderColor(unpack(border or C.border))
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
local filtered = {}      -- perks shown in the middle list
local catRows, perkRows = {}, {}
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
            local c = { key = cat.key, name = cat.name, color = cat.color }
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
local function makeButton(parent, label, width, onClick)
    local b = CreateFrame("Button", nil, parent)
    b:SetSize(width, 22)
    backdrop(b, C.btn)
    b.label = text(b, "GameFontNormalSmall")
    b.label:SetPoint("CENTER")
    b.label:SetText(label)
    b.label:SetTextColor(unpack(C.gold))
    b:SetScript("OnEnter", function(self)
        self:SetBackdropColor(unpack(C.btnHover)); self:SetBackdropBorderColor(unpack(C.borderHi))
    end)
    b:SetScript("OnLeave", function(self)
        self:SetBackdropColor(unpack(C.btn)); self:SetBackdropBorderColor(unpack(C.border))
    end)
    b:SetScript("OnMouseDown", function(self) self.label:SetPoint("CENTER", 1, -1) end)
    b:SetScript("OnMouseUp", function(self) self.label:SetPoint("CENTER", 0, 0) end)
    b:SetScript("OnClick", function() PlaySound("igMainMenuOptionCheckBoxOn"); onClick() end)
    return b
end

local function makeEditBox(parent, width)
    local e = CreateFrame("EditBox", nil, parent)
    e:SetSize(width, 22)
    e:SetAutoFocus(false)
    e:SetFontObject(ChatFontSmall)
    e:SetTextInsets(6, 6, 0, 0)
    e:SetTextColor(unpack(C.text))
    backdrop(e, { 0.02, 0.03, 0.05, 1 })
    e:SetScript("OnEscapePressed", function(self) self:ClearFocus() end)
    e:SetScript("OnEditFocusGained", function(self) self:SetBackdropBorderColor(unpack(C.borderHi)) end)
    e:SetScript("OnEditFocusLost", function(self) self:SetBackdropBorderColor(unpack(C.border)) end)
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

local function onServerState(list)
    local on = {}
    for id in string.gmatch(list, "%d+") do on[tonumber(id)] = true end
    for _, perk in ipairs(P.PERKS) do
        if perk.works and not perk.permanent then db.active[perk.id] = on[perk.id] end
    end
    if refresh then refresh() end
end

local function togglePerk(perk)
    if perk.permanent then return end
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
            row.bar:SetVertexColor(unpack(c.color))
            row.name:SetText(c.name)
            row.count:SetText(activeCount(c.key) .. "/" .. #perksByCat[c.key])
            if c.key == selectedCat then
                row:SetBackdropColor(unpack(C.rowSel))
                row.name:SetTextColor(1, 1, 1)
            else
                row:SetBackdropColor(0, 0, 0, 0)
                row.name:SetTextColor(unpack(C.text))
            end
            row:Show()
        else
            row:Hide()
        end
    end
end

local function updatePerkList()
    local offset = FauxScrollFrame_GetOffset(ui.scroll)
    for i, row in ipairs(perkRows) do
        local perk = filtered[i + offset]
        if perk then
            row.perk = perk
            row.name:SetText(perk.name)
            row.box:SetVertexColor(unpack(isOn(perk) and C.on or C.off))
            if perk == selectedPerk then
                row:SetBackdropColor(unpack(C.rowSel))
                row.name:SetTextColor(1, 1, 1)
            else
                row:SetBackdropColor(0, 0, 0, 0)
                row.name:SetTextColor(unpack(isOn(perk) and C.text or C.muted))
            end
            row:Show()
        else
            row:Hide()
        end
    end
    FauxScrollFrame_Update(ui.scroll, #filtered, #perkRows, ROW_H)
    setShown(ui.empty, #filtered == 0)
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
    d.accent:SetVertexColor(unpack(c.color))
    if perk.permanent then
        d.state:SetText("Always Active"); d.state:SetTextColor(unpack(C.active)); d.check:Show()
        d.toggle:Hide()
    elseif isOn(perk) then
        d.state:SetText("Active"); d.state:SetTextColor(unpack(C.active)); d.check:Show()
        d.toggle.label:SetText("Turn Off"); d.toggle:Show()
    else
        d.state:SetText("Inactive"); d.state:SetTextColor(unpack(C.muted)); d.check:Hide()
        d.toggle.label:SetText("Turn On"); d.toggle:Show()
    end
    local body = perk.desc or ""
    if perk.live then
        local ok, line = pcall(perk.live)
        if ok and line then body = body .. (perk.liveInline and "\n" or "\n\n") .. line end
    end
    if perk.pets then
        body = body .. "\n\n|cff8a94a8This perk also works for your pets.|r"
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
    updatePerkList()
    updateDetails()
    updateLoadoutBar()
    loadoutStatus()
end

local function selectCategory(key)
    selectedCat = key
    ui.search:SetText("")
    FauxScrollFrame_SetOffset(ui.scroll, 0)
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
    backdrop(frame, C.bg, C.borderHi)
    frame:Hide()
    tinsert(UISpecialFrames, "UnboundPerksFrame") -- Escape closes it

    -- header glow
    local glow = frame:CreateTexture(nil, "BORDER")
    glow:SetTexture(WHITE)
    glow:SetPoint("TOPLEFT", 1, -1); glow:SetPoint("TOPRIGHT", -1, -1); glow:SetHeight(56)
    glow:SetGradientAlpha("VERTICAL", 0.10, 0.16, 0.28, 0, 0.16, 0.24, 0.42, 0.55)

    local icon = frame:CreateTexture(nil, "ARTWORK")
    icon:SetSize(36, 36)
    icon:SetPoint("TOPLEFT", 14, -12)
    icon:SetTexture("Interface\\Icons\\Achievement_General")
    icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    local iconBorder = CreateFrame("Frame", nil, frame)
    iconBorder:SetPoint("TOPLEFT", icon, -1, 1); iconBorder:SetPoint("BOTTOMRIGHT", icon, 1, -1)
    iconBorder:SetBackdrop({ edgeFile = WHITE, edgeSize = 1 })
    iconBorder:SetBackdropBorderColor(unpack(C.gold))

    local title = text(frame, "GameFontNormalLarge")
    title:SetPoint("TOPLEFT", icon, "TOPRIGHT", 10, -2)
    title:SetText("Character Perks")
    title:SetTextColor(unpack(C.gold))
    local sub = text(frame, "GameFontHighlightSmall")
    sub:SetPoint("TOPLEFT", title, "BOTTOMLEFT", 0, -3)
    sub:SetText("Toggle perks on to gain their power")
    sub:SetTextColor(unpack(C.muted))

    local close = makeButton(frame, "X", 22, function() frame:Hide() end)
    close:SetPoint("TOPRIGHT", -10, -10)
    close.label:SetTextColor(1, 0.35, 0.3)

    separator(frame, -58, 1, 1)

    -- loadout bar
    local bar = makePanel(frame)
    bar:SetPoint("TOPLEFT", 12, -66); bar:SetPoint("TOPRIGHT", -12, -66); bar:SetHeight(36)
    local lbl = text(bar, "GameFontNormalSmall")
    lbl:SetPoint("LEFT", 10, 0); lbl:SetText("LOADOUT"); lbl:SetTextColor(unpack(C.gold))

    ui.drop = CreateFrame("Frame", "UnboundPerksLoadoutDropDown", bar, "UIDropDownMenuTemplate")
    ui.drop:SetPoint("LEFT", lbl, "RIGHT", -8, -2)
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

    ui.nameBox = makeEditBox(bar, 150)
    ui.nameBox:SetPoint("LEFT", ui.drop, "RIGHT", -6, 2)
    ui.nameBox:SetScript("OnEnterPressed", doRename)

    local apply = makeButton(bar, "Apply", 72, doApply)
    apply:SetPoint("LEFT", ui.nameBox, "RIGHT", 10, 0)
    local save = makeButton(bar, "Save", 72, doSave)
    save:SetPoint("LEFT", apply, "RIGHT", 6, 0)
    local rename = makeButton(bar, "Rename", 72, doRename)
    rename:SetPoint("LEFT", save, "RIGHT", 6, 0)
    local delete = makeButton(bar, "Delete", 72, doDelete)
    delete:SetPoint("LEFT", rename, "RIGHT", 6, 0)

    ui.status = text(bar, "GameFontHighlightSmall")
    ui.status:SetPoint("RIGHT", -10, 0)
    ui.status:SetTextColor(unpack(C.muted))

    -- three panels
    local top, bottom = -110, 28
    local left = makePanel(frame)
    left:SetPoint("TOPLEFT", 12, top); left:SetPoint("BOTTOMLEFT", 12, bottom); left:SetWidth(176)
    local right = makePanel(frame)
    right:SetPoint("TOPRIGHT", -12, top); right:SetPoint("BOTTOMRIGHT", -12, bottom); right:SetWidth(DETAIL_W)
    local mid = makePanel(frame)
    mid:SetPoint("TOPLEFT", left, "TOPRIGHT", 10, 0); mid:SetPoint("BOTTOMRIGHT", right, "BOTTOMLEFT", -10, 0)

    -- categories
    local ch = text(left, "GameFontNormalSmall")
    ch:SetPoint("TOPLEFT", 10, -10); ch:SetText("CATEGORIES"); ch:SetTextColor(unpack(C.gold))
    separator(left, -26)
    for i = 1, #P.CATEGORIES do
        local row = CreateFrame("Button", nil, left)
        row:SetHeight(CAT_H)
        row:SetPoint("TOPLEFT", 4, -32 - (i - 1) * (CAT_H + 2))
        row:SetPoint("TOPRIGHT", -4, -32 - (i - 1) * (CAT_H + 2))
        row:SetBackdrop({ bgFile = WHITE })
        row:SetBackdropColor(0, 0, 0, 0)
        row.bar = row:CreateTexture(nil, "ARTWORK")
        row.bar:SetTexture(WHITE); row.bar:SetWidth(3)
        row.bar:SetPoint("TOPLEFT"); row.bar:SetPoint("BOTTOMLEFT")
        row.name = text(row, "GameFontHighlightSmall"); row.name:SetPoint("LEFT", 12, 0)
        row.count = text(row, "GameFontNormalSmall"); row.count:SetPoint("RIGHT", -8, 0)
        row.count:SetTextColor(unpack(C.gold))
        row:SetScript("OnEnter", function(self)
            if self.cat and self.cat.key ~= selectedCat then self:SetBackdropColor(unpack(C.rowHover)) end
        end)
        row:SetScript("OnLeave", function(self)
            if self.cat and self.cat.key ~= selectedCat then self:SetBackdropColor(0, 0, 0, 0) end
        end)
        row:SetScript("OnClick", function(self)
            PlaySound("igMainMenuOptionCheckBoxOn")
            selectCategory(self.cat.key)
        end)
        catRows[i] = row
    end

    -- search
    ui.search = makeEditBox(mid, 10)
    ui.search:SetPoint("TOPLEFT", 10, -10); ui.search:SetPoint("TOPRIGHT", -10, -10)
    local hint = text(ui.search, "GameFontDisableSmall")
    hint:SetPoint("LEFT", 8, 0); hint:SetText("Search all perks...")
    ui.search:SetScript("OnTextChanged", function(self)
        setShown(hint, self:GetText() == "" and not self:HasFocus())
        FauxScrollFrame_SetOffset(ui.scroll, 0); ui.scroll:SetVerticalScroll(0)
        if frame:IsShown() then refresh() end
    end)
    ui.search:HookScript("OnEditFocusGained", function() hint:Hide() end)
    ui.search:HookScript("OnEditFocusLost", function(self) setShown(hint, self:GetText() == "") end)

    -- perk list
    local listTop = -40
    ui.scroll = CreateFrame("ScrollFrame", "UnboundPerksScroll", mid, "FauxScrollFrameTemplate")
    ui.scroll:SetPoint("TOPLEFT", 6, listTop); ui.scroll:SetPoint("BOTTOMRIGHT", -30, 8)
    ui.scroll:SetScript("OnVerticalScroll", function(self, offset)
        FauxScrollFrame_OnVerticalScroll(self, offset, ROW_H, updatePerkList)
    end)
    local visible = math.floor((FRAME_H - 110 - 28 - 40 - 8) / ROW_H)
    for i = 1, visible do
        local row = CreateFrame("Button", nil, mid)
        row:SetHeight(ROW_H)
        row:SetPoint("TOPLEFT", 6, listTop - (i - 1) * ROW_H)
        row:SetPoint("TOPRIGHT", -30, listTop - (i - 1) * ROW_H)
        row:SetBackdrop({ bgFile = WHITE })
        row:SetBackdropColor(0, 0, 0, 0)
        row.boxBtn = CreateFrame("Button", nil, row)
        row.boxBtn:SetSize(16, 16); row.boxBtn:SetPoint("LEFT", 4, 0)
        row.box = row.boxBtn:CreateTexture(nil, "ARTWORK")
        row.box:SetTexture(WHITE); row.box:SetSize(9, 9); row.box:SetPoint("CENTER")
        row.boxBtn:SetScript("OnClick", function() togglePerk(row.perk) end)
        row.name = text(row, "GameFontHighlightSmall"); row.name:SetPoint("LEFT", 24, 0)
        row:SetScript("OnEnter", function(self)
            if self.perk ~= selectedPerk then self:SetBackdropColor(unpack(C.rowHover)) end
        end)
        row:SetScript("OnLeave", function(self)
            if self.perk ~= selectedPerk then self:SetBackdropColor(0, 0, 0, 0) end
        end)
        row:SetScript("OnClick", function(self) selectedPerk = self.perk; refresh() end)
        row:SetScript("OnDoubleClick", function(self) togglePerk(self.perk) end)
        perkRows[i] = row
    end
    ui.empty = text(mid, "GameFontDisableSmall")
    ui.empty:SetPoint("TOP", 0, listTop - 20)
    ui.empty:SetText("No perks match your search.")

    -- details
    local d = {}
    ui.details = d
    d.none = text(right, "GameFontDisableSmall")
    d.none:SetPoint("TOP", 0, -30); d.none:SetText("Select a perk to see what it does.")
    d.content = CreateFrame("Frame", nil, right)
    d.content:SetAllPoints()
    local cnt = d.content
    d.accent = cnt:CreateTexture(nil, "ARTWORK")
    d.accent:SetTexture(WHITE); d.accent:SetWidth(3)
    d.accent:SetPoint("TOPLEFT", 10, -10); d.accent:SetHeight(48)
    d.icon = cnt:CreateTexture(nil, "ARTWORK")
    d.icon:SetSize(40, 40); d.icon:SetPoint("TOPLEFT", 20, -14)
    d.icon:SetTexCoord(0.07, 0.93, 0.07, 0.93)
    d.name = text(cnt, "GameFontNormal")
    d.name:SetPoint("TOPLEFT", d.icon, "TOPRIGHT", 10, -1); d.name:SetWidth(DETAIL_W - 70)
    d.name:SetJustifyH("LEFT")
    d.name:SetTextColor(unpack(C.gold))
    d.cat = text(cnt, "GameFontHighlightSmall")
    d.cat:SetPoint("TOPLEFT", d.name, "BOTTOMLEFT", 0, -3)
    d.check = cnt:CreateTexture(nil, "ARTWORK")
    d.check:SetTexture("Interface\\Buttons\\UI-CheckBox-Check")
    d.check:SetSize(14, 14); d.check:SetPoint("TOPLEFT", d.cat, "BOTTOMLEFT", -2, -1)
    d.state = text(cnt, "GameFontHighlightSmall")
    d.state:SetPoint("TOPLEFT", d.cat, "BOTTOMLEFT", 14, -3)

    separator(cnt, -72)
    local eh = text(cnt, "GameFontNormalSmall")
    eh:SetPoint("TOPLEFT", 12, -84); eh:SetText("EFFECT"); eh:SetTextColor(unpack(C.gold))
    d.desc = text(cnt, "GameFontHighlightSmall")
    -- 3.3.5 font strings only wrap with an explicit width (two side anchors keep them on one line)
    d.desc:SetPoint("TOPLEFT", eh, "BOTTOMLEFT", 0, -6); d.desc:SetWidth(DETAIL_W - 24)
    d.desc:SetJustifyH("LEFT"); d.desc:SetJustifyV("TOP")
    d.desc:SetTextColor(unpack(C.text))
    d.note = text(cnt, "GameFontHighlightSmall")
    d.note:SetPoint("TOPLEFT", d.desc, "BOTTOMLEFT", 0, -6); d.note:SetWidth(DETAIL_W - 24)
    d.note:SetJustifyH("LEFT")
    d.note:SetTextColor(unpack(C.muted))
    d.toggle = makeButton(cnt, "Turn On", 120, function() if selectedPerk then togglePerk(selectedPerk) end end)
    d.toggle:SetPoint("BOTTOM", 0, 14)

    -- footer
    local foot = text(frame, "GameFontDisableSmall")
    foot:SetPoint("BOTTOMLEFT", 14, 9)
    foot:SetText("Perks can't be changed in combat.  Click a square or double-click a perk to toggle it.")

    frame:SetScript("OnShow", function() PlaySound("igCharacterInfoOpen"); refresh() end)
    frame:SetScript("OnHide", function() PlaySound("igCharacterInfoClose") end)
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
    sendServer("SYNC")
end)

local comm = CreateFrame("Frame")
comm:RegisterEvent("CHAT_MSG_ADDON")
comm:SetScript("OnEvent", function(_, _, prefix, message, channel, sender)
    if prefix ~= PREFIX or channel ~= "WHISPER" or sender ~= UnitName("player") or not db then return end
    local kind, rest = string.match(message, "^(%u+):(.*)$")
    if kind == "STATE" then
        onServerState(rest)
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
