"""Uji kasus dari soal dan beberapa kondisi batas. Jalankan: python uji_program.py"""

import tempfile
import unittest
from pathlib import Path

from MMAIKelompok4 import bellman_ford, compare, dijkstra, load_graph


ROOT = Path(__file__).parent


class ShortestPathTests(unittest.TestCase):
    def test_contoh_a(self):
        graph, start, goal = load_graph(ROOT / "graf.txt")
        for result in compare(graph, start, goal):
            self.assertEqual(result.path, ("V1", "V2", "V5", "V9", "V12", "V15"))
            self.assertEqual(result.cost, 505)

    def test_contoh_b(self):
        graph, start, _ = load_graph(ROOT / "graf.txt")
        for result in compare(graph, start, "V10"):
            self.assertEqual(result.path, ("V1", "V4", "V6", "V10"))
            self.assertEqual(result.cost, 400)

    def test_contoh_c(self):
        graph, start, goal = load_graph(ROOT / "graf_contoh_C.txt")
        for result in compare(graph, start, goal):
            self.assertEqual(result.path, ("B", "C", "F", "E", "H"))
            self.assertEqual(result.cost, 9)

    def test_graf_tidak_terhubung_dan_simpul_sama(self):
        graph = {"A": {"B": 2}, "B": {}, "C": {}}
        for algorithm in (dijkstra, bellman_ford):
            self.assertEqual(algorithm(graph, "A", "C").path, ())
            self.assertEqual(algorithm(graph, "A", "A").path, ("A",))

    def test_bobot_negatif_ditolak(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "graf.txt"
            path.write_text("graph = {'A': {'B': -1}, 'B': {}}\nA B\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "harus hingga dan >= 0"):
                load_graph(path)

    def test_input_tidak_dieksekusi(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "graf.txt"
            path.write_text("graph = {'A': {'B': __import__('os').system('echo BAD')}, 'B': {}}\nA B\n",
                            encoding="utf-8")
            with self.assertRaises(ValueError):
                load_graph(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
