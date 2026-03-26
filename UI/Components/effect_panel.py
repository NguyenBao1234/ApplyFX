"""
effects_panel.py
----------------
Panel chọn Effect Preset và điều chỉnh tham số của effect đó.

Bố cục:

    EFFECTS PRESET     [Dropdown v]  [Apply]

    Param 1: [────────────────O──] value
    Param 2: [──O─────────────── ] value
    ...


Mỗi effect có tập params khác nhau - panel tự render
lại các slider ngang khi user chọn preset mới.
"""

import customtkinter as ctk
from UI.style import COLOR, FONT, SIZE
from Core.Presets import ALL_PRESETS, get_preset_by_name, Preset


# ------------------------------------------------------------------
# Định nghĩa params hiển thị cho từng effect
# key: tên effect (khớp với Preset.effect)
# value: list of (param_key, label, min, max, fmt)
# ------------------------------------------------------------------
_EFFECT_PARAM_DEFS: dict[str, list[tuple]] = {
    "echo": [
        ("delay_ms", "Delay",    50.0,  800.0, "{:.0f} ms"),
        ("feedback", "Feedback",  0.0,    0.95, "{:.2f}"),
        ("wet",      "Wet",       0.0,    1.0,  "{:.2f}"),
    ],
    "reverb": [
        ("room_size", "Room Size", 0.1,  1.0,  "{:.2f}"),
        ("damping",   "Damping",   0.0,  0.99, "{:.2f}"),
        ("wet",       "Wet",       0.0,  1.0,  "{:.2f}"),
    ],
    "chorus": [
        ("depth_ms", "Depth",   0.5,  5.0,  "{:.1f} ms"),
        ("rate_hz",  "Rate",    0.2,  5.0,  "{:.1f} Hz"),
        ("wet",      "Wet",     0.0,  1.0,  "{:.2f}"),
    ],
    "flanger": [
        ("depth_ms", "Depth",    0.5,  5.0,  "{:.1f} ms"),
        ("rate_hz",  "Rate",     0.1,  3.0,  "{:.1f} Hz"),
        ("feedback", "Feedback", 0.0,  0.95, "{:.2f}"),
        ("wet",      "Wet",      0.0,  1.0,  "{:.2f}"),
    ],
    "distortion": [
        ("drive", "Drive",  1.0, 20.0, "{:.1f}"),
        ("tone",  "Tone",   0.0,  1.0, "{:.2f}"),
        ("wet",   "Wet",    0.0,  1.0, "{:.2f}"),
    ],
}

# Tên hiển thị cho mode của distortion
_DISTORTION_MODES = ["soft", "hard", "fuzz"]


