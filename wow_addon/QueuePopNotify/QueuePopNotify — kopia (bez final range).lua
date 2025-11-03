-- =========================================================
-- QueuePopNotify v4.35 — RimFrame Edition ✅ (Stable WotLK UI)
-- WotLK 3.3.5a compatible — Confirm + Expire + Enter + Tests
-- Author: Remoh (UI cleanup by GPT-5)
-- =========================================================

local addonName = "QueuePopNotify"
local frame = CreateFrame("Frame", "QueuePopNotifyFrame")

-- ===================== DB & Defaults =====================
QueuePopNotifyDB = QueuePopNotifyDB or {
    enabled         = true,
    listening       = true,
    soundEnabled    = true,
    screenshotDelay = 2,
    rimThickness    = 2,
    selectedSound   = "ReadyCheck",
    uiErrorsEnabled = true,

    downloadLink    = "https://example.com/android",
    qr_android      = "qr_android.tga",
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

-- Blizzard WotLK SFX-safe sounds
local SOUND_LIST = {
    { key="ReadyCheck", label="ReadyCheck (default)", path="Sound\\Interface\\ReadyCheck.wav" },
    { key="RaidWarning",label="Raid Warning",         path="Sound\\Interface\\RaidWarning.wav" },
    { key="PVPFlag",    label="PVP Flag Taken",       path="Sound\\Interface\\PVPFlagTakenMono.wav" },
    { key="LevelUp",    label="Level Up",             path="Sound\\Interface\\LevelUp.wav" },
    { key="Auction",    label="Auction Won",          path="Sound\\Interface\\AuctionWindowOpen.wav" },
}

local function PlaySoundIfEnabled()
    if not QueuePopNotifyDB.soundEnabled then return end
    for _, s in ipairs(SOUND_LIST) do
        if s.key == QueuePopNotifyDB.selectedSound then
            PlaySoundFile(s.path, "SFX")
            return
        end
    end
end

local function TakeScreenshot()
    Delay(0.25, Screenshot)
    Print("Screenshot taken")
end

-- ===================== Rim Border ========================
local borders = {}
local function CreateRim(name, p1, p2, w, h)
    local f = CreateFrame("Frame", name, UIParent)
    f:SetFrameStrata("FULLSCREEN_DIALOG")
    f:SetFrameLevel(10000)
    f:EnableMouse(false)
    f:SetAlpha(1)
    f:SetPoint(p1, UIParent, p1)
    f:SetPoint(p2, UIParent, p2)
    if w then f:SetWidth(w) end
    if h then f:SetHeight(h) end
    local tex = f:CreateTexture(nil, "ARTWORK")
    tex:SetAllPoints(true)
    tex:SetTexture(1,1,1,1)
    f.tex = tex
    f:Hide()
    table.insert(borders, f)
end

CreateRim("QPN_Top",    "TOPLEFT",    "TOPRIGHT",    nil, QueuePopNotifyDB.rimThickness)
CreateRim("QPN_Bottom", "BOTTOMLEFT", "BOTTOMRIGHT", nil, QueuePopNotifyDB.rimThickness)
CreateRim("QPN_Left",   "TOPLEFT",    "BOTTOMLEFT",   QueuePopNotifyDB.rimThickness, nil)
CreateRim("QPN_Right",  "TOPRIGHT",   "BOTTOMRIGHT",  QueuePopNotifyDB.rimThickness, nil)

-- cancelable rim timer
local rimHideHandler = nil

local function QPN_ShowRim(r,g,b,dur)
    -- cancel previous hide timer
    if rimHideHandler and rimHideHandler.cancel then
        rimHideHandler.cancel()
    end

    for _,f in ipairs(borders) do
        f.tex:SetVertexColor(r,g,b,1)
        f:Show()
    end

    local container = { active = true }
    rimHideHandler = container

    Delay(dur or 3, function()
        if container.active then
            for _,f in ipairs(borders) do f:Hide() end
        end
    end)

    function container.cancel()
        container.active = false
    end
end

-- ===================== Queue detection ===================
local POLL = 0.2
local lastNotify = 0
local debounce = 5
local CONFIRM_GRACE = 1
local state = "IDLE"
local queueActive = false
local confirmLastSeen = 0
local testMode = false
local acc = 0

local function CheckQueue()
    for i = 1, MAX_BATTLEFIELD_QUEUES do
        local status, map = GetBattlefieldStatus(i)
        if status and status ~= "none" then
            return status, (map or "Arena")
        end
    end
    return "none", ""
end

local function ResetAllSoft()
    state = "IDLE"
    queueActive = false
    testMode = false
end

frame:SetScript("OnUpdate", function(_, elapsed)
    if not QueuePopNotifyDB.enabled then return end
    if not QueuePopNotifyDB.listening then return end
    if testMode then return end

    acc = acc + elapsed
    if acc < POLL then return end
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

    if state=="CONFIRM" and (GetTime()-confirmLastSeen)>=CONFIRM_GRACE then
        NotifyUI("|cffff5555POPUP EXPIRED!|r")
        Print("Popup expired")
        QPN_ShowRim(1,0,0,2.8)
        Delay(1.4,TakeScreenshot)
        ResetAllSoft()
    end
end)

-- ===================== Arena enter =======================
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

        Delay(0.15, ResetAllSoft)
    end
end)

