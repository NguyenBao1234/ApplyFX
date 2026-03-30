"""
export_panel.py
---------------
Panel xuất file âm thanh đã qua DSP ra đĩa.

Bố cục:
  ┌──────────────────────────────────────────────────┐
  │  EXPORT          [Format: WAV ▼]  [📁 Export]   │
  │  Output: C:/path/to/output.wav          [Browse] │
  │  [████████████████████░░░░░░] 72%  Đang xử lý..│
  └──────────────────────────────────────────────────┘

Render toàn bộ DSP chain trên thread riêng để không
block UI, hiển thị progress bar theo từng chunk.
"""

import threading
import os
from pathlib import Path
from tkinter import filedialog, messagebox

import numpy as np
import customtkinter as ctk
import soundfile as sf

from UI.style import COLOR, FONT, SIZE


# Định dạng export được hỗ trợ
_FORMATS = {
    "WAV  (PCM 16-bit)":  ("wav",  "PCM_16"),
    "WAV  (PCM 24-bit)":  ("wav",  "PCM_24"),
    "WAV  (Float 32-bit)":("wav",  "FLOAT"),
    "FLAC (Lossless)":    ("flac", None),
    "OGG  (Vorbis)":      ("ogg",  None),
    "MP3 ":      ("mp3",  None)
}

# Số frame xử lý mỗi chunk khi render (để cập nhật progress)
_RENDER_CHUNK = 44100 * 2   # ~2 giây


