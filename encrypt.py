import pyodbc, os, ast, urllib, sys
from datetime import datetime
from cryptography.fernet import Fernet
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

keyVaultName = os.environ["AZ_KEY_VAULT_NAME"]
KVUri = f"https://{keyVaultName}.vault.azure.net"
print("===============KVUri::", type(KVUri))
credential = DefaultAzureCredential()
client = SecretClient(vault_url=KVUri, credential=credential)
retrieved_secret = client.get_secret('SOCRATE-SQL-PASS-DEV')
db_encryption_secret = client.get_secret('SOCRATE-SQL-DB-ENCRYPTION-KEY')
PASSWORD_ORI = retrieved_secret.value
PASSWORD = urllib.parse.quote_plus(PASSWORD_ORI)
DB_ENCRYPTION_KEY = ast.literal_eval(db_encryption_secret.value)
print("===========DB_ENCRYPTION_KEY:", DB_ENCRYPTION_KEY)
#sys.exit()

# Generate a key for encryption (Keep this key secure, as it's needed for decryption)
#key = Fernet.generate_key()
# keyStr = os.environ['SOCRATE-SQL-DB-ENCRYPTION-KEY']
# key = ast.literal_eval(keyStr)
# print("key:", type(key), key)

cipher_suite = Fernet(DB_ENCRYPTION_KEY)

# Encrypt function
def encrypt_text(text):
    encrypted_text = cipher_suite.encrypt(text.encode())
    return encrypted_text

# Decrypt function
def decrypt_text(encrypted_text):
    decrypted_text = cipher_suite.decrypt(encrypted_text).decode()
    return decrypted_text

plain_text = "This is a secret message...."
encrypted_text = encrypt_text(plain_text)
# Connection parameters
server = os.environ.get('SQL_DATABASE_HOST')
database = os.environ.get('SQL_DBNAME')
username = os.environ.get('SQL_USERNAME')
password = os.environ.get('SQL_PASS')

# Establish a connection
connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

# Replace 'your_values' with the actual values you want to insert
record = {
    'id': 'myid200',
    'transcript': encrypted_text,
    'bintext': (pyodbc.Binary(encrypted_text)),
    'created_at': datetime.now(),
    'username': 'your_username',
    'userid': 2,
    'updated_at': datetime.now(),
    'dialog_title': 'test your_dialog_title',
    'dialog_content': 'your_dialog_content',
    'status': 0,
    'dialog_feedbacks': 'your_dialog_feedbacks'
}

# Build the SQL query
query = """
    INSERT INTO [gpt].[testtable]
    ([id], [transcript], [bintext], [created_at], [username], [userid], [updated_at],
     [dialog_title], [dialog_content], [status], [dialog_feedbacks])
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

# Execute the query with the provided values
#cursor.execute(query, tuple(record.values()))
#connection.commit()

# Close the cursor and connection

#id = 'e1a5f20c-463a-40ee-9e25-0c1d92750b4b'
#id = 'bb1502b9-0dff-41f4-8d44-96bb42fad056'
id = '73da1967-a402-4551-a70a-0595f9495abb'
# Query the encrypted text from the database
cursor.execute(f"SELECT * FROM gpt.transcripts WHERE id = '{id}'")
row = cursor.fetchone()
dialog_content_bin = None
transcript_bin = None
# Decrypt the text when retrieving from the database
if row:
  dialog_content_bin = decrypt_text(row.dialog_content_bin)
if row:
  transcript_bin = decrypt_text(row.transcript_bin)

# Print the results
print("Original text:", plain_text)
print("Encrypted text:", encrypted_text)
print("Encrypted text bin:", pyodbc.Binary(encrypted_text))

print("\n======Decrypted dialog_content_bin:\n",  dialog_content_bin)
print("\n======Decrypted transcript_bin:\n",  transcript_bin)


# Query the encrypted text from the database
cursor.execute(f"SELECT * FROM gpt.user_state WHERE id = '{id}'")
rowUserState = cursor.fetchone()

# Decrypt the text when retrieving from the database
state_bin = decrypt_text(rowUserState.state_bin)
print("\n======Decrypted state_bin:\n", type(state_bin), state_bin)

cursor.close()
connection.close()