class EffectsPanel(ctk.CTkFrame):
    """
    Panel chọn Effect Preset và hiệu chỉnh tham số.

    Args:
        parent: widget cha
        on_preset_change (callable | None):
            callback(preset: Preset) khi user nhấn Apply.
            App dùng callback này để cập nhật DSPProcessor và EQPanel.
    """

    def __init__(self, parent, *, on_preset_change=None):
        super().__init__(parent,
                         fg_color=COLOR["bg_panel"],
                         corner_radius=SIZE["corner_radius"])

        self._on_preset_change = on_preset_change
        self._current_preset: Preset | None = None

        # Widget params động — lưu để xoá khi render lại
        self._param_widgets: list[ctk.CTkFrame] = []
        self._param_vars:    dict[str, ctk.DoubleVar] = {}
        self._mode_var:      ctk.StringVar | None = None

        self._build_ui()

    # ------------------------------------------------------------------
    # Build layout cố định
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Tạo header + dropdown + nút Apply. Params sẽ render động."""
        self.columnconfigure(0, weight=1)

        # --- Header ---
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew",
                          padx=14, pady=(12, 6))
        header_frame.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header_frame, text="EFFECTS PRESET",
            font=FONT["title"],
            text_color=COLOR["text_primary"]
        ).grid(row=0, column=0, sticky="w")

        # Dropdown chọn preset
        preset_names = ["- Chọn preset -"] + [p.name for p in ALL_PRESETS]
        self._dropdown = ctk.CTkOptionMenu(
            header_frame,
            values=preset_names,
            font=FONT["label"],
            fg_color=COLOR["bg_card"],
            button_color=COLOR["accent_dim"],
            button_hover_color=COLOR["accent"],
            dropdown_fg_color=COLOR["bg_card"],
            dropdown_hover_color=COLOR["accent_dim"],
            text_color=COLOR["text_primary"],
            width=220,
            command=self._on_dropdown_select
        )
        self._dropdown.grid(row=0, column=1, padx=(14, 8), sticky="ew")
        self._dropdown.set("- Chọn preset -")

        # Nút Apply
        self._btn_apply = ctk.CTkButton(
            header_frame, text="✓ Apply",
            font=FONT["label"],
            fg_color=COLOR["accent"],
            hover_color=COLOR["accent_dim"],
            corner_radius=SIZE["btn_corner_radius"],
            width=80, height=32,
            state="disabled",
            command=self._on_apply
        )
        self._btn_apply.grid(row=0, column=2, padx=(0, 0))

        # Nút Clear effect
        self._btn_clear = ctk.CTkButton(
            header_frame, text="✕ Clear",
            font=FONT["label"],
            fg_color=COLOR["bg_card"],
            hover_color=COLOR["separator"],
            corner_radius=SIZE["btn_corner_radius"],
            width=70, height=32,
            command=self._on_clear
        )
        self._btn_clear.grid(row=0, column=3, padx=(6, 0))

        # Label mô tả preset
        self._lbl_descript = ctk.CTkLabel(
            self, text="",
            font=FONT["label_sm"],
            text_color=COLOR["text_secondary"],
            wraplength=680,
            justify="left"
        )
        self._lbl_descript.grid(row=1, column=0,
                                padx=14, pady=(0, 4), sticky="w")

        # Đường kẻ phân cách
        ctk.CTkFrame(self, height=1,
                     fg_color=COLOR["separator"]
                     ).grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 6))

        # Frame chứa params động (row 3)
        self._params_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._params_frame.grid(row=3, column=0, sticky="ew",
                                padx=14, pady=(0, 12))
        self._params_frame.columnconfigure(0, weight=1)

        # Label khi không có effect
        self._lbl_no_effect = ctk.CTkLabel(
            self._params_frame,
            text="Chọn một preset để xem tham số",
            font=FONT["label_sm"],
            text_color=COLOR["text_secondary"]
        )
        self._lbl_no_effect.grid(row=0, column=0, pady=8)

    # ------------------------------------------------------------------
    # Dropdown select
    # ------------------------------------------------------------------

    def _on_dropdown_select(self, name: str) -> None:
        """
        Khi user chọn preset từ dropdown: cập nhật mô tả
        và render params tương ứng.

        Args:
            name (str): tên preset được chọn
        """
        if name.startswith("—"):
            self._current_preset = None
            self._lbl_descript.configure(text="")
            self._btn_apply.configure(state="disabled")
            self._render_params(None)
            return

        preset = get_preset_by_name(name)
        if preset is None:
            return

        self._current_preset = preset
        self._lbl_descript.configure(text=preset.description)
        self._btn_apply.configure(state="normal")
        self._render_params(preset)

    # ------------------------------------------------------------------
    # Render params động
    # ------------------------------------------------------------------

    def _render_params(self, preset: Preset | None) -> None:
        """
        Xoá params cũ và tạo lại slider ngang cho effect của preset.

        Args:
            preset (Preset | None): preset được chọn, None để clear
        """
        # Xoá widgets cũ
        for w in self._param_widgets:
            w.destroy()
        self._param_widgets.clear()
        self._param_vars.clear()
        self._mode_var = None

        # Ẩn label "chọn preset"
        self._lbl_no_effect.grid_remove()

        # Không có effect params → hiện lại label
        if preset is None or preset.effect is None:
            self._lbl_no_effect.grid()
            return

        effect = preset.effect #effect type
        paramFx = preset.effect_params
        param_defs = _EFFECT_PARAM_DEFS.get(effect, [])

        if not param_defs:
            self._lbl_no_effect.configure(
                text=f"Effect '{effect}' không có tham số."
            )
            self._lbl_no_effect.grid()
            return

        # Tạo slider ngang cho từng param
        for row_idx, (pkey, plabel, pmin, pmax, pfmt) in enumerate(param_defs):
            row_frame = self._make_param_row(
                row_idx, pkey, plabel, pmin, pmax,
                paramFx.get(pkey, (pmin + pmax) / 2),
                pfmt
            )
            self._param_widgets.append(row_frame)

        # Nếu distortion: thêm mode selector
        if effect == "distortion":
            mode_frame = self._make_mode_selector(
                len(param_defs),
                paramFx.get("mode", "soft")
            )
            self._param_widgets.append(mode_frame)

    def _make_param_row(self, row: int, pkey: str, label: str,
                        pmin: float, pmax: float,
                        default: float, fmt: str) -> ctk.CTkFrame:
        """
        Tạo 1 hàng slider ngang: [Label] [────O────] [value].

        Args:
            row (int): index hàng trong params_frame
            pkey (str): key param (VD: "wet", "delay_ms")
            label (str): tên hiển thị
            pmin (float): giá trị nhỏ nhất
            pmax (float): giá trị lớn nhất
            default (float): giá trị khởi tạo
            fmt (str): format string giá trị

        Returns:
            ctk.CTkFrame: frame chứa toàn bộ hàng
        """
        frame = ctk.CTkFrame(self._params_frame, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", pady=3)
        frame.columnconfigure(1, weight=1)

        # Label tên param
        ctk.CTkLabel(
            frame, text=label,
            font=FONT["label"],
            text_color=COLOR["text_secondary"],
            width=80, anchor="e"
        ).grid(row=0, column=0, padx=(0, 10))

        # DoubleVar liên kết slider ↔ label giá trị
        var = ctk.DoubleVar(value=default)
        self._param_vars[pkey] = var

        # Label giá trị (bên phải)
        lbl_val = ctk.CTkLabel(
            frame, text=fmt.format(default),
            font=FONT["value"],
            text_color=COLOR["text_value"],
            width=70, anchor="w"
        )
        lbl_val.grid(row=0, column=2, padx=(10, 0))

        # Slider ngang
        slider = ctk.CTkSlider(
            frame,
            from_=pmin, to=pmax,
            variable=var,
            fg_color=COLOR["bg_slider"],
            progress_color=COLOR["accent_dim"],
            button_color=COLOR["accent"],
            button_hover_color=COLOR["accent_glow"],
            height=16,
            command=lambda v, lv=lbl_val, f=fmt: lv.configure(text=f.format(v))
        )
        slider.grid(row=0, column=1, sticky="ew")

        return frame

    def _make_mode_selector(self, row: int,
                            current_mode: str) -> ctk.CTkFrame:
        """
        Tạo selector mode cho Distortion (soft / hard / fuzz).

        Args:
            row (int): index hàng tiếp theo
            current_mode (str): mode hiện tại từ preset

        Returns:
            ctk.CTkFrame: frame chứa mode selector
        """
        frame = ctk.CTkFrame(self._params_frame, fg_color="transparent")
        frame.grid(row=row, column=0, sticky="ew", pady=(6, 0))

        ctk.CTkLabel(
            frame, text="Mode",
            font=FONT["label"],
            text_color=COLOR["text_secondary"],
            width=80, anchor="e"
        ).grid(row=0, column=0, padx=(0, 10))

        self._mode_var = ctk.StringVar(value=current_mode)

        for col, mode in enumerate(_DISTORTION_MODES):
            ctk.CTkRadioButton(
                frame, text=mode.capitalize(),
                variable=self._mode_var,
                value=mode,
                font=FONT["label"],
                text_color=COLOR["text_primary"],
                fg_color=COLOR["accent"],
                hover_color=COLOR["accent_dim"]
            ).grid(row=0, column=col + 1, padx=12)

        return frame

    # ------------------------------------------------------------------
    # Apply / Clear
    # ------------------------------------------------------------------

    def _on_apply(self) -> None:
        """
        Đọc giá trị params hiện tại từ sliders, tạo preset tạm
        rồi gọi callback on_preset_change.
        """
        if self._current_preset is None:
            return

        # Lấy giá trị params từ DoubleVar
        effect_params = {k: v.get() for k, v in self._param_vars.items()}

        # Thêm mode nếu là distortion
        if self._current_preset.effect == "distortion" and self._mode_var:
            effect_params["mode"] = self._mode_var.get()

        # Tạo preset tạm với params đã chỉnh
        from Core.Presets import Preset as P
        applied = P(
            name          = self._current_preset.name,
            eq            = self._current_preset.eq.copy(),
            effect        = self._current_preset.effect,
            effect_params = effect_params,
            pan           = self._current_preset.pan,
            description   = self._current_preset.description,
        )

        if self._on_preset_change:
            self._on_preset_change(applied)

    def _on_clear(self) -> None:
        """
        Xoá effect hiện tại: reset dropdown, clear params,
        gọi callback với preset None-effect.
        """
        self._dropdown.set("— Chọn preset —")
        self._current_preset = None
        self._lbl_descript.configure(text="")
        self._btn_apply.configure(state="disabled")
        self._render_params(None)

        # Gọi callback với preset flat (không effect)
        if self._on_preset_change:
            from Core.Presets import get_preset_by_name
            flat = get_preset_by_name("Flat (Default)")
            if flat:
                self._on_preset_change(flat)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_preset(self, preset: Preset) -> None:
        """
        Đặt preset từ bên ngoài (VD: khi reset toàn app).
        Không gọi callback.

        Args:
            preset (Preset): preset cần hiển thị
        """
        self._dropdown.set(preset.name)
        self._current_preset = preset
        self._lbl_descript.configure(text=preset.description)
        self._btn_apply.configure(
            state="normal" if preset.effect else "disabled"
        )
        self._render_params(preset)
