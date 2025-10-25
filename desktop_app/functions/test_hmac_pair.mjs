// test_hmac_pair.mjs
import crypto from "crypto";

// ten sam klucz
const secret = "73b5abc506edd15dbae2a0fc1569cdbf8c391e4e59ebd8f2f8c5ac418581d123";

// dokładnie ten sam payload
const payload = {
  schema: "1",
  type: "arena_pop",
  eventId: "12345",
  endsAt: "1761390245304",
  duration: "40",
  sentAtMs: "1761390205304",
  desktopOffset: "0",
};

// funkcja canonicalizacji (sortuje klucze i generuje JSON identyczny jak w Pythonie)
function canonicalize(obj) {
  return JSON.stringify(
    Object.keys(obj)
      .sort()
      .reduce((acc, k) => {
        acc[k] = obj[k];
        return acc;
      }, {}),
    null,
    0
  );
}

const msg = canonicalize(payload);
const signature = crypto.createHmac("sha256", secret).update(msg).digest("hex");

console.log("NODE CANONICAL JSON:");
console.log(msg);
console.log("\nNode HMAC:", signature);
