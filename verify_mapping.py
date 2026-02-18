from webform_connector import WebFormConnector
from contact_model import Contact
import os

def verify():
    # Use a temp file
    storage = 'verify_contacts.json'
    if os.path.exists(storage):
        os.remove(storage)
        
    connector = WebFormConnector(storage_file=storage)
    
    # Simulate submission
    data = {
        'first_name': 'Ben',
        'last_name': 'Tester',
        'phone': '0411222333',
        'suburb': 'Fitzroy',
        'postcode': '3065',
        'scooter_name': 'Apollo',
        'scooter_model': 'Ghost'
    }
    
    print(f"Simulating submission: {data}")
    connector._process_contact_data(data)
    
    contacts = connector.fetch_contacts()
    if not contacts:
        print("No contacts found!")
        return

    c = contacts[0]
    print("\n--- Mapped Contact ---")
    print(f"Name: {c.first_name} {c.last_name}")
    print(f"Phone: {c.phone}")
    
    # Check Address
    if c.addresses:
        addr = c.addresses[0]
        print(f"Address: City='{addr.get('city')}', Postcode='{addr.get('postal_code')}'")
        if addr.get('postal_code') == '3065':
            print("✅ Postcode mapped correctly")
        else:
            print(f"❌ Postcode mismatch: expected 3065, got '{addr.get('postal_code')}'")
    else:
        print("❌ No address mapped")
        
    # Check Scooter
    print(f"Extra Fields: {c.extra_fields}")
    expected_scooter = "Apollo Ghost"
    if c.extra_fields.get('escooter1') == expected_scooter:
        print(f"✅ Scooter info combined into 'escooter1': '{expected_scooter}'")
    else:
        print(f"ℹ️ Scooter info mapped to: {c.extra_fields}")

    # Cleanup
    if os.path.exists(storage):
        os.remove(storage)

if __name__ == "__main__":
    verify()
