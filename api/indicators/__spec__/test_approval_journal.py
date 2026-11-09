import unittest
from datetime import datetime
from types import SimpleNamespace

from api.indicators.journal import aggregate_approval_rows


def row(**kwargs):
    return SimpleNamespace(**kwargs)


class ApprovalJournalAggregateTest(unittest.TestCase):
    def test_document_is_approved_when_every_curator_field_is_approved(self):
        first = datetime(2026, 1, 1)
        second = datetime(2026, 2, 1)
        rows = aggregate_approval_rows(
            [
                row(document_id=5, time_confirmation=first, hospital_id=1, hospital_title="А", curator_field_id=10, approved=True),
                row(document_id=5, time_confirmation=second, hospital_id=2, hospital_title="Б", curator_field_id=11, approved=True),
            ]
        )
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["approved"])
        self.assertEqual(rows[0]["hospital"], "Б")
        self.assertEqual(rows[0]["hospitalId"], 2)
        self.assertEqual(rows[0]["confirmAt"], second)

    def test_one_open_indicator_keeps_the_document_unapproved(self):
        moment = datetime(2026, 3, 1)
        rows = aggregate_approval_rows(
            [
                row(document_id=5, time_confirmation=moment, hospital_id=1, hospital_title="А", curator_field_id=10, approved=True),
                row(document_id=5, time_confirmation=moment, hospital_id=1, hospital_title="А", curator_field_id=11, approved=False),
            ]
        )
        self.assertFalse(rows[0]["approved"])

    def test_group_without_curator_field_does_not_approve_the_document(self):
        rows = aggregate_approval_rows(
            [
                row(document_id=7, time_confirmation=datetime(2026, 4, 1), hospital_id=3, hospital_title="В", curator_field_id=None, approved=False),
            ]
        )
        self.assertFalse(rows[0]["approved"])

    def test_each_research_of_the_document_must_be_approved(self):
        moment = datetime(2026, 5, 1)
        rows = aggregate_approval_rows(
            [
                row(document_id=8, time_confirmation=moment, hospital_id=1, hospital_title="А", curator_field_id=10, approved=True),
                row(document_id=8, time_confirmation=moment, hospital_id=1, hospital_title="А", curator_field_id=12, approved=False),
            ]
        )
        self.assertFalse(rows[0]["approved"])


if __name__ == "__main__":
    unittest.main()
