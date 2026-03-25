"""
eq_panel.py
-----------
Panel chứa 6 thanh trượt dọc song song đại diện cho:
  VOL, BASS, MID, HI, ECHO, PAN

Kết nối trực tiếp với DSPProcessor thông qua callback.
"""

import customtkinter as ctk
from UI.style import COLOR, FONT, SIZE
from UI.Components.verticle_slider import VerticalSlider


# Cấu hình từng slider
# (key, label, unit, min, max, default, fmt)
_SLIDER_CONFIGS = [
    ("vol",  "VOL",   "x",  0.0,  2.0,  1.0, "{:.2f}"),
    ("bass", "BASS",  "dB", -12.0, 12.0, 0.0, "{:+.1f}"),
    ("mid",  "MID",   "dB", -12.0, 12.0, 0.0, "{:+.1f}"),
    ("hi",   "HI",    "dB", -12.0, 12.0, 0.0, "{:+.1f}"),
    ("echo", "ECHO",  "",   0.0,  1.0,  0.0, "{:.2f}"),
    ("pan",  "PAN",   "",  -1.0,  1.0,  0.0, "{:+.2f}"),
]


class EQPanel(ctk.CTkFrame):
    """
    Panel 6 slider dọc — trung tâm điều chỉnh âm thanh.

    Args:
        parent: widget cha
        on_param_change (callable): callback(key: str, value: float)
            được gọi khi bất kỳ slider nào thay đổi
    """

    def __init__(self, parent, *, on_param_change=None):
        super().__init__(parent,
                         fg_color=COLOR["bg_panel"],
                         corner_radius=SIZE["corner_radius"])

        self._on_param_change = on_param_change
        self._sliders: dict[str, VerticalSlider] = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Tạo header và 6 slider dọc."""

        # Header
        header = ctk.CTkLabel(
            self, text="EQ  &  CONTROLS",
            font=FONT["title"],
            text_color=COLOR["text_primary"]
        )
        header.grid(row=0, column=0, columnspan=len(_SLIDER_CONFIGS),
                    pady=(12, 8), padx=16, sticky="w")

        # Đường kẻ ngang phân cách
        sep = ctk.CTkFrame(self, height=1,
                           fg_color=COLOR["separator"])
        sep.grid(row=1, column=0, columnspan=len(_SLIDER_CONFIGS),
                 sticky="ew", padx=16, pady=(0, 8))

        # 6 slider
        for col, (key, label, unit, mn, mx, default, fmt) in enumerate(_SLIDER_CONFIGS):
            self.columnconfigure(col, weight=1)

            slider = VerticalSlider(
                self,
                label=label,
                unit=unit,
                min_val=mn,
                max_val=mx,
                default_val=default,
                fmt=fmt,
                on_change=self._make_callback(key)
            )
            slider.grid(row=2, column=col, padx=6, pady=(0, 12), sticky="n")
            self._sliders[key] = slider

            # Đường kẻ dọc phân cách (trừ cái cuối)
            if col < len(_SLIDER_CONFIGS) - 1:
                vsep = ctk.CTkFrame(self, width=1,
                                    fg_color=COLOR["separator"])
                vsep.grid(row=2, column=col,
                          sticky="nse", padx=0, pady=8)

    # ------------------------------------------------------------------
    # Callback factory
    # ------------------------------------------------------------------

    def _make_callback(self, key: str):
        """
        Tạo callback cho từng slider, đóng gói key vào closure.

        Args:
            key (str): tên tham số DSP ("vol", "bass", ...)

        Returns:
            callable: hàm callback(value: float)
        """
        def cb(value: float):
            if self._on_param_change:
                self._on_param_change(key, value)
        return cb

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_values(self, values: dict) -> None:
        """
        Cập nhật tất cả slider theo dict giá trị — dùng khi load preset.
        Không trigger callback để tránh vòng lặp.

        Args:
            values (dict): {key: value} VD: {"vol": 1.0, "bass": 3.0, ...}
        """
        for key, val in values.items():
            if key in self._sliders:
                self._sliders[key].set_silent(val)

    def get_values(self) -> dict:
        """
        Lấy giá trị hiện tại của tất cả slider.

        Returns:
            dict: {key: float} cho tất cả 6 slider
        """
        return {key: sl.get() for key, sl in self._sliders.items()}

    def reset(self) -> None:
        """Đặt lại tất cả slider về giá trị mặc định."""
        defaults = {key: default
                    for key, _, _, _, _, default, _ in _SLIDER_CONFIGS}
        self.set_values(defaults)