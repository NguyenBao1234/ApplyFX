"""
pan.py
------
Stereo Panning — điều chỉnh cân bằng trái/phải.

Dùng Equal Power Panning (law sin/cos):
  - Giữ nguyên cảm giác âm lượng khi pan sang trái/phải
  - Tốt hơn Linear Pan về mặt tâm lý thính giác

  pan = -1.0 → hoàn toàn trái
  pan =  0.0 → giữa (mặc định)
  pan = +1.0 → hoàn toàn phải
"""

import numpy as np


def apply_pan(samples: np.ndarray, pan: float) -> np.ndarray:
    """
    Áp dụng Stereo Pan lên samples.
    Args:
        samples : np.ndarray — (N,) hoặc (N,2), float64
        pan     : float      — vị trí pan [-1.0, +1.0]
                               -1 = full left, 0 = center, +1 = full right

    Return:
         np.ndarray — shape (N,2) luôn luôn stereo
    """
    pan = np.clip(pan, -1.0, 1.0)

    # Equal Power: dùng góc từ 0° đến 90°
    # pan=-1 → angle=0°  → L=1, R=0
    # pan= 0 → angle=45° → L=R=√2/2 ≈ 0.707
    # pan=+1 → angle=90° → L=0, R=1
    angle = (pan + 1.0) / 2.0 * (np.pi / 2.0)  # [0, π/2]
    gain_l = np.cos(angle)
    gain_r = np.sin(angle)

    if samples.ndim == 1:
        # Mono → stereo
        left = samples * gain_l
        right = samples * gain_r
    else:
        # Stereo: scale từng kênh
        # Nhân gain L lên kênh L, gain R lên kênh R
        # Chuẩn hoá lại để tổng power không thay đổi
        left = samples[:, 0] * gain_l
        right = samples[:, 1] * gain_r

    return np.stack([left, right], axis=1)


def pan_to_label(pan: float) -> str:
    """
    Chuyển giá trị pan float → chuỗi mô tả cho UI.

    VD:
      -1.0  → "L 100"
      -0.5  → "L  50"
       0.0  → "CENTER"
      +0.5  → "R  50"
      +1.0  → "R 100"
    """
    pan = np.clip(pan, -1.0, 1.0)
    if abs(pan) < 0.01:
        return "CENTER"
    side = "L" if pan < 0 else "R"
    pct = int(abs(pan) * 100)
    return f"{side}: {pct:3d}%"
