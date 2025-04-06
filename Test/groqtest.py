import os

from groq import Groq

client = Groq(
    api_key=""
)

chat_completion = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "hi"
        }
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)