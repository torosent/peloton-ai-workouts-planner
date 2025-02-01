# Python
import os
from langchain_openai import AzureChatOpenAI

def get_llm(temperature=0.5):
    return AzureChatOpenAI(
        model="gpt-4o",
        azure_deployment="gpt-4o",
        openai_api_version="2024-08-01-preview",
        temperature=temperature,
        max_retries=5
    )