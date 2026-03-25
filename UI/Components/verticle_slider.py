"""
vertical_slider.py
------------------
Widget thanh trượt dọc tuỳ chỉnh dùng tkinter Canvas.

Vì customtkinter không có slider dọc built-in,
ta vẽ thủ công: track + thumb hình tròn + label giá trị.

Dùng callback on_change để thông báo khi giá trị thay đổi.
"""

import tkinter as tk
import customtkinter as ctk
from UI.style import COLOR, FONT, SIZE


class VerticalSlider(ctk.CTkFrame):
    """
    Widget thanh trượt dọc có label tên và hiển thị giá trị hiện tại.

    Args:
        parent: widget cha
        label (str): tên hiển thị phía trên slider (VD: "BASS")
        unit (str): đơn vị hiển thị (VD: "dB", "", "x")
        min_val (float): giá trị nhỏ nhất
        max_val (float): giá trị lớn nhất
        default_val (float): giá trị khởi tạo
        on_change (callable): callback(value: float) khi kéo slider
        fmt (str): format string cho giá trị (VD: "{:+.1f}", "{:.2f}")
    """

    def __init__(self, parent, *,
                 label: str       = "PARAM",
                 unit: str        = "",
                 min_val: float   = -12.0,
                 max_val: float   = 12.0,
                 default_val: float = 0.0,
                 on_change       = None,
                 fmt: str         = "{:+.1f}"):

        super().__init__(parent,
                         fg_color=COLOR["bg_panel"],
                         corner_radius=SIZE["corner_radius"])

        self._min      = min_val
        self._max      = max_val
        self._value    = default_val
        self._on_change = on_change
        self._fmt      = fmt
        self._unit     = unit
        self._dragging = False

        # Kích thước canvas
        self._cw = SIZE["slider_width"]
        self._ch = SIZE["slider_height"]
        self._track_x   = self._cw // 2          # x tâm track
        self._track_top = 12                      # y đầu track
        self._track_bot = self._ch - 12           # y cuối track
        self._track_len = self._track_bot - self._track_top

        self._build_ui(label)
        self._drawSlider()

    # ------------------------------------------------------------------
    # Build layout
    # ------------------------------------------------------------------

    def _build_ui(self, label: str) -> None:
        """Tạo các widget con: label tên, canvas, label giá trị."""
        self.columnconfigure(0, weight=1)

        # Label tên (trên đầu)
        self._lbl_name = ctk.CTkLabel(
            self, text=label,
            font=FONT["label"],
            text_color=COLOR["text_secondary"]
        )
        self._lbl_name.grid(row=0, column=0, pady=(8, 2))

        # Canvas vẽ slider
        self._canvas = tk.Canvas(
            self,
            width=self._cw,
            height=self._ch,
            bg=COLOR["bg_panel"],
            highlightthickness=0,
            cursor="hand2"
        )
        self._canvas.grid(row=1, column=0, padx=10)

        # Label giá trị (dưới đáy)
        self._lbl_val = ctk.CTkLabel(
            self, text=self._format_value(),
            font=FONT["value"],
            text_color=COLOR["text_value"]
        )
        self._lbl_val.grid(row=2, column=0, pady=(2, 8))

        # Bind sự kiện chuột
        self._canvas.bind("<ButtonPress-1>",   self._on_press)
        self._canvas.bind("<B1-Motion>",        self._on_drag)
        self._canvas.bind("<ButtonRelease-1>",  self._on_release)
        self._canvas.bind("<MouseWheel>",       self._on_scroll)
        self._canvas.bind("<Enter>",            self._on_enter)
        self._canvas.bind("<Leave>",            self._on_leave)

    # ------------------------------------------------------------------
    # Vẽ
    # ------------------------------------------------------------------

    def _val_to_y(self, value: float) -> int:
        """Chuyển giá trị → toạ độ y trên canvas (trên=max, dưới=min)."""
        ratio = (value - self._min) / (self._max - self._min)
        ratio = max(0.0, min(1.0, ratio))
        return int(self._track_bot - ratio * self._track_len)

    def _y_to_val(self, y: int) -> float:
        """Chuyển toạ độ y → giá trị."""
        ratio = (self._track_bot - y) / self._track_len
        ratio = max(0.0, min(1.0, ratio))
        return self._min + ratio * (self._max - self._min)

    def _drawSlider(self) -> None:
        """Vẽ lại toàn bộ slider."""
        c = self._canvas
        c.delete("all")

        cx     = self._track_x
        top    = self._track_top
        bot    = self._track_bot
        thumb_r = SIZE["thumb_radius"]
        thumb_y = self._val_to_y(self._value)

        # --- Track nền (màu tối) ---
        c.create_rounded_rect = _rounded_rect  # gán helper
        _rounded_rect(c, cx - SIZE["track_width"]//2, top,
                         cx + SIZE["track_width"]//2, bot,
                         r=3, fill=COLOR["bg_slider"], outline="")

        # --- Track fill (từ giá trị 0 lên thumb) ---
        zero_y = self._val_to_y(0.0)  # vị trí y tương ứng với 0
        fill_top = min(thumb_y, zero_y)
        fill_bot = max(thumb_y, zero_y)
        if fill_bot > fill_top:
            c.create_rectangle(
                cx - SIZE["track_width"]//2 + 1, fill_top,
                cx + SIZE["track_width"]//2 - 1, fill_bot,
                fill=COLOR["accent_dim"], outline=""
            )

        # --- Vạch chia giữa (0 dB) ---
        c.create_line(cx - 8, zero_y, cx + 8, zero_y,
                      fill=COLOR["text_secondary"], width=1, dash=(3, 3))

        # --- Thumb ---
        thumb_color = COLOR["thumb_hover"] if self._dragging else COLOR["thumb"]
        c.create_oval(
            cx - thumb_r, thumb_y - thumb_r,
            cx + thumb_r, thumb_y + thumb_r,
            fill=thumb_color, outline=COLOR["bg_panel"], width=2
        )

    # ------------------------------------------------------------------
    # Sự kiện chuột
    # ------------------------------------------------------------------

    def _on_press(self, event) -> None:
        self._dragging = True
        self._update_from_y(event.y)

    def _on_drag(self, event) -> None:
        if self._dragging:
            self._update_from_y(event.y)
            self._drawSlider()

    def _on_release(self, event) -> None:
        self._dragging = False
        self._drawSlider()

    def _on_scroll(self, event) -> None:
        """Cuộn chuột để chỉnh giá trị nhỏ."""
        step = (self._max - self._min) / 100.0
        delta = event.delta / 120  # Windows: 120 per notch
        self._set_value(self._value + delta * step)
        self._drawSlider()

    def _on_enter(self, event) -> None:
        self._canvas.configure(cursor="hand2")

    def _on_leave(self, event) -> None:
        if not self._dragging:
            self._dragging = False
            self._drawSlider()

    def _update_from_y(self, y: int) -> None:
        """Cập nhật giá trị từ toạ độ y chuột."""
        val = self._y_to_val(y)
        self._set_value(val)

    # ------------------------------------------------------------------
    # Giá trị
    # ------------------------------------------------------------------

    def _set_value(self, value: float) -> None:
        """Đặt giá trị, redraw, gọi callback."""
        self._value = max(self._min, min(self._max, value))
        self._lbl_val.configure(text=self._format_value())
        self._draw()
        if self._on_change:
            self._on_change(self._value)

    def _format_value(self) -> str:
        """Format giá trị thành chuỗi hiển thị."""
        try:
            text = self._fmt.format(self._value)
        except Exception:
            text = f"{self._value:.1f}"
        if self._unit:
            text += f" {self._unit}"
        return text

    def get(self) -> float:
        """
        Trả về giá trị hiện tại của slider.

        Returns:
            float: giá trị trong [min_val, max_val]
        """
        return self._value

    def set(self, value: float) -> None:
        """
        Đặt giá trị slider từ bên ngoài (VD: khi load preset).
        Không gọi callback.

        Args:
            value (float): giá trị mới
        """
        self._value = max(self._min, min(self._max, value))
        self._lbl_val.configure(text=self._format_value())
        self._draw()

    def set_silent(self, value: float) -> None:
        """
        Đặt giá trị mà không trigger callback on_change.
        Dùng khi load preset để tránh vòng lặp sự kiện.

        Args:
            value (float): giá trị mới
        """
        cb = self._on_change
        self._on_change = None
        self.set(value)
        self._on_change = cb
        self._drawSlider()


# ------------------------------------------------------------------
# Helper vẽ hình chữ nhật bo góc trên Canvas
# ------------------------------------------------------------------

def _rounded_rect(canvas: tk.Canvas, x1, y1, x2, y2,
                  r=5, **kwargs) -> None:
    """
    Vẽ hình chữ nhật bo góc trên tk.Canvas.

    Args:
        canvas (tk.Canvas): canvas cần vẽ
        x1, y1 (int): góc trên trái
        x2, y2 (int): góc dưới phải
        r (int): bán kính bo góc
        **kwargs: tham số truyền thêm cho create_polygon
    """
    points = [
        x1+r, y1,
        x2-r, y1,
        x2,   y1+r,
        x2,   y2-r,
        x2-r, y2,
        x1+r, y2,
        x1,   y2-r,
        x1,   y1+r,
    ]
    canvas.create_polygon(points, smooth=True, **kwargs)