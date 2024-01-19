import os, openai
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class AzureGptSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AzureGptSingleton, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        #keyVaultName = os.environ["AZ_KEY_VAULT_NAME"]
        keyVaultName = "rhnonprodkv"
        KVUri = f"https://{keyVaultName}.vault.azure.net"
        print("=======module==AZ_KV_Uri in socratic_dialogue:", KVUri)
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KVUri, credential=credential)

        openai.api_type = "azure"
        openai.api_version = "2023-07-01-preview"
        openai.api_base = client.get_secret('SOCRATE-AZ-OPENAI-API-BASE').value
        self.api_base = client.get_secret('SOCRATE-AZ-OPENAI-API-BASE').value
        openai.api_key = client.get_secret('SOCRATE-AZ-OPENAI-API-KEY').value
        self.openai = openai
        print('=======module==az.openai.api_base:', openai.api_base)
    
    def get_api_base(self):
        return self.api_base
    def get_openai_instance(self):
        return self.openai

def getAzureGptInstance():
    return AzureGptSingleton()
