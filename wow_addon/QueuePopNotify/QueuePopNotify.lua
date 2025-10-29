-- =========================================================
-- QueuePopNotify v4.20 — RimFrame Edition ✅ (Improved UX)
-- WotLK 3.3.5a compatible — Confirm + Expire + Enter + Tests
-- NEW: Toggle detection + UI message checkbox + slash commands
-- Author: Remoh
-- =========================================================

local addonName = "QueuePopNotify"
local frame = CreateFrame("Frame", "QueuePopNotifyFrame")

-- State & Timers
local POLL_INTERVAL       = 0.2
local CONFIRM_LOST_GRACE  = 1.0
local lastNotify          = 0
local debounce            = 5

local state            = "IDLE"
local queueActive      = false
local confirmLastSeen  = 0
local testMode         = false

QueuePopNotifyDB = QueuePopNotifyDB or {
    soundEnabled    = true,
    screenshotDelay = 2,
    selectedSound   = "Sound\\Interface\\ReadyCheck.wav",
    uiErrorsEnabled = true,    -- ✅ NEW
    listening       = true     -- ✅ NEW
}

-------------------------------------------------------------
-- ✅ Utility
-------------------------------------------------------------
local function Print(msg)
    DEFAULT_CHAT_FRAME:AddMessage("|cff33ff99QPN:|r "..tostring(msg))
end

function Delay(sec, fn)
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

local function PlaySoundIfEnabled()
    if QueuePopNotifyDB.soundEnabled then
        PlaySoundFile(QueuePopNotifyDB.selectedSound)
    end
end

local function TakeScreenshot()
    Delay(0.2, function()
        Screenshot()
        Print("Screenshot taken")
    end)
end

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

-------------------------------------------------------------
-- ✅ FULLSCREEN RIMFRAME BORDER
-------------------------------------------------------------
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

-------------------------------------------------------------
-- 🔄 QUEUE FSM
-------------------------------------------------------------
local acc = 0
frame:SetScript("OnUpdate", function(_, elapsed)
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

-------------------------------------------------------------
-- ✅ Arena enter
-------------------------------------------------------------
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

-------------------------------------------------------------
-- 🧪 Tests
-------------------------------------------------------------
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

-------------------------------------------------------------
-- ⚙ Options Panel + NEW CHECKBOX
-------------------------------------------------------------
local panel = CreateFrame("Frame","QueuePopNotifyOptions",UIParent)
panel.name = addonName

local title = panel:CreateFontString(nil,"ARTWORK","GameFontNormalLarge")
title:SetPoint("TOPLEFT",16,-16)
title:SetText("QueuePopNotify Settings")

local soundCheck = CreateFrame("CheckButton","QPN_SoundCheck",panel,"InterfaceOptionsCheckButtonTemplate")
soundCheck:SetPoint("TOPLEFT",title,"BOTTOMLEFT",0,-20)
_G["QPN_SoundCheckText"]:SetText("Enable sound alert")

local uiMsgCheck = CreateFrame("CheckButton","QPN_UIErrorsCheck",panel,"InterfaceOptionsCheckButtonTemplate")
uiMsgCheck:SetPoint("TOPLEFT",soundCheck,"BOTTOMLEFT",0,-10)
_G["QPN_UIErrorsCheckText"]:SetText("Show UI popup messages")

local slider = CreateFrame("Slider","QPN_Slider",panel,"OptionsSliderTemplate")
slider:SetPoint("TOPLEFT",uiMsgCheck,"BOTTOMLEFT",0,-35)
slider:SetWidth(200)
slider:SetMinMaxValues(2,10)
slider:SetValueStep(1)
_G[slider:GetName().."Low"]:SetText("2s")
_G[slider:GetName().."High"]:SetText("10s")

local bp = CreateFrame("Button",nil,panel,"UIPanelButtonTemplate")
bp:SetSize(160,24)
bp:SetText("TEST: Popup")
bp:SetPoint("TOPLEFT",slider,"BOTTOMLEFT",0,-20)
bp:SetScript("OnClick",SimPopup)

local ba = CreateFrame("Button",nil,panel,"UIPanelButtonTemplate")
ba:SetSize(160,24)
ba:SetText("TEST: Enter Arena/BG")
ba:SetPoint("LEFT",bp,"RIGHT",10,0)
ba:SetScript("OnClick",SimArena)

panel:SetScript("OnShow", function()
    slider:SetValue(QueuePopNotifyDB.screenshotDelay)
    soundCheck:SetChecked(QueuePopNotifyDB.soundEnabled)
    uiMsgCheck:SetChecked(QueuePopNotifyDB.uiErrorsEnabled)
end)

soundCheck:SetScript("OnClick", function(self)
    QueuePopNotifyDB.soundEnabled=self:GetChecked()
end)

uiMsgCheck:SetScript("OnClick", function(self)
    QueuePopNotifyDB.uiErrorsEnabled=self:GetChecked()
end)

slider:SetScript("OnValueChanged", function(self,value)
    value=math.floor(value)
    QueuePopNotifyDB.screenshotDelay=value
    _G[self:GetName().."Text"]:SetText("Screenshot delay ("..value.."s)")
end)

InterfaceOptions_AddCategory(panel)

-------------------------------------------------------------
-- 📜 Slash Commands — NEW!
-------------------------------------------------------------
SLASH_QUEUEPOP1="/qp"
SlashCmdList["QUEUEPOP"] = function(msg)
    msg=msg:lower()
    if msg=="toggle" then
        QueuePopNotifyDB.listening = not QueuePopNotifyDB.listening
        Print("Listening: "..tostring(QueuePopNotifyDB.listening))
        return
    end
    if msg=="status" then
        Print("Listening: "..tostring(QueuePopNotifyDB.listening)
            .." | Sound: "..tostring(QueuePopNotifyDB.soundEnabled)
            .." | UI Msg: "..tostring(QueuePopNotifyDB.uiErrorsEnabled))
        return
    end

    InterfaceOptionsFrame_OpenToCategory(panel)
    InterfaceOptionsFrame_OpenToCategory(panel)
end
