"""
audio_engine.py
---------------
Quản lý dữ liệu âm thanh thô (raw samples).

Quy ước nội bộ:
  - samples  : np.ndarray, shape (N,) mono hoặc (N, 2) stereo, dtype float64
  - samplerate: int, Hz (VD: 44100, 48000)
  - Giá trị mẫu nằm trong [-1.0, 1.0]
"""

import soundfile as sf
import numpy as np
from pathlib import Path


# Các định dạng file được hỗ trợ
SUPPORTED_EXTENSIONS = {".wav", ".flac", ".ogg", ".aiff", ".aif"}


class AudioEngine:
    """
    Lớp trung tâm quản lý audio data.

    Attributes
    ----------
    filepath     : Path | None   — đường dẫn file gốc
    samples      : np.ndarray    — dữ liệu mẫu gốc (không bao giờ thay đổi)
    samplerate   : int           — tần số lấy mẫu
    n_channels   : int           — số kênh (1=mono, 2=stereo)
    duration_sec : float         — thời lượng (giây)
    """

    def __init__(self):
        self.filepath: Path | None = None
        self.samples: np.ndarray | None = None      # dữ liệu GỐC
        self.samplerate: int = 0
        self.n_channels: int = 0
        self.duration_sec: float = 0.0

    # ------------------------------------------------------------------
    # LOAD
    # ------------------------------------------------------------------
    def load(self, filepath: str) -> None:
        """
        Đọc file âm thanh vào bộ nhớ.

        Parameters
        ----------
        filepath : str — đường dẫn đến file âm thanh

        Raises
        ------
        ValueError  — nếu định dạng không hỗ trợ
        RuntimeError — nếu đọc file thất bại
        """
        path = Path(filepath)

        if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            raise ValueError(
                f"Định dạng '{path.suffix}' không được hỗ trợ.\n"
                f"Hỗ trợ: {', '.join(SUPPORTED_EXTENSIONS)}"
            )

        try:
            # soundfile trả về (data: ndarray, samplerate: int)
            # always_2d=False → mono = shape (N,), stereo = shape (N, 2)
            data, sr = sf.read(str(path), dtype="float64", always_2d=False)
        except Exception as e:
            raise RuntimeError(f"Không thể đọc file: {e}")

        # Chuẩn hoá về [-1, 1] nếu cần (soundfile với dtype float64 đã là [-1,1])
        data = np.clip(data, -1.0, 1.0)

        self.filepath = path
        self.samples = data
        self.samplerate = sr
        self.n_channels = 1 if data.ndim == 1 else data.shape[1]
        self.duration_sec = len(data) / sr

    # ------------------------------------------------------------------
    # SAVE
    # ------------------------------------------------------------------
    def save(self, output_path: str, processed_samples: np.ndarray) -> None:
        """
        Ghi dữ liệu đã xử lý ra file WAV.

        Parameters
        ----------
        output_path       : str          — đường dẫn file đầu ra
        processed_samples : np.ndarray   — dữ liệu đã qua DSP
        """
        if self.samplerate == 0:
            raise RuntimeError("Chưa load file âm thanh nào.")

        # Clip lại lần cuối trước khi ghi để tránh clipping artifact
        out = np.clip(processed_samples, -1.0, 1.0)
        sf.write(output_path, out, self.samplerate)

    # ------------------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------------------
    def is_loaded(self) -> bool:
        """Trả về True nếu đã load file."""
        return self.samples is not None

    def get_mono(self) -> np.ndarray | None:
        """
        Trả về bản mono của samples gốc (trung bình 2 kênh nếu stereo).
        Dùng để vẽ waveform hoặc phân tích.
        """
        if self.samples is None:
            return None
        if self.samples.ndim == 1:
            return self.samples.copy()
        return self.samples.mean(axis=1)

    def get_stereo(self) -> np.ndarray | None:
        """
        Trả về bản stereo shape (N, 2).
        Nếu file gốc là mono, nhân đôi thành 2 kênh giống nhau.
        """
        if self.samples is None:
            return None
        if self.samples.ndim == 2:
            return self.samples.copy()
        # mono → stereo
        stereo = np.stack([self.samples, self.samples], axis=1)
        return stereo

    def format_duration(self) -> str:
        """Trả về chuỗi 'MM:SS' từ duration_sec."""
        return _seconds_to_mmss(self.duration_sec)

    @property
    def info_str(self) -> str:
        """Chuỗi mô tả ngắn để hiển thị trên UI."""
        if not self.is_loaded():
            return "Chưa có file"
        ch = "Mono" if self.n_channels == 1 else "Stereo"
        return (
            f"{self.filepath.name}  |  "
            f"{ch}  |  "
            f"{self.samplerate} Hz  |  "
            f"{self.format_duration()}"
        )


# ------------------------------------------------------------------
# Utility độc lập
# ------------------------------------------------------------------
def _seconds_to_mmss(seconds: float) -> str:
    """Chuyển số giây → 'MM:SS'."""
    total = int(seconds)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"