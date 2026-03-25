"""
filters.py
----------
Các bộ lọc Biquad IIR xử lý tín hiệu âm thanh ở cấp độ mẫu (sample-level).

Lý thuyết Biquad IIR (dạng Direct Form II Transposed):
  Mỗi bộ lọc được mô tả bằng 5 hệ số: b0, b1, b2, a1, a2
  (a0 đã chuẩn hoá = 1)

  Phương trình sai phân:
    y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2]
           - a1*y[n-1] - a2*y[n-2]

  Dùng scipy.signal.sosfilt để áp dụng filter ổn định hơn dạng ba hệ số,
  tránh vấn đề numerical instability ở order cao.

Các loại filter được cài:
  - Low Shelf  → chỉnh BASS  (tăng/giảm toàn bộ dải tần thấp)
  - Peaking EQ → chỉnh MID   (tăng/giảm dải tần giữa theo bell curve)
  - High Shelf → chỉnh HI    (tăng/giảm toàn bộ dải tần cao)
  - Volume     → nhân biên độ đơn giản (không phải filter, nhưng đặt ở đây cho gọn)
"""

import numpy as np
from scipy.signal import sosfilt, sosfilt_zi


# ------------------------------------------------------------------
# Helper: chuyển b/a coefficients → SOS (Second-Order Sections)
# ------------------------------------------------------------------

def _ba_to_sos(b: list[float], a: list[float]) -> np.ndarray:
    """
    Chuyển hệ số [b0,b1,b2], [a0,a1,a2] sang định dạng SOS.
    SOS shape: (1, 6) = [[b0, b1, b2, 1, a1, a2]]
    (a0 đã chuẩn hoá = 1, scipy dùng dấu dương cho a1,a2)
    """
    b0, b1, b2 = b # thực hiện việc unpackin, lấy số đầu tiên trong danh sách b gán cho biến b0, số thứ hai cho b1, và số thứ ba cho b2
    a0, a1, a2 = a
    # Chuẩn hoá theo a0
    return np.array([[b0/a0, b1/a0, b2/a0, 1.0, a1/a0, a2/a0]])


# ------------------------------------------------------------------
# 1. LOW SHELF FILTER — BASS, shelf như 1 cái kệ, thềm, khác với cut xoá bỏ
# ------------------------------------------------------------------

def design_low_shelf(gain_db: float, fs: int,
                     f0: float = 200.0, S: float = 1.0) -> np.ndarray:
    """
    Thiết kế Low Shelf Filter (Audio EQ Cookbook — Robert Bristow-Johnson).

    Args:
        gain_db : float — độ khuếch đại (dương=boost, âm=cut), VD: +6.0, -3.0
        fs      : int   — sample rate (Hz)
        f0      : float — tần số shelf (Hz), mặc định 200 Hz
        S       : float — độ dốc shelf (1.0 = dốc chuẩn)
    Returns:
        sos : np.ndarray shape (1,6) — dùng với sosfilt()
    """
    A  = 10 ** (gain_db / 40.0)          # sqrt(10^(dB/20))
    w0 = 2 * np.pi * f0 / fs
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha  = sin_w0 / 2 * np.sqrt((A + 1/A) * (1/S - 1) + 2)

    b0 =     A * ((A+1) - (A-1)*cos_w0 + 2*np.sqrt(A)*alpha)
    b1 = 2 * A * ((A-1) - (A+1)*cos_w0)
    b2 =     A * ((A+1) - (A-1)*cos_w0 - 2*np.sqrt(A)*alpha)
    a0 =          (A+1) + (A-1)*cos_w0 + 2*np.sqrt(A)*alpha
    a1 =    -2 * ((A-1) + (A+1)*cos_w0)
    a2 =          (A+1) + (A-1)*cos_w0 - 2*np.sqrt(A)*alpha

    return _ba_to_sos([b0, b1, b2], [a0, a1, a2])


# ------------------------------------------------------------------
# 2. PEAKING EQ FILTER — MID,  hàm Peaking này giống như một cái "núi" / "thung lũng", khác với shelf cái thềm
# ------------------------------------------------------------------

def design_peaking(gain_db: float, fs: int,
                   f0: float = 1000.0, Q: float = 1.0) -> np.ndarray:
    """
    Thiết kế Peaking EQ Filter (bell curve). bộ lọc hình chuông

    Args:
        gain_db : float — độ khuếch đại tại f0;
        fs      : int   — sample rate (Hz);
        f0      : float — tần số trung tâm (Hz), mặc định 1000 Hz (giọng hát);
        Q       : float — bandwidth (Q cao = dải hẹp, Q thấp = dải rộng);
    Returns:
        sos : np.ndarray shape (1,6)
    """
    A  = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / fs
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha  = sin_w0 / (2 * Q)

    b0 =  1 + alpha * A
    b1 = -2 * cos_w0
    b2 =  1 - alpha * A
    a0 =  1 + alpha / A
    a1 = -2 * cos_w0
    a2 =  1 - alpha / A

    return _ba_to_sos([b0, b1, b2], [a0, a1, a2])


