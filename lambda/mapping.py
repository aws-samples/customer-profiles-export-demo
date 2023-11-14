PROFILE_TO_SF_CONTACT = {
    'LastName': 'LastName',
    'FirstName': 'FirstName',
    'MiddleName': 'MiddleName',
    'Address.Address1': 'OtherStreet',
    'Address.City': 'OtherCity',
    'Address.State': 'OtherState',
    'Address.Country': 'OtherCountry',
    'Address.PostalCode': 'OtherPostalCode',
    'MailingAddress.Address1': 'MailingStreet',
    'MailingAddress.City': 'MailingCity',
    'MailingAddress.State': 'MailingState',
    'MailingAddress.Country': 'MailingCountry',
    'MailingAddress.PostalCode': 'MailingPostalCode',
    'PhoneNumber': 'Phone',
    'HomePhoneNumber': 'HomePhone',
    'MobilePhoneNumber': 'MobilePhone',
    'EmailAddress': 'Email',
    'BirthDate': 'Birthdate',
}

def get_salesforce_contact_id(profile):
    return get_attribute(profile, 'Attributes.sfdcContactId')

def get_attribute(dct, attribute):
    for chunk in attribute.split('.'):
        try:
            dct = dct[chunk]
        except KeyError:
            return None
    return dct

def map_profile_to_salesforce_contact(profile):
    contact = {}
    for map_from, map_to in PROFILE_TO_SF_CONTACT.items():
        value = get_attribute(profile, map_from)
        if value is not None:
            contact[map_to] = value
    return contact

