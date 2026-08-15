import unittest

import app


class VisiblePaymentBehavior(unittest.TestCase):
    def setUp(self):
        app.GRANTED_ACCESS.clear()
        if hasattr(app, "PROCESSED_EVENT_IDS"):
            app.PROCESSED_EVENT_IDS.clear()

    def test_successful_payment_grants_access(self):
        app.handle_payment({"id": "evt-1", "user_id": "student-2", "status": "succeeded"})
        self.assertEqual(app.access_count("student-2"), 1)


if __name__ == "__main__":
    unittest.main()
