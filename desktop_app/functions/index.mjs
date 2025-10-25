// index.mjs — stable version with full HMAC + byte logging
import { onRequest } from "firebase-functions/v2/https";
import { setGlobalOptions } from "firebase-functions/v2/options";
import admin from "firebase-admin";
import crypto from "crypto";
import express from "express";

// --- Global settings ---
setGlobalOptions({ region: "us-central1" });

console.log("🚀 Starting pushArena function...");

// --- Firebase Admin initialization ---
const databaseURL =
  process.env.FIREBASE_DATABASE_URL ||
  "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/";

try {
  admin.initializeApp({
    credential: admin.credential.applicationDefault(),
    databaseURL,
  });
  console.log("🔥 Firebase Admin initialized (with ADC)");
} catch (err) {
  console.error("❌ Firebase Admin init failed:", err);
}

let rtdb = null;
function getRTDB() {
  if (!rtdb) {
    console.log("⚙️ Initializing RTDB connection...");
    rtdb = admin.database();
  }
  return rtdb;
}

const app = express();

// --- Capture raw body exactly as received ---
app.use(
  express.json({
    limit: "20kb",
    verify: (req, res, buf) => {
      req.rawBody = buf;
    },
  })
);

// --- Simple healthcheck ---
app.get("/ping", (req, res) => {
  console.log("🏓 Ping OK");
  res.json({ ok: true, ts: Date.now() });
});

// --- Main pushArena handler ---
app.post("/", async (req, res) => {
  console.log("📩 Received pushArena POST request");

  const SERVER_SECRET = process.env.WOW_SECRET || "local-dev-secret";
  const sig = req.header("X-Signature") || "";

  // --- Raw body validation ---
  if (!req.rawBody) {
    console.error("❌ Missing rawBody (cannot verify signature)");
    return res.status(400).json({ ok: false, error: "Missing rawBody" });
  }

  // --- Decode raw string ---
  const rawString = req.rawBody.toString("utf8");
  const rawBytes = Buffer.from(rawString, "utf8");
  const byteValues = [...rawBytes.slice(0, 12), "...", ...rawBytes.slice(-12)];
  console.log("🧾 Canonical JSON:", rawString);
  console.log("📏 Body length:", rawBytes.length);
  console.log("🔢 Byte sample:", byteValues);

  // --- HMAC verification ---
  const expected = crypto.createHmac("sha256", SERVER_SECRET).update(rawString).digest("hex");
  const valid = sig === expected;
  const secretHash = crypto.createHash("sha256").update(SERVER_SECRET).digest("hex").substring(0, 16);

  console.log("🧩 SECRET LENGTH:", SERVER_SECRET.length);
  console.log("🧩 SECRET HASH START:", secretHash);
  console.log("🔐 Signature valid:", valid ? "✅ OK" : "❌ INVALID");

  if (!valid) {
    console.log("🧮 Expected HMAC:", expected);
    console.log("🧮 Received HMAC:", sig);
    return res.status(401).json({ ok: false, error: "Invalid signature" });
  }

  // --- Parse payload ---
  const { pairing_id, event, start_time, duration } = req.body;
  if (!pairing_id || !event) {
    console.error("⚠️ Missing parameters in request:", req.body);
    return res.status(400).json({ ok: false, error: "Missing parameters" });
  }

  // --- Write to RTDB ---
  try {
    console.log(`🧠 Writing to RTDB: /devices/${pairing_id}/arena`);
    const ref = getRTDB().ref(`/devices/${pairing_id}/arena`);
    await ref.set({
      event,
      start_time,
      duration,
      server_ts: Date.now(),
    });
    console.log(`✅ Event stored for ${pairing_id}: ${event}`);
    return res.json({ ok: true });
  } catch (err) {
    console.error("🔥 RTDB WRITE ERROR:", err);
    return res.status(500).json({ ok: false, error: err.message });
  }
});

// --- Export for Firebase ---
export const pushArena = onRequest(app);
