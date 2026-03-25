"""
style.py
---------
Định nghĩa theme, màu sắc và font dùng xuyên suốt app.
Tất cả component import từ đây để đảm bảo đồng nhất.
"""

import customtkinter as ctk

# ------------------------------------------------------------------
# Theme toàn cục
# ------------------------------------------------------------------
APP_THEME      = "dark"
APP_COLOR_THEME = "blue"

# ------------------------------------------------------------------
# Bảng màu chính
# ------------------------------------------------------------------
COLOR = {
    # Nền
    "bg_root"     : "#1a1a2e",   # nền cửa sổ chính
    "bg_panel"    : "#16213e",   # nền panel/frame
    "bg_card"     : "#0f3460",   # nền card/widget
    "bg_slider"   : "#0d0d1a",   # track của slider

    # Accent
    "accent"      : "#e94560",   # màu chủ đạo (đỏ hồng)
    "accent_dim"  : "#a32f43",   # accent tối hơn
    "accent_glow" : "#ff6b8a",   # accent sáng hơn

    # Text
    "text_primary" : "#eaeaea",  # chữ chính
    "text_secondary": "#8888aa", # chữ phụ / label
    "text_value"   : "#e94560",  # giá trị slider

    # Slider thumb / handle
    "thumb"        : "#e94560",
    "thumb_hover"  : "#ff6b8a",

    # Transport buttons
    "btn_play"     : "#27ae60",
    "btn_pause"    : "#9b59b6",
    "btn_stop"     : "#e74c3c",
    "btn_import"   : "#2980b9",

    # Separator
    "separator"    : "#2a2a4a",
}

# ------------------------------------------------------------------
# Font
# ------------------------------------------------------------------
FONT = {
    "label"   : ("Segoe UI", 11),
    "label_sm": ("Segoe UI", 9),
    "value"   : ("Consolas", 11, "bold"),
    "title"   : ("Segoe UI", 13, "bold"),
    "header"  : ("Segoe UI", 16, "bold"),
    "mono"    : ("Consolas", 10),
}

# ------------------------------------------------------------------
# Kích thước
# ------------------------------------------------------------------
SIZE = {
    "slider_height"     : 220,   # chiều cao vùng slider dọc
    "slider_width"      : 54,    # chiều rộng mỗi slider column
    "thumb_radius"      : 10,    # bán kính thumb hình tròn
    "track_width"       : 6,     # độ rộng track slider
    "corner_radius"     : 10,
    "btn_corner_radius" : 8,
    "panel_pad"         : 12,
    "transport_height"  : 80,
}


def apply_theme() -> None:
    """Áp dụng theme customtkinter toàn cục."""
    ctk.set_appearance_mode(APP_THEME)
    ctk.set_default_color_theme(APP_COLOR_THEME)