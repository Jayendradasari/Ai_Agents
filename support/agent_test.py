import os
from anthropic import Anthropic
from decouple import config


client = Anthropic(
    api_key=config("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

message = client.messages.create(
    max_tokens=1024,
    messages=[
        {
            "role": "user",
            "content": "Hello, Claude",
        }
    ],

    model=config("ANTHROPIC_MODEL"),
)

print(message.content)