package pl.remoh.wowarenanotify.fcm

import android.util.Log
import com.google.firebase.database.*

object TimeSync {
    var firebaseOffsetMs: Long = 0
        private set

    fun start() {
        try {
            val db = FirebaseDatabase.getInstance(
                "https://wow-arena-notify-default-rtdb.europe-west1.firebasedatabase.app/"
            )
            val offsetRef = db.getReference(".info/serverTimeOffset")

            offsetRef.addValueEventListener(object : ValueEventListener {
                override fun onDataChange(snapshot: DataSnapshot) {
                    firebaseOffsetMs = snapshot.getValue(Long::class.java) ?: 0L
                    Log.w("TimeSync", "🕒 Firebase offset updated: $firebaseOffsetMs ms")
                }

                override fun onCancelled(error: DatabaseError) {
                    Log.w("TimeSync", "⚠ Failed to read offset: ${error.message}")
                }
            })
        } catch (e: Exception) {
            Log.e("TimeSync", "❌ Error initializing TimeSync", e)
        }
    }
}
