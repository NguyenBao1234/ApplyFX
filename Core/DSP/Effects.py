"""
effects.py
----------
Các hiệu ứng âm thanh xử lý ở cấp độ mẫu (sample-level).

Mỗi effect là 1 hàm thuần túy (pure function):
  input  → np.ndarray samples (float64)
  output → np.ndarray samples (float64, cùng shape)

Danh sách:
  1. Echo       — phản âm lặp lại (delay + feedback)
  2. Reverb     — mô phỏng không gian (Schroeder reverberator)
  3. Chorus     — làm dày âm thanh (LFO modulated delay)
  4. Flanger    — chorus với delay ngắn hơn, tạo hiệu ứng whoosh
  5. Distortion — méo tín hiệu (hard/soft clip + overdrive)
"""

import numpy as np
from scipy.signal import lfilter


# ==================================================================
# UTILITY
# ==================================================================

def _apply_per_channel(samples: np.ndarray, fn) -> np.ndarray:
    """
    Áp dụng hàm xử lý fn lên từng kênh của samples.Hỗ trợ cả mono (N,) và stereo (N,2).
    """
    if samples.ndim == 1:
        return fn(samples.copy())
    else:
        left = fn(samples[:, 0].copy())
        right = fn(samples[:, 1].copy())
        return np.stack([left, right], axis=1)

# ==================================================================
# 1. ECHO
# ==================================================================

def apply_echo(samples: np.ndarray, samplerate: int,delay_ms: float = 300.0,feedback: float = 0.4,wet: float = 0.5) -> np.ndarray:
    """
    Echo đơn giản: y[n] = x[n] + feedback * y[n - delay_samples]
    Args:
        samples    : np.ndarray — (N,) or (N,2)
        samplerate : int
        delay_ms   : float — độ trễ (milliseconds), mặc định 300ms
        feedback   : float — tỉ lệ phản hồi [0,1), càng cao càng lâu tắt
        wet        : float — tỉ lệ hoà trộn [0,1]; 0=dry, 1=chỉ echo
    Returns:
        out - np.ndarray — cùng shape
    """
    delay_samples = int(samplerate * delay_ms / 1000.0)
    feedback = np.clip(feedback, 0.0, 0.95)
    wet = np.clip(wet, 0.0, 1.0)

    def _echo_channel(x: np.ndarray) -> np.ndarray:
        out = np.zeros_like(x)
        for i in range(len(x)):
            delayed = out[i - delay_samples] if i >= delay_samples else 0.0
            out[i] = x[i] + feedback * delayed
        return x * (1 - wet) + out * wet

    return _apply_per_channel(samples, _echo_channel)


# ==================================================================
# 2. REVERB — Schroeder Reverberator
# ==================================================================
# Cấu trúc: 4 Comb Filters song song → 2 Allpass Filters nối tiếp
# Tham khảo: M.R. Schroeder (1962), "Natural sounding artificial reverberation"

_COMB_DELAYS_MS = [29.7, 37.1, 41.1, 43.7]  # ms — Schroeder gốc
_ALLPASS_DELAYS_MS = [5.0, 1.7]  # ms
_ALLPASS_GAIN = 0.7


def apply_reverb(samples: np.ndarray, samplerate: int, room_size: float = 0.5, damping: float = 0.5, wet: float = 0.3) -> np.ndarray:
    """
    Reverb dùng Schroeder Reverberator.
    Args:
        room_size : float [0,1] — kích thước phòng (scale delay của comb)
        damping   : float [0,1] — hấp thụ âm thanh (low-pass trên feedback comb)
        wet       : float [0,1] — tỉ lệ wet/dry
    Returns:
        out : np.ndarray
    """
    wet = np.clip(wet, 0.0, 1.0)
    room_size = np.clip(room_size, 0.1, 1.0)
    damping = np.clip(damping, 0.0, 0.99)

    def _reverb_channel(x: np.ndarray) -> np.ndarray:
        # Scale delay theo room_size
        comb_delays = [int(d * room_size * samplerate / 1000.0)
                       for d in _COMB_DELAYS_MS]
        allpass_delays = [int(d * samplerate / 1000.0)
                          for d in _ALLPASS_DELAYS_MS]

        # --- 4 Comb Filters song song ---
        comb_out = np.zeros(len(x))
        for delay in comb_delays:
            if delay < 1:
                continue
            fb = 0.84 * room_size  # feedback gain tuỳ room_size
            comb_out += _comb_filter(x, delay, fb, damping)
        comb_out /= 4.0  # trung bình 4 comb

        # --- 2 Allpass Filters nối tiếp ---
        ap_out = comb_out
        for delay in allpass_delays:
            if delay < 1:
                continue
            ap_out = _allpass_filter(ap_out, delay, _ALLPASS_GAIN)

        return x * (1 - wet) + ap_out * wet

    return _apply_per_channel(samples, _reverb_channel)


