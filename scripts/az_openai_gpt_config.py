import openai, os
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

def init():
    keyVaultName = os.environ["AZ_KEY_VAULT_NAME"]
    KVUri = f"https://{keyVaultName}.vault.azure.net"
    print("=======module==AZ_KV_Uri in socratic_dialogue:", KVUri)
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url=KVUri, credential=credential)

    openai.api_type = "azure"
    openai.api_version = "2023-07-01-preview"
    openai.api_base = client.get_secret('SOCRATE-AZ-OPENAI-API-BASE').value
    openai.api_key = client.get_secret('SOCRATE-AZ-OPENAI-API-KEY').value
    print('=======module==az.openai.api_base:', openai.api_base)