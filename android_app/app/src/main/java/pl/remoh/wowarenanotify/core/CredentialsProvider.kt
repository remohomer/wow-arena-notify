package pl.remoh.wowarenanotify.core

class CredentialsProvider {
    fun getRtdbUrl(): String =
        "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"

    fun getPushArenaUrl(): String =
        "https://us-central1-wow-arena-notify.cloudfunctions.net/pushArena"

    fun getPairDeviceUrl(): String =
        "https://us-central1-wow-arena-notify.cloudfunctions.net/pairDevice"
}
