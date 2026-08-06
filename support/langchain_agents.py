from django.conf import settings
from langchain_anthropic import ChatAnthropic

#initialize the agent with the API key from settings
llm = ChatAnthropic(model = settings.ANTHROPIC_MODEL, api_key=settings.ANTHROPIC_API_KEY)