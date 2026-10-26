"""Offline unit tests for the historical RUM report. Run: python -m unittest discover -s tests"""
import datetime as dt
import unittest
from unittest.mock import patch

from gather_historical_rum import month_starts, cutoff, rum_from_attributes, report, add_growth, UTC


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

    def test_growth_complete_and_zero_baseline(self):
        rows = [{"month": "2026-01", "rum": 0},
                {"month": "2026-02", "rum": 100},
                {"month": "2026-03", "rum": 125},
                {"month": "2026-04", "rum": None},
                {"month": "2026-05", "rum": 140}]
        add_growth(rows)
        self.assertIsNone(rows[0]["growth_rum"])
        self.assertEqual(rows[1]["growth_rum"], 100)
        self.assertIsNone(rows[1]["growth_percent"])
        self.assertEqual(rows[2]["growth_rum"], 25)
        self.assertEqual(rows[2]["growth_percent"], 25.0)
        self.assertIsNone(rows[3]["growth_rum"])
        self.assertIsNone(rows[4]["growth_rum"])

    def test_workspace_growth_separated(self):
        rows = [{"workspace_id": "a", "rum": 5},
                {"workspace_id": "a", "rum": 9},
                {"workspace_id": "b", "rum": 100},
                {"workspace_id": "b", "rum": 90}]
        add_growth(rows, ("workspace_id",))
        self.assertEqual([r["growth_rum"] for r in rows], [None, 4, None, -10])
        self.assertEqual(rows[-1]["growth_percent"], -10.0)

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
