import unittest

from app.services.urgency import calculate_urgency


class UrgencyTests(unittest.TestCase):
    def score(self, **overrides):
        values = {
            "findings": [], "confidence_scores": [], "symptom_count": 0,
            "waiting_hours": 0, "animal_age_years": None,
        }
        values.update(overrides)
        return calculate_urgency(**values)

    def test_low_band_and_exact_upper_edge(self):
        result = self.score(findings=["low"], symptom_count=5, waiting_hours=11.2)
        self.assertEqual(result["score"], 39)
        self.assertEqual(result["level"], "LOW")

    def test_medium_band_and_exact_lower_edge(self):
        result = self.score(findings=["low"], symptom_count=5, waiting_hours=12)
        self.assertEqual(result["score"], 40)
        self.assertEqual(result["level"], "MEDIUM")

    def test_high_band_and_exact_lower_edge(self):
        result = self.score(findings=["high"], confidence_scores=[1], symptom_count=3, waiting_hours=2.4)
        self.assertEqual(result["score"], 70)
        self.assertEqual(result["level"], "HIGH")

    def test_all_components_cap_at_100(self):
        result = self.score(findings=["high"], confidence_scores=[1], symptom_count=100, waiting_hours=100, animal_age_years=8)
        self.assertEqual(result["score"], 100)
        self.assertEqual(result["level"], "HIGH")
        self.assertEqual(result["breakdown"]["symptoms_counted"], 5)
        self.assertEqual(result["breakdown"]["waiting_points"], 15)

    def test_separate_findings_use_highest_severity_and_confidence_not_average(self):
        result = self.score(
            findings=["HEALTHY", "RINGWORM", "FMD"], confidence_scores=[0.2, 0.95, 0.6],
        )
        breakdown = result["breakdown"]
        self.assertEqual(breakdown["disease_severity_points"], 30)
        self.assertEqual(breakdown["ai_confidence"], 0.95)
        self.assertEqual(breakdown["ai_confidence_points"], 23.75)
        self.assertEqual(breakdown["highest_severity_finding"], "FMD")

    def test_confidence_wait_and_age_edges_are_clamped_and_bounded(self):
        result = self.score(confidence_scores=[-0.5, 2, float("nan")], waiting_hours=-5, animal_age_years=float("nan"))
        self.assertEqual(result["breakdown"]["ai_confidence"], 1)
        self.assertEqual(result["breakdown"]["waiting_points"], 0)
        self.assertEqual(result["breakdown"]["animal_age_points"], 0)
        self.assertIsNone(result["breakdown"]["animal_age_years"])
        self.assertEqual(self.score(animal_age_years=5)["breakdown"]["animal_age_points"], 6)
        self.assertEqual(self.score(animal_age_years=3)["breakdown"]["animal_age_points"], 3)
        self.assertEqual(self.score(animal_age_years=8)["breakdown"]["animal_age_points"], 10)

    def test_missing_or_unknown_inputs_are_low_and_zero(self):
        result = self.score(findings=["not mapped"], confidence_scores=[None], animal_age_years=None)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["level"], "LOW")


if __name__ == "__main__":
    unittest.main()
