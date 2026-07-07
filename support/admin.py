from django.contrib import admin
from .models import Message,AgentLog,Conversation


admin.site.register(Message)
admin.site.register(AgentLog)   
admin.site.register(Conversation)


