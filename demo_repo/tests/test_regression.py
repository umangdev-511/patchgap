import unittest

import app


class PaymentRegressionBehavior(unittest.TestCase):
    def setUp(self):
        app.GRANTED_ACCESS.clear()
        if hasattr(app, "PROCESSED_EVENT_IDS"):
            app.PROCESSED_EVENT_IDS.clear()

    def test_non_successful_payments_do_not_grant_access(self):
        for status in ("failed", "processing"):
            app.handle_payment({"id": f"evt-{status}", "user_id": "student-2", "status": status})
        self.assertEqual(app.access_count("student-2"), 0)

    def test_distinct_success_events_still_grant_access(self):
        app.handle_payment({"id": "evt-1", "user_id": "student-2", "status": "succeeded"})
        app.handle_payment({"id": "evt-2", "user_id": "student-2", "status": "succeeded"})
        self.assertEqual(app.access_count("student-2"), 2)


if __name__ == "__main__":
    unittest.main()