def _comb_filter(x: np.ndarray, delay: int,
                 feedback: float, damping: float) -> np.ndarray:
    """
    Feedback Comb Filter với low-pass damping.
    y[n] = x[n] + feedback * lowpass(y[n-delay])
    """
    out = np.zeros(len(x))
    buf = np.zeros(delay)
    lp_state = 0.0
    idx = 0
    for i in range(len(x)):
        delayed = buf[idx]
        # Low-pass đơn giản: lp[n] = (1-d)*delayed + d*lp[n-1]
        lp_state = delayed * (1 - damping) + lp_state * damping
        out[i] = x[i] + feedback * lp_state
        buf[idx] = out[i]
        idx = (idx + 1) % delay
    return out


def _allpass_filter(x: np.ndarray, delay: int, gain: float) -> np.ndarray:
    """
    Allpass Filter: y[n] = -gain*x[n] + x[n-delay] + gain*y[n-delay]
    Giữ nguyên biên độ tần số, chỉ thay đổi pha → diffuse âm.
    """
    out = np.zeros(len(x))
    buf = np.zeros(delay)
    idx = 0
    for i in range(len(x)):
        delayed_in = buf[idx]
        delayed_out = out[i - delay] if i >= delay else 0.0
        out[i] = -gain * x[i] + delayed_in + gain * delayed_out
        buf[idx] = x[i]
        idx = (idx + 1) % delay
    return out


# ==================================================================
# 3. CHORUS
# ==================================================================
# LFO modulated delay: làm dày âm thanh bằng cách trộn
# bản gốc với bản bị trễ một lượng dao động theo LFO (sin)

def apply_chorus(samples: np.ndarray, samplerate: int,
                 depth_ms: float = 2.0,
                 rate_hz: float = 1.5,
                 wet: float = 0.5) -> np.ndarray:
    """
    Chorus Effect.
    Args:
        depth_ms : float — biên độ dao động delay (ms), mặc định 2ms
        rate_hz  : float — tốc độ LFO (Hz), mặc định 1.5 Hz
        wet      : float — tỉ lệ wet

    Returns:
        out - np.ndarray
    """
    wet = np.clip(wet, 0.0, 1.0)
    max_delay = int(samplerate * (depth_ms * 2 + 5) / 1000.0) + 1

    def _chorus_channel(x: np.ndarray) -> np.ndarray:
        N = len(x)
        t = np.arange(N) / samplerate
        # LFO: dao động delay từ 0 đến depth_ms
        lfo = depth_ms / 1000.0 * samplerate * (0.5 + 0.5 * np.sin(2 * np.pi * rate_hz * t))

        out = np.zeros(N)
        buf = np.zeros(max_delay + 2)
        buf_idx = 0

        for i in range(N):
            # Linear interpolation để lấy mẫu delay không nguyên
            d = lfo[i]
            d_int = int(d)
            d_frac = d - d_int

            i0 = (buf_idx - d_int) % (max_delay + 2)
            i1 = (buf_idx - d_int - 1) % (max_delay + 2)
            delayed = buf[i0] * (1 - d_frac) + buf[i1] * d_frac

            out[i] = x[i] * (1 - wet) + delayed * wet
            buf[buf_idx] = x[i]
            buf_idx = (buf_idx + 1) % (max_delay + 2)

        return out

    return _apply_per_channel(samples, _chorus_channel)


