package pl.remoh.wowarenanotify.core

import android.content.Context

object SettingsManager {
    private const val PREFS_NAME = "wow_arena_settings"
    private const val KEY_NOTIFICATIONS = "notifications_enabled"
    private const val KEY_VIBRATION = "vibration_enabled"
    private const val KEY_SOUNDS = "sounds_enabled"
    private const val KEY_FINAL_SECONDS = "final_seconds"
    private const val KEY_BACKGROUND_ENABLED = "background_enabled"

    fun isNotificationsEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_NOTIFICATIONS, true)

    fun isVibrationEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_VIBRATION, true)

    fun isSoundsEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_SOUNDS, true)

    fun getFinalSeconds(context: Context): Int =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getInt(KEY_FINAL_SECONDS, 10)

    fun setNotificationsEnabled(context: Context, value: Boolean) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_NOTIFICATIONS, value).apply()

    fun setVibrationEnabled(context: Context, value: Boolean) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_VIBRATION, value).apply()

    fun setSoundsEnabled(context: Context, value: Boolean) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_SOUNDS, value).apply()

    fun setFinalSeconds(context: Context, value: Int) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putInt(KEY_FINAL_SECONDS, value).apply()

    fun isBackgroundEnabled(context: Context): Boolean =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .getBoolean(KEY_BACKGROUND_ENABLED, true)

    fun setBackgroundEnabled(context: Context, value: Boolean) =
        context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
            .edit().putBoolean(KEY_BACKGROUND_ENABLED, value).apply()
}
