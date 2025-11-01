-- =========================================================
-- QueuePopNotify v4.31 — RimFrame Edition ✅ (Stable WotLK UI)
-- WotLK 3.3.5a compatible — Confirm + Expire + Enter + Tests
-- FEATURES:
--  - Master toggle (Enable addon)
--  - Sound picker (cykliczny przycisk + custom filename w media/)
--  - Screenshot delay: stabilny slider (OptionsSliderTemplate)
--  - Links: 2 pola + "Place in chat" + "Copy (highlight)"
--  - QR previews 128x128 (z media/*.tga)
--  - "Show floating messages" (UIErrorsFrame)
--  - Restore defaults
--  - ScrollFrame (nic się nie rozjedzie)
-- Author: Remoh
-- =========================================================

local addonName = "QueuePopNotify"
local frame = CreateFrame("Frame", "QueuePopNotifyFrame")

-- ===================== DB & Defaults =====================
QueuePopNotifyDB = QueuePopNotifyDB or {
    enabled         = true,                 -- master toggle
    listening       = true,                 -- slash /qp toggle dla OnUpdate
    soundEnabled    = true,
    screenshotDelay = 2,                    -- 2..10
    selectedSound   = "ReadyCheck",         -- ReadyCheck / RaidWarning / Bell / LevelUp / Custom
    customSoundFile = "mysound.wav",        -- /Interface/AddOns/QueuePopNotify/media/<file>
    uiErrorsEnabled = true,                 -- "floating messages"
    desktopLink     = "https://example.com/desktop",
    androidLink     = "https://example.com/android",
    qr_desktop      = "qr_desktop.tga",     -- media/qr_desktop.tga
    qr_android      = "qr_android.tga",     -- media/qr_android.tga
}

-- ===================== Utils =============================
local function Print(msg)
    DEFAULT_CHAT_FRAME:AddMessage("|cff33ff99QPN:|r "..tostring(msg))
end

local function Delay(sec, fn)
    local f = CreateFrame("Frame")
    local start = GetTime()
    f:SetScript("OnUpdate", function(self)
        if GetTime() - start >= sec then
            self:SetScript("OnUpdate", nil)
            pcall(fn)
        end
    end)
end

local function NotifyUI(msg)
    if QueuePopNotifyDB.uiErrorsEnabled then
        UIErrorsFrame:AddMessage(msg)
    end
end

-- ✅ lista dźwięków (stabilne ścieżki 3.3.5a + Custom)
local SOUND_LIST = {
    { key="ReadyCheck", label="ReadyCheck (default)", path="Sound\\Interface\\ReadyCheck.wav" },
    { key="RaidWarning",label="RaidWarning",          path="Sound\\Interface\\RaidWarning.ogg" },
    { key="Bell",       label="Alarm Bell",           path="Sound\\Interface\\AlarmClockWarning3.ogg" },
    { key="LevelUp",    label="Level Up",             path="Sound\\Interface\\LevelUp.ogg" },
    { key="Custom",     label="Custom (media/<filename>)", path=nil },
}

local function PlaySoundIfEnabled()
    if not QueuePopNotifyDB.soundEnabled then return end
    local chosen = QueuePopNotifyDB.selectedSound or "ReadyCheck"
    for _, s in ipairs(SOUND_LIST) do
        if s.key == chosen then
            if s.key == "Custom" then
                local fname = QueuePopNotifyDB.customSoundFile or "mysound.wav"
                PlaySoundFile("Interface\\AddOns\\QueuePopNotify\\media\\"..fname)
            else
                PlaySoundFile(s.path)
            end
            return
        end
    end
    -- fallback: potraktuj chosen jako plik w media/
    PlaySoundFile("Interface\\AddOns\\QueuePopNotify\\media\\"..chosen)
end

local function TakeScreenshot()
    Delay(0.2, function()
        Screenshot()
        Print("Screenshot taken")
    end)
end

-- ===================== Fullscreen rim ====================
local BORDER_SIZE = 2
local borders = {}

local function CreateRim(name, p1, p2, w, h)
    local f = CreateFrame("Frame", name, UIParent)
    f:SetFrameStrata("FULLSCREEN_DIALOG")
    f:SetFrameLevel(10000)
    f:SetAlpha(1)
    f:EnableMouse(false)
    f:SetPoint(p1, UIParent, p1, 0, 0)
    f:SetPoint(p2, UIParent, p2, 0, 0)
    if w then f:SetWidth(w) end
    if h then f:SetHeight(h) end
    local tex = f:CreateTexture(nil, "ARTWORK")
    tex:SetAllPoints(true)
    tex:SetTexture(1,1,1,1)
    f.tex = tex
    f:Hide()
    table.insert(borders, f)
end

CreateRim("QPN_Top",    "TOPLEFT",    "TOPRIGHT",    nil, BORDER_SIZE)
CreateRim("QPN_Bottom", "BOTTOMLEFT", "BOTTOMRIGHT", nil, BORDER_SIZE)
CreateRim("QPN_Left",   "TOPLEFT",    "BOTTOMLEFT", BORDER_SIZE, nil)
CreateRim("QPN_Right",  "TOPRIGHT",   "BOTTOMRIGHT", BORDER_SIZE, nil)

local function QPN_ShowRim(r,g,b,dur)
    for _,f in ipairs(borders) do
        f.tex:SetVertexColor(r,g,b,1)
        f:Show()
    end
    Delay(dur or 3, function()
        for _,f in ipairs(borders) do f:Hide() end
    end)
end

-- ===================== Queue detection ==================
local POLL_INTERVAL       = 0.2
local CONFIRM_LOST_GRACE  = 1.0
local lastNotify          = 0
local debounce            = 5

local state            = "IDLE"
local queueActive      = false
local confirmLastSeen  = 0
local testMode         = false

local function CheckQueue()
    for i = 1, MAX_BATTLEFIELD_QUEUES do
        local status, map = GetBattlefieldStatus(i)
        if status and status ~= "none" then
            return status, (map or "Arena")
        end
    end
    return "none", nil
end

local function ResetAll()
    state = "IDLE"
    queueActive = false
    testMode = false
end

-- FSM
local acc = 0
frame:SetScript("OnUpdate", function(_, elapsed)
    if not QueuePopNotifyDB.enabled then return end
    if not QueuePopNotifyDB.listening then return end
    if testMode then return end

    acc = acc + elapsed
    if acc < POLL_INTERVAL then return end
    acc = 0

    local now = time()
    local status, map = CheckQueue()

    if status == "confirm" then
        confirmLastSeen = GetTime()
        if state ~= "CONFIRM" then
            state="CONFIRM"
            queueActive=true

            if (now-lastNotify)>debounce then
                lastNotify=now
                PlaySoundIfEnabled()
                NotifyUI("|cff00ff00Arena/BG POPPED → "..map.."|r")
                Print("Queue popped for "..map)

                QPN_ShowRim(0,1,0,QueuePopNotifyDB.screenshotDelay+1.2)
                Delay(QueuePopNotifyDB.screenshotDelay, TakeScreenshot)
            end
        end
        return
    end

    if state=="CONFIRM" and (GetTime()-confirmLastSeen)>=CONFIRM_LOST_GRACE then
        NotifyUI("|cffff5555POPUP EXPIRED!|r")
        Print("Popup expired")
        QPN_ShowRim(1,0,0,2.8)
        Delay(1.4, TakeScreenshot)
        ResetAll()
    end
end)

-- ===================== Arena enter ======================
local function IsArena()
    local inst, typ = IsInInstance()
    if inst and typ=="arena" then return true end
    if IsActiveBattlefieldArena and IsActiveBattlefieldArena() then return true end
    return false
end

frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:RegisterEvent("ZONE_CHANGED_NEW_AREA")
frame:SetScript("OnEvent", function()
    if queueActive and IsArena() then
        NotifyUI("|cff00ff00ENTER ARENA ✅|r")
        Print("ENTER ARENA ✅")
        QPN_ShowRim(1,0,0,3.5)
        Delay(2.5, TakeScreenshot)
        ResetAll()
    end
end)

-- ===================== Tests ============================
local function SimPopup()
    testMode=true
    state="CONFIRM"
    queueActive=true
    confirmLastSeen=GetTime()
    NotifyUI("|cff00ffffTEST Popup|r")
    Print("TEST Queue Popup")
    QPN_ShowRim(0,1,0,3)
    Delay(1.5,TakeScreenshot)
end

local function SimArena()
    testMode=true
    state="CONFIRM"
    queueActive=true
    NotifyUI("|cff00ff00TEST ENTER|r")
    Print("TEST Enter Arena/BG")
    QPN_ShowRim(1,0,0,3.5)
    Delay(2.0,TakeScreenshot)
    ResetAll()
end

-- ===================== Settings UI ======================
-- Layout UX:
-- 1) Enable addon
-- 2) Detection (sound on/off, floating msg, screenshot delay + sound picker)
-- 3) Download links + QR (128x128)
-- 4) Test buttons
-- 5) Restore defaults
-----------------------------------------------------------

local panel = CreateFrame("Frame","QueuePopNotifyOptions",UIParent)
panel.name = addonName

-- Scroll (żeby nic się nie rozjechało)
local scrollFrame = CreateFrame("ScrollFrame", "QPN_Scroll", panel, "UIPanelScrollFrameTemplate")
scrollFrame:SetPoint("TOPLEFT", panel, "TOPLEFT", 0, -8)
scrollFrame:SetPoint("BOTTOMRIGHT", panel, "BOTTOMRIGHT", -28, 8)

local content = CreateFrame("Frame", nil, scrollFrame)
content:SetSize(1, 1)
scrollFrame:SetScrollChild(content)

local y = -16

local function addTitle(text)
    local t = content:CreateFontString(nil,"ARTWORK","GameFontNormalLarge")
    t:SetPoint("TOPLEFT", 16, y)
    t:SetText(text)
    y = y - 28
    return t
end

local function addCheck(label, anchorY)
    local name = "QPN_Check"..math.random(100000)
    local check = CreateFrame("CheckButton", name, content, "InterfaceOptionsCheckButtonTemplate")
    check:SetPoint("TOPLEFT", 16, anchorY or y)
    local txt = _G[name.."Text"]
    if txt then txt:SetText(label) end
    y = (anchorY or y) - 26
    return check
end

local function addLabel(text, anchorY)
    local l = content:CreateFontString(nil,"ARTWORK","GameFontNormal")
    l:SetPoint("TOPLEFT", 16, anchorY or y)
    l:SetText(text)
    y = (anchorY or y) - 18
    return l
end

-- 🔧 PROSTA, BEZBŁĘDNA WERSJA SLIDERA (WotLK 3.3.5a)
-- Sygnatura: addSlider(min, max, step, labelText, anchorY)
local function addSlider(min, max, step, labelText, anchorY)
    local name = "QPN_Slider"..math.random(100000)
    local s = CreateFrame("Slider", name, content, "OptionsSliderTemplate")
    s:SetPoint("TOPLEFT", 16, anchorY or y)
    s:SetWidth(200)
    s:SetHeight(16)

    s:SetOrientation("HORIZONTAL")
    s:SetMinMaxValues(min, max)
    s:SetValueStep(step or 1)

    local current = QueuePopNotifyDB.screenshotDelay or min
    if current < min then current = min end
    if current > max then current = max end
    s:SetValue(current)

    local low  = _G[name.."Low"]
    local high = _G[name.."High"]
    local txt  = _G[name.."Text"]

    if low  then low:SetText(tostring(min).."s") end
    if high then high:SetText(tostring(max).."s") end
    if txt  then txt:SetText((labelText or "Value").." ("..current.."s)") end

    y = (anchorY or y) - 52
    return s, txt
end

local function addButton(w,h,text, ox, oy)
    local b = CreateFrame("Button", nil, content, "UIPanelButtonTemplate")
    b:SetSize(w,h)
    b:SetText(text)
    b:SetPoint("TOPLEFT", 16+(ox or 0), (oy or y))
    y = (oy or y) - (h+8)
    return b
end

local function addEditBox(width, height, ox, oy, multiline)
    local eb = CreateFrame("EditBox", nil, content, "InputBoxTemplate")
    eb:SetAutoFocus(false)
    if multiline then eb:SetMultiLine(true) end
    eb:SetSize(width, height)
    eb:SetPoint("TOPLEFT", 16+(ox or 0), (oy or y))
    y = (oy or y) - (height+10)
    return eb
end

local function addTexture(w, h, ox, oy)
    local t = content:CreateTexture(nil, "ARTWORK")
    t:SetSize(w,h)
    t:SetPoint("TOPLEFT", 16+(ox or 0), (oy or y))
    return t
end

-- ---- 1) Title
addTitle("QueuePopNotify Settings")

-- ---- 1) Enable addon
local enableCheck = addCheck("Enable QueuePopNotify addon")

-- ---- 2) Detection
local soundCheck = addCheck("Enable sound alert")
local uiMsgCheck = addCheck("Show floating messages")

local delayLabel = addLabel("Screenshot delay:", y)
local slider, sliderText = addSlider(2, 10, 1, "Screenshot delay")

-- Sound picker (cykliczny button)
local soundLabel = addLabel("Sound:", y)
local soundBtn = addButton(180, 22, "Sound: ReadyCheck", 0, y+2)
-- Custom filename input + test
local customInput = addEditBox(180, 22, 200, y+24, false)
customInput:SetText(QueuePopNotifyDB.customSoundFile or "mysound.wav")
local testSoundBtn = addButton(90, 22, "Play test", 0, y)

-- ---- 3) Download section
addLabel("Download links (select or use buttons to copy):", y-6)

local desktopEdit = addEditBox(420, 40, 0, y, true)
local placeDesktopBtn = addButton(170, 22, "Place desktop link in chat", 0, y+6)
local copyDesktopBtn  = addButton(170, 22, "Copy (highlight) desktop", 180, y+28)

local androidEdit = addEditBox(420, 40, 0, y, true)
local placeAndroidBtn = addButton(170, 22, "Place android link in chat", 0, y+6)
local copyAndroidBtn  = addButton(170, 22, "Copy (highlight) android", 180, y+28)

-- QR previews (128x128)
addLabel("QR previews:", y-2)
local qrDesktopTex = addTexture(128,128, 0, y-6)
local qrAndroidTex = addTexture(128,128, 148, y-6)
y = y - 140

-- ---- 4) Test buttons
local bp = addButton(160, 24, "TEST: Popup", 0, y)
local ba = addButton(160, 24, "TEST: Enter Arena/BG", 170, y+24)

-- ---- 5) Restore defaults
local resetBtn = addButton(160, 24, "↩️ Restore defaults", 0, y)

-- Spacer
y = y - 16
content:SetHeight(-y + 20)

-- ============== UI Behaviours / Wiring ==================

panel:SetScript("OnShow", function()
    enableCheck:SetChecked(QueuePopNotifyDB.enabled)
    soundCheck:SetChecked(QueuePopNotifyDB.soundEnabled)
    uiMsgCheck:SetChecked(QueuePopNotifyDB.uiErrorsEnabled)

    slider:SetValue(QueuePopNotifyDB.screenshotDelay or 2)
    if sliderText then sliderText:SetText("Screenshot delay ("..(QueuePopNotifyDB.screenshotDelay or 2).."s)") end

    -- Sound label
    local chosen = QueuePopNotifyDB.selectedSound or "ReadyCheck"
    local label = chosen
    for _, s in ipairs(SOUND_LIST) do
        if s.key == chosen then label = s.label; break end
    end
    soundBtn:SetText("Sound: "..label)

    customInput:SetText(QueuePopNotifyDB.customSoundFile or "mysound.wav")

    desktopEdit:SetText(QueuePopNotifyDB.desktopLink or "")
    androidEdit:SetText(QueuePopNotifyDB.androidLink or "")

    qrDesktopTex:SetTexture("Interface\\AddOns\\QueuePopNotify\\media\\" .. (QueuePopNotifyDB.qr_desktop or "qr_desktop.tga"))
    qrAndroidTex:SetTexture("Interface\\AddOns\\QueuePopNotify\\media\\" .. (QueuePopNotifyDB.qr_android or "qr_android.tga"))
end)

enableCheck:SetScript("OnClick", function(self)
    QueuePopNotifyDB.enabled = self:GetChecked()
    Print("Addon enabled: "..(QueuePopNotifyDB.enabled and "ON" or "OFF"))
end)

soundCheck:SetScript("OnClick", function(self)
    QueuePopNotifyDB.soundEnabled = self:GetChecked()
    Print("Sound: "..(QueuePopNotifyDB.soundEnabled and "ON" or "OFF"))
end)

uiMsgCheck:SetScript("OnClick", function(self)
    QueuePopNotifyDB.uiErrorsEnabled = self:GetChecked()
    Print("Floating messages: "..(QueuePopNotifyDB.uiErrorsEnabled and "ON" or "OFF"))
end)

slider:SetScript("OnValueChanged", function(self, value)
    value = math.floor(value or 2)
    if value < 2 then value = 2 end
    if value > 10 then value = 10 end
    QueuePopNotifyDB.screenshotDelay = value
    if sliderText then sliderText:SetText("Screenshot delay ("..value.."s)") end
end)

-- 🔊 Cykl dźwięków przy każdym kliknięciu (Zero-problemów w 3.3.5a)
local soundIndex = 1
local function updateSoundBtnFromDB()
    local key = QueuePopNotifyDB.selectedSound or "ReadyCheck"
    for i, s in ipairs(SOUND_LIST) do
        if s.key == key then
            soundIndex = i
            local lab = s.label
            if s.key == "Custom" then
                lab = "Custom ("..(QueuePopNotifyDB.customSoundFile or "mysound.wav")..")"
            end
            soundBtn:SetText("Sound: "..lab)
            return
        end
    end
    -- jeśli nic nie znaleziono:
    QueuePopNotifyDB.selectedSound = "ReadyCheck"
    soundBtn:SetText("Sound: ReadyCheck (default)")
end
updateSoundBtnFromDB()

soundBtn:SetScript("OnClick", function()
    soundIndex = soundIndex + 1
    if soundIndex > #SOUND_LIST then soundIndex = 1 end
    local s = SOUND_LIST[soundIndex]
    QueuePopNotifyDB.selectedSound = s.key
    local lab = s.label
    if s.key == "Custom" then
        lab = "Custom ("..(QueuePopNotifyDB.customSoundFile or "mysound.wav")..")"
    end
    soundBtn:SetText("Sound: "..lab)
end)

testSoundBtn:SetScript("OnClick", function()
    local custom = customInput:GetText() or ""
    if custom ~= "" then
        QueuePopNotifyDB.customSoundFile = custom
    end
    PlaySoundIfEnabled()
end)

customInput:SetScript("OnEnterPressed", function(self)
    local v = self:GetText() or ""
    QueuePopNotifyDB.customSoundFile = v
    if (QueuePopNotifyDB.selectedSound or "ReadyCheck") == "Custom" then
        soundBtn:SetText("Sound: Custom ("..v..")")
    end
    self:ClearFocus()
end)
customInput:SetScript("OnEscapePressed", function(self)
    self:ClearFocus()
end)

-- Helpers do copy / place in chat
local function placeInChat(text)
    text = text or ""
    if text == "" then
        Print("No link provided")
        return
    end
    local eb = ChatFrame1EditBox
    if eb then
        eb:SetText(text)
        eb:SetFocus()
        eb:HighlightText()
        Print("Link placed in chat. Press Ctrl+C to copy.")
    else
        Print("Unable to access chat edit box; copy manually.")
    end
end

local function copyHighlight(editBox)
    local txt = (editBox:GetText() or "")
    if txt == "" then
        Print("No link provided")
        return
    end
    editBox:SetFocus()
    editBox:HighlightText()
    Print("Highlighted. Press Ctrl+C to copy.")
end

placeDesktopBtn:SetScript("OnClick", function()
    local txt = desktopEdit:GetText() or ""
    QueuePopNotifyDB.desktopLink = txt
    placeInChat(txt)
end)
copyDesktopBtn:SetScript("OnClick", function()
    QueuePopNotifyDB.desktopLink = desktopEdit:GetText() or ""
    copyHighlight(desktopEdit)
end)

placeAndroidBtn:SetScript("OnClick", function()
    local txt = androidEdit:GetText() or ""
    QueuePopNotifyDB.androidLink = txt
    placeInChat(txt)
end)
copyAndroidBtn:SetScript("OnClick", function()
    QueuePopNotifyDB.androidLink = androidEdit:GetText() or ""
    copyHighlight(androidEdit)
end)

-- Enter/Escape na polach z linkami
local function bindCommit(eb, key)
    eb:SetScript("OnEnterPressed", function(self)
        local v = self:GetText() or ""
        QueuePopNotifyDB[key] = v
        self:ClearFocus()
    end)
    eb:SetScript("OnEscapePressed", function(self)
        self:ClearFocus()
    end)
end
bindCommit(desktopEdit, "desktopLink")
bindCommit(androidEdit, "androidLink")

-- Defaults
resetBtn:SetScript("OnClick", function()
    QueuePopNotifyDB.enabled         = true
    QueuePopNotifyDB.listening       = true
    QueuePopNotifyDB.soundEnabled    = true
    QueuePopNotifyDB.screenshotDelay = 2
    QueuePopNotifyDB.selectedSound   = "ReadyCheck"
    QueuePopNotifyDB.customSoundFile = "mysound.wav"
    QueuePopNotifyDB.uiErrorsEnabled = true
    QueuePopNotifyDB.desktopLink     = "https://example.com/desktop"
    QueuePopNotifyDB.androidLink     = "https://example.com/android"
    QueuePopNotifyDB.qr_desktop      = "qr_desktop.tga"
    QueuePopNotifyDB.qr_android      = "qr_android.tga"

    enableCheck:SetChecked(true)
    soundCheck:SetChecked(true)
    uiMsgCheck:SetChecked(true)
    slider:SetValue(2)
    if sliderText then sliderText:SetText("Screenshot delay (2s)") end

    updateSoundBtnFromDB()
    customInput:SetText("mysound.wav")
    desktopEdit:SetText(QueuePopNotifyDB.desktopLink)
    androidEdit:SetText(QueuePopNotifyDB.androidLink)
    qrDesktopTex:SetTexture("Interface\\AddOns\\QueuePopNotify\\media\\"..QueuePopNotifyDB.qr_desktop)
    qrAndroidTex:SetTexture("Interface\\AddOns\\QueuePopNotify\\media\\"..QueuePopNotifyDB.qr_android)

    Print("Defaults restored ✓")
    UIErrorsFrame:AddMessage("|cff00ff00Defaults restored ✓|r")
end)

-- Tooltips
soundBtn:SetScript("OnEnter", function(self)
    GameTooltip:SetOwner(self, "ANCHOR_RIGHT")
    GameTooltip:AddLine("Select sound to play on popup.")
    GameTooltip:AddLine("Custom uses: Interface/AddOns/QueuePopNotify/media/<filename>")
    GameTooltip:Show()
end)
soundBtn:SetScript("OnLeave", function() GameTooltip:Hide() end)

-- Rejestracja panelu
InterfaceOptions_AddCategory(panel)

-- ================== Slash Commands ======================
SLASH_QUEUEPOP1="/qp"
SlashCmdList["QUEUEPOP"] = function(msg)
    msg = (msg or ""):lower()
    if msg == "toggle" then
        QueuePopNotifyDB.listening = not QueuePopNotifyDB.listening
        Print("Listening: "..(QueuePopNotifyDB.listening and "ON" or "OFF"))
        return
    elseif msg == "status" then
        Print("Enabled: "..(QueuePopNotifyDB.enabled and "ON" or "OFF")
            .." | Listening: "..(QueuePopNotifyDB.listening and "ON" or "OFF")
            .." | Sound: "..(QueuePopNotifyDB.soundEnabled and "ON" or "OFF")
            .." | Floating msg: "..(QueuePopNotifyDB.uiErrorsEnabled and "ON" or "OFF"))
        return
    elseif msg == "testpop" then
        SimPopup(); return
    elseif msg == "testenter" then
        SimArena(); return
    end
    InterfaceOptionsFrame_OpenToCategory(panel)
    InterfaceOptionsFrame_OpenToCategory(panel) -- Blizzard quirk
end

-- end of file
