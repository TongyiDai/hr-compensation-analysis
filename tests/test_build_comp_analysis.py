import json
import unittest
from pathlib import Path

from scripts.build_comp_analysis import analyze, render_markdown


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "engineering-bands.json"


class CompensationAnalysisTest(unittest.TestCase):
    def load(self):
        return json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_calculates_compa_ratio_and_penetration(self):
        report = analyze(self.load())
        first = report["records"][0]
        self.assertEqual(first["compa_ratio"], 0.9)
        self.assertEqual(first["range_penetration"], 0.25)

    def test_marks_outside_band(self):
        report = analyze(self.load())
        positions = {row["person_ref"]: row["position"] for row in report["records"]}
        self.assertEqual(positions["P-003"], "高于带宽")
        self.assertEqual(positions["P-004"], "低于带宽")

    def test_adds_small_sample_review(self):
        report = analyze(self.load())
        reasons = [item["reason"] for item in report["review_queue"]]
        self.assertIn("样本量小于 3", reasons)

    def test_rejects_sensitive_field(self):
        data = self.load()
        data["people"][0]["full_name"] = "test"
        with self.assertRaisesRegex(ValueError, "sensitive fields"):
            analyze(data)

    def test_rejects_extra_person_field(self):
        data = self.load()
        data["people"][0]["free_text_notes"] = "原始讨论内容"
        with self.assertRaisesRegex(ValueError, "unsupported fields"):
            analyze(data)

    def test_rejects_invalid_band(self):
        data = self.load()
        data["bands"][0]["midpoint"] = 360000
        with self.assertRaisesRegex(ValueError, "minimum < midpoint < maximum"):
            analyze(data)

    def test_rejects_unknown_factor(self):
        data = self.load()
        data["people"][0]["explained_factors"] = ["manager_likeability"]
        with self.assertRaisesRegex(ValueError, "approved neutral"):
            analyze(data)

    def test_markdown_keeps_human_boundary(self):
        report = analyze(self.load())
        self.assertIn("人工决策边界", render_markdown(report))


if __name__ == "__main__":
    unittest.main()
