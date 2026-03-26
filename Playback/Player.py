"""
player.py
---------
Playback Engine dùng sounddevice.OutputStream.

Mỗi Player chạy trên 1 thread riêng, stream audio theo từng chunk.
App tạo 2 instance: 1 cho Original, 1 cho Preview.

Vòng đời:
    load() → play() → pause() → resume() → stop()

Thread model:
    - Main thread: gọi play/pause/stop, cập nhật UI
    - Worker thread: đọc chunk → ghi vào OutputStream
    - Dùng threading.Event để đồng bộ pause/stop

Callback:
    on_tick(current_sec, total_sec)  — gọi mỗi chunk (~100ms) để UI cập nhật timestamp
    on_finish()                      — gọi khi phát hết file
"""

import threading
import numpy as np
import sounddevice as sd

# Kích thước mỗi chunk (số frame) — ~100ms tại 44100 Hz
CHUNK_FRAMES = 4096


class Player:
    """
    Phát audio từ numpy array qua sounddevice.OutputStream.

    Args:
        on_tick (callable | None): callback(current_sec: float, total_sec: float)
            được gọi mỗi chunk để cập nhật timestamp trên UI.
        on_finish (callable | None): callback() khi phát xong hoặc stop.
    """

    def __init__(self, on_tick=None, on_finish=None):
        self._on_tick   = on_tick
        self._on_finish = on_finish

        # Audio data
        self._samples:    np.ndarray | None = None
        self._samplerate: int = 44100
        self._total_frames: int = 0

        # Trạng thái phát
        self._cursor:   int = 0          # frame hiện tại đang đọc
        self._state:    str = "stopped"  # "stopped" | "playing" | "paused"

        # Đồng bộ thread
        self._pause_event = threading.Event()
        self._pause_event.set()          # set = không bị block
        self._stop_event  = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, samples: np.ndarray, samplerate: int) -> None:
        """
        Nạp audio data vào player. Tự động stop nếu đang phát.

        Args:
            samples (np.ndarray): (N,) mono hoặc (N,2) stereo, float64
            samplerate (int): tần số lấy mẫu (Hz)
        """
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        with self._lock:
            # Chuẩn hoá về stereo float32 cho sounddevice
            self._samples    = _to_stereo_f32(samples)
            self._samplerate = samplerate
            self._total_frames = len(self._samples)


    def play(self) -> None:
        """
        Bắt đầu phát từ vị trí cursor hiện tại.
        Nếu đang paused thì resume. Nếu hết file thì replay từ đầu.
        """
        if self._samples is None:
            return

        if self._state == "playing":
            return

        if self._state == "paused":
            self._state = "playing"
            print("Resume from pause")
            self._pause_event.set()    # unblock worker thread
            return

        # stopped hoặc đã hết → play từ đầu (hoặc từ cursor)
        if self._cursor >= self._total_frames:
            self._cursor = 0

        self._state = "playing"
        self._stop_event.clear()
        self._pause_event.set()

        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def pause(self) -> None:
        """Tạm dừng phát, giữ nguyên cursor."""
        if self._state == "playing":
            self._state = "paused"
            self._pause_event.clear()  # block worker thread

    def stop(self) -> None:
        """Dừng hẳn và reset cursor về đầu."""
        self._state = "stopped"
        self._pause_event.set()        # unblock nếu đang paused
        self._stop_event.set()         # báo worker thoát

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None

        with self._lock:
            self._cursor = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> str:
        """
        Trạng thái hiện tại.

        Returns:
            str: "stopped" | "playing" | "paused"
        """
        return self._state

    @property
    def current_sec(self) -> float:
        """
        Thời gian phát hiện tại (giây).

        Returns:
            float: vị trí cursor / samplerate
        """
        if self._samplerate == 0:
            return 0.0
        return self._cursor / self._samplerate #t = s/v

    @property
    def total_sec(self) -> float:
        """
        Tổng thời lượng (giây).

        Returns:
            float: total_frames / samplerate
        """
        if self._samplerate == 0:
            return 0.0
        return self._total_frames / self._samplerate

    def is_loaded(self) -> bool:
        """
        Kiểm tra đã load audio chưa.

        Returns:
            bool: True nếu đã load
        """
        return self._samples is not None

    # ------------------------------------------------------------------
    # Worker thread
    # ------------------------------------------------------------------

    def _worker(self) -> None:
        """
        Thread phát audio: đọc chunk → ghi vào OutputStream.
        Chạy cho đến khi hết file hoặc _stop_event được set.
        """
        try:
            with sd.OutputStream(
                samplerate=self._samplerate,
                channels=2,
                dtype="float32",
                blocksize=CHUNK_FRAMES,
            ) as stream:
                while not self._stop_event.is_set():

                    # --- Pause: block tại đây cho đến khi resume ---
                    self._pause_event.wait()
                    if self._stop_event.is_set():
                        break

                    # --- Lấy chunk ---
                    with self._lock:
                        start = self._cursor
                        end   = min(start + CHUNK_FRAMES, self._total_frames)
                        chunk = self._samples[start:end]
                        self._cursor = end

                    if len(chunk) == 0:
                        break  # hết file

                    # Pad chunk cuối nếu ngắn hơn CHUNK_FRAMES
                    if len(chunk) < CHUNK_FRAMES:
                        pad   = np.zeros((CHUNK_FRAMES - len(chunk), 2), dtype="float32")
                        chunk = np.vstack([chunk, pad])

                    stream.write(chunk)

                    # --- Tick callback để UI cập nhật timestamp ---
                    if self._on_tick:
                        self._on_tick(self.current_sec, self.total_sec)

                    # --- Kiểm tra đã hết file ---
                    if self._cursor >= self._total_frames:
                        break

        except Exception as e:
            print(f"[Player] Lỗi stream: {e}")

        finally:
            # Kết thúc: reset state
            prev_state = self._state
            self._state = "stopped"
            with self._lock:
                self._cursor = 0

            if self._on_finish and prev_state != "stopped":
                # Gọi on_finish từ main thread để tránh crash UI
                _call_on_main(self._on_finish)

# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------

def _to_stereo_f32(samples: np.ndarray) -> np.ndarray:
    """
    Chuyển samples về stereo float32 cho sounddevice.

    Args:
        samples (np.ndarray): (N,) mono hoặc (N,2) stereo, float64 hoặc float32

    Returns:
        np.ndarray: shape (N,2), dtype float32
    """
    if samples.ndim == 1:
        stereo = np.stack([samples, samples], axis=1)
    else:
        stereo = samples.copy()
    return stereo.astype("float32")


def _call_on_main(fn) -> None:
    """
    Lên lịch gọi fn trên main thread bằng cách dùng flag.
    Thực ra chỉ gọi thẳng — tkinter after() sẽ được dùng ở tầng App.

    Args:
        fn (callable): hàm cần gọi
    """
    try:
        fn()
    except Exception as e:
        print(f"[Player] on_finish error: {e}")