"""
transport_bar.py
----------------
Widget Transport Bar — Play / Pause / Stop + hiển thị thời gian.

Mỗi TransportBar đại diện cho 1 track (Original hoặc Preview).
App tạo 2 instance độc lập nhau.

Trạng thái nội bộ: "stopped" | "playing" | "paused"
"""

import customtkinter as ctk
from UI.style import COLOR, FONT, SIZE


class TransportBar(ctk.CTkFrame):
    """
    Widget điều khiển phát nhạc cho 1 track.

    Args:
        parent: widget cha
        title (str): tiêu đề track (VD: "Original", "Preview")
        on_play (callable): callback() khi nhấn Play
        on_pause (callable): callback() khi nhấn Pause
        on_stop (callable): callback() khi nhấn Stop
    """

    def __init__(self, parent, *,
                 title: str      = "Track",
                 on_play         = None,
                 on_pause        = None,
                 on_stop         = None):
        super().__init__(parent,
                         fg_color=COLOR["bg_card"],
                         corner_radius=SIZE["corner_radius"])

        self._on_play  = on_play
        self._on_pause = on_pause
        self._on_stop  = on_stop
        self._state    = "stopped"   # "stopped" | "playing" | "paused"

        self._build_ui(title)

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build_ui(self, title: str) -> None:
        """Tạo layout: title | timestamp | buttons."""

        self.columnconfigure(0, weight=1)  # title co giãn
        self.columnconfigure(1, weight=0)  # timestamp cố định
        self.columnconfigure(2, weight=0)  # buttons cố định

        # --- Title ---
        self._lbl_title = ctk.CTkLabel(
            self, text=title,
            font=FONT["title"],
            text_color=COLOR["text_primary"]
        )
        self._lbl_title.grid(row=0, column=0,
                             padx=(14, 6), pady=14, sticky="w")

        # --- Timestamp ---
        self._lbl_time = ctk.CTkLabel(
            self, text="00:00 / 00:00",
            font=FONT["mono"],
            text_color=COLOR["text_secondary"]
        )
        self._lbl_time.grid(row=0, column=1,
                            padx=12, pady=14)

        # --- Buttons frame ---
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=(6, 14), pady=10)

        btn_cfg = dict(
            width=70, height=34,
            corner_radius=SIZE["btn_corner_radius"],
            font=FONT["label"],
            border_width=0
        )

        self._btn_play = ctk.CTkButton(
            btn_frame, text="▶  Play",
            fg_color=COLOR["btn_play"],
            hover_color=COLOR["btn_play"],
            command=self._handle_play,
            **btn_cfg
        )
        self._btn_play.grid(row=0, column=0, padx=4)

        self._btn_pause = ctk.CTkButton(
            btn_frame, text="⏸ Pause",
            fg_color=COLOR["btn_pause"],
            hover_color=COLOR["btn_pause"],
            command=self._handle_pause,
            state="disabled",
            **btn_cfg
        )
        self._btn_pause.grid(row=0, column=1, padx=4)

        self._btn_stop = ctk.CTkButton(
            btn_frame, text="■  Stop",
            fg_color=COLOR["btn_stop"],
            hover_color=COLOR["btn_stop"],
            command=self._handle_stop,
            state="disabled",
            **btn_cfg
        )
        self._btn_stop.grid(row=0, column=2, padx=4)

    # ------------------------------------------------------------------
    # Handlers nội bộ
    # ------------------------------------------------------------------

    def _handle_play(self) -> None:
        """Xử lý nhấn Play: chuyển state và gọi callback."""
        if self._state in ("stopped", "paused"):
            self._state = "playing"
            self._sync_buttons()
            if self._on_play:
                self._on_play()

    def _handle_pause(self) -> None:
        """Xử lý nhấn Pause."""
        if self._state == "playing":
            self._state = "paused"
            self._sync_buttons()
            if self._on_pause:
                self._on_pause()

    def _handle_stop(self) -> None:
        """Xử lý nhấn Stop: reset về đầu."""
        self._state = "stopped"
        self._sync_buttons()
        if self._on_stop:
            self._on_stop()

    def _sync_buttons(self) -> None:
        """Cập nhật trạng thái enable/disable của buttons theo state."""
        if self._state == "playing":
            self._btn_play .configure(state="disabled")
            self._btn_pause.configure(state="normal")
            self._btn_stop .configure(state="normal")
        elif self._state == "paused":
            self._btn_play .configure(state="normal",  text="▶  Resume")
            self._btn_pause.configure(state="disabled")
            self._btn_stop .configure(state="normal")
        else:  # stopped
            self._btn_play .configure(state="normal",  text="▶  Play")
            self._btn_pause.configure(state="disabled")
            self._btn_stop .configure(state="disabled")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_time(self, current_sec: float, total_sec: float) -> None:
        """
        Cập nhật hiển thị thời gian — gọi từ playback engine mỗi ~100ms.

        Args:
            current_sec (float): thời gian hiện tại (giây)
            total_sec (float): tổng thời lượng (giây)
        """
        self._lbl_time.configure(text=f"{_fmt(current_sec)} / {_fmt(total_sec)}")
        print(f"{_fmt(current_sec)} / {_fmt(total_sec)}")

    def force_stop(self) -> None:
        """
        Buộc chuyển về trạng thái stopped từ bên ngoài
        (VD: khi hết file, hoặc load file mới).
        """
        self._state = "stopped"
        self._sync_buttons()

    def set_enabled(self, enabled: bool) -> None:
        """
        Bật/tắt toàn bộ transport bar (khi chưa load file).

        Args:
            enabled (bool): True = bật, False = tắt (grey out)
        """
        state = "normal" if enabled else "disabled"
        # Play luôn available khi enabled, buttons khác theo state
        self._btn_play.configure(state=state if enabled else "disabled")
        if not enabled:
            self._btn_pause.configure(state="disabled")
            self._btn_stop .configure(state="disabled")
            self._state = "stopped"

    @property
    def state(self) -> str:
        """
        Trạng thái hiện tại của transport.

        Returns:
            str: "stopped" | "playing" | "paused"
        """
        return self._state


# ------------------------------------------------------------------
# Utility
# ------------------------------------------------------------------

def _fmt(seconds: float) -> str:
    """
    Chuyển giây → chuỗi MM:SS.

    Args:
        seconds (float): số giây

    Returns:
        str: VD "03:24"
    """
    total = max(0, int(seconds))
    m, s  = divmod(total, 60)
    return f"{m:02d}:{s:02d}"