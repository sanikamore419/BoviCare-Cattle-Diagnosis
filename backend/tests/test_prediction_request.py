import unittest

from pydantic import ValidationError

from app.schemas.prediction import PredictionRequest


class PredictionRequestTests(unittest.TestCase):
    def test_requires_symptoms_milk_or_existing_image_result(self):
        with self.assertRaises(ValidationError):
            PredictionRequest.model_validate({})

    def test_accepts_symptom_prediction(self):
        request = PredictionRequest.model_validate({"symptoms": ["coughing"], "case_id": 7})
        self.assertEqual(request.case_id, 7)
        self.assertFalse(request.image_only)

    def test_accepts_image_result_lookup_with_case_id(self):
        request = PredictionRequest.model_validate({"case_id": 7, "image_only": True})
        self.assertTrue(request.image_only)

    def test_image_result_lookup_requires_case_id(self):
        with self.assertRaises(ValidationError):
            PredictionRequest.model_validate({"image_only": True})

    def test_image_result_lookup_rejects_mixed_inputs(self):
        with self.assertRaises(ValidationError):
            PredictionRequest.model_validate({"case_id": 7, "image_only": True, "symptoms": ["coughing"]})

    def test_partial_milk_data_is_still_rejected(self):
        with self.assertRaises(ValidationError):
            PredictionRequest.model_validate({"milk_data": {"Milk_Temperature": 37.0}})


if __name__ == "__main__":
    unittest.main()
