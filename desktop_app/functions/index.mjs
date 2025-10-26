// index.mjs — unified & secure version (2025-10-26)
// ✅ HMAC based on raw bytes
// ✅ Full diagnostic logging
// ✅ Unified naming (RTDB_URL, PAIR_DEVICE_URL, PUSH_ARENA_URL)
// ✅ Compatible with Firebase Functions v2

import { onRequest } from "firebase-functions/v2/https";
import { setGlobalOptions } from "firebase-functions/v2/options";
import admin from "firebase-admin";
import crypto from "crypto";
import express from "express";
import { defineSecret } from "firebase-functions/params";

// --- Cloud Secret ---
const WOW_SECRET = defineSecret("WOW_SECRET");

// --- Global settings ---
setGlobalOptions({ region: "us-central1" });
console.log("🚀 Starting WoW Arena Notify backend...");

// --- Unified environment aliases ---
const RTDB_URL =
  process.env.FIREBASE_DATABASE_URL ||
  "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/";

const PAIR_DEVICE_URL =
  process.env.PAIR_DEVICE_URL ||
  "https://us-central1-wow-arena-notify.cloudfunctions.net/pairDevice";

const PUSH_ARENA_URL =
  process.env.PUSH_ARENA_URL ||
  "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena";

console.log("🌍 RTDB_URL       =", RTDB_URL);
console.log("🌐 PAIR_DEVICE_URL =", PAIR_DEVICE_URL);
console.log("🌐 PUSH_ARENA_URL  =", PUSH_ARENA_URL);

// --- Firebase Admin initialization ---
try {
  admin.initializeApp({
    credential: admin.credential.applicationDefault(),
    databaseURL: RTDB_URL,
  });
  console.log("🔥 Firebase Admin initialized with ADC");
} catch (err) {
  console.error("❌ Firebase Admin init failed:", err);
}

// --- Realtime Database accessor ---
let rtdb = null;
function getRTDB() {
  if (!rtdb) {
    console.log("⚙️ Initializing RTDB connection...");
    rtdb = admin.database();
  }
  return rtdb;
}

// --- Express app setup ---
const app = express();

// Capture the raw body exactly as received
app.use(
  express.raw({
    type: (req) => {
      const ct = req.headers["content-type"] || "";
      return ct.startsWith("application/json");
    },
    limit: "20kb",
  })
);

// --- Healthcheck ---
app.get("/ping", (req, res) => {
  console.log("🏓 Ping OK");
  res.json({ ok: true, ts: Date.now(), region: "us-central1" });
});

// ───────────────────────────────────────────────────────────────
// MAIN HANDLER — pushArena
// ───────────────────────────────────────────────────────────────
app.post("/", async (req, res) => {
  console.log("📩 Received pushArena POST request");

  try {
    const SERVER_SECRET = WOW_SECRET.value() || "local-dev-secret";
    const sig = req.header("X-Signature") || "";

    // --- Ensure raw body exists ---
    const rawBuffer = req.rawBody || req.body;
    if (!rawBuffer || !rawBuffer.length) {
      console.error("❌ Missing raw request body (cannot verify signature)");
      return res.status(400).json({ ok: false, error: "Missing raw body" });
    }

    // --- Log diagnostics ---
    const rawString = rawBuffer.toString("utf8");
    const byteValues = [
      ...rawBuffer.slice(0, 12),
      "...",
      ...rawBuffer.slice(-12),
    ];
    console.log("🧾 Canonical JSON:", rawString);
    console.log("📏 Body length:", rawBuffer.length);
    console.log("🔢 Byte sample:", byteValues);

    // --- HMAC verification ---
    const expected = crypto
      .createHmac("sha256", SERVER_SECRET)
      .update(rawBuffer)
      .digest("hex");

    const valid = sig === expected;
    const secretHash = crypto
      .createHash("sha256")
      .update(SERVER_SECRET)
      .digest("hex")
      .substring(0, 16);

    console.log("🧩 SECRET LENGTH:", SERVER_SECRET.length);
    console.log("🧩 SECRET HASH START:", secretHash);
    console.log("🔐 Signature valid:", valid ? "✅ OK" : "❌ INVALID");

    if (!valid) {
      console.log("🧮 Expected HMAC:", expected);
      console.log("🧮 Received HMAC:", sig);
      return res.status(401).json({ ok: false, error: "Invalid signature" });
    }

    // --- Parse payload ---
    let bodyObj;
    try {
      bodyObj = JSON.parse(rawString);
    } catch (err) {
      console.error("❌ JSON parse error:", err);
      return res.status(400).json({ ok: false, error: "Invalid JSON" });
    }

    const { pairing_id, event, start_time, duration } = bodyObj;
    if (!pairing_id || !event) {
      console.error("⚠️ Missing parameters in request:", bodyObj);
      return res
        .status(400)
        .json({ ok: false, error: "Missing parameters in request" });
    }

    // --- Write to RTDB ---
    try {
      console.log(`🧠 Writing to RTDB: /devices/${pairing_id}/arena`);
      const ref = getRTDB().ref(`/arena_events/${pairing_id}/current`);
      await ref.set({
        type: event, // Android expects "type"
        endsAt: Date.now() + parseInt(duration || 0) * 1000,
        duration,
        desktopOffset: bodyObj.desktopOffset || "0",
        server_ts: Date.now(),
      });
console.log(`✅ Event stored in /arena_events/${pairing_id}/current (${event})`);
      console.log(`✅ Event stored for ${pairing_id}: ${event}`);
      return res.json({ ok: true });
    } catch (err) {
      console.error("🔥 RTDB WRITE ERROR:", err);
      return res.status(500).json({ ok: false, error: err.message });
    }
  } catch (err) {
    console.error("🔥 UNCAUGHT ERROR in pushArena:", err);
    return res.status(500).json({ ok: false, error: err.message });
  }
});

