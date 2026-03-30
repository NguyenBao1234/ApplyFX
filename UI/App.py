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

from Playback.Player import Player
from UI.Components.effect_panel import EffectsPanel
from UI.Components.export_panel import ExportPanel
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
    APP_HEIGHT = 980
    MIN_WIDTH  = 700
    MIN_HEIGHT = 980

    def __init__(self):
        apply_theme()
        super().__init__()

        self._engine    = AudioEngine()
        self._processor = DSPProcessor()

        self._player_orig = Player(
            on_tick= lambda curSec, totalSec: self._schedule_tick("orig", curSec, totalSec),
            on_finish= lambda: self._schedule_finish("orig"),
        )
        self._player_prev = Player(
            on_tick= lambda curSec, totalSec: self._schedule_tick("prev", curSec, totalSec),
            on_finish= lambda: self._schedule_finish("prev"),
        )
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
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)

        self._build_header()       # row 0
        self._build_file_info()    # row 1
        self._build_transports()   # row 2 & 3
        self._build_eq_panel()     # row 4
        self._build_effects_panel()# row 5
        self._build_export_panel()

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

    def _build_effects_panel(self):
        self._effects_panel = EffectsPanel(
            self,
            on_preset_change=self._on_preset_change
        )
        self._effects_panel.grid(row=5, column=0,
                                 padx=16, pady=(0, 14), sticky="nsew")

    def _build_export_panel(self):
            """Export Panel: chọn format và xuất file đã xử lý."""
            self._export_panel = ExportPanel(
                self,
                get_engine=lambda: self._engine,
                get_processor=lambda: self._processor,
            )
            self._export_panel.grid(row=6, column=0,
                                    padx=16, pady=(0, 14), sticky="ew")

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------

    def _on_import(self) -> None:
        """Mở hộp thoại chọn file âm thanh."""
        path = filedialog.askopenfilename(
            title="Chọn file âm thanh",
            filetypes=[
                ("Audio files", "*.wav *.flac *.ogg *.aiff *.aif *.mp3"),
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

        # Dừng cả 2 player, đề phòng đang phát, mà import
        self._player_orig.stop()
        self._player_prev.stop()
        self._transport_orig.force_stop()
        self._transport_prev.force_stop()

        # Cập nhật processor sample rate
        self._processor.samplerate = self._engine.samplerate
        self._processor.reset()
        self._eq_panel.reset()

        # Load samples gốc vào Original player
        self._player_orig.load(self._engine.get_stereo(), self._engine.samplerate)

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
        if self._player_prev.state == "playing":
            self._player_prev.stop()
            self._load_preview_player()
            self._transport_prev.force_stop()

    def _on_preset_change(self, preset) -> None:
        """
        Nhận preset từ EffectsPanel, áp dụng lên processor và cập nhật sliders.

        Args:
            preset (Preset): preset đã được chọn và Apply
        """
        self._processor.load_preset(preset)
        self._eq_panel.set_values(self._processor.get_slider_values())

    # ------------------------------------------------------------------
    # Preview rendering
    # ------------------------------------------------------------------
    def _load_preview_player(self) -> None:
        """
        Render samples gốc qua toàn bộ DSP chain rồi load vào Preview player.
        Gọi trước mỗi lần Play Preview hoặc khi params thay đổi lúc đang play.
        """
        if not self._engine.is_loaded():
            return
        processed = self._processor.process(self._engine.get_stereo())
        self._player_prev.load(processed, self._engine.samplerate)

    def _schedule_tick(self, track: str, cur: float, tot: float) -> None:
        """
        Nhận tick từ Player worker thread, chuyển về main thread qua after().

        Args:
            track (str): "orig" hoặc "prev"
            cur (float): giây hiện tại
            tot (float): tổng giây
        """
        self.after(0, self._do_tick, track, cur, tot)

    def _do_tick(self, track: str, cur: float, tot: float) -> None:
        """
        Cập nhật timestamp trên TransportBar (chạy trên main thread).

        Args:
            track (str): "orig" hoặc "prev"
            cur (float): giây hiện tại
            tot (float): tổng giây
        """
        bar = self._transport_orig if track == "orig" else self._transport_prev
        bar.update_time(cur, tot)
    def _on_transport(self, track: str, action: str) -> None:
        """
        Stub xử lý transport

        Args:
            track (str): "orig" hoặc "prev"
            action (str): "play" | "pause" | "stop"
        """
        player  = self._player_orig if track == "orig" else self._player_prev
        other_player = self._player_prev if track == "orig" else self._player_orig
        other_transport = self._transport_prev if track == "orig" else self._transport_orig
        # Khi 1 track play, dừng track kia
        if action == "play":
            if other_player.state == "playing":
                other_player.stop()
                other_transport.force_stop()
            if track == "prev":
                self._load_preview_player()
            player.play()

        elif action == "pause":
            player.pause()

        elif action == "stop":
            player.stop()

        print(f"[Transport] {track} - {action}")

    def _schedule_finish(self, track: str):
        """
       Nhận tín hiệu hết file từ worker thread, chuyển về main thread.

       Args:
           track (str): "orig" hoặc "prev"
       """
        self.after(0, self._do_finish, track)

    def _do_finish(self, track: str) -> None:
        """
        Phát xong: reset TransportBar, timestamp về 00:00.

        Args:
            track (str): "orig" hoặc "prev"
        """
        bar = self._transport_orig if track == "orig" else self._transport_prev
        total = self._engine.duration_sec if self._engine.is_loaded() else 0
        bar.force_stop()
        bar.update_time(0, total)

    def _on_close(self) -> None:
        """Dừng tất cả player trước khi thoát để tránh thread leak."""
        self._player_orig.stop()
        self._player_prev.stop()
        self.destroy()

def run() -> None:
    """Khởi chạy ứng dụng."""
    app = App()
    app.mainloop()