"""
processor.py
------------
DSP Processor — lớp trung tâm kết hợp tất cả bộ xử lý.

Thứ tự xử lý chuẩn (signal chain):
  1. EQ       : Bass (Low Shelf) → Mid (Peaking) → Hi (High Shelf)
  2. Effect   : Echo / Reverb / Chorus / Flanger / Distortion
  3. Pan      : Stereo Panning
  4. Volume   : Điều chỉnh âm lượng đầu ra cuối cùng

Đây là "trái tim" DSP của app. UI chỉ cần gọi:
    processor.set_param("bass", 6.0)
    output = processor.process(raw_samples)
"""

import numpy as np

from Core.DSP.Effects import apply_echo, apply_reverb, apply_chorus, apply_flanger, apply_distortion
from Core.DSP.Filters import apply_eq, apply_volume
from Core.DSP.Pan import apply_pan

# ------------------------------------------------------------------
# Giá trị mặc định
# ------------------------------------------------------------------
DEFAULT_PARAMS: dict = {
    # EQ (dB)
    "bass"  : 0.0,
    "mid"   : 0.0,
    "hi"    : 0.0,
    # Volume
    "vol"   : 1.0,    # linear gain (1.0 = 0 dB)
    # Echo (tỉ lệ 0–1, map sang delay_ms và feedback trong process)
    "echo"  : 0.0,    # 0=tắt, 1=max
    # Pan
    "pan"   : 0.0,    # -1 left … 0 center … +1 right
    # Effect hiện tại
    "effect": None,   # str hoặc None
    "effect_params": {},
}

# Map tên echo 0–1 → delay_ms và feedback
_ECHO_MAX_DELAY_MS = 500.0
_ECHO_MAX_FEEDBACK = 0.7


class DSPProcessor:
    """
    Quản lý trạng thái tham số DSP và áp dụng chúng lên samples.

    Attributes
    ----------
    params      : dict — bản sao hiện tại của các tham số
    samplerate  : int  — cần biết để thiết kế filter
    """

    def __init__(self, samplerate: int = 44100):
        self.samplerate = samplerate
        self.params: dict = DEFAULT_PARAMS.copy()
        self.params["effect_params"] = {}

    # ------------------------------------------------------------------
    # Cập nhật tham số
    # ------------------------------------------------------------------

    def set_param(self, key: str, value) -> None:
        """
        Cập nhật 1 tham số.
        Args:
            key   : str — tên tham số ("bass", "mid", "hi", "vol",
                                       "echo", "pan", "effect", "effect_params")
            value : any — giá trị mới
        """
        if key not in self.params and key != "effect_params":
            raise KeyError(f"Tham số không hợp lệ: '{key}'")
        self.params[key] = value

    def set_effect(self, effect_name: str | None,
                   effect_params: dict | None = None) -> None:
        """
        Đặt effect hiện tại và tham số của nó.

        Args:
            effect_name   : str | None — "echo","reverb","chorus",
                                     "flanger","distortion", hoặc None
            effect_params : dict | None — tham số riêng của effect
        """
        self.params["effect"] = effect_name
        self.params["effect_params"] = effect_params or {}

    def load_preset(self, preset) -> None:
        """
        Nạp toàn bộ preset vào params.
        Args:
             preset : object từ presets.py

        """
        eq = preset.eq
        self.params["vol"]   = eq.get("vol",  1.0)
        self.params["bass"]  = eq.get("bass", 0.0)
        self.params["mid"]   = eq.get("mid",  0.0)
        self.params["hi"]    = eq.get("hi",   0.0)
        self.params["echo"]  = eq.get("echo", 0.0)
        self.params["pan"]   = preset.pan
        self.params["effect"] = preset.effect
        self.params["effect_params"] = preset.effect_params.copy()

    def get_slider_values(self) -> dict:
        """
        Trả về dict các giá trị hiện tại cho UI sliders.
        Keys: vol, bass, mid, hi, echo, pan
        """
        return {
            "vol" : self.params["vol"],
            "bass": self.params["bass"],
            "mid" : self.params["mid"],
            "hi"  : self.params["hi"],
            "echo": self.params["echo"],
            "pan" : self.params["pan"],
        }

    # ------------------------------------------------------------------
    # Xử lý tín hiệu chính
    # ------------------------------------------------------------------

    def process(self, samples: np.ndarray) -> np.ndarray:
        """
        Áp dụng toàn bộ DSP chain lên samples.
        Thứ tự: EQ → Effect → Echo → Pan → Volume → Clip

        Args:
            samples : np.ndarray — (N,) mono hoặc (N,2) stereo, float64

        Returns
            np.ndarray — (N,2) stereo float64, clipped [-1,1]
        """
        out = samples.copy()

        # 1. EQ
        out = apply_eq(out, self.samplerate,
                       bass_db=self.params["bass"],
                       mid_db =self.params["mid"],
                       hi_db  =self.params["hi"])

        # 2. Effect (nếu có)
        effect = self.params["effect"]
        ep = self.params["effect_params"]
        if effect == "echo":
            out = apply_echo(out, self.samplerate, **ep)
        elif effect == "reverb":
            out = apply_reverb(out, self.samplerate, **ep)
        elif effect == "chorus":
            out = apply_chorus(out, self.samplerate, **ep)
        elif effect == "flanger":
            out = apply_flanger(out, self.samplerate, **ep)
        elif effect == "distortion":
            out = apply_distortion(out, **ep)

        # 3. Echo (từ slider ECHO — độc lập với Effect dropdown)
        echo_level = self.params["echo"]
        if echo_level > 0.01:
            delay_ms = echo_level * _ECHO_MAX_DELAY_MS
            feedback = echo_level * _ECHO_MAX_FEEDBACK
            out = apply_echo(out, self.samplerate,
                             delay_ms=delay_ms,
                             feedback=feedback,
                             wet=echo_level * 0.6)

        # 4. Pan
        out = apply_pan(out, self.params["pan"])  # kết quả luôn là (N,2)

        # 5. Volume
        out = apply_volume(out, self.params["vol"])

        # 6. Final clip
        out = np.clip(out, -1.0, 1.0)

        return out

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Đặt lại tất cả tham số về mặc định."""
        self.params = DEFAULT_PARAMS.copy()
        self.params["effect_params"] = {}