# ==================================================================
# 4. FLANGER
# ==================================================================
# Giống Chorus nhưng delay rất ngắn (0.5–5ms) → hiệu ứng "woosh/comb"

def apply_flanger(samples: np.ndarray, samplerate: int, depth_ms: float = 2.0, rate_hz: float = 0.5,
                  feedback: float = 0.5,
                  wet: float = 0.7) -> np.ndarray:
    """
    Flanger Effect.

    Parameters:
        depth_ms : float — chiều sâu delay dao động (ms)
        rate_hz  : float — tốc độ LFO (Hz)
        feedback : float — hồi tiếp tạo comb filter mạnh hơn
        wet      : float — tỉ lệ wet

    Returns:
        out - np.ndarray
    """
    wet = np.clip(wet, 0.0, 1.0)
    feedback = np.clip(feedback, -0.95, 0.95)
    max_delay = int(samplerate * (depth_ms * 2 + 2) / 1000.0) + 2

    def _flanger_channel(x: np.ndarray) -> np.ndarray:
        N = len(x)
        t = np.arange(N) / samplerate
        lfo = depth_ms / 1000.0 * samplerate * (0.5 + 0.5 * np.sin(2 * np.pi * rate_hz * t))

        out = np.zeros(N)
        buf = np.zeros(max_delay + 2)
        buf_idx = 0

        for i in range(N):
            d = lfo[i]
            d_int = int(d)
            d_frac = d - d_int

            i0 = (buf_idx - d_int) % (max_delay + 2)
            i1 = (buf_idx - d_int - 1) % (max_delay + 2)
            delayed = buf[i0] * (1 - d_frac) + buf[i1] * d_frac

            out[i] = x[i] * (1 - wet) + delayed * wet
            buf[buf_idx] = x[i] + feedback * delayed
            buf_idx = (buf_idx + 1) % (max_delay + 2)
        return out

    return _apply_per_channel(samples, _flanger_channel)

# ==================================================================
# 5. DISTORTION
# ==================================================================

def apply_distortion(samples: np.ndarray,
                     drive: float = 5.0,
                     tone: float = 0.5,
                     wet: float = 0.8,
                     mode: str = "soft") -> np.ndarray:
    """
    Distortion / Overdrive Effect.

    Parameters
    ----------
    drive : float [1, 20] — mức độ méo (1=clean, 20=heavy distortion)
    tone  : float [0, 1]  — điều chỉnh âm sắc sau méo (0=tối, 1=sáng)
    wet   : float [0, 1]  — tỉ lệ wet
    mode  : str           — "soft" (overdrive nhẹ) | "hard" (distortion cứng)
                            | "fuzz" (fuzz cực đoan)

    Returns
    -------
    out : np.ndarray
    """
    drive = np.clip(drive, 1.0, 20.0)
    wet = np.clip(wet, 0.0, 1.0)

    def _distort(x: np.ndarray) -> np.ndarray:
        # Khuếch đại trước khi méo
        driven = x * drive

        if mode == "hard":
            # Hard clip: cắt phẳng tại ±1
            clipped = np.clip(driven, -1.0, 1.0)

        elif mode == "fuzz":
            # Fuzz: sign(x) * (1 - e^(-|x|))  → gần vuông
            clipped = np.sign(driven) * (1 - np.exp(-np.abs(driven)))

        else:  # "soft" — mặc định, overdrive
            # Soft clip: arctan (mịn hơn hard clip)
            clipped = (2 / np.pi) * np.arctan(driven)

        # Tone control: low-pass đơn giản
        # tone=0 → nhiều LP (ấm), tone=1 → ít LP (sáng)
        alpha = 1 - tone * 0.8  # alpha [0.2, 1.0]
        toned = np.zeros_like(clipped)
        toned[0] = clipped[0]
        for i in range(1, len(clipped)):
            toned[i] = alpha * clipped[i] + (1 - alpha) * toned[i - 1]

        # Normalise lại về biên độ gốc
        max_amp = np.max(np.abs(toned))
        if max_amp > 1e-6:
            toned = toned / max_amp * np.max(np.abs(x))

        return x * (1 - wet) + toned * wet

    return _apply_per_channel(samples, _distort)