"""Antarmuka Tkinter untuk eksplorasi graf dan animasi jalur terpendek.

Modul ini sengaja tidak mengimpor mesin algoritma. Fungsi pembaca graf,
perbandingan, tata letak, dan format angka diberikan oleh program utama.
Dengan demikian logika perhitungan tetap mudah diuji tanpa membuka GUI.
"""

from __future__ import annotations

import math
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable


class GraphApp:
    """Dashboard interaktif untuk dua algoritma shortest path."""

    BG = "#08111f"
    PANEL = "#101f33"
    SURFACE = "#0c1a2b"
    BORDER = "#20344e"
    TEXT = "#eef6ff"
    MUTED = "#8ea5bf"
    CYAN = "#4edff0"
    BLUE = "#73a8ff"
    GREEN = "#42d8a4"
    GOLD = "#ffc76c"
    RED = "#ff7d8b"

    def __init__(
        self,
        root: tk.Tk,
        file_path: Path,
        load_graph: Callable,
        compare: Callable,
        layout: Callable,
        fmt: Callable,
    ) -> None:
        self.root = root
        self.load_graph = load_graph
        self.compare = compare
        self.layout = layout
        self.fmt = fmt
        self.file_path = file_path
        self.graph: dict[str, dict[str, float]] = {}
        self.results: tuple[Any, Any] | None = None
        self.active: Any = None
        self.index = 0
        self.playing = False
        self.after_id: str | None = None
        self.positions: dict[str, tuple[float, float]] = {}
        self.hover_node: str | None = None
        self._syncing_scale = False
        self.algorithm_name = "Dijkstra"

        root.title("Graph Task (Group 4)  |  MMAI1001")
        screen_width, screen_height = root.winfo_screenwidth(), root.winfo_screenheight()
        window_width = min(1310, max(900, screen_width - 40))
        window_height = min(820, max(580, screen_height - 90))
        root.geometry(f"{window_width}x{window_height}+20+15")
        root.minsize(900, 580)
        root.configure(bg=self.BG)
        self._configure_style()
        self._build()
        self.open_file(file_path)
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.bind("<space>", self._space)
        root.bind("<Right>", self._right_key)
        root.bind("<Left>", self._left_key)

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Graph.TCombobox", font=("Segoe UI", 10), padding=7,
            foreground=self.TEXT, fieldbackground=self.SURFACE,
            background=self.PANEL, bordercolor=self.BORDER,
            lightcolor=self.BORDER, darkcolor=self.BORDER,
            arrowcolor=self.CYAN,
        )
        style.map("Graph.TCombobox",
                  fieldbackground=[("readonly", self.SURFACE)],
                  foreground=[("readonly", self.TEXT)],
                  selectbackground=[("readonly", self.SURFACE)],
                  selectforeground=[("readonly", self.TEXT)])

    @staticmethod
    def _natural_key(name: str):
        """Urutkan V2 sebelum V10 pada daftar simpul."""
        return tuple((1, int(part)) if part.isdigit() else (0, part.lower())
                     for part in re.split(r"(\d+)", name))

    def _label(self, parent, text: str, *, size=10, color=None, bold=False, **kw):
        return tk.Label(
            parent, text=text, bg=parent.cget("bg"), fg=color or self.TEXT,
            font=("Segoe UI Semibold" if bold else "Segoe UI", size), **kw,
        )

    def _button(self, parent, text: str, command: Callable, *, accent=False,
                width=None, compact=False):
        normal = self.CYAN if accent else self.PANEL
        hover = "#8af0fa" if accent else "#1a3351"
        button = tk.Button(
            parent, text=text, command=command, bg=normal,
            fg=self.BG if accent else self.TEXT,
            activebackground=hover, activeforeground=self.BG if accent else self.TEXT,
            relief="flat", bd=0, cursor="hand2", width=width,
            padx=10 if compact else 14, pady=6 if compact else 10,
            font=("Segoe UI Semibold", 9 if compact else 10),
        )
        button.bind("<Enter>", lambda _event: button.configure(bg=hover))
        button.bind("<Leave>", lambda _event: button.configure(bg=normal))
        return button

    def _card(self, parent, *, bg=None, padx=15, pady=12):
        return tk.Frame(
            parent, bg=bg or self.PANEL, padx=padx, pady=pady,
            highlightthickness=1, highlightbackground=self.BORDER,
        )

    def _build(self) -> None:
        self._build_header()
        self._build_summary()
        self._build_workspace()

    def _build_header(self) -> None:
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=22, pady=(10, 6))
        icon = tk.Canvas(header, width=43, height=43, bg=self.BG,
                         highlightthickness=0)
        icon.pack(side="left", padx=(0, 12))
        icon.create_line(9, 30, 21, 12, 34, 26, fill=self.CYAN, width=3)
        for x, y, fill in ((9, 30, self.GREEN), (21, 12, self.CYAN),
                           (34, 26, self.GOLD)):
            icon.create_oval(x-5, y-5, x+5, y+5, fill=fill, outline=self.BG, width=2)
        title_box = tk.Frame(header, bg=self.BG)
        title_box.pack(side="left")
        self._label(title_box, "GRAPH TASK (GROUP 4)", size=19, bold=True).pack(anchor="w")
        self._label(title_box, "MMAI1001  /  EKSPLORASI GRAF", size=9,
                    color=self.MUTED).pack(anchor="w")
        self._button(header, "+  Buka berkas graf", self.choose_file,
                     accent=True).pack(side="right")
        self.header_file = self._label(header, "", size=9, color=self.MUTED)
        self.header_file.pack(side="right", padx=16)

    def _summary_card(self, parent, heading: str, value: str, accent: str):
        card = self._card(parent, padx=17, pady=9)
        card.pack(side="left", fill="both", expand=True, padx=(0, 10))
        tk.Frame(card, bg=accent, width=4).pack(side="left", fill="y", padx=(0, 12))
        content = tk.Frame(card, bg=self.PANEL)
        content.pack(side="left", fill="both", expand=True)
        self._label(content, heading, size=9, color=self.MUTED,
                    bold=True).pack(anchor="w")
        label = self._label(content, value, size=14, color=self.TEXT, bold=True,
                            anchor="w", justify="left")
        label.pack(anchor="w", fill="x", pady=(3, 0))
        return label

    def _build_summary(self) -> None:
        row = tk.Frame(self.root, bg=self.BG)
        row.pack(fill="x", padx=(22, 12), pady=(0, 8))
        self.route_value = self._summary_card(row, "RUTE TERPENDEK", "—", self.CYAN)
        self.cost_value = self._summary_card(row, "BOBOT MINIMUM", "—", self.GOLD)
        self.match_value = self._summary_card(row, "VERIFIKASI ALGORITMA", "Menunggu", self.GREEN)

    def _build_workspace(self) -> None:
        body = tk.Frame(self.root, bg=self.BG)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 10))
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, minsize=330)
        body.grid_rowconfigure(0, weight=1)

        left = self._card(body, bg=self.SURFACE, padx=0, pady=0)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)
        graph_head = tk.Frame(left, bg=self.SURFACE)
        graph_head.grid(row=0, column=0, sticky="ew", padx=16, pady=(13, 9))
        self._label(graph_head, "PETA GRAF", size=12, bold=True).pack(side="left")
        self.graph_meta = self._label(graph_head, "", size=9, color=self.MUTED)
        self.graph_meta.pack(side="right")

        self.canvas = tk.Canvas(left, bg=self.SURFACE, highlightthickness=0,
                                cursor="crosshair")
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=2)
        self.canvas.bind("<Configure>", lambda _event: self.redraw())
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_canvas_click)

        legend = tk.Frame(left, bg=self.SURFACE)
        legend.grid(row=2, column=0, sticky="ew", padx=15, pady=(3, 5))
        for color, text in ((self.GREEN, "Awal"), (self.GOLD, "Tujuan"),
                            (self.CYAN, "Jalur akhir"), (self.BLUE, "Sudah diproses")):
            tk.Label(legend, text="●", bg=self.SURFACE, fg=color,
                     font=("Segoe UI", 12)).pack(side="left")
            self._label(legend, text, size=9, color=self.MUTED).pack(
                side="left", padx=(1, 12))
        self._label(legend, "Klik simpul: awal  ·  Shift+klik: tujuan",
                    size=8, color=self.MUTED).pack(side="right")

        transport = tk.Frame(left, bg=self.PANEL, padx=12, pady=9)
        transport.grid(row=3, column=0, sticky="ew")
        self._button(transport, "|<", self.jump_start, compact=True,
                     width=3).pack(side="left", padx=2)
        self._button(transport, "<", self.previous_step, compact=True,
                     width=3).pack(side="left", padx=2)
        self.play_button = self._button(transport, "▶ Putar", self.toggle_play,
                                        accent=True, compact=True, width=9)
        self.play_button.pack(side="left", padx=5)
        self._button(transport, ">", self.next_step, compact=True,
                     width=3).pack(side="left", padx=2)
        self._button(transport, ">|", self.jump_end, compact=True,
                     width=3).pack(side="left", padx=2)
        self.progress_var = tk.IntVar(value=0)
        self.progress = tk.Scale(
            transport, from_=0, to=1, variable=self.progress_var,
            command=self.seek, orient="horizontal", showvalue=False,
            bg=self.PANEL, fg=self.TEXT, troughcolor=self.BORDER,
            activebackground=self.CYAN, highlightthickness=0, bd=0,
            sliderlength=15,
        )
        self.progress.pack(side="left", fill="x", expand=True, padx=(15, 10))
        self.progress_caption = self._label(transport, "0 / 0", size=9,
                                            color=self.MUTED)
        self.progress_caption.pack(side="right")
        self.speed_var = tk.StringVar(value="Normal")
        self.speed_combo = ttk.Combobox(
            transport, textvariable=self.speed_var, style="Graph.TCombobox",
            state="readonly", values=("Lambat", "Normal", "Cepat"), width=7,
        )
        self.speed_combo.pack(side="right", padx=(9, 7))
        self._label(transport, "Kecepatan", size=8, color=self.MUTED).pack(
            side="right")

        side = tk.Frame(body, bg=self.BG, width=330)
        side.grid(row=0, column=1, sticky="nsew")
        side.grid_propagate(False)
        side.grid_rowconfigure(2, weight=1)
        side.grid_columnconfigure(0, weight=1)
        self._build_controls(side)
        self._build_comparison(side)
        self._build_trace(side)

    def _build_controls(self, side) -> None:
        controls = self._card(side, padx=12, pady=8)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 7))
        self._label(controls, "PENGATURAN", size=10, bold=True).pack(
            anchor="w", pady=(0, 5))

        pair = tk.Frame(controls, bg=self.PANEL)
        pair.pack(fill="x")
        self.start_var = tk.StringVar()
        self.goal_var = tk.StringVar()
        for column, caption, variable in ((0, "DARI", self.start_var),
                                          (1, "KE", self.goal_var)):
            field = tk.Frame(pair, bg=self.PANEL)
            field.grid(row=0, column=column, sticky="ew",
                       padx=(0, 7) if column == 0 else (7, 0))
            pair.grid_columnconfigure(column, weight=1)
            self._label(field, caption, size=8, color=self.MUTED,
                        bold=True).pack(anchor="w", pady=(0, 2))
            combo = ttk.Combobox(field, textvariable=variable,
                                 style="Graph.TCombobox", state="readonly",
                                 width=10)
            combo.pack(fill="x")
            combo.bind("<<ComboboxSelected>>", lambda _event: self.run())
            if column == 0:
                self.start_combo = combo
            else:
                self.goal_combo = combo

        self._button(controls, "Hitung & bandingkan", self.run,
                     accent=True, compact=True).pack(fill="x", pady=(7, 0))

    def _build_comparison(self, side) -> None:
        panel = self._card(side, padx=12, pady=6)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, 7))
        self._label(panel, "DUA ALGORITMA", size=10, bold=True).pack(
            anchor="w", pady=(0, 5))
        self.algorithm_cards: dict[str, tuple[tk.Frame, tk.Label]] = {}
        for name in ("Dijkstra", "Bellman-Ford"):
            card = tk.Frame(panel, bg=self.SURFACE, padx=9, pady=3,
                            highlightthickness=1, highlightbackground=self.BORDER,
                            cursor="hand2")
            card.pack(fill="x", pady=2)
            top = tk.Frame(card, bg=self.SURFACE)
            top.pack(fill="x")
            name_label = tk.Label(top, text=name, bg=self.SURFACE, fg=self.TEXT,
                                  font=("Segoe UI Semibold", 10))
            name_label.pack(side="left")
            metric_label = tk.Label(top, text="— ms", bg=self.SURFACE,
                                    fg=self.CYAN, font=("Consolas", 10, "bold"))
            metric_label.pack(side="right")
            self.algorithm_cards[name] = (card, metric_label)
            for widget in (card, top, name_label, metric_label):
                widget.bind("<Button-1>",
                            lambda _event, chosen=name: self.select_algorithm(chosen))

    def _build_trace(self, side) -> None:
        panel = self._card(side, padx=12, pady=8)
        panel.grid(row=2, column=0, sticky="nsew")
        self._label(panel, "JEJAK PENCARIAN", size=10, bold=True).pack(anchor="w")
        self.step_label = self._label(
            panel, "Buka berkas graf untuk memulai.", size=10,
            color=self.TEXT, wraplength=278, justify="left", anchor="w",
        )
        self.step_label.pack(fill="x", pady=(4, 2))
        self.step_meta = self._label(panel, "", size=8, color=self.MUTED)
        self.step_meta.pack(anchor="w", pady=(0, 5))
        separator = tk.Frame(panel, height=1, bg=self.BORDER)
        separator.pack(fill="x", pady=(0, 5))
        self._label(panel, "JARAK SEMENTARA", size=9, bold=True,
                    color=self.MUTED).pack(anchor="w")
        text_box = tk.Frame(panel, bg=self.PANEL)
        text_box.pack(fill="both", expand=True, pady=(5, 0))
        scrollbar = tk.Scrollbar(text_box, bg=self.PANEL, troughcolor=self.SURFACE,
                                 activebackground=self.CYAN)
        scrollbar.pack(side="right", fill="y")
        self.distance_text = tk.Text(
            text_box, bg=self.SURFACE, fg=self.TEXT, relief="flat", bd=0,
            insertbackground=self.TEXT, font=("Consolas", 9), height=5,
            state="disabled", yscrollcommand=scrollbar.set, padx=9, pady=7,
        )
        self.distance_text.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.distance_text.yview)

    def choose_file(self) -> None:
        selected = filedialog.askopenfilename(
            title="Pilih berkas graf", initialdir=str(self.file_path.parent),
            filetypes=(("Berkas teks", "*.txt"), ("Semua berkas", "*.*")),
        )
        if selected:
            self.open_file(Path(selected))

    def open_file(self, path: Path) -> None:
        try:
            graph, start, goal = self.load_graph(path)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Gagal membaca graf", str(exc), parent=self.root)
            return
        self.stop()
        self.file_path = path
        self.graph = graph
        nodes = tuple(sorted(graph, key=self._natural_key))
        self.start_combo["values"] = nodes
        self.goal_combo["values"] = nodes
        self.start_var.set(start)
        self.goal_var.set(goal)
        count_edges = sum(len(neighbours) for neighbours in graph.values())
        self.header_file.config(text=path.name)
        self.graph_meta.config(text=f"{len(nodes)} SIMPUL  ·  {count_edges} SISI BERARAH")
        self.run()

    def run(self) -> None:
        if not self.graph:
            return
        self.stop()
        start, goal = self.start_var.get(), self.goal_var.get()
        try:
            self.results = self.compare(self.graph, start, goal)
        except (ValueError, RuntimeError, KeyError) as exc:
            messagebox.showerror("Perhitungan gagal", str(exc), parent=self.root)
            return
        self.active = next(result for result in self.results
                           if result.algorithm == self.algorithm_name)
        self.index = 0
        first, second = self.results
        route = "  →  ".join(first.path) if first.path else "Tidak ada jalur"
        self.route_value.config(text=route, wraplength=480)
        self.cost_value.config(text=self.fmt(first.cost))
        self.match_value.config(text="✓  Hasil sama" if first.cost == second.cost
                                else "!  Hasil berbeda")
        for result in self.results:
            _, metric = self.algorithm_cards[result.algorithm]
            metric.config(text=f"{result.seconds * 1000:.4f} ms")
        self._style_algorithm_cards()
        self.progress.config(to=max(0, len(self.active.steps) - 1))
        self._show_step()

    def select_algorithm(self, name: str) -> None:
        if name not in self.algorithm_cards:
            return
        self.algorithm_name = name
        if self.graph:
            self.run()
        else:
            self._style_algorithm_cards()

    def _style_algorithm_cards(self) -> None:
        for name, (card, metric) in self.algorithm_cards.items():
            selected = name == self.algorithm_name
            card.configure(highlightbackground=self.CYAN if selected else self.BORDER)
            metric.configure(fg=self.CYAN if selected else self.MUTED)

    def stop(self) -> None:
        self.playing = False
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None
        if hasattr(self, "play_button"):
            self.play_button.config(text="▶ Putar")

    def toggle_play(self) -> None:
        if not self.active:
            return
        if self.playing:
            self.stop()
            return
        if self.index >= len(self.active.steps) - 1:
            self.index = 0
            self._show_step()
        self.playing = True
        self.play_button.config(text="Ⅱ Jeda")
        self._advance()

    def _advance(self) -> None:
        if not self.playing or not self.active:
            return
        if self.index >= len(self.active.steps) - 1:
            self.stop()
            return
        self.index += 1
        self._show_step()
        delay = {"Lambat": 850, "Normal": 420, "Cepat": 140}.get(
            self.speed_var.get(), 420)
        self.after_id = self.root.after(delay, self._advance)

    def previous_step(self) -> None:
        self.stop()
        if self.active:
            self.index = max(0, self.index - 1)
            self._show_step()

    def next_step(self) -> None:
        self.stop()
        if self.active:
            self.index = min(len(self.active.steps) - 1, self.index + 1)
            self._show_step()

    def jump_start(self) -> None:
        self.stop()
        if self.active:
            self.index = 0
            self._show_step()

    def jump_end(self) -> None:
        self.stop()
        if self.active:
            self.index = len(self.active.steps) - 1
            self._show_step()

    def seek(self, value: str) -> None:
        if self._syncing_scale or not self.active:
            return
        self.stop()
        self.index = max(0, min(int(float(value)), len(self.active.steps) - 1))
        self._show_step()

    def _show_step(self) -> None:
        if not self.active:
            return
        step = self.active.steps[self.index]
        self.step_label.config(text=step.message)
        unit = "simpul" if self.algorithm_name == "Dijkstra" else "putaran"
        self.step_meta.config(
            text=f"Langkah {self.index + 1}/{len(self.active.steps)}  ·  "
                 f"{self.active.examined} {unit}  ·  {self.active.relaxations} pembaruan")
        self.progress_caption.config(text=f"{self.index + 1}/{len(self.active.steps)}")
        self._syncing_scale = True
        self.progress_var.set(self.index)
        self._syncing_scale = False
        self.distance_text.config(state="normal")
        self.distance_text.delete("1.0", "end")
        for node, distance in sorted(step.distances,
                                     key=lambda item: self._natural_key(item[0])):
            marker = "●" if node == step.changed else " "
            self.distance_text.insert(
                "end", f"{marker} {node:<11}{self.fmt(distance):>9}\n")
        self.distance_text.config(state="disabled")
        self.redraw()

    def _edges(self):
        drawn: set[tuple[str, str]] = set()
        for source in sorted(self.graph, key=self._natural_key):
            for target, weight in sorted(self.graph[source].items(),
                                         key=lambda item: self._natural_key(item[0])):
                if (source, target) in drawn:
                    continue
                symmetric = self.graph.get(target, {}).get(source) == weight
                drawn.add((source, target))
                if symmetric:
                    drawn.add((target, source))
                yield source, target, weight, symmetric

    def _line_points(self, source, target, symmetric):
        x1, y1 = self.positions[source]
        x2, y2 = self.positions[target]
        dx, dy = x2 - x1, y2 - y1
        length = max(1.0, math.hypot(dx, dy))
        if not symmetric and source in self.graph.get(target, {}):
            # Pisahkan dua sisi berarah yang bobotnya berbeda.
            shift = 6
            x1, y1 = x1 - dy / length * shift, y1 + dx / length * shift
            x2, y2 = x2 - dy / length * shift, y2 + dx / length * shift
        radius = 21
        return (x1 + dx / length * radius, y1 + dy / length * radius,
                x2 - dx / length * radius, y2 - dy / length * radius)

    def redraw(self) -> None:
        if not self.graph:
            return
        canvas = self.canvas
        canvas.delete("all")
        width = max(canvas.winfo_width(), 420)
        height = max(canvas.winfo_height(), 320)
        for x in range(24, width, 38):
            for y in range(21, height, 38):
                canvas.create_oval(x, y, x+1, y+1, fill="#21334a", outline="")

        self.positions = self.layout(self.graph, self.start_var.get(), width, height)
        step = self.active.steps[self.index] if self.active else None
        finished = bool(self.active and self.index == len(self.active.steps) - 1)
        path_edges = set(zip(self.active.path, self.active.path[1:])) if finished else set()
        edges = list(self._edges())

        for source, target, _, symmetric in edges:
            canvas.create_line(*self._line_points(source, target, symmetric),
                               fill="#405775", width=2,
                               arrow=tk.NONE if symmetric else tk.LAST,
                               arrowshape=(9, 11, 4))
        for source, target, _, symmetric in edges:
            on_path = ((source, target) in path_edges or
                       (symmetric and (target, source) in path_edges))
            active = step and step.edge in ((source, target), (target, source))
            if on_path or active:
                points = self._line_points(source, target, symmetric)
                color = self.GOLD if active else self.CYAN
                canvas.create_line(*points, fill="#204b61", width=9)
                canvas.create_line(*points, fill=color, width=4,
                                   arrow=tk.NONE if symmetric else tk.LAST,
                                   arrowshape=(10, 12, 5))
        for source, target, weight, symmetric in edges:
            x1, y1, x2, y2 = self._line_points(source, target, symmetric)
            mx, my = (x1+x2)/2, (y1+y2)/2
            label = self.fmt(weight)
            half = max(15, 5 + len(label) * 4)
            canvas.create_rectangle(mx-half, my-10, mx+half, my+10,
                                    fill=self.SURFACE, outline=self.BORDER)
            canvas.create_text(mx, my, text=label, fill=self.MUTED,
                               font=("Segoe UI Semibold", 8))

        distances = dict(step.distances) if step else {}
        for node in sorted(self.graph, key=self._natural_key):
            x, y = self.positions[node]
            on_path = finished and node in self.active.path
            is_start = node == self.start_var.get()
            is_goal = node == self.goal_var.get()
            current = step and node == step.current
            fill = (self.GREEN if is_start else self.GOLD if is_goal else
                    self.CYAN if on_path else self.BLUE if step and node in step.settled
                    else "#274866")
            if current or self.hover_node == node:
                canvas.create_oval(x-29, y-29, x+29, y+29,
                                   fill="", outline=self.GOLD if current else self.CYAN,
                                   width=2)
            canvas.create_oval(x-21, y-21, x+21, y+21,
                               fill=fill, outline="#c7e8f6" if on_path else self.BORDER,
                               width=2)
            canvas.create_text(x, y, text=node,
                               fill=self.BG if fill in (self.GREEN, self.GOLD, self.CYAN)
                               else self.TEXT,
                               font=("Segoe UI Semibold", 10))

        canvas.create_text(17, 15, anchor="nw", text="INTERAKTIF  /  KLIK SIMPUL UNTUK MEMILIH AWAL",
                           fill=self.MUTED, font=("Segoe UI", 8))
        if step:
            canvas.create_text(width-18, 15, anchor="ne",
                               text=f"{self.algorithm_name.upper()}  ·  {self.index+1}/{len(self.active.steps)}",
                               fill=self.CYAN, font=("Segoe UI Semibold", 8))
        if self.hover_node:
            node = self.hover_node
            value = self.fmt(distances.get(node, math.inf))
            x, y = self.positions[node]
            tx = min(max(x, 80), width-80)
            ty = max(55, y-53)
            canvas.create_rectangle(tx-73, ty-17, tx+73, ty+17,
                                    fill=self.PANEL, outline=self.CYAN)
            canvas.create_text(tx, ty, text=f"{node}   jarak: {value}",
                               fill=self.TEXT, font=("Segoe UI", 9))

    def _node_at(self, x: float, y: float) -> str | None:
        for node, (nx, ny) in self.positions.items():
            if (x-nx)**2 + (y-ny)**2 <= 24**2:
                return node
        return None

    def _on_motion(self, event) -> None:
        node = self._node_at(event.x, event.y)
        if node != self.hover_node:
            self.hover_node = node
            self.canvas.configure(cursor="hand2" if node else "crosshair")
            self.redraw()

    def _on_leave(self, _event) -> None:
        if self.hover_node:
            self.hover_node = None
            self.redraw()

    def _on_canvas_click(self, event) -> None:
        node = self._node_at(event.x, event.y)
        if node is None:
            return
        if event.state & 0x0001:
            self.goal_var.set(node)
        else:
            self.start_var.set(node)
        self.hover_node = None
        self.run()

    def _space(self, _event) -> None:
        self.toggle_play()

    def _right_key(self, event) -> None:
        if not isinstance(event.widget, ttk.Combobox):
            self.next_step()

    def _left_key(self, event) -> None:
        if not isinstance(event.widget, ttk.Combobox):
            self.previous_step()

    def _close(self) -> None:
        self.stop()
        self.root.destroy()
