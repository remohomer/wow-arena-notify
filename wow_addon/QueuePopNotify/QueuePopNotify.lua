local frame = CreateFrame("Frame")
local lastNotify = 0
local debounce = 5
local screenshotDelay = 3
local pollInterval = 0.2
local waitingForScreenshot = false
local queueActive = false

QueuePopNotifyDB = QueuePopNotifyDB or {}
QueuePopNotifyDB.soundEnabled = (QueuePopNotifyDB.soundEnabled ~= false)

SLASH_QUEUEPOP1 = "/qp"
SlashCmdList["QUEUEPOP"] = function(msg)
    msg = msg:lower()
    if msg == "sound on" then
        QueuePopNotifyDB.soundEnabled = true
        print("|cff33ff99QueuePopNotify:|r Sound enabled.")
    elseif msg == "sound off" then
        QueuePopNotifyDB.soundEnabled = false
        print("|cff33ff99QueuePopNotify:|r Sound disabled.")
    else
        print("|cff33ff99QueuePopNotify Commands:|r")
        print("  /qp sound on  - enable arena popup sound")
        print("  /qp sound off - disable arena popup sound")
    end
end

local function Delay(seconds, func)
    local f = CreateFrame("Frame")
    local start = GetTime()
    f:SetScript("OnUpdate", function(self)
        if GetTime() - start >= seconds then
            self:SetScript("OnUpdate", nil)
            func()
        end
    end)
end

local function CheckBattlefieldNow()
    for i = 1, MAX_BATTLEFIELD_QUEUES do
        local status, mapName = GetBattlefieldStatus(i)
        if status == "confirm" then
            return true, mapName or "Battlefield"
        end
    end
    return false, nil
end

local function ResetQueueState()
    waitingForScreenshot = false
    queueActive = false
    lastNotify = 0
end

local function TakeScreenshot()
    print("|cff33ff99QueuePopNotify:|r Taking screenshot now...")
    Screenshot()
end

local prevHasConfirm = false

frame:SetScript("OnUpdate", function(self, elapsed)
    frame.lastPoll = (frame.lastPoll or 0) + elapsed
    if frame.lastPoll < pollInterval then return end
    frame.lastPoll = 0

    local now = time()
    if now - lastNotify < debounce then return end

    local hasConfirm, name = CheckBattlefieldNow()

    -- 🟢 1️⃣ Nowy popup – zaczynamy countdown
    if hasConfirm and not waitingForScreenshot then
        waitingForScreenshot = true
        queueActive = true
        prevHasConfirm = true
        lastNotify = now

        if QueuePopNotifyDB.soundEnabled then
            PlaySoundFile("Sound\\Interface\\ReadyCheck.wav")
        end

        UIErrorsFrame:AddMessage("Queue popped for " .. name .. "! (screenshot in " .. screenshotDelay .. "s)", 1, 1, 0, 53, 5)
        print("|cff33ff99QueuePopNotify:|r Detected queue pop for:", name)
        Delay(screenshotDelay, TakeScreenshot)

    -- 🔴 2️⃣ Popup zniknął (timeout, brak wejścia)
    elseif not hasConfirm and prevHasConfirm then
        -- Potwierdzenie, że wcześniej było confirm, a teraz nie ma
        print("|cff33ff99QueuePopNotify:|r Queue popup expired — creating timeout screenshot.")
        TakeScreenshot()
        ResetQueueState()
        prevHasConfirm = false
    end

    -- Aktualizacja stanu „czy wcześniej był popup”
    prevHasConfirm = hasConfirm
end)

frame:RegisterEvent("PLAYER_ENTERING_WORLD")
frame:RegisterEvent("BATTLEFIELD_QUEUE_TIMEOUT")
frame:RegisterEvent("BATTLEFIELD_CANCEL")

frame:SetScript("OnEvent", function(_, event)
    if event == "PLAYER_ENTERING_WORLD" or event == "BATTLEFIELD_QUEUE_TIMEOUT" or event == "BATTLEFIELD_CANCEL" then
        if queueActive then
            TakeScreenshot()  -- dodatkowy screenshot przy wejściu na arene/BG lub anulowaniu
        end
        ResetQueueState()
        print("|cff33ff99QueuePopNotify:|r Queue reset (" .. event .. ")")
    end
end)
