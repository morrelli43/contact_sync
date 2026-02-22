from google_connector import GoogleContactsConnector
from contact_model import Contact
import traceback

connector = GoogleContactsConnector()
connector.authenticate()

# Try to create a dummy contact first
contact = Contact()
contact.first_name = "Test"
contact.last_name = "Contact 400"
connector._create_contact(contact)
contact_id = contact.source_ids.get('google')
print(f"Created: {contact_id}")

try:
    person = connector._contact_to_person(contact)

    # Get etag
    current = connector._retry_api_call(
        connector.service.people().get(
            resourceName=contact_id,
            personFields='names'
        ).execute
    )
    
    def try_update(field_name, payload):
        import copy
        test_person = copy.deepcopy(person)
        test_person['etag'] = current.get('etag')
        test_person.update(payload)
        
        try:
            connector._retry_api_call(
                connector.service.people().updateContact(
                    resourceName=contact_id,
                    updatePersonFields='names,emailAddresses,phoneNumbers,organizations,addresses,biographies,userDefined',
                    body=test_person
                ).execute
            )
            print(f"SUCCESS with {field_name}")
        except Exception as e:
            print(f"FAILED with {field_name}: {e}")

    # Test 1: empty userDefined
    try_update("empty userDefined value", {
        "userDefined": [{"key": "escooter1", "value": ""}]
    })

    # Test 2: empty arrays for everything else
    try_update("empty arrays", {
        "emailAddresses": [],
        "phoneNumbers": [],
        "organizations": [],
        "addresses": [],
        "biographies": []
    })

    # Test 3: space in organization name
    try_update("space in org name", {
        "organizations": [{"name": " ", "title": "Some Title"}]
    })

finally:
    # Clean up
    connector.delete_contact(contact_id)