class ExportPanel(ctk.CTkFrame):
    """
    Panel xuất file audio đã qua DSP.

    Args:
        parent: widget cha
        get_engine (callable): trả về AudioEngine hiện tại
        get_processor (callable): trả về DSPProcessor hiện tại
    """

    def __init__(self, parent, *, get_engine, get_processor):
        super().__init__(parent,
                         fg_color=COLOR["bg_panel"],
                         corner_radius=SIZE["corner_radius"])

        self._get_engine    = get_engine
        self._get_processor = get_processor
        self._export_thread: threading.Thread | None = None
        self._is_exporting  = False

        self._build_ui()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Tạo layout: header, output path, progress bar."""
        self.columnconfigure(0, weight=1)

        # --- Row 0: Header + format + nút Export ---
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        top.columnconfigure(1, weight=1)

        ctk.CTkLabel(
            top, text="EXPORT",
            font=FONT["title"],
            text_color=COLOR["text_primary"]
        ).grid(row=0, column=0, sticky="w")

        # Dropdown format
        self._fmt_var = ctk.StringVar(value=list(_FORMATS.keys())[0])
        self._fmt_menu = ctk.CTkOptionMenu(
            top,
            values=list(_FORMATS.keys()),
            variable=self._fmt_var,
            font=FONT["label"],
            fg_color=COLOR["bg_card"],
            button_color=COLOR["accent_dim"],
            button_hover_color=COLOR["accent"],
            dropdown_fg_color=COLOR["bg_card"],
            dropdown_hover_color=COLOR["accent_dim"],
            text_color=COLOR["text_primary"],
            width=200,
        )
        self._fmt_menu.grid(row=0, column=1, padx=14, sticky="w")

        # Nút Export
        self._btn_export = ctk.CTkButton(
            top, text="📁  Export",
            font=FONT["label"],
            fg_color=COLOR["accent"],
            hover_color=COLOR["accent_dim"],
            corner_radius=SIZE["btn_corner_radius"],
            width=100, height=32,
            command=self._on_export_click
        )
        self._btn_export.grid(row=0, column=2)

        # --- Row 1: Output path + Browse ---
        path_row = ctk.CTkFrame(self, fg_color="transparent")
        path_row.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 6))
        path_row.columnconfigure(0, weight=1)

        self._path_var = ctk.StringVar(value="")
        self._entry_path = ctk.CTkEntry(
            path_row,
            textvariable=self._path_var,
            font=FONT["mono"],
            fg_color=COLOR["bg_card"],
            border_color=COLOR["separator"],
            text_color=COLOR["text_primary"],
            placeholder_text="Chưa chọn đường dẫn output...",
            height=30,
        )
        self._entry_path.grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(
            path_row, text="Browse",
            font=FONT["label_sm"],
            fg_color=COLOR["bg_card"],
            hover_color=COLOR["separator"],
            corner_radius=SIZE["btn_corner_radius"],
            width=70, height=30,
            command=self._on_browse
        ).grid(row=0, column=1)

        # --- Row 2: Progress bar + status ---
        prog_row = ctk.CTkFrame(self, fg_color="transparent")
        prog_row.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 12))
        prog_row.columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(
            prog_row,
            fg_color=COLOR["bg_card"],
            progress_color=COLOR["accent"],
            height=12,
            corner_radius=6,
        )
        self._progress.set(0)
        self._progress.grid(row=0, column=0, sticky="ew", padx=(0, 10))

        self._lbl_status = ctk.CTkLabel(
            prog_row, text="Sẵn sàng",
            font=FONT["label_sm"],
            text_color=COLOR["text_secondary"],
            width=120, anchor="w"
        )
        self._lbl_status.grid(row=0, column=1)

    # ------------------------------------------------------------------
    # Browse output path
    # ------------------------------------------------------------------

    def _on_browse(self) -> None:
        """Mở hộp thoại chọn nơi lưu file."""
        engine = self._get_engine()
        if not engine.is_loaded():
            messagebox.showwarning("Chưa có file", "Vui lòng import file âm thanh trước.")
            return

        # Gợi ý tên file dựa trên file gốc
        fmt_key  = self._fmt_var.get()
        ext      = _FORMATS[fmt_key][0]
        stem     = engine.filepath.stem if engine.filepath else "output"
        init_name = f"{stem}_processed.{ext}"

        path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu file",
            defaultextension=f".{ext}",
            initialfile=init_name,
            filetypes=[
                ("WAV",  "*.wav"),
                ("FLAC", "*.flac"),
                ("OGG",  "*.ogg"),
                ("All",  "*.*"),
            ]
        )
        if path:
            self._path_var.set(path)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _on_export_click(self) -> None:
        """Validate rồi bắt đầu export trên thread riêng."""
        if self._is_exporting:
            return

        engine = self._get_engine()
        if not engine.is_loaded():
            messagebox.showwarning("Chưa có file", "Vui lòng import file âm thanh trước.")
            return

        out_path = self._path_var.get().strip()
        if not out_path:
            # Nếu chưa chọn path thì mở Browse luôn
            self._on_browse()
            out_path = self._path_var.get().strip()
            if not out_path:
                return

        # Tạo thư mục nếu chưa có
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)

        fmt_key   = self._fmt_var.get()
        fmt_ext, subtype = _FORMATS[fmt_key]

        self._start_export(engine, out_path, fmt_ext, subtype)

    def _start_export(self, engine, out_path: str,
                      fmt_ext: str, subtype: str | None) -> None:
        """
        Khởi động thread export.

        Args:
            engine: AudioEngine đang có data
            out_path (str): đường dẫn file output
            fmt_ext (str): "wav" | "flac" | "ogg"
            subtype (str | None): "PCM_16" | "PCM_24" | "FLOAT" | None
        """
        self._is_exporting = True
        self._btn_export.configure(state="disabled", text="Đang xuất...")
        self._progress.set(0)
        self._lbl_status.configure(text="Đang khởi động...")

        processor = self._get_processor()
        samples   = engine.get_stereo().copy()
        sr        = engine.samplerate

        self._export_thread = threading.Thread(
            target=self._render_and_write,
            args=(samples, sr, processor, out_path, fmt_ext, subtype),
            daemon=True
        )
        self._export_thread.start()

    def _render_and_write(self, samples: np.ndarray, sr: int,
                          processor, out_path: str,
                          fmt_ext: str, subtype: str | None) -> None:
        """
        Render DSP + ghi file — chạy trên worker thread.

        Chia samples thành chunk để cập nhật progress bar.

        Args:
            samples (np.ndarray): samples gốc stereo (N,2)
            sr (int): sample rate
            processor: DSPProcessor
            out_path (str): đường dẫn output
            fmt_ext (str): định dạng file
            subtype (str | None): subtype soundfile
        """
        try:
            total  = len(samples)
            chunks = []
            done   = 0

            self._update_status(0.0, "Đang render DSP...")

            # Render từng chunk để báo progress
            while done < total:
                end   = min(done + _RENDER_CHUNK, total)
                chunk = samples[done:end]

                # Áp dụng toàn bộ DSP chain lên chunk
                processed = processor.process(chunk)
                chunks.append(processed)

                done = end
                self._update_status(done / total * 0.85,
                                    f"Render... {int(done/total*100)}%")

            # Ghép tất cả chunk lại
            self._update_status(0.87, "Ghép dữ liệu...")
            output = np.concatenate(chunks, axis=0)
            output = np.clip(output, -1.0, 1.0)

            # Ghi file
            self._update_status(0.92, "Ghi file...")
            write_kwargs = dict(samplerate=sr)
            if subtype:
                write_kwargs["subtype"] = subtype

            sf.write(out_path, output, **write_kwargs)

            self._update_status(1.0, "✅ Hoàn thành!")
            self._on_export_done(success=True, path=out_path)

        except Exception as e:
            self._update_status(0.0, f"❌ Lỗi: {e}")
            self._on_export_done(success=False, path=str(e))

    # ------------------------------------------------------------------
    # Thread → main thread bridge
    # ------------------------------------------------------------------

    def _update_status(self, progress: float, text: str) -> None:
        """
        Cập nhật progress bar và label — schedule về main thread.

        Args:
            progress (float): 0.0 → 1.0
            text (str): nội dung hiển thị
        """
        try:
            self.after(0, self._do_update_status, progress, text)
        except Exception:
            pass

    def _do_update_status(self, progress: float, text: str) -> None:
        """
        Thực sự cập nhật UI — chạy trên main thread.

        Args:
            progress (float): giá trị progress bar
            text (str): status text
        """
        self._progress.set(progress)
        self._lbl_status.configure(text=text)

    def _on_export_done(self, success: bool, path: str) -> None:
        """
        Khi export xong — schedule về main thread để reset UI.

        Args:
            success (bool): True nếu thành công
            path (str): path output (hoặc error message nếu thất bại)
        """
        self.after(0, self._do_export_done, success, path)

    def _do_export_done(self, success: bool, path: str) -> None:
        """
        Reset UI sau khi export xong — chạy trên main thread.

        Args:
            success (bool): True nếu thành công
            path (str): đường dẫn file hoặc error message
        """
        self._is_exporting = False
        self._btn_export.configure(state="normal", text="📁  Export")

        if success:
            filename = Path(path).name
            messagebox.showinfo(
                "Export thành công",
                f"Đã lưu file:\n{filename}\n\nĐường dẫn:\n{path}"
            )
        else:
            messagebox.showerror("Export thất bại", f"Lỗi:\n{path}")