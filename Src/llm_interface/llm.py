#simple interface for now. will integrate will other models to make orchestration simpler.For 
# faster tasks you can do with lighter models
from dotenv import load_dotenv
import os
# from groq import Groq # Commented out
# from openai import OpenAI # Commented out
import sys
import json
import litellm # Added import for litellm

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from Utils.ter_interface import TerminalInterface


# Load environment variables from .env file
load_dotenv()

# Accessing an environment variable

# from mistralai import Mistral # Commented out

# def get_model_name(): # Commented out as logic moved to LiteLLMInterface.load_config()
#     config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
#     with open(config_path, "r") as config_file:
#         config = json.load(config_file)
#         return config.get("model_name", "mistral-large-latest")

class LiteLLMInterface:
    def __init__(self):
        self.terminal = TerminalInterface()
        self.model_name = self.load_config()

    def load_config(self):
        config_path = os.path.join(os.path.dirname(__file__), '../../config.json')
        try:
            with open(config_path, "r") as config_file:
                config = json.load(config_file)
                return config.get("model_name", "gpt-3.5-turbo") # Default to gpt-3.5-turbo
        except FileNotFoundError:
            print(f"Warning: Config file not found at {config_path}. Defaulting model to gpt-3.5-turbo.")
            return "gpt-3.5-turbo"
        except json.JSONDecodeError:
            print(f"Warning: Error decoding JSON from {config_path}. Defaulting model to gpt-3.5-turbo.")
            return "gpt-3.5-turbo"

    def chat(self, messages):
        response_content = ""
        try:
            stream_response = litellm.completion(
                model=self.model_name,
                messages=messages,
                stream=True,
                temperature=0.2
            )

            for chunk in stream_response:
                content = chunk.choices[0].delta.content
                if content:
                    self.terminal.process_markdown_chunk(content)
                    response_content += content
            
            self.terminal.flush_markdown()
            return response_content
        except Exception as e:
            # litellm maps exceptions to OpenAI exceptions.
            # The executor should catch these and handle them.
            
            self.terminal.flush_markdown() # Ensure terminal is flushed even on error
            raise 


# class MistralModel:
#     def __init__(self):
#         api_key = os.environ.get('MISTRAL_API_KEY')
#         self.client = Mistral(api_key=api_key)
#         self.terminal = TerminalInterface()
#         self.model_name = get_model_name()

#     def chat(self, messages):
        
#         response = ""
#         stream_response = self.client.chat.stream(
#             model=self.model_name,
#             messages=messages,
#             temperature=0.2,
#         )

#         for chunk in stream_response:
#             content = chunk.data.choices[0].delta.content
#             if content:
#                 self.terminal.process_markdown_chunk(content)
#                 response += content

#         self.terminal.flush_markdown()
#         return response

        
# class Groqinference:
#     def __init__(self):
#         api_key = os.environ.get('GROQ_API_KEY')
#         self.client = Groq(
#             api_key=api_key,
#         )
#         self.model_name = get_model_name()

#     def chat(self, messages):
#         chat_completion = self.client.chat.completions.create(
#             messages=messages,
#             model=self.model_name,
#         )
#         return chat_completion

# class OpenAi:
#     def __init__(self):
#         api_key = os.environ.get('OPENAI_API_KEY')
#         self.client = OpenAI(api_key=api_key)
#         self.terminal = TerminalInterface()
#         self.model_name = get_model_name()

#     def chat(self, messages):
#         response = ""
#         stream = self.client.chat.completions.create(
#             model=self.model_name,
#             messages=messages,
#             stream=True
#         )

#         for chunk in stream:
#             content = chunk.choices[0].delta.content
#             if content is not None:
#                 self.terminal.process_markdown_chunk(content)
#                 response += content

#         self.terminal.flush_markdown()
#         return response

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
