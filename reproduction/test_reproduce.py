import unittest

from reproduce import build_report, manifest_hashes


class ReproductionTest(unittest.TestCase):
    def test_published_counts(self) -> None:
        report = build_report()
        by_name = {item["name"]: item for item in report["primary"]}
        self.assertEqual(by_name["extra_prediction_inversion"]["mismatches"], 109)
        self.assertEqual(by_name["extra_prediction_inversion"]["compared_rows"], 115)
        self.assertEqual(by_name["no_extra_prediction_inversion"]["mismatches"], 6)
        self.assertEqual(by_name["no_extra_prediction_inversion"]["compared_rows"], 115)
        self.assertEqual(by_name["no_inversion_offset_minus_1"]["mismatches"], 4)
        self.assertEqual(by_name["no_inversion_offset_minus_1"]["compared_rows"], 114)

    def test_input_hashes_match_the_frozen_manifest(self) -> None:
        self.assertEqual(build_report()["input_hashes"], manifest_hashes())


if __name__ == "__main__":
    unittest.main()
