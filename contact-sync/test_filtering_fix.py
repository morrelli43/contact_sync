
import sys
import os

# Add the contact-sync directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'contact-sync')))

from contact_model import Contact
from square_connector import SquareConnector

def test_filtering_logic():
    # Mock some dependencies to avoid actual Square API calls during init
    os.environ['SQUARE_ACCESS_TOKEN'] = 'fake_token'
    
    # We need to bypass the _ensure_custom_attribute_definitions call in __init__
    # So we'll mock it or just test the _convert_to_contact method directly
    
    # Creating a dummy class to test the method
    class MockSquareConnector(SquareConnector):
        def __init__(self):
            # Do nothing init
            self.attribute_keys = {}
            pass
            
    connector = MockSquareConnector()
    
    scenarios = [
        {
            "name": "Full Contact",
            "customer": {"given_name": "John", "family_name": "Doe", "email_address": "john@example.com", "phone_number": "0412345678"},
            "expected_filtered": False
        },
        {
            "name": "No Email, Both Names",
            "customer": {"given_name": "John", "family_name": "Doe", "phone_number": "0412345678"},
            "expected_filtered": False
        },
        {
            "name": "No Email, First Name Only",
            "customer": {"given_name": "John", "phone_number": "0412345678"},
            "expected_filtered": False # Previously this was filtered out!
        },
        {
            "name": "No Email, Phone Only",
            "customer": {"phone_number": "0412345678"},
            "expected_filtered": False # Previously this was filtered out!
        },
        {
            "name": "No Email, No Phone, First Name Only",
            "customer": {"given_name": "John"},
            "expected_filtered": False
        },
        {
            "name": "No Email, No Phone, No Name",
            "customer": {},
            "expected_filtered": True
        }
    ]
    
    print("Testing relaxed Square filtering logic...\n")
    all_passed = True
    for scenario in scenarios:
        contact = connector._convert_to_contact(scenario["customer"])
        is_filtered = contact is None
        
        status = "PASSED" if is_filtered == scenario["expected_filtered"] else "FAILED"
        if status == "FAILED":
            all_passed = False
            
        print(f"Scenario: {scenario['name']}")
        print(f"  Result: {'Filtered' if is_filtered else 'Kept'} (Expected: {'Filtered' if scenario['expected_filtered'] else 'Kept'}) -> {status}")
        
    if all_passed:
        print("\n✅ All scenarios passed! The filtering logic is now correctly relaxed.")
    else:
        print("\n❌ Some scenarios failed.")
        sys.exit(1)

if __name__ == "__main__":
    test_filtering_logic()
