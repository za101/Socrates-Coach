import bcrypt, random, string, pyodbc, urllib, sys,os, ast
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
keyVaultName = os.environ["AZ_KEY_VAULT_NAME"]
KVUri = f"https://{keyVaultName}.vault.azure.net"
print("===============KVUri::", type(KVUri))
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)
retrieved_secret = client.get_secret('SOCRATE-SQL-PASS-PROD')
db_encryption_secret = client.get_secret('SOCRATE-SQL-DB-ENCRYPTION-KEY')
PASSWORD_ORI = retrieved_secret.value
PASSWORD = urllib.parse.quote_plus(PASSWORD_ORI)
print("===========DB_PASSWORD:", PASSWORD)
#sys.exit()

# server = os.environ.get('SQL_DATABASE_HOST')
# database = os.environ.get('SQL_DBNAME')
# username = os.environ.get('SQL_USERNAME')
# password = os.environ.get('SQL_PASS')

server = os.environ.get('SQL_DATABASE_HOST_PROD')
database = os.environ.get('SQL_DBNAME')
username = os.environ.get('SQL_USERNAME_PROD')
password = os.environ.get('SQL_PASS_PROD')

connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

import csv

# Open the CSV file
csv_file_path = 'Socrates_User_Accounts.csv'

# Use 'with' to automatically close the file when the block is exited
with open(csv_file_path, 'r') as file:
    # Create a CSV reader object
    csv_reader = csv.reader(file)

    # Skip the header row if it exists
    header = next(csv_reader, None)
    if header:
        print(f"Header: {header}")

    # Loop through the rows in the CSV file
    for row in csv_reader:
        # Access individual columns by index
        seq, user_name, password, salt_hash = row
        #salt_hash_bytes = ast.literal_eval(salt_hash.encode('utf-8').decode('unicode_escape'))
        record = {
            'username': user_name.lstrip(),
            'token_usage': 0,
            'token_usage_limit': 1000000
        }
        print(f"user_name: |{user_name.lstrip()}|" )
        query = """
                    INSERT INTO [gpt].[user_usage]
                    ( [username], [token_usage], [token_usage_limit])
                    VALUES (?, ?, ?)
                """
        cursor.execute(query, tuple(record.values()))
connection.commit()