import os, openai
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential

class OpenAiGptSingleton:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAiGptSingleton, cls).__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        keyVaultName = os.environ["KEY_VAULT_NAME"]
        KVUri = f"https://{keyVaultName}.vault.azure.net"
        print("=========KVUri in socratic_dialogue:", KVUri)
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=KVUri, credential=credential)
        openai.organization = client.get_secret('SOCRATE-OPENAI-ORG').value
        openai.api_key = client.get_secret('SOCRATE-OPENAI-API-KEY').value
        self.api_base = client.get_secret('SOCRATE-OPENAI-ORG').value
        print('=========openai.organization:', openai.organization)
        self.openai = openai
    
    def get_api_base(self):
        return self.api_base
    def get_openai_instance(self):
        return self.openai

def getOpenAiGptInstance():
    return OpenAiGptSingleton()
