package pl.remoh.wowarenanotify

import android.content.Context
import android.util.Log
import androidx.work.Worker
import androidx.work.WorkerParameters

class HeartbeatWorker(context: Context, workerParams: WorkerParameters) :
    Worker(context, workerParams) {

    override fun doWork(): Result {
        Log.d("HeartbeatWorker", "💓 Heartbeat ping sent at ${System.currentTimeMillis()}")
        // Tutaj możesz np. wysłać request do Firebase lub backendu
        return Result.success()
    }
}
