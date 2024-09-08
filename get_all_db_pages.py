import requests
import json
import os, sys
sys.path.insert(1, "/".join(os.path.realpath(__file__).split("/")[0:-2]))
from main import settings_local as authentication
from lxml import etree
import chardet
import re

qbUsername = authentication.QB_USERNAME
qbPassword = authentication.QB_PASSWORD
qbAppToken = authentication.QB_TOKEN
qbRealmHost = authentication.QB_REALM_HOST
qbHours = authentication.QB_HOURS
qbBaseURL = authentication.QB_BASE_URL
qbApplicationDBID = authentication.QB_APPLICATION_DBID

class DatabaseClient:
    def __init__(self):
        self.qb_dbid = getattr(self, 'qb_dbid', None) 
        self.field_values = {}
        self.username = qbUsername
        self.password = qbPassword
        self.apptoken = qbAppToken
        self.realmhost = qbRealmHost
        self.hours = qbHours
        self.base_url = qbBaseURL
        self.application_dbid = qbApplicationDBID
        self.session = requests.Session()

    def authenticate(self):
        temp_auth = f"{qbBaseURL}/db/main?a=API_Authenticate"
        temp_auth += f"&username={qbUsername}&password={qbPassword}&hours={qbHours}"
        response = requests.post(temp_auth)
        ticket = etree.fromstring(response.content).findtext('ticket')
        return ticket

    def get_all_database_pages(self):
        query_ticket = self.authenticate()
        data_url = f"{qbBaseURL}/db/{qbApplicationDBID}?a=AppDBPages&ticket={query_ticket}"
        data_response = self.session.get(data_url)
        response_content = data_response.content.decode('utf-8')

        if data_response.status_code == 200:
            # Ensure correct encoding
            data_response.encoding = 'utf-8'
            # Get the raw text content
            response_content = data_response.text
            try:
                # Regex to extract the modelData JavaScript array
                pattern = re.compile(r"input\.modelData\s*=\s*(\[\s*{.*?}\s*]);", re.DOTALL)
                match = pattern.search(response_content)
                if match:
                    # Extract the JavaScript array
                    model_data_js = match.group(1)
                    # Clean up the JavaScript object for JSON compliance
                    model_data_js_cleaned = clean_js_to_json(model_data_js)
                    # Convert to Python dictionary (from JSON)
                    model_data = json.loads(model_data_js_cleaned)
                    # Extract name and id into a dictionary
                    extracted_data = {item['name']: item['id'] for item in model_data}
                    # Format the extracted data with each key-value pair on its own line
                    formatted_lines = [f'    "{key}": {value}' for key, value in extracted_data.items()]
                    json_data_custom = '{\n' + ',\n'.join(formatted_lines) + '\n}'
                    print(json_data_custom)
                else:
                    print("No model data found.")
            except json.JSONDecodeError as e:
                print("JSON Decode Error:", str(e))
            except Exception as e:
                print("An error occurred while processing the response:", str(e))
        else:
            print(f"Request failed with status code: {data_response.status_code}")



def clean_js_to_json(js_data):
    # Replace True/False/None with JSON-compatible values
    js_data = js_data.replace("True", "true").replace("False", "false").replace("None", "null")

    # Replace single quotes with double quotes
    js_data = js_data.replace("'", '"')

    # Ensure that property names are quoted (double quotes)
    # This regex finds unquoted property names and wraps them in double quotes
    js_data = re.sub(r'(\w+)\s*:', r'"\1":', js_data)

    return js_data

# Example usage
client = DatabaseClient()
client.get_all_database_pages()
