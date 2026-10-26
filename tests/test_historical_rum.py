"""Offline unit tests for the historical RUM report. Run: python -m unittest discover -s tests"""
import datetime as dt
import unittest
from unittest.mock import patch

from gather_historical_rum import month_starts, cutoff, rum_from_attributes, report, UTC


class FakeAPI:
    def pages(self, path, params=None):
        if path.endswith("/workspaces"):
            return iter([
                {"id": "ws-1", "attributes": {"name": "test", "created-at": "2026-01-10T00:00:00Z"}}
            ])
        return iter([
            {"id": "sv-1", "attributes": {
                "created-at": "2026-01-15T00:00:00Z", "status": "finalized", "billable-rum-count": 5}},
            {"id": "sv-2", "attributes": {
                "created-at": "2026-03-01T00:00:00Z", "status": "finalized", "billable-rum-count": 9}}
        ])

    def get(self, path):
        raise AssertionError("Unexpected detail read")


class Tests(unittest.TestCase):
    def test_month_boundaries(self):
        self.assertEqual(list(month_starts("2025-12", "2026-02")),
                         ["2025-12", "2026-01", "2026-02"])
        self.assertEqual(cutoff("2025-12"), dt.datetime(2026, 1, 1, tzinfo=UTC))

    def test_count_exclusions(self):
        a = {"resources": [
            {"type": "aws_instance", "count": 4, "provider": "aws"},
            {"type": "terraform_data", "count": 10, "provider": "terraform"},
            {"type": "data.aws_ami", "count": 20, "provider": "aws"},
            {"type": "null_resource", "count": 1,
             "provider": 'provider["registry.terraform.io/hashicorp/null"]'}
        ]}
        self.assertEqual(rum_from_attributes(a), 4)
        self.assertEqual(rum_from_attributes({"resources-processed": False}), None)
        self.assertEqual(rum_from_attributes({"billable-rum-count": 3}), 3)

    def test_month_end_carry_forward(self):
        summary, rows = report(FakeAPI(), "org", ["2025-12", "2026-01", "2026-02", "2026-03"])
        self.assertEqual([x["rum"] for x in summary], [0, 5, 5, 9])
        self.assertTrue(all(x["complete"] for x in summary))
        self.assertEqual(len(rows), 3)

    def test_unknown_before_first_retained_state(self):
        class Missing(FakeAPI):
            def pages(self, path, params=None):
                if path.endswith("/workspaces"):
                    return iter([{"id": "ws-1", "attributes": {
                        "name": "test", "created-at": "2025-10-01T00:00:00Z"}}])
                return iter([{"id": "sv-1", "attributes": {
                    "created-at": "2026-02-10T00:00:00Z",
                    "status": "finalized", "billable-rum-count": 4}}])
        summary, _ = report(Missing(), "org", ["2026-01"])
        self.assertIsNone(summary[0]["rum"])
        self.assertEqual(summary[0]["unknown_workspaces"], 1)


if __name__ == "__main__":
    unittest.main()
