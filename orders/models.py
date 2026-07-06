from django.db import models
from django.contrib.auth.models import User

class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    in_stock = models.PositiveIntegerField(default=True)
    category = models.CharField(max_length=100) 

    def __str__(self):
        return self.name
    
class Order(models.Model):
    status_choices = [
        ('pending', 'Pending'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)    
    product=models.ForeignKey(Product, on_delete=models.SET_NULL, null=True,related_name='orders')
    product_name=models.CharField(max_length=255)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=status_choices, default='pending')
    carrier = models.CharField(max_length=100, blank=True, null=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    delivery = models.TextField(blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True,null=True)

    def __str__(self):
        return f"Order {self.id} - {self.product_name} - {self.status}"
    

class RefundRequest(models.Model):
        order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='refund_requests')
        user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='refund_requests')
        reason = models.TextField()
        status_choices = [
            ('pending', 'Pending'),
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ]
        status = models.CharField(max_length=20, choices=status_choices, default='pending')
        created_at = models.DateTimeField()
        updated_at = models.DateTimeField(auto_now=True,null=True)

        def __str__(self):
            return f"Refund Request for Order #{self.order.id} - {self.status}"