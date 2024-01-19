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
#print("===========DB_PASSWORD:", PASSWORD)
#sys.exit()

server = os.environ.get('SQL_DATABASE_HOST')
database = os.environ.get('SQL_DBNAME')
username = os.environ.get('SQL_USERNAME')
password = os.environ.get('SQL_PASS')
connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
connection = pyodbc.connect(connection_string)
cursor = connection.cursor()

cursor.execute(f"SELECT * FROM gpt.credentials WHERE username = 'SocrtMqr7Eq1'")
row = cursor.fetchone()
print("===salthash:", row.password_salthash)

def check_password(input_password, stored_hashed_password):
    # Check if the input password matches the stored hashed password
    return bcrypt.checkpw(input_password.encode('utf-8'), stored_hashed_password)

input_password = 'SocrtMqr7Eq1'
if check_password(input_password, row.password_salthash):
#if check_password(input_password, b'$2b$12$.PVj.jgU9p/CLAiNGiKp4OAyCfKqpAhjh2IK08jKAKFm4VF8IN5Oa'):
    print("Password is correct!!!!")
else:
    print("Password is incorrect....")