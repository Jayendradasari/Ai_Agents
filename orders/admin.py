from django.contrib import admin

from orders.models import Product, Order, RefundRequest

# Register your models here.
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'in_stock', 'category')
class OrderAdmin(admin.ModelAdmin):
    list_display = ('user', 'product_name', 'amount', 'status', 'carrier', 'tracking_number')
class refundRequestAdmin(admin.ModelAdmin):
    list_display = ('order', 'user', 'reason', 'status', 'created_at')

admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(RefundRequest, refundRequestAdmin)
    
