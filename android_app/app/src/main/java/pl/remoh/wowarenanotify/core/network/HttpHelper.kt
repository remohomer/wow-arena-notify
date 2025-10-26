package pl.remoh.wowarenanotify.core.network

import android.util.Log
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import java.util.concurrent.TimeUnit

/**
 * 🌐 HttpHelper — universal OkHttp wrapper (v1, 2025-10-26)
 * ---------------------------------------------------------
 * ✅ Unified REST helper for all Firebase Cloud Functions.
 * ✅ Supports JSON POST & GET with timeouts and error handling.
 * ✅ Safe to call from background threads (use Thread/Coroutine).
 */
object HttpHelper {

    private const val TAG = "HttpHelper"
    private val JSON = "application/json; charset=utf-8".toMediaTypeOrNull()

    // 🔹 Shared, reusable OkHttp client
    private val client: OkHttpClient by lazy {
        OkHttpClient.Builder()
            .connectTimeout(10, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(10, TimeUnit.SECONDS)
            .build()
    }

    /**
     * Perform a simple GET request and return body as String (or null if error).
     */
    fun get(url: String): String? {
        return try {
            val request = Request.Builder()
                .url(url)
                .get()
                .build()

            client.newCall(request).execute().use { response ->
                val body = response.body?.string()
                Log.i(TAG, "GET [$url] → ${response.code}")
                if (!response.isSuccessful) {
                    Log.w(TAG, "⚠️ GET failed (${response.code}): $body")
                }
                body
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ GET request failed for $url", e)
            null
        }
    }

    /**
     * Perform a JSON POST request.
     * @param url Endpoint URL
     * @param json JSON string payload
     * @param headers Optional headers (e.g. X-Signature)
     * @return Pair(statusCode, responseBody)
     */
    fun postJson(
        url: String,
        json: String,
        headers: Map<String, String> = emptyMap()
    ): Pair<Int, String?> {
        return try {
            val body = json.toRequestBody(JSON)
            val requestBuilder = Request.Builder()
                .url(url)
                .post(body)
                .addHeader("Content-Type", "application/json; charset=utf-8")

            // custom headers (e.g. HMAC signature)
            for ((k, v) in headers) {
                requestBuilder.addHeader(k, v)
            }

            val request = requestBuilder.build()
            client.newCall(request).execute().use { response ->
                val respText = response.body?.string()
                Log.i(TAG, "POST [$url] → ${response.code}")
                if (!response.isSuccessful) {
                    Log.w(TAG, "⚠️ POST failed (${response.code}): $respText")
                }
                response.code to respText
            }
        } catch (e: Exception) {
            Log.e(TAG, "❌ POST request failed for $url", e)
            -1 to e.message
        }
    }
}