-- ===================== Tests =============================
local function SimPopup()
    testMode=true
    state="CONFIRM"
    queueActive=true
    confirmLastSeen=GetTime()
    NotifyUI("|cff00ffffTEST Popup|r")
    QPN_ShowRim(0,1,0,3)
    Delay(1.5,TakeScreenshot)
end

local function SimArena()
    testMode=true
    state="CONFIRM"
    queueActive=true
    NotifyUI("|cff00ff00TEST ENTER|r")
    QPN_ShowRim(1,0,0,3.5)
    Delay(2.0,TakeScreenshot)
    Delay(0.15,ResetAllSoft)
end

-- ===================== Settings UI =======================
local panel = CreateFrame("Frame","QueuePopNotifyOptions",UIParent)
panel.name = addonName

local scroll = CreateFrame("ScrollFrame","QPN_Scroll",panel,"UIPanelScrollFrameTemplate")
scroll:SetPoint("TOPLEFT",0,-8)
scroll:SetPoint("BOTTOMRIGHT",-28,8)

local content = CreateFrame("Frame",nil,scroll)
content:SetSize(1,1)
scroll:SetScrollChild(content)

local y = -16

local function label(t)
    local f = content:CreateFontString(nil,"ARTWORK","GameFontNormal")
    f:SetPoint("TOPLEFT",16,y)
    f:SetText(t)
    y = y - 18
end

local function check(t)
    local name = "QPN_Check"..math.random(99999)
    local c = CreateFrame("CheckButton",name,content,"InterfaceOptionsCheckButtonTemplate")
    c:SetPoint("TOPLEFT",16,y)
    local txt=_G[name.."Text"] txt:SetText(t)
    y=y-26
    return c
end

local function addButton(w,h,t,ox,oy)
    local b = CreateFrame("Button",nil,content,"UIPanelButtonTemplate")
    b:SetSize(w,h)
    b:SetText(t)
    b:SetPoint("TOPLEFT",16+(ox or 0),(oy or y))
    return b
end

local function addEditBox(w,h,ox,oy)
    local e = CreateFrame("EditBox",nil,content,"InputBoxTemplate")
    e:SetAutoFocus(false)
    e:SetSize(w,h)
    e:SetPoint("TOPLEFT",16+(ox or 0),(oy or y))
    return e
end

local function addTexture(w,h,ox,oy)
    local t = content:CreateTexture(nil,"ARTWORK")
    t:SetSize(w,h)
    t:SetPoint("TOPLEFT",16+(ox or 0),(oy or y))
    return t
end

-- Title
local title = content:CreateFontString(nil,"ARTWORK","GameFontNormalLarge")
title:SetPoint("TOPLEFT",16,y)
title:SetText("QueuePopNotify Settings")
y=y-32

local enable = check("Enable QueuePopNotify addon")
local uiFL   = check("Show chat messages")
local sndA   = check("Enable sound alert")
y=y-8

-- Sound
label("Sound alert:")
local soundDrop = CreateFrame("Frame","QPN_SoundDrop",content,"UIDropDownMenuTemplate")
soundDrop:SetFrameStrata("HIGH")
soundDrop:SetFrameLevel(10)
soundDrop:SetPoint("TOPLEFT",16,y-4)
UIDropDownMenu_SetWidth(soundDrop,150)
UIDropDownMenu_JustifyText(soundDrop,"LEFT")
y=y-36

-- Rim thickness
label("Rim thickness (Increases screen capture detection accuracy):")
local rimSlider = CreateFrame("Slider","QPN_RimSlider",content,"OptionsSliderTemplate")
rimSlider:SetPoint("TOPLEFT",16,y)

local rimValue = content:CreateFontString(nil,"ARTWORK","GameFontHighlightSmall")
rimValue:SetPoint("LEFT", rimSlider, "RIGHT", 10, 0)
rimValue:SetText(QueuePopNotifyDB.rimThickness.."px")

rimSlider:SetMinMaxValues(2,20)
rimSlider:SetValueStep(1)
rimSlider:SetValue(QueuePopNotifyDB.rimThickness)
_G["QPN_RimSliderLow"]:SetText("2px")
_G["QPN_RimSliderHigh"]:SetText("20px")
_G["QPN_RimSliderText"]:SetText("")
y = y - 40

label("Screenshot delay (Matches delay in desktop app for queue processing):")

local slider = CreateFrame("Slider","QPN_Slider",content,"OptionsSliderTemplate")
slider:SetPoint("TOPLEFT",16,y)

local delayValue = content:CreateFontString(nil,"ARTWORK","GameFontHighlightSmall")
delayValue:SetPoint("LEFT", slider, "RIGHT", 10, 0)
delayValue:SetText(QueuePopNotifyDB.screenshotDelay.."s")

