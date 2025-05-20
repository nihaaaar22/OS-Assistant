#simple interface for now. will integrate will other models to make orchestration simpler.For 
# faster tasks you can do with lighter models
from dotenv import load_dotenv
import os
from groq import Groq
from openai import OpenAI
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Src.Utils.ter_interface import TerminalInterface


# Load environment variables from .env file
load_dotenv()

# Accessing an environment variable

from mistralai import Mistral

def get_model_name():
    config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
    with open(config_path, "r") as config_file:
        config = json.load(config_file)
        return config.get("model_name", "mistral-large-latest")

class MistralModel:
    def __init__(self):
        api_key = os.environ.get('MISTRAL_API_KEY')
        self.client = Mistral(api_key=api_key)
        self.terminal = TerminalInterface()
        self.model_name = get_model_name()

    def chat(self, messages):
        
        response = ""
        stream_response = self.client.chat.stream(
            model=self.model_name,
            messages=messages,
            temperature=0.2,
        )

        for chunk in stream_response:
            content = chunk.data.choices[0].delta.content
            if content:
                self.terminal.process_markdown_chunk(content)
                response += content

        self.terminal.flush_markdown()
        return response

        
class Groqinference:
    def __init__(self):
        api_key = os.environ.get('GROQ_API_KEY')
        self.client = Groq(
            api_key=api_key,
        )
        self.model_name = get_model_name()

    def chat(self, messages):
        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model=self.model_name,
        )
        return chat_completion

class OpenAi:
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY')
        self.client = OpenAI(api_key=api_key)
        self.terminal = TerminalInterface()
        self.model_name = get_model_name()

    def chat(self, messages):
        response = ""
        stream = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            stream=True
        )

        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                self.terminal.process_markdown_chunk(content)
                response += content

        self.terminal.flush_markdown()
        return response

# for groq 
# print(chat_completion.choices[0].message.content)

        # # Iterate over the stream and store chunks
        # for chunk in stream_response:
        #     content = chunk.data.choices[0].delta.content
        #     print(content, end="")  # Print in real-time
        #     full_response += content  # Append to the full response

        # # Now `full_response` contains the complete response
        # # Perform operations on the complete response
        # print("\n\nFull response captured:")
