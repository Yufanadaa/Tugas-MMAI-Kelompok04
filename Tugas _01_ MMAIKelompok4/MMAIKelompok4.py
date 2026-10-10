"""Visualizer jalur terpendek untuk Tugas 1 MMAI1001.

Jalankan ``python MMAIKelompokX.py`` untuk GUI, atau tambahkan ``--cli``
untuk membandingkan kedua algoritma di terminal. Hanya pustaka standar
Python yang digunakan.
"""

from __future__ import annotations

import argparse
import ast
import heapq
import math
import re
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path

Graph = dict[str, dict[str, float]]


@dataclass(frozen=True)
class Step:
    """Satu kejadian yang dapat ditampilkan oleh animasi GUI."""

    message: str
    current: str | None = None
    edge: tuple[str, str] | None = None
    changed: str | None = None
    distances: tuple[tuple[str, float], ...] = ()
    settled: frozenset[str] = frozenset()


@dataclass(frozen=True)
class Result:
    algorithm: str
    path: tuple[str, ...]
    cost: float
    seconds: float
    steps: tuple[Step, ...]
    examined: int
    relaxations: int


def load_graph(file_path: Path) -> tuple[Graph, str, str]:
    """Baca assignment literal ``graph``/``graf`` dan dua simpul terakhir.

    ``ast.literal_eval`` membaca data tanpa mengeksekusi kode di graf.txt.
    Bobot harus numerik, hingga, dan tidak negatif agar kedua algoritma
    dapat dibandingkan secara sah.
    """
    content = file_path.read_text(encoding="utf-8-sig")
    lines = content.splitlines()
    assignment = next(
        (i for i, line in enumerate(lines)
         if re.match(r"^\s*(?:graph|graf)\s*=\s*\{", line)),
        None,
    )
    if assignment is None:
        raise ValueError("Awal graf harus berupa 'graph = {' atau 'graf = {'.")
    first_brace = lines[assignment].index("{")
    literal_lines = [lines[assignment][first_brace:]]
    raw = None
    end = assignment
    for end in range(assignment, len(lines)):
        if end > assignment:
            literal_lines.append(lines[end])
        try:
            raw = ast.literal_eval("\n".join(literal_lines))
            break
        except (SyntaxError, ValueError):
            continue
    if raw is None or not isinstance(raw, dict) or not raw:
        raise ValueError("Struktur graf bukan dictionary Python yang valid.")
    if any(not isinstance(node, str) or not node.strip() for node in raw):
        raise ValueError("Semua nama verteks harus berupa string tidak kosong.")
    graph: Graph = {}
    for node, neighbours in raw.items():
        if not isinstance(neighbours, dict):
            raise ValueError(f"Tetangga {node} harus berupa dictionary.")
        graph[node] = {}
        for neighbour, weight in neighbours.items():
            if neighbour not in raw:
                raise ValueError(f"Tetangga {neighbour!r} dari {node!r} belum didefinisikan.")
            if isinstance(weight, bool) or not isinstance(weight, (int, float)):
                raise ValueError(f"Bobot {node} -> {neighbour} harus berupa angka.")
            if not math.isfinite(weight) or weight < 0:
                raise ValueError(f"Bobot {node} -> {neighbour} harus hingga dan >= 0.")
            graph[node][neighbour] = float(weight)
    remainder = [line.strip() for line in lines[end + 1:]
                 if line.strip() and not line.lstrip().startswith("#")]
    if len(remainder) != 1 or len(remainder[0].split()) != 2:
        raise ValueError("Sesudah dictionary harus ada satu baris: VERTEKS_AWAL VERTEKS_AKHIR.")
    start, goal = remainder[0].split()
    if start not in graph or goal not in graph:
        raise ValueError("Verteks awal dan akhir harus ada dalam graf.")
    return graph, start, goal


def _step(message: str, distances: dict[str, float], settled: set[str],
          current: str | None = None, edge: tuple[str, str] | None = None,
          changed: str | None = None) -> Step:
    return Step(message, current, edge, changed,
                tuple(sorted(distances.items())), frozenset(settled))


def _path(previous: dict[str, str], start: str, goal: str,
          cost: float) -> tuple[str, ...]:
    if math.isinf(cost):
        return ()
    route = [goal]
    while route[-1] != start:
        if route[-1] not in previous:
            raise RuntimeError("Rantai pendahulu tidak lengkap.")
        route.append(previous[route[-1]])
    return tuple(reversed(route))


def dijkstra(graph: Graph, start: str, goal: str) -> Result:
    """Dijkstra dengan heap: O((V + E) log V), memori O(V + E)."""
    begin = time.perf_counter()
    distances = {node: math.inf for node in graph}
    distances[start] = 0.0
    previous: dict[str, str] = {}
    heap = [(0.0, start)]
    settled: set[str] = set()
    steps = [_step(f"Mulai dari {start} (jarak 0).", distances, settled, start)]
    examined = relaxations = 0
    while heap:
        distance, node = heapq.heappop(heap)
        if node in settled or distance != distances[node]:
            continue
        settled.add(node)
        examined += 1
        steps.append(_step(f"Tetapkan {node}: jarak minimum {fmt(distance)}.",
                           distances, settled, node))
        if node == goal:
            break
        for neighbour, weight in sorted(graph[node].items()):
            candidate = distance + weight
            if candidate < distances[neighbour]:
                distances[neighbour] = candidate
                previous[neighbour] = node
                heapq.heappush(heap, (candidate, neighbour))
                relaxations += 1
                steps.append(_step(
                    f"Perbarui {neighbour} via {node}: {fmt(candidate)}.",
                    distances, settled, node, (node, neighbour), neighbour))
    cost = distances[goal]
    route = _path(previous, start, goal, cost)
    steps.append(_step("Selesai: " + (" -> ".join(route) if route else "tidak ada jalur"),
                       distances, settled, goal))
    return Result("Dijkstra", route, cost, time.perf_counter() - begin,
                  tuple(steps), examined, relaxations)


