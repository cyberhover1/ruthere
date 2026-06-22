package com.ruthere.app.ui.screens.friends

import android.graphics.Bitmap
import androidx.core.graphics.createBitmap
import androidx.core.graphics.set
import com.google.zxing.BarcodeFormat
import com.google.zxing.qrcode.QRCodeWriter

/** Encode a string into a square QR code Bitmap using zxing-core. */
fun generateQrBitmap(content: String, size: Int = 600): Bitmap {
    val bits = QRCodeWriter().encode(content, BarcodeFormat.QR_CODE, size, size)
    val bmp = createBitmap(size, size)
    for (x in 0 until size) {
        for (y in 0 until size) {
            bmp[x, y] = if (bits[x, y]) 0xFF000000.toInt() else 0xFFFFFFFF.toInt()
        }
    }
    return bmp
}
