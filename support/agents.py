from anthropic import Anthropic
from django.conf import settings
from .tools import get_order_details,get_refund_history,check_delivery_status
from .models import Conversation,Message,AgentLog
from django.shortcuts import get_object_or_404

client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

anthropic_model=settings.ANTHROPIC_MODEL

# SUPPORT SYSTEM PROMPT --> Tara's JOB DESCRIPTION 
SUPPORT_SYSTEM_PROMPT="""
You are Tara,a customer support agent at coolBreeze AC.
you help customers with issues related to their AC orders.

Your Responsibilities:
- always use your tools to gather facts before responding
- Check order details when customer mentions their order
- Check refund history before making any refund decisions
- Be empathetic but honest

Your personality:
- Friendly and professional
- patient even when customer is angry
- clear and concise in your replies
- Don't use emojies

Important rules:
- Always check order details first before responding
- Never approve or deny a refund yourself
- If refund decision is needed - tell customer you are checking with your team


"""

#SUPPORT TOOLS --> Tool Schemas, that ai agents will read
SUPPORT_TOOLS=[
    {
        "name":"get_order_details",
        "description":"Fetch complete order details including status,carrier,tracking number and days since order was placed.Use this when customer mentions their order or complains about delivery",
        "input_schema":{
          "type":"object",
          "properties":{
             "order_id":{
                "type":"integer",
                "description":"The order ID to look up"
            }
        },
        "required":["order_id"]

      }
    },

    {
        "name":"get_refund_details",
        "description":"Get complete refund history for a user.Use this before making any refund decisions",
        "input_schema":{
          "type":"object",
          "properties":{
             "user_id":{
                "type":"integer",
                "description":"The user ID to check refund history for"
            }
        },
        "required":["user_id"]

      }
    },

    {
        "name":"check_delivery_status",
        "description":"Check current delivery status using tracking number and carrier.Use this when customer complains about delayed or missing order",
        "input_schema":{
          "type":"object",
          "properties":{
              "tracking_number":{
                  "type":"string",
                  "description":"the shipment tracking number"
              },
             "carrier":{
                "type":"string",
                "description":"The carrier name for example ekart or delhivery"
            }
        },
        "required":["tracking_number", "carrier"]

      }
    },


]

# execute_tool()-->bridge between claude and python functions (tools)

def execute_tool(tool_name,tool_input): 

    if tool_name == "get_order_details":
        return get_order_details(tool_input["order_id"])
    
    elif tool_name == "get_refund_history":
        return get_refund_history(tool_input["user_id"])
    
    elif tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"],tool_input["carrier"])
    

def run_support_agent(user_message, conversation_id):
    conv = get_object_or_404(Conversation, id=conversation_id)

    conversation_messages=[]
    for msg in conv.messages.order_by("created_at"):
        conversation_messages.append({
            "role":msg.role,
            "content":msg.content
        })

    # send this conversation to LLM

    response = client.messages.create(
        model=anthropic_model,
        max_tokens=1024,
        system=SUPPORT_SYSTEM_PROMPT,
        messages=conversation_messages
    )    

    final_text = response.content[0].text

    return final_text