// --- Export pushArena ---
export const pushArena = onRequest({ secrets: [WOW_SECRET] }, app);

// ───────────────────────────────────────────────────────────────
// verifySecret — debug endpoint
// ───────────────────────────────────────────────────────────────
app.get("/verifySecret", (req, res) => {
  const SERVER_SECRET = WOW_SECRET.value() || "local-dev-secret";
  const hash = crypto
    .createHash("sha256")
    .update(SERVER_SECRET)
    .digest("hex")
    .substring(0, 16);
  console.log("🔍 verifySecret called →", hash);
  res.json({
    ok: true,
    region: "us-central1",
    secretHash: hash,
    timestamp: Date.now(),
  });
});

// ───────────────────────────────────────────────────────────────
// pairDevice — creates device_secret in RTDB under /devices/<pid>
// ───────────────────────────────────────────────────────────────
export const pairDevice = onRequest(
  { secrets: [WOW_SECRET] },
  async (req, res) => {
    res.set("Access-Control-Allow-Origin", "*");
    res.set("Access-Control-Allow-Methods", "POST, OPTIONS");
    res.set("Access-Control-Allow-Headers", "Content-Type");

    if (req.method === "OPTIONS") return res.status(204).send("");
    if (req.method !== "POST")
      return res
        .status(405)
        .json({ ok: false, error: "Method not allowed" });

    const raw = req.rawBody || req.body;
    if (!raw || !raw.length) {
      console.error("❌ pairDevice: Missing raw body");
      return res.status(400).json({ ok: false, error: "Missing raw body" });
    }

    // --- Parse JSON ---
    let obj;
    try {
      const txt = Buffer.isBuffer(raw) ? raw.toString("utf8") : String(raw);
      obj = JSON.parse(txt);
    } catch (e) {
      console.error("❌ pairDevice: Invalid JSON:", e);
      return res.status(400).json({ ok: false, error: "Invalid JSON" });
    }

    const pid = (obj.pid || "").trim();
    const deviceId = (obj.deviceId || "").trim();
    if (!pid || !deviceId)
      return res
        .status(400)
        .json({ ok: false, error: "Missing pid or deviceId" });

    const MASTER = WOW_SECRET.value();
    if (!MASTER) {
      console.error("❌ pairDevice: WOW_SECRET not set in env");
      return res
        .status(500)
        .json({ ok: false, error: "Server misconfigured" });
    }

    // --- Generate device_secret ---
    const device_secret = crypto
      .createHmac("sha256", MASTER)
      .update(`${pid}:${deviceId}`)
      .digest("hex");

  // --- Write to RTDB ---
try {
  const ref = getRTDB().ref(`/devices/${pid}`);

  const payload = {
    deviceId,
    device_secret,
    fcmToken: obj.fcmToken || null,
    createdAt: Date.now(),
    version: 1,
  };

  await ref.set(payload);

  console.log("✅ pairDevice RTDB write successful:");
  console.log("📂 Path:", `/devices/${pid}`);
  console.log("📦 Payload:", payload);

  return res.status(200).json({
    ok: true,
    pairing_id: pid,
    deviceId,
    device_secret,
  });
} catch (err) {
  console.error("🔥 pairDevice RTDB write error:", err);
  return res.status(500).json({ ok: false, error: "RTDB write failed" });
}

  }
);