# ------------------------------------------------------------------
# 3. HIGH SHELF FILTER — HI / TREBLE
# ------------------------------------------------------------------

def design_high_shelf(gain_db: float, fs: int,
                      f0: float = 8000.0, S: float = 1.0) -> np.ndarray:
    """
    Thiết kế High Shelf Filter.

    Args:
        gain_db : float — độ khuếch đại;
        fs      : int   — sample rate (Hz);
        f0      : float — tần số shelf (Hz), mặc định 8000 Hz;
        S       : float — độ dốc shelf;
    Returns:
        sos - np.ndarray shape (1,6)
    """
    A  = 10 ** (gain_db / 40.0)
    w0 = 2 * np.pi * f0 / fs
    cos_w0 = np.cos(w0)
    sin_w0 = np.sin(w0)
    alpha  = sin_w0 / 2 * np.sqrt((A + 1/A) * (1/S - 1) + 2)

    b0 =     A * ((A+1) + (A-1)*cos_w0 + 2*np.sqrt(A)*alpha)
    b1 = -2 * A * ((A-1) + (A+1)*cos_w0)
    b2 =     A * ((A+1) + (A-1)*cos_w0 - 2*np.sqrt(A)*alpha)
    a0 =          (A+1) - (A-1)*cos_w0 + 2*np.sqrt(A)*alpha
    a1 =     2 * ((A-1) - (A+1)*cos_w0)
    a2 =          (A+1) - (A-1)*cos_w0 - 2*np.sqrt(A)*alpha

    return _ba_to_sos([b0, b1, b2], [a0, a1, a2])


# ------------------------------------------------------------------
# 4. Equalizer APPLY FILTERS lên audio data
# ------------------------------------------------------------------

def apply_eq(samples: np.ndarray, samplerate: int,
             bass_db: float = 0.0,
             mid_db: float  = 0.0,
             hi_db: float   = 0.0) -> np.ndarray:
    """
    Áp dụng chuỗi 3 bộ lọc EQ lên samples.

    Xử lý từng kênh độc lập nếu stereo.
    Thứ tự: Low Shelf → Peaking → High Shelf

    Args:
        samples    : np.ndarray — (N,) mono hoặc (N,2) stereo, float64
        samplerate : int
        bass_db    : float — gain dB cho dải trầm
        mid_db     : float — gain dB cho dải giữa
        hi_db      : float — gain dB cho dải cao

    Returns:
        out - np.ndarray — cùng shape với samples
    """
    # Thiết kế các filter
    sos_bass = design_low_shelf(bass_db,  samplerate)
    sos_mid  = design_peaking(mid_db,     samplerate)
    sos_hi   = design_high_shelf(hi_db,   samplerate)

    def _process_channel(x: np.ndarray) -> np.ndarray:
        x = sosfilt(sos_bass, x)
        x = sosfilt(sos_mid,  x)
        x = sosfilt(sos_hi,   x)
        return x

    if samples.ndim == 1:
        out = _process_channel(samples.copy())
    else:
        # Stereo: xử lý từng kênh
        left  = _process_channel(samples[:, 0])
        right = _process_channel(samples[:, 1])
        out   = np.stack([left, right], axis=1)

    return out


# ------------------------------------------------------------------
# 5. VOLUME — nhân biên độ
# ------------------------------------------------------------------

def apply_volume(samples: np.ndarray, volume: float) -> np.ndarray:
    """
    Điều chỉnh âm lượng đầu ra.

    Args:
        samples : np.ndarray — dữ liệu âm thanh
        volume  : float      — hệ số khuếch đại tuyến tính (0.0 = im lặng, 1.0 = gốc, 2.0 = +6dB)
    """
    return samples * np.clip(volume, 0.0, 4.0)


# ------------------------------------------------------------------
# 6. VOLUME từ dB sang linear (tiện dụng cho UI)
# ------------------------------------------------------------------

def db_to_linear(db: float) -> float:
    """Chuyển dB → hệ số tuyến tính. VD: 0 dB → 1.0, +6 dB → ~2.0"""
    return 10 ** (db / 20.0)


def linear_to_db(linear: float) -> float:
    """Chuyển hệ số tuyến tính → dB. Tránh log(0)."""
    linear = max(linear, 1e-10)
    return 20 * np.log10(linear)