from anthropic import Anthropic
from django.conf import settings
from .tools import get_order_details,get_refund_history,check_delivery_status,get_customer_risk_profile
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
# MANAGER SYSTEM PROMPT --> Involvement of manager
MANAGER_SYSTEM_PROMPT="""
You are a senior support manager at CoolBreeze AC.
A support agent has escalated a customer case to you for a refund decision.

Your responsibilities:
- Review the case summary carefully
- Consider the customer's refund history
- make a fair and final refund decision
- Give a clear reason for your decision

Your decision options:
- Aprrove refund - if the case is genuine and within policy
- Deny refund - if the case is suspicious or outside policy
- Escalate to risk team - if you suspect fraud

Important Rules:
- Be fair but firm
- Base decision on facts - not emotions
- Always give a specific reason for your decision
- keep your response concise and professional
"""

RISK_SYSTEM_PROMPT="""
You are a fraud risk analyst at coolBreeze AC.
A support manager has sent you a customer profile for risk assessment.

Your job:
- Analyse the customer's order and refund patterns
- Identify suspicious behavior
- Return a clear risk verdict

Risk levels:
- LOW - genuine customer, normal behavior
- MEDIUM - some suspicious signals,proceed with caution
- HIGH - clear fraud pattern, recommend denial


Your response format:
- Risk Level: LOW / MEDIUM / HIGH
- Key Signals: what you found suspicious or genuine
- Recommendation: what manager should do

Important:
- Be objective — base verdict on data only
- One bad refund does not make someone fraudulent
- Look for patterns — not isolated incidents

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
    {
        "name":"escalate_to_manager",
        "description":"escalate the case to manager for refund decision.Use this when customer requests a refund or compensation. Prepare a detailed case summary including order details, refund history and customer complaint before escalating ",
        "input_schema":{
          "type":"object",
          "properties":{
             "order_id":{
                "type":"string",
                "description":"Complete case summary including order details, refund history and customer complaint"
            }
        },
        "required":["case_summary"]

      }
    }


]

MANAGER_TOOLS = [
    {
        "name": "assess_fraud_risk",
        "description": "Consult the risk agent to assess fraud risk for a customer. Use this when refund request looks suspicious or customer has multiple refund requests. Pass the user_id to get a risk verdict.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The user ID to assess fraud risk for"
                }
            },
            "required": ["user_id"]
        }
    }
]


RISK_TOOLS = [
    {
        "name": "get_customer_risk_profile",
        "description": "Get complete risk profile for a customer including order history, refund patterns and ratio. Use this to assess fraud risk.",
        "input_schema": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "integer",
                    "description": "The user ID to assess risk for"
                }
            },
            "required": ["user_id"]
        }
    }
]


# execute_tool()-->bridge between claude and python functions (tools)

def execute_tool(tool_name,tool_input): 

    if tool_name == "get_order_details":
        return get_order_details(tool_input["order_id"])
    
    if tool_name == "get_refund_history":
        return get_refund_history(tool_input["user_id"])
    
    if tool_name == "check_delivery_status":
        return check_delivery_status(tool_input["tracking_number"],tool_input["carrier"])
    if tool_name == "escalate_to_manager":
        case_summary = tool_input["case_summary"]
        decision = run_manager_agent(case_summary)
        return decision
    if tool_name == "assess_fraud_risk":
        user_id = tool_input['user_id']
        verdict = run_risk_agent(user_id)
        return verdict
    
    if tool_name == "get_customer_risk_profile":
        return get_customer_risk_profile(tool_input['user_id'])
    
    
    

def run_support_agent(user_message, conversation_id, order_id, user_id):
    conv = get_object_or_404(Conversation, id=conversation_id)

    conversation_messages=[]
    for msg in conv.messages.order_by("created_at"):
        conversation_messages.append({
            "role":msg.role,
            "content":msg.content
        })

    # send this conversation to LLM
    while True:

      response = client.messages.create(
         model=anthropic_model,
         max_tokens=1024,
         system=SUPPORT_SYSTEM_PROMPT + f"\n\nContext: This conversation is about order #{order_id}, user_id: {user_id}",
         tools=SUPPORT_TOOLS,
         messages=conversation_messages
      )
      print('stop_reason==>', response.stop_reason)
      print('content==>', response.content)

      if response.stop_reason == 'tool_use':
          tool_result=[]
          for block in response.content:
              if block.type == 'tool_use':
                  print("tool_call==>",block.name)
                  print("tool_input==>",block.input)

                  # execute the tool
                  result = execute_tool(block.name, block.input)
                  print('tool_result==>', result)

                  tool_result.append({
                      "type":"tool_result",
                      "tool_use_id":block.id,
                      "content":str(result)
                  })

          conversation_messages.append({
              "role":"assistant",
              "content":response.content
          })

          conversation_messages.append({
              "role":"user",
              "content":tool_result
          })


      else:
        return response.content[0].text
      

def run_manager_agent(case_summary):
    manager_messages = [
        {"role":"user", "content":case_summary} #user is task giver ,so here user is tara agent
    ]    

    while True:
        response = client.messages.create(
            model = anthropic_model,
            max_tokens=1024,
            system = MANAGER_SYSTEM_PROMPT,
            tools = MANAGER_TOOLS,
            messages = manager_messages
        )  

        if response.stop_reason == 'tool_use':
          tool_result=[]
          for block in response.content:
              if block.type == 'tool_use':
                  
                # execute the tool
                  result = execute_tool(block.name, block.input)
                  tool_result.append({
                      "type":"tool_result",
                      "tool_use_id":block.id,
                      "content":str(result)
                  })

          manager_messages.append({
              "role":"assistant",
              "content":response.content
          })

          manager_messages.append({
              "role":"user",
              "content":tool_result
          })


        else:
          return response.content[0].text

def run_risk_agent(user_id):
     risk_messages = [
        {"role": "user", "content": f"Please assess the fraud risk for user ID {user_id}. User your tool to get their profile and return a verdict."}
    ]
     
     while True:
         response = client.messages.create(
             model= anthropic_model,
             max_tokens=1024,
             system=RISK_SYSTEM_PROMPT,
             tools=RISK_TOOLS,
             messages=risk_messages
         )

         if response.stop_reason == 'tool_use':
                tool_result=[]
                for block in response.content:
                  if block.type == 'tool_use':
                  
                # execute the tool
                    result = execute_tool(block.name, block.input)
                    tool_result.append({
                       "type":"tool_result",
                       "tool_use_id":block.id,
                       "content":str(result)
                    })

                risk_messages.append({
                "role":"assistant",
                "content":response.content
                })

                risk_messages.append({
                "role":"user",
                "content":tool_result
                })
    
        
         else:
           return response.content[0].text

