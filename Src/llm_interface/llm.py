#simple interface for now. will integrate will other models to make orchestration simpler.For 
# faster tasks you can do with lighter models
from dotenv import load_dotenv
import os
from groq import Groq
from openai import OpenAI


# Load environment variables from .env file
load_dotenv()

# Accessing an environment variable
api_key = os.environ.get('MISTRAL_API_KEY')
from mistralai import Mistral


model = "qwen-2.5-coder-32b"

class MistralModel:
    def __init__(self):
        self.client = Mistral(api_key=api_key)

    def chat(self,messages):

        stream_response = self.client.chat.stream(
            model = model,
            messages=messages
        )

        return stream_response

        
class Groqinference:
    def __init__(self):
        self.client = Groq(
            api_key=os.environ.get("GROQ_API_KEY"),
        )

    def chat(self,messages):

        chat_completion = self.client.chat.completions.create(
            messages=messages,
            model="meta-llama/llama-4-maverick-17b-128e-instruct",
        )

        return chat_completion

class OpenAi:
    def __init__(self):
        self.client = OpenAI()

    def chat(self,messages): 

        response = self.client.chat.completions.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages
        )

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
