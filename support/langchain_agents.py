from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_agent
from .langchain_tools import get_order_details,get_refund_history,check_delivery_status,search_knowledge_base
from .agents import SUPPORT_SYSTEM_PROMPT
from langgraph.checkpoint.memory import InMemorySaver
from .models import Conversation,Message,AgentLog
from langchain.agents.middleware import wrap_tool_call



#initialize the agent with the API key from settings
llm = ChatAnthropic(model = settings.ANTHROPIC_MODEL, api_key=settings.ANTHROPIC_API_KEY)

SUPPORT_TOOLS = [get_order_details,get_refund_history,check_delivery_status,search_knowledge_base]

checkpointer = InMemorySaver()



def run_support_agent_langchain(user_message, conversation_id, order_id, user_id):
    conv = Conversation.objects.get(id=conversation_id)
    config = {"configurable": {"thread_id": str(conversation_id)}}

    contextual_message = f"[Context: This conversation is about order #{order_id}, user_id: {user_id}] {user_message}"

    #using middleware to log tool calls
    @wrap_tool_call
    def log_tool_calls_middleware(request, handler):
        #before tool execution
        tool_name = request.tool_call["name"]
        tool_args = request.tool_call["args"]
        # log tool call
        AgentLog.objects.create(
            conversation=conv,
            event_type="tool_call",
            message=f"Calling tool: {tool_name}, Args: {tool_args}"
        )

        result = handler(request)  # this is where the tools are being executed

        #after tool execution
        AgentLog.objects.create(conversation = conv, event_type="tool_result", message=f" {tool_name} returned: {str(result.content)[:200]}" )
        return result

    support_agent = create_agent(
          model=llm,
          tools=SUPPORT_TOOLS,
          system_prompt=SUPPORT_SYSTEM_PROMPT,
          checkpointer=checkpointer,
          middleware=[log_tool_calls_middleware]
        )  
    



    result = support_agent.invoke(
        {"messages": [{"role": "user", "content": contextual_message}]},
        config=config,
    )

    final_reply = result["messages"][-1].content

    # Store the final reply to AgentLog
    AgentLog.objects.create(
        conversation=conv,
        event_type="final",
        message=final_reply
    )
    return final_reply