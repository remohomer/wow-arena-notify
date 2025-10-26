package pl.remoh.wowarenanotify.core

import android.content.Context
import android.util.Log

object ConfigHelper {
    private const val PREFS_NAME = "wow_arena_prefs"
    private const val TAG = "ConfigHelper"

    fun getPairingId(context: Context): String? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val id = prefs.getString("pairing_id", null)
        Log.i(TAG, "🔍 getPairingId() = $id")
        return id
    }

    fun getDeviceId(context: Context): String? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val id = prefs.getString("device_id", null)
        Log.i(TAG, "🔍 getDeviceId() = $id")
        return id
    }

    fun getDesktopId(context: Context): String? {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val id = prefs.getString("desktop_id", null)
        Log.i(TAG, "🔍 getDesktopId() = $id")
        return id
    }

    fun savePairingId(context: Context, pairingId: String, deviceId: String? = null) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().apply {
            putString("pairing_id", pairingId)
            if (!deviceId.isNullOrEmpty()) putString("device_id", deviceId)
            apply()
        }
        Log.i(TAG, "💾 savePairingId() saved pairing_id=$pairingId, device_id=$deviceId")
    }

    fun saveDesktopId(context: Context, desktopId: String) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().putString("desktop_id", desktopId).apply()
        Log.i(TAG, "💾 saveDesktopId() = $desktopId")
    }

    fun clearAll(context: Context) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        prefs.edit().clear().apply()
        Log.i(TAG, "🧹 Cleared all pairing preferences")
    }
}
