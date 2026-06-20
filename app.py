import json
import os
import re
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

from scripts.ai_distillation import PROVIDER_PRESETS, distill_text_file


class DistillationApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("长篇网文蒸馏器 - Windows 版")
        self.root.geometry("1080x760")
        self.root.minsize(1024, 700)

        self.input_path: str | None = None
        self.output_dir: str | None = None
        self.config_path = Path(os.getenv("APPDATA", str(Path.home()))) / "novel_distillation" / "config.json"
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        self._build_ui()
        self._load_config()

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Title.TLabel", font=("Microsoft YaHei", 18, "bold"), foreground="#1f4e79")
        style.configure("Subtitle.TLabel", font=("Microsoft YaHei", 10), foreground="#4a4a4a")
        style.configure("Field.TLabel", font=("Microsoft YaHei", 10))
        style.configure("Header.TLabelframe.Label", font=("Microsoft YaHei", 11, "bold"))
        style.configure("Progress.TProgressbar", thickness=14)

        main = ttk.Frame(self.root, padding=16)
        main.pack(fill="both", expand=True)

        header = ttk.Frame(main)
        header.pack(fill="x", pady=(0, 10))
        ttk.Label(header, text="长篇网文蒸馏器", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header, text="上传作品文本，填写密钥，自动生成高保真蒸馏档案。", style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))

        left = ttk.Frame(main)
        left.pack(side="left", fill="both", expand=True)
        right = ttk.Frame(main)
        right.pack(side="right", fill="both", expand=True, padx=(12, 0))

        config_frame = ttk.LabelFrame(left, text="模型配置", padding=12)
        config_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(config_frame, text="模型提供商：", style="Field.TLabel").grid(row=0, column=0, sticky="w", pady=4)
        self.provider_var = tk.StringVar()
        self.provider_combo = ttk.Combobox(config_frame, textvariable=self.provider_var, state="readonly", width=40)
        self.provider_combo["values"] = list(PROVIDER_PRESETS.keys())
        self.provider_combo.grid(row=0, column=1, sticky="ew", pady=4, padx=(8, 0))
        self.provider_combo.bind("<<ComboboxSelected>>", self._on_provider_changed)

        ttk.Label(config_frame, text="API Key：", style="Field.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        self.api_key_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.api_key_var, width=50, show="*").grid(row=1, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(config_frame, text="Base URL：", style="Field.TLabel").grid(row=2, column=0, sticky="w", pady=4)
        self.base_url_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.base_url_var, width=50).grid(row=2, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(config_frame, text="Model：", style="Field.TLabel").grid(row=3, column=0, sticky="w", pady=4)
        self.model_var = tk.StringVar()
        ttk.Entry(config_frame, textvariable=self.model_var, width=50).grid(row=3, column=1, sticky="ew", pady=4, padx=(8, 0))

        ttk.Label(config_frame, text="作品标题：", style="Field.TLabel").grid(row=4, column=0, sticky="w", pady=4)
        self.title_var = tk.StringVar(value="未命名作品")
        ttk.Entry(config_frame, textvariable=self.title_var, width=50).grid(row=4, column=1, sticky="ew", pady=4, padx=(8, 0))

        config_frame.columnconfigure(1, weight=1)

        files_frame = ttk.LabelFrame(left, text="输入与输出", padding=12)
        files_frame.pack(fill="x", pady=(0, 10))

        ttk.Button(files_frame, text="选择输入文件", command=self._choose_input_file).grid(row=0, column=0, sticky="w", pady=4)
        self.input_path_var = tk.StringVar(value="未选择")
        ttk.Label(files_frame, textvariable=self.input_path_var, wraplength=420, foreground="#3b3b3b").grid(row=0, column=1, sticky="w", padx=(8, 0), pady=4)

        ttk.Button(files_frame, text="选择输出目录", command=self._choose_output_dir).grid(row=1, column=0, sticky="w", pady=4)
        self.output_dir_var = tk.StringVar(value="未选择")
        ttk.Label(files_frame, textvariable=self.output_dir_var, wraplength=420, foreground="#3b3b3b").grid(row=1, column=1, sticky="w", padx=(8, 0), pady=4)

        action_frame = ttk.Frame(left)
        action_frame.pack(fill="x", pady=(0, 10))
        self.run_button = ttk.Button(action_frame, text="开始蒸馏", command=self._start_distillation)
        self.run_button.pack(side="left")
        self.status_var = tk.StringVar(value="等待输入")
        ttk.Label(action_frame, textvariable=self.status_var, foreground="#005a9c").pack(side="left", padx=(12, 0))

        self.progress_var = tk.DoubleVar(value=0.0)
        self.progress_bar = ttk.Progressbar(left, mode="determinate", variable=self.progress_var, style="Progress.TProgressbar")
        self.progress_bar.pack(fill="x", pady=(0, 10))

        log_frame = ttk.LabelFrame(left, text="运行日志", padding=10)
        log_frame.pack(fill="both", expand=True)
        self.log_text = ScrolledText(log_frame, height=15, wrap="word", font=("Microsoft YaHei", 10))
        self.log_text.pack(fill="both", expand=True)
        self._append_log("请填写模型配置并选择文件后开始蒸馏。")

        preview_frame = ttk.LabelFrame(right, text="结果预览", padding=10)
        preview_frame.pack(fill="both", expand=True)
        self.file_tree = ttk.Treeview(preview_frame, show="tree", columns=("path",), height=10)
        self.file_tree.column("#0", width=260, anchor="w")
        self.file_tree.column("path", width=260, anchor="w")
        self.file_tree.heading("#0", text="文件")
        self.file_tree.heading("path", text="路径")
        self.file_tree.pack(fill="x", pady=(0, 8))
        self.file_tree.bind("<<TreeviewSelect>>", self._show_selected_preview)

        self.preview_text = ScrolledText(preview_frame, height=16, wrap="word", font=("Consolas", 10))
        self.preview_text.pack(fill="both", expand=True)
        self.preview_text.insert("end", "运行完成后，点击左侧文件列表即可预览内容。\n")
        self.preview_text.configure(state="disabled")

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _load_config(self) -> None:
        if not self.config_path.exists():
            self.provider_var.set("DeepSeek")
            self._on_provider_changed(None)
            return
        try:
            data = json.loads(self.config_path.read_text(encoding="utf-8"))
            self.provider_var.set(data.get("provider", "DeepSeek"))
            self.api_key_var.set(data.get("api_key", ""))
            self.base_url_var.set(data.get("base_url", ""))
            self.model_var.set(data.get("model", ""))
            self.title_var.set(data.get("title", "未命名作品"))
            self.input_path_var.set(data.get("input_path", "未选择"))
            self.output_dir_var.set(data.get("output_dir", "未选择"))
            self.input_path = data.get("input_path") if data.get("input_path") and data.get("input_path") != "未选择" else None
            self.output_dir = data.get("output_dir") if data.get("output_dir") and data.get("output_dir") != "未选择" else None
        except Exception:
            self.provider_var.set("DeepSeek")
            self._on_provider_changed(None)

    def _save_config(self) -> None:
        data = {
            "provider": self.provider_var.get(),
            "api_key": self.api_key_var.get(),
            "base_url": self.base_url_var.get(),
            "model": self.model_var.get(),
            "title": self.title_var.get(),
            "input_path": self.input_path or self.input_path_var.get(),
            "output_dir": self.output_dir or self.output_dir_var.get(),
        }
        self.config_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _on_provider_changed(self, _event: object | None) -> None:
        provider = self.provider_var.get()
        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["DeepSeek"])
        self.base_url_var.set(preset["base_url"])
        self.model_var.set(preset["model"])
        self._save_config()

    def _choose_input_file(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if not path:
            return
        self.input_path = path
        self.input_path_var.set(path)
        self.title_var.set(Path(path).stem)
        self._save_config()
        self._append_log(f"已选择输入文件：{path}")

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory()
        if not path:
            return
        self.output_dir = path
        self.output_dir_var.set(path)
        self._save_config()
        self._append_log(f"已选择输出目录：{path}")

    def _start_distillation(self) -> None:
        api_key = self.api_key_var.get().strip()
        base_url = self.base_url_var.get().strip()
        model = self.model_var.get().strip()
        title = self.title_var.get().strip()
        if not api_key:
            messagebox.showerror("错误", "请输入 API Key")
            return
        if not self.input_path:
            messagebox.showerror("错误", "请选择输入文本文件")
            return
        if not self.output_dir:
            messagebox.showerror("错误", "请选择输出目录")
            return

        self._save_config()
        self.run_button.config(state="disabled")
        self.status_var.set("正在蒸馏...")
        self.progress_var.set(0.0)
        self._append_log("开始调用模型进行蒸馏...")
        self._clear_preview()
        self.thread = threading.Thread(target=self._run_distillation, args=(api_key, base_url, model, title), daemon=True)
        self.thread.start()

    def _run_distillation(self, api_key: str, base_url: str, model: str, title: str) -> None:
        try:
            input_path = Path(self.input_path)
            output_dir = Path(self.output_dir)
            def progress(message: str, percent: int) -> None:
                self.root.after(0, self._update_progress, message, percent)
            def log_message(message: str) -> None:
                self.root.after(0, self._append_log, message)
            distill_text_file(
                input_path=input_path,
                output_dir=output_dir,
                title=title,
                api_key=api_key,
                base_url=base_url,
                model=model,
                progress_callback=progress,
                log_callback=log_message,
            )
            self.root.after(0, self._on_distillation_finished, output_dir)
        except Exception as exc:  # noqa: BLE001
            self.root.after(0, self._on_distillation_failed, str(exc))

    def _update_progress(self, message: str, percent: int) -> None:
        self.progress_var.set(float(percent))
        self.status_var.set(message)

    def _on_distillation_finished(self, output_dir: Path) -> None:
        self.run_button.config(state="normal")
        self.status_var.set("蒸馏完成")
        self.progress_var.set(100.0)
        self._append_log(f"蒸馏完成，输出目录：{output_dir}")
        self._populate_result_tree(output_dir)
        messagebox.showinfo("完成", f"蒸馏已完成，结果保存在：{output_dir}")

    def _on_distillation_failed(self, error_text: str) -> None:
        self.run_button.config(state="normal")
        self.status_var.set("失败")
        self.progress_var.set(0.0)
        self._append_log(f"错误：{error_text}")
        messagebox.showerror("失败", error_text)

    def _clear_preview(self) -> None:
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("end", "正在生成结果...\n")
        self.preview_text.configure(state="disabled")

    def _populate_result_tree(self, output_dir: Path) -> None:
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)
        files = [output_dir / "README.md", output_dir / "metadata.json"]
        archive_dir = output_dir / "distillation_archive"
        if archive_dir.exists():
            files.extend(sorted(archive_dir.glob("*.md")))
        prompts_dir = output_dir / "prompts"
        if prompts_dir.exists():
            files.extend(sorted(prompts_dir.glob("*.md")))
        for file_path in files:
            if file_path.exists():
                rel = file_path.relative_to(output_dir)
                self.file_tree.insert("", "end", text=file_path.name, values=(str(rel),))

    def _show_selected_preview(self, _event: object) -> None:
        selected_item = self.file_tree.selection()
        if not selected_item:
            return
        file_name = self.file_tree.item(selected_item[0], "text")
        output_dir = Path(self.output_dir) if self.output_dir else None
        if not output_dir:
            return
        candidate_paths = [
            output_dir / "README.md",
            output_dir / "metadata.json",
            output_dir / "prompts" / "main_prompt.md",
            output_dir / "distillation_archive" / file_name,
        ]
        for path in candidate_paths:
            if path.exists():
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception:
                    text = "无法读取文件内容。"
                self.preview_text.configure(state="normal")
                self.preview_text.delete("1.0", "end")
                self.preview_text.insert("end", f"# {path.name}\n\n{text}")
                self.preview_text.configure(state="disabled")
                return

    def on_closing(self) -> None:
        self._save_config()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    app = DistillationApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
