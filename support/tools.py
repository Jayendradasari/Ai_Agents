from datetime import timezone
from .tracking_data import DELIVERY_DATA
from django.shortcuts import render
from orders.models import Order,RefundRequest
from datetime import timedelta
from .rag import search_knowledge_base as rag_search

def get_order_details(order_id):
    # here request param is not used because agent calls this function to get order details for a specific order_id
    try:
        order = Order.objects.get(id=order_id)
        return {
            'order_id': order.id,
            'product_name': order.product_name,
            'amount': str(order.amount),
            'status': order.status,
            'carrier': order.carrier,
            'tracking_number': order.tracking_number,
            'delivery_address': order.delivery,
            'ordered_on':order.created_at.strftime("%d %b %Y"), # 5 july 2026
            'days_since_order':(timezone.now() - order.created_at).days,  # Calculate days since order
        }
    except Order.DoesNotExist:
        return {"error": f"order #{order_id} not found."}
    
def get_refund_history(user_id):
    # here request param is not used because agent calls this function to get refund history for a specific user_id
    refunds = RefundRequest.objects.filter(user__id=user_id).order_by('-created_at')  # Get all refund requests for the user, ordered by most recent
    
    history = []
    for refund in refunds:
        history.append({
            'order_id': refund.order.id,
            'product':refund.order.product_name,
            'reason': refund.reason,
            'status': refund.status,
            'requested_on': refund.created_at.strftime("%d %b %Y"),  # Format date as "5 July 2026"
            # 'days_since_request': (timezone.now() - refund.created_at).days,  # Calculate days since request
        })
    return{
        "total_refund_requests":len(history),
        "history":history
    }    
def check_delivery_status(tracking_number,carrier):
    default_response={
        "status": "unknown",
        "last_location": "Tracking info unavailable",
        "last_update": "N/A",
        "estimated_delivery": "contact carrier directly",
        "delay_reason": "No updates from carrier",
       
    }
    result= DELIVERY_DATA.get(tracking_number,default_response)
    result["tracking_number"]= tracking_number
    result["carrier"]= carrier
    return result
     
def get_customer_risk_profile(user_id):
    # print('user_id==>', user_id)
    refunds = RefundRequest.objects.filter(user_id=user_id)
    orders = Order.objects.filter(user_id=user_id)

    # recent 90 days refund requests
    recent_refunds = refunds.filter(created_at__gte=timezone.now() - timedelta(days=90)).count()

    denied = refunds.filter(status="denied").count()
    approved = refunds.filter(status="approved").count()
    pending = refunds.filter(status="pending").count()

    total_orders = orders.count()
    total_refunds = refunds.count()

    if total_orders > 0:
        refund_to_order_ratio = round(total_refunds / total_orders, 2) # order = 8, refund = 12
    else:
        refund_to_order_ratio = 0
    
    return {
        "user_id": user_id,
        "total_orders": total_orders,
        "total_refund_requests": total_refunds,
        "refunds_last_90_days": recent_refunds,
        "denied_refunds": denied,
        "approved_refunds": approved,
        "pending_refunds": pending,
        "refund_to_order_ratio": refund_to_order_ratio
    }

#wrapper function
def search_knowledge_base(query):
    # Call the RAG module to search the knowledge base
    result = rag_search(query)
    return {"result": result}
