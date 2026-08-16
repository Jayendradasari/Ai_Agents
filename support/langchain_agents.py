from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from .langchain_tools import get_order_details,get_refund_history,check_delivery_status,search_knowledge_base
from .agents import SUPPORT_SYSTEM_PROMPT
from langgraph.checkpoint.memory import InMemorySaver


#initialize the agent with the API key from settings
llm = ChatAnthropic(model = settings.ANTHROPIC_MODEL, api_key=settings.ANTHROPIC_API_KEY)

SUPPORT_TOOLS = [get_order_details,get_refund_history,check_delivery_status,search_knowledge_base]

checkpointer = InMemorySaver()

support_agent = create_agent(
    model=llm,
    tools=SUPPORT_TOOLS,
    system_prompt=SUPPORT_SYSTEM_PROMPT,
    checkpointer=checkpointer
)

def run_support_agent_langchain(user_message, conversation_id, order_id, user_id):
    
    config = {"configurable": {"thread_id": str(conversation_id)}}

    contextual_message = f"[Context: This conversation is about order #{order_id}, user_id: {user_id}] {user_message}"

    result = support_agent.invoke(
        {"messages": [{"role": "user", "content": contextual_message}]},
        config=config,
    )

    final_text = result["messages"][-1].content
    return final_text