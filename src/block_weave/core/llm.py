import os
from enum import Enum
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import ollama

# TODO: only require imports that we're using?

load_dotenv(dotenv_path="environment/.env")

class Providers(Enum):
    OPENAI = "OPENAI"
    MISTRAL = "MISTRAL"
    OLLAMA = "OLLAMA"

class CallLM:
    def __init__(self, provider: str, model: str, temperature: float = 0.5):
        """
        Call API to run an LLM model

        Args:
            provider (str):
            model (str):  
            temperature (float):
        """
        # TODO: allow using different models than from openai
        #   - Handle calling models that don't exist
        #   (later) local model

        self.model = model
        self.temperature = temperature

        # e.g. OPENAI, MISTRAL, OLLAMA
        self.provider = provider.upper()
        self.provider_map = {
            # TODO (later): manual, when using e.g. a chat model
            Providers.OPENAI.value: self.openai,
            Providers.OLLAMA.value: self.ollama,
            # "MISTRAL": self.mistral,
        }

        self.api_key = self.get_api_key(self.provider)

    def __call__(self, prompt: str) -> str:
        return self.run(prompt=prompt, provider=self.provider, model=self.model, temperature=self.temperature)
    
    @staticmethod
    def get_api_key(provider: str):
        # Assumes in .env API key is given as PROVIDERNAME_API_KEY
        suffix = "_API_KEY"
        key_name = provider+suffix
        key = os.getenv(key_name)
        return key

    def run(self, prompt: str, provider: str, model: str, temperature: float = 0.5) -> str:
        func = self.provider_map[provider]

        out = func(prompt=prompt, model=model, temperature=temperature)

        return out
    
    def openai(self, prompt:str, model:str='gpt-3.5', temperature: float=0.5) -> str:
        llm = ChatOpenAI(openai_api_key=self.api_key, model=model, temperature=temperature)

        messages = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant."),
        ("user", "{input}")])

        chain = messages | llm | StrOutputParser()
        out = chain.invoke({"input": prompt})

        return out
    
    def ollama(self, prompt: str, model: str='phi3', temperature: float=0.5) -> str:
        # models: phi3 (3.8B), llama3 (7B)
        # TODO: warn that temperature is not used, or make it used
        # Need to install ollama on your machine first and pull models
        response = ollama.chat(model=model, messages=[
        {
            'role': 'user',
            'content': prompt,
        },
        ])
        return response['message']['content']
    