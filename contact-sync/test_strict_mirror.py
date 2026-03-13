
import unittest
from unittest.mock import MagicMock
from datetime import datetime, timedelta, timezone
from contact_model import Contact
from sync_engine import SyncEngine

class TestStrictMirror(unittest.TestCase):
    def setUp(self):
        self.engine = SyncEngine()
        self.google_conn = MagicMock()
        self.square_conn = MagicMock()
        
        self.engine.register_connector('google', self.google_conn)
        self.engine.register_connector('square', self.square_conn)
        
        # Dynamic mock behaviors to support dirty checking
        self.google_conn._contact_to_person.side_effect = lambda c: {"names": [{"givenName": c.first_name}]}
        self.square_conn._contact_to_customer.side_effect = lambda c: {"given_name": c.first_name}
        self.google_conn.push_contact.return_value = True
        self.google_conn.delete_contact.return_value = True

    def test_square_overwrites_google_change(self):
        """If a contact exists in both, Square (Source of Truth) should overwrite Google."""
        # 1. Square Contact
        sq_c = Contact()
        sq_c.first_name = "Square Name"
        sq_c.phone = "0400111222"
        sq_c.source_ids['square'] = "sq_1"
        sq_c.last_modified = datetime.now(timezone.utc)
        
        # 2. Google Contact (different name, same phone/sq_id)
        go_c = Contact()
        go_c.first_name = "Manual Change in Google"
        go_c.phone = "0400111222"
        go_c.source_ids['square'] = "sq_1"
        go_c.source_ids['google'] = "people/go_1"
        go_c.last_modified = datetime.now(timezone.utc) + timedelta(minutes=5) # Manually changed later
        
        self.square_conn.fetch_contacts.return_value = [sq_c]
        self.google_conn.fetch_contacts.return_value = [go_c]
        
        self.engine.sync_all()
        
        # Verify that push_contact was called with "Square Name" for Google
        # Even though Google was "newer", it's NOT the source of truth, so Square wins.
        pushed_contacts = [call.args[0] for call in self.google_conn.push_contact.call_args_list]
        self.assertTrue(any(c.first_name == "Square Name" for c in pushed_contacts))

    def test_square_deletion_propagates_to_google(self):
        """Deleting a contact in Square should result in deletion in Google."""
        # 1. Square is empty (contact deleted)
        self.square_conn.fetch_contacts.return_value = []
        
        # 2. Google still has the contact that was linked to Square
        go_c = Contact()
        go_c.first_name = "To Be Deleted"
        go_c.source_ids['square'] = "sq_gone"
        go_c.source_ids['google'] = "people/go_gone"
        
        self.google_conn.fetch_contacts.return_value = [go_c]
        
        self.engine.sync_all()
        
        # Verify that delete_contact was called for the Google resource
        self.google_conn.delete_contact.assert_called_once_with("people/go_gone")

    def test_google_only_contact_is_safe(self):
        """A contact only in Google (not linked to Square) should NOT be deleted."""
        self.square_conn.fetch_contacts.return_value = []
        
        go_c = Contact()
        go_c.first_name = "Google Only"
        go_c.phone = "0499999999"
        # NO square source ID
        
        self.google_conn.fetch_contacts.return_value = [go_c]
        
        self.engine.sync_all()
        
        # delete_contact should NOT be called
        self.google_conn.delete_contact.assert_not_called()

if __name__ == "__main__":
    unittest.main()
