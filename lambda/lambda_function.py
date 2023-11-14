import json
import base64
from salesforce import Salesforce
from mapping import get_salesforce_contact_id, map_profile_to_salesforce_contact

salesforce = Salesforce()

def lambda_handler(event, context): 
    for record in event['Records']:
        data = base64.b64decode(record['kinesis']['data']).decode('utf8')
        payload = json.loads(data)
        print({ 'record': record, 'payload': payload })

        # Update Salesforce Contact object if this is profile update event
        if payload['EventType'] == 'UPDATED' and payload['ObjectTypeName'] == '_profile':
            response = update_contact(payload['Object'])
            print({ 'response': response })
    
    return {}

def update_contact(profile):
    sobject = 'Contact'

    # Extract Salesforce Contact ID
    sobj_id = get_salesforce_contact_id(profile)
    if sobj_id is None:
        print('Attributes.sfdcContactId not found. Skipping.')
        return None

    # Construct Contact object data
    data = map_profile_to_salesforce_contact(profile)
    print({ 'sobject': sobject, 'sobj_id': sobj_id, 'data': data })

    return salesforce.update(sobject, sobj_id, data)

if __name__ == '__main__':
    update_contact({
        'Address': { 'Address1': 'Foo' },
        'PhoneNumber': '+17777777777',
        'Attributes': { 'sfdcContactId': '0032v00003aKADPAA4' }
    })

