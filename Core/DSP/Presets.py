"""
presets.py
----------
Định nghĩa các preset EQ + Effect sẵn có.

Mỗi preset là 1 dict chứa:
  - "name"      : str            — tên hiển thị
  - "eq"        : dict           — giá trị Equalization (vol, bass, mid, hi)
  - "effect"    : str | None     — tên effect ("echo","reverb","chorus",
                                    "flanger","distortion", hoặc None)
  - "effect_params" : dict       — tham số cho effect (nếu có)
  - "pan"       : float          — vị trí pan [-1, 1]
  - "description": str           — mô tả ngắn cho UI
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Preset:
    name: str
    eq: dict[str, float]
    effect: str | None
    effect_params: dict[str, Any]
    pan: float
    description: str


# ------------------------------------------------------------------
# Giá trị EQ mặc định (flat / không chỉnh gì)
# ------------------------------------------------------------------
_FLAT_EQ = {
    "vol":  1.0,    # linear gain
    "bass": 0.0,    # dB
    "mid":  0.0,    # dB
    "hi":   0.0,    # dB
    "echo": 0.0,    # 0 = tắt
}

# ------------------------------------------------------------------
# EQ PRESETS
# ------------------------------------------------------------------
EQ_PRESETS: list[Preset] = [
    Preset(
        name="Flat (Default)",
        eq={"vol": 1.0, "bass": 0.0, "mid": 0.0, "hi": 0.0, "echo": 0.0},
        effect=None,
        effect_params={},
        pan=0.0,
        description="Không chỉnh gì — âm thanh nguyên bản."
    ),
    Preset(
        name="Pop",
        eq={"vol": 1.0, "bass": 3.0, "mid": -1.0, "hi": 4.0, "echo": 0.0},
        effect=None,
        effect_params={},
        pan=0.0,
        description="Âm trầm nhẹ, âm cao sáng — điển hình nhạc Pop."
    ),
    Preset(
        name="Rock",
        eq={"vol": 1.1, "bass": 5.0, "mid": 2.0, "hi": 3.0, "echo": 0.0},
        effect="distortion",
        effect_params={"drive": 3.0, "tone": 0.6, "wet": 0.3, "mode": "soft"},
        pan=0.0,
        description="Bass và treble mạnh, mid nổi, overdrive nhẹ."
    ),
    Preset(
        name="Jazz",
        eq={"vol": 0.95, "bass": 2.0, "mid": 1.0, "hi": -2.0, "echo": 0.0},
        effect="reverb",
        effect_params={"room_size": 0.4, "damping": 0.6, "wet": 0.2},
        pan=0.0,
        description="Ấm, mid rõ, treble mềm — cảm giác club nhỏ."
    ),
    Preset(
        name="Classical",
        eq={"vol": 0.9, "bass": 1.0, "mid": 0.0, "hi": 1.0, "echo": 0.0},
        effect="reverb",
        effect_params={"room_size": 0.8, "damping": 0.3, "wet": 0.4},
        pan=0.0,
        description="Không gian rộng, tự nhiên — phòng hoà nhạc lớn."
    ),
    Preset(
        name="Vocal Boost",
        eq={"vol": 1.0, "bass": -2.0, "mid": 5.0, "hi": 2.0, "echo": 0.0},
        effect=None,
        effect_params={},
        pan=0.0,
        description="Đẩy mid để giọng hát nổi bật."
    ),
    Preset(
        name="Bass Boost",
        eq={"vol": 1.0, "bass": 8.0, "mid": 0.0, "hi": -1.0, "echo": 0.0},
        effect=None,
        effect_params={},
        pan=0.0,
        description="Đẩy mạnh âm trầm, phù hợp EDM / Hip-hop."
    ),
]

# ------------------------------------------------------------------
# EFFECT PRESETS (focus vào hiệu ứng, EQ flat)
# ------------------------------------------------------------------
EFFECT_PRESETS: list[Preset] = [
    Preset(
        name="Echo — Short",
        eq=_FLAT_EQ.copy(),
        effect="echo",
        effect_params={"delay_ms": 150.0, "feedback": 0.3, "wet": 0.4},
        pan=0.0,
        description="Echo ngắn, lặp nhanh."
    ),
    Preset(
        name="Echo — Long",
        eq=_FLAT_EQ.copy(),
        effect="echo",
        effect_params={"delay_ms": 500.0, "feedback": 0.5, "wet": 0.5},
        pan=0.0,
        description="Echo dài, canyon / sơn cước."
    ),
    Preset(
        name="Reverb — Room",
        eq=_FLAT_EQ.copy(),
        effect="reverb",
        effect_params={"room_size": 0.3, "damping": 0.7, "wet": 0.25},
        pan=0.0,
        description="Phòng nhỏ, gần gũi."
    ),
    Preset(
        name="Reverb — Hall",
        eq=_FLAT_EQ.copy(),
        effect="reverb",
        effect_params={"room_size": 0.7, "damping": 0.4, "wet": 0.4},
        pan=0.0,
        description="Sảnh lớn, vang vọng."
    ),
    Preset(
        name="Reverb — Church",
        eq=_FLAT_EQ.copy(),
        effect="reverb",
        effect_params={"room_size": 1.0, "damping": 0.1, "wet": 0.6},
        pan=0.0,
        description="Nhà thờ lớn, vang rất lâu."
    ),
    Preset(
        name="Chorus — Subtle",
        eq=_FLAT_EQ.copy(),
        effect="chorus",
        effect_params={"depth_ms": 1.5, "rate_hz": 1.2, "wet": 0.4},
        pan=0.0,
        description="Làm dày âm thanh nhẹ nhàng."
    ),
    Preset(
        name="Chorus — Deep",
        eq=_FLAT_EQ.copy(),
        effect="chorus",
        effect_params={"depth_ms": 3.0, "rate_hz": 0.8, "wet": 0.7},
        pan=0.0,
        description="Chorus rõ, nhiều giọng."
    ),
    Preset(
        name="Flanger",
        eq=_FLAT_EQ.copy(),
        effect="flanger",
        effect_params={"depth_ms": 2.0, "rate_hz": 0.5, "feedback": 0.5, "wet": 0.7},
        pan=0.0,
        description="Hiệu ứng whoosh / jet plane."
    ),
    Preset(
        name="Overdrive",
        eq=_FLAT_EQ.copy(),
        effect="distortion",
        effect_params={"drive": 4.0, "tone": 0.6, "wet": 0.6, "mode": "soft"},
        pan=0.0,
        description="Méo nhẹ kiểu guitar overdrive."
    ),
    Preset(
        name="Heavy Distortion",
        eq=_FLAT_EQ.copy(),
        effect="distortion",
        effect_params={"drive": 12.0, "tone": 0.7, "wet": 0.9, "mode": "hard"},
        pan=0.0,
        description="Distortion cứng, kim loại."
    ),
    Preset(
        name="Fuzz",
        eq=_FLAT_EQ.copy(),
        effect="distortion",
        effect_params={"drive": 8.0, "tone": 0.4, "wet": 0.85, "mode": "fuzz"},
        pan=0.0,
        description="Fuzz cực đoan, Jimi Hendrix style."
    ),
]

# ------------------------------------------------------------------
# TẤT CẢ preset gộp lại (cho UI dropdown)
# ------------------------------------------------------------------
ALL_PRESETS: list[Preset] = EQ_PRESETS + EFFECT_PRESETS


def get_preset_names() -> list[str]:
    """Trả về danh sách tên preset để hiển thị trên dropdown."""
    return [p.name for p in ALL_PRESETS]


def get_preset_by_name(name: str) -> Preset | None:
    """Tìm preset theo tên. Trả về None nếu không tìm thấy."""
    for p in ALL_PRESETS:
        if p.name == name:
            return p
    return None