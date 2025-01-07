#simple interface for now. will integrate will other models to make orchestration simpler.For 
# faster tasks you can do with lighter models
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Accessing an environment variable
api_key = os.environ.get('MISTRAL_API_KEY')
from mistralai import Mistral


model = "mistral-large-latest"

class MistralModel:
    def __init__(self):
        self.client = Mistral(api_key=api_key)

    def chat(self,messages):

        stream_response = self.client.chat.stream(
            model = model,
            messages=messages
        )

        return stream_response


        # # Iterate over the stream and store chunks
        # for chunk in stream_response:
        #     content = chunk.data.choices[0].delta.content
        #     print(content, end="")  # Print in real-time
        #     full_response += content  # Append to the full response

        # # Now `full_response` contains the complete response
        # # Perform operations on the complete response
        # print("\n\nFull response captured:")
