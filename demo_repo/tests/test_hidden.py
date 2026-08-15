import unittest

import app


class DuplicateDeliveryInvariant(unittest.TestCase):
    def setUp(self):
        app.GRANTED_ACCESS.clear()
        if hasattr(app, "PROCESSED_EVENT_IDS"):
            app.PROCESSED_EVENT_IDS.clear()

    def test_repeated_success_event_grants_access_exactly_once(self):
        event = {"id": "evt-1", "user_id": "student-2", "status": "succeeded"}
        app.handle_payment(event)
        app.handle_payment(event)
        self.assertEqual(app.access_count("student-2"), 1)


if __name__ == "__main__":
    unittest.main()