slider:SetMinMaxValues(2,5)
slider:SetValueStep(1)
slider:SetValue(QueuePopNotifyDB.screenshotDelay)
_G["QPN_SliderLow"]:SetText("2s")
_G["QPN_SliderHigh"]:SetText("5s")
_G["QPN_SliderText"]:SetText("")
y = y - 40

-- Tests
local bPop   = addButton(160,24,"TEST: Popup",0,y)
local bArena = addButton(160,24,"TEST: Enter Arena",180,y)
y=y-40

local reset = addButton(160,24,"Restore defaults",0,y)
y=y-40

-- Download
label("Download the required desktop + android app:")
local linkBox = addEditBox(300,22,0,y)
y=y-40

local qr = addTexture(128,128,0,y)
y=y-140

-- Height
content:SetHeight(-y+40)

-- Wiring UI
panel:SetScript("OnShow",function()
    enable:SetChecked(QueuePopNotifyDB.enabled)
    sndA:SetChecked(QueuePopNotifyDB.soundEnabled)
    uiFL:SetChecked(QueuePopNotifyDB.uiErrorsEnabled)

    slider:SetValue(QueuePopNotifyDB.screenshotDelay)
    rimSlider:SetValue(QueuePopNotifyDB.rimThickness)
    linkBox:SetText(QueuePopNotifyDB.downloadLink)

    qr:SetTexture("Interface\\AddOns\\QueuePopNotify\\media\\"..QueuePopNotifyDB.qr_android)
    UIDropDownMenu_SetText(soundDrop, QueuePopNotifyDB.selectedSound)
    rimValue:SetText(QueuePopNotifyDB.rimThickness.."px")
    delayValue:SetText(QueuePopNotifyDB.screenshotDelay.."s")
end)

enable:SetScript("OnClick",function(self)
    QueuePopNotifyDB.enabled=self:GetChecked()
end)

sndA:SetScript("OnClick",function(self)
    QueuePopNotifyDB.soundEnabled=self:GetChecked()
end)

uiFL:SetScript("OnClick",function(self)
    QueuePopNotifyDB.uiErrorsEnabled=self:GetChecked()
end)

slider:SetScript("OnValueChanged", function(self,v)
    QueuePopNotifyDB.screenshotDelay = v
    delayValue:SetText(v.."s")
end)

rimSlider:SetScript("OnValueChanged", function(self,v)
    QueuePopNotifyDB.rimThickness = v
    rimValue:SetText(v.."px")

    QPN_Top:SetHeight(v)
    QPN_Bottom:SetHeight(v)
    QPN_Left:SetWidth(v)
    QPN_Right:SetWidth(v)
end)

local function dropdownInit()
    local info=UIDropDownMenu_CreateInfo()
    for _,s in ipairs(SOUND_LIST) do
        info.text=s.label
        info.value=s.key
        info.func = function()
            QueuePopNotifyDB.selectedSound = s.key
            UIDropDownMenu_SetText(soundDrop, s.label)
            PlaySoundFile(s.path, "SFX")
        end
        UIDropDownMenu_AddButton(info)
    end
end

UIDropDownMenu_Initialize(soundDrop,dropdownInit)

bPop:SetScript("OnClick",SimPopup)
bArena:SetScript("OnClick",SimArena)

linkBox:SetScript("OnEnterPressed",function(self)
    QueuePopNotifyDB.downloadLink=self:GetText()
    self:ClearFocus()
end)
linkBox:SetScript("OnEscapePressed",function(self) self:ClearFocus() end)

reset:SetScript("OnClick",function()
    QueuePopNotifyDB.enabled = true
    QueuePopNotifyDB.soundEnabled=true
    QueuePopNotifyDB.uiErrorsEnabled=true
    QueuePopNotifyDB.screenshotDelay=2
    QueuePopNotifyDB.selectedSound="ReadyCheck"
    QueuePopNotifyDB.downloadLink="https://example.com/android"

    enable:SetChecked(true)
    sndA:SetChecked(true)
    uiFL:SetChecked(true)
    slider:SetValue(2)
    QueuePopNotifyDB.rimThickness = 2
    rimSlider:SetValue(2)
    QPN_Top:SetHeight(2)
    QPN_Bottom:SetHeight(2)
    QPN_Left:SetWidth(2)
    QPN_Right:SetWidth(2)
    linkBox:SetText(QueuePopNotifyDB.downloadLink)
    qr:SetTexture("Interface\\AddOns\\QueuePopNotify\\media\\"..QueuePopNotifyDB.qr_android)

    Print("Defaults restored ✓")
    UIErrorsFrame:AddMessage("|cff00ff00Defaults restored ✓|r")
end)

InterfaceOptions_AddCategory(panel)

-- ================= Slash ======================
SLASH_QUEUEPOP1="/qp"
SlashCmdList["QUEUEPOP"]=function(msg)
    msg=(msg or ""):lower()
    if msg=="testpop" then SimPopup();return end
    if msg=="testenter" then SimArena();return end
    InterfaceOptionsFrame_OpenToCategory(panel)
end
