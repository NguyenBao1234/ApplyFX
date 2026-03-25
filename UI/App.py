"""
app.py
------
MainWindow — cửa sổ chính của Apply FX

Layout tổng thể (từ trên xg):

  │  Header: tên app + nút Import

  │  File info bar (tên file, sr, dur)

  │  Transport — Original

  │  Transport — Preview

  │  EQ Panel (6 sliders)

  │  Effects Panel (dropdown + params)

"""

from tkinter import filedialog, messagebox
import customtkinter as ctk

from UI.style import COLOR, FONT, SIZE, apply_theme
from UI.Components.eq_panel      import EQPanel
from UI.Components.transport_bar import TransportBar
from Core.audio_engine  import AudioEngine
from Core.Processor import DSPProcessor


class App(ctk.CTk):
    """
    Cửa sổ chính của Apply FX.

    Quản lý:
        - AudioEngine: đọc file
        - DSPProcessor: áp dụng DSP
        - EQPanel: 6 slider điều chỉnh
        - 2x TransportBar: điều khiển phát (stub ở phase này)
    """

    APP_TITLE  = "Apply FX"
    APP_WIDTH  = 780
    APP_HEIGHT = 720
    MIN_WIDTH  = 700
    MIN_HEIGHT = 620

    def __init__(self):
        apply_theme()
        super().__init__()

        self._engine    = AudioEngine()
        self._processor = DSPProcessor()

        self._setup_window()
        self._build_ui()

    # ------------------------------------------------------------------
    # Window setup
    # ------------------------------------------------------------------

    def _setup_window(self) -> None:
        """Cấu hình cửa sổ chính."""
        self.title(self.APP_TITLE)
        self.geometry(f"{self.APP_WIDTH}x{self.APP_HEIGHT}")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self.configure(fg_color=COLOR["bg_root"])

        # Căn giữa màn hình
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self.APP_WIDTH)  // 2
        y  = (sh - self.APP_HEIGHT) // 2
        self.geometry(f"{self.APP_WIDTH}x{self.APP_HEIGHT}+{x}+{y}")

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Tạo toàn bộ layout chính."""
        self.rowconfigure(4, weight=1)      # EQ Panel co giãn
        self.columnconfigure(0, weight=1)

        self._build_header()       # row 0
        self._build_file_info()    # row 1
        self._build_transports()   # row 2 & 3
        self._build_eq_panel()     # row 4

    # --- Header ---

    def _build_header(self) -> None:
        """Header: logo text + nút Import File."""
        frame = ctk.CTkFrame(self, fg_color=COLOR["bg_panel"],
                             corner_radius=0)
        frame.grid(row=0, column=0, sticky="ew")
        frame.columnconfigure(0, weight=1)

        # Logo
        ctk.CTkLabel(
            frame, text="🎛 Apply FX",
            font=FONT["header"],
            text_color=COLOR["accent"]
        ).grid(row=0, column=0, padx=20, pady=14, sticky="w")

        # Nút Import
        self._btn_import = ctk.CTkButton(
            frame, text="📂  Import File",
            font=FONT["label"],
            fg_color=COLOR["btn_import"],
            hover_color="#1a6a9a",
            corner_radius=SIZE["btn_corner_radius"],
            width=130, height=36,
            command=self._on_import
        )
        self._btn_import.grid(row=0, column=1, padx=20, pady=14)

        # Nút Reset
        self._btn_reset = ctk.CTkButton(
            frame, text="↺  Reset",
            font=FONT["label"],
            fg_color=COLOR["bg_card"],
            hover_color=COLOR["separator"],
            corner_radius=SIZE["btn_corner_radius"],
            width=90, height=36,
            command=self._on_reset
        )
        self._btn_reset.grid(row=0, column=2, padx=(0, 20), pady=14)



    # --- File info bar ---

    def _build_file_info(self) -> None:
        """Thanh hiển thị thông tin file đang load."""
        frame = ctk.CTkFrame(self, fg_color=COLOR["separator"],
                             corner_radius=0, height=2)
        frame.grid(row=1, column=0, sticky="ew")

        self._lbl_file_info = ctk.CTkLabel(
            self, text="Chưa có file — nhấn Import để bắt đầu",
            font=FONT["label_sm"],
            text_color=COLOR["text_secondary"]
        )
        self._lbl_file_info.grid(row=1, column=0,
                                 padx=20, pady=6, sticky="w")

    # --- Transport bars ---

    def _build_transports(self) -> None:
        """Tạo 2 transport bars: Original và Preview."""
        pad = dict(padx=16, pady=(8, 4), sticky="ew")

        # Transport — Original (stub: chưa kết nối player)
        self._transport_orig = TransportBar(
            self,
            title="▶  Original",
            on_play  = lambda: self._on_transport("orig", "play"),
            on_pause = lambda: self._on_transport("orig", "pause"),
            on_stop  = lambda: self._on_transport("orig", "stop"),
        )
        self._transport_orig.grid(row=2, column=0, **pad)
        self._transport_orig.set_enabled(False)

        # Transport — Preview (stub)
        self._transport_prev = TransportBar(
            self,
            title="🎚  Preview",
            on_play  = lambda: self._on_transport("prev", "play"),
            on_pause = lambda: self._on_transport("prev", "pause"),
            on_stop  = lambda: self._on_transport("prev", "stop"),
        )
        self._transport_prev.grid(row=3, column=0,
                                  padx=16, pady=(4, 8), sticky="ew")
        self._transport_prev.set_enabled(False)

    # --- EQ Panel ---

    def _build_eq_panel(self) -> None:
        """EQ Panel với 6 slider dọc."""
        self._eq_panel = EQPanel(
            self,
            on_param_change=self._on_param_change )
        self._eq_panel.grid(row=4, column=0,
                            padx=16, pady=(0, 12), sticky="nsew")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_import(self) -> None:
        """Mở hộp thoại chọn file âm thanh."""
        path = filedialog.askopenfilename(
            title="Chọn file âm thanh",
            filetypes=[
                ("Audio files", "*.wav *.flac *.ogg *.aiff *.aif"),
                ("WAV",  "*.wav"),
                ("FLAC", "*.flac"),
                ("All",  "*.*"),
            ]
        )
        if not path:
            return

        try:
            self._engine.load(path)
        except (ValueError, RuntimeError) as e:
            messagebox.showerror("Lỗi đọc file", str(e))
            return

        # Cập nhật processor sample rate
        self._processor.samplerate = self._engine.samplerate
        self._processor.reset()
        self._eq_panel.reset()

        # Cập nhật UI
        self._lbl_file_info.configure(text=self._engine.info_str)
        total = self._engine.duration_sec
        self._transport_orig.update_time(0, total)
        self._transport_prev.update_time(0, total)
        self._transport_orig.set_enabled(True)
        self._transport_prev.set_enabled(True)

    def _on_reset(self) -> None:
        """Reset tất cả slider và processor về mặc định."""
        self._processor.reset()
        self._eq_panel.reset()

    def _on_param_change(self, key: str, value: float) -> None:
        """
        Nhận thay đổi từ EQPanel và cập nhật DSPProcessor.

        Args:
            key (str): tên tham số ("vol", "bass", "mid", "hi", "echo", "pan")
            value (float): giá trị mới
        """
        self._processor.set_param(key, value)
        # Phase 4 sẽ trigger re-render preview ở đây

    def _on_transport(self, track: str, action: str) -> None:
        """
        Stub xử lý transport — sẽ kết nối Player thực ở Phase 4.

        Args:
            track (str): "orig" hoặc "prev"
            action (str): "play" | "pause" | "stop"
        """
        # Khi 1 track play, dừng track kia
        if action == "play":
            if track == "orig":
                self._transport_prev.force_stop()
            else:
                self._transport_orig.force_stop()

        print(f"[Transport] {track} → {action}")  # debug, xóa ở phase 4


def run() -> None:
    """Khởi chạy ứng dụng."""
    app = App()
    app.mainloop()