def bellman_ford(graph: Graph, start: str, goal: str) -> Result:
    """Bellman-Ford dengan berhenti dini: O(VE), memori O(V + E)."""
    begin = time.perf_counter()
    distances = {node: math.inf for node in graph}
    distances[start] = 0.0
    previous: dict[str, str] = {}
    edges = [(u, v, w) for u in sorted(graph)
             for v, w in sorted(graph[u].items())]
    steps = [_step(f"Mulai dari {start} (jarak 0).", distances, set(), start)]
    examined = relaxations = 0
    for number in range(1, len(graph)):
        changed = False
        examined += 1
        steps.append(_step(f"Putaran {number}: periksa semua sisi.",
                           distances, set()))
        for source, target, weight in edges:
            if math.isinf(distances[source]):
                continue
            candidate = distances[source] + weight
            if candidate < distances[target]:
                distances[target] = candidate
                previous[target] = source
                relaxations += 1
                changed = True
                steps.append(_step(
                    f"Putaran {number}: {source} -> {target}, jarak {fmt(candidate)}.",
                    distances, set(), source, (source, target), target))
        if not changed:
            steps.append(_step("Tidak ada pembaruan; berhenti dini.",
                               distances, set()))
            break
    cost = distances[goal]
    route = _path(previous, start, goal, cost)
    steps.append(_step("Selesai: " + (" -> ".join(route) if route else "tidak ada jalur"),
                       distances, set(), goal))
    return Result("Bellman-Ford", route, cost, time.perf_counter() - begin,
                  tuple(steps), examined, relaxations)


def fmt(value: float) -> str:
    """Tampilkan integer tanpa desimal, atau pecahan ringkas."""
    if math.isinf(value):
        return "∞"
    return f"{value:g}"


def format_result(result: Result) -> str:
    route = " -> ".join(result.path) if result.path else "Tidak ada jalur"
    return (f"{result.algorithm}: {route}\n"
            f"Bobot minimum: {fmt(result.cost)}\n"
            f"Waktu algoritma: {result.seconds * 1000:.4f} ms\n"
            f"Verteks/putaran: {result.examined}; pembaruan: {result.relaxations}")


def compare(graph: Graph, start: str, goal: str) -> tuple[Result, Result]:
    first = dijkstra(graph, start, goal)
    second = bellman_ford(graph, start, goal)
    if first.cost != second.cost:
        raise RuntimeError("Bobot hasil kedua algoritma berbeda.")
    return first, second


def layout(graph: Graph, start: str, width: int, height: int) -> dict[str, tuple[float, float]]:
    """Letakkan simpul menurut jarak BFS agar alur dari awal mudah dibaca."""
    adjacency = {node: set(neighbours) for node, neighbours in graph.items()}
    for source, neighbours in graph.items():
        for target in neighbours:
            adjacency[target].add(source)
    levels = {start: 0}
    queue = deque([start])
    while queue:
        node = queue.popleft()
        for neighbour in sorted(adjacency[node]):
            if neighbour not in levels:
                levels[neighbour] = levels[node] + 1
                queue.append(neighbour)
    for node in sorted(graph):
        if node not in levels:
            levels[node] = max(levels.values()) + 1
    groups: dict[int, list[str]] = {}
    for node, level in levels.items():
        groups.setdefault(level, []).append(node)
    x_span = max(1, len(groups) - 1)
    return {
        node: (74 + level * (max(width, 400) - 148) / x_span,
               70 + (index + 1) * (max(height, 350) - 140) / (len(group) + 1))
        for level, group in groups.items()
        for index, node in enumerate(sorted(group))
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bandingkan Dijkstra dan Bellman-Ford pada graf.txt.")
    parser.add_argument("--file", type=Path, default=Path(__file__).with_name("graf.txt"),
                        help="Lokasi berkas graf (default: graf.txt di samping program).")
    parser.add_argument("--cli", action="store_true", help="Cetak hasil tanpa GUI.")
    arguments = parser.parse_args()
    if arguments.cli:
        graph, start, goal = load_graph(arguments.file)
        results = compare(graph, start, goal)
        print(f"Berkas: {arguments.file}\nAwal: {start}; tujuan: {goal}\n")
        print("\n\n".join(map(format_result, results)))
        print("\nKonsisten: bobot minimum sama.")
        return 0
    import tkinter as tk
    from tampilan import GraphApp

    root = tk.Tk()
    GraphApp(root, arguments.file, load_graph, compare, layout, fmt)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

