from django.db import models

class OrderModel(models.Model):
    """
    Django ORM mapping for Prisma's 'order' table.
    Managed by Prisma (managed = False).
    """
    id = models.UUIDField(primary_key=True)
    estimated_time = models.IntegerField(null=True, blank=True)
    delivery_type = models.CharField(max_length=50, null=True, blank=True)
    payment_type = models.CharField(max_length=50, null=True, blank=True)
    status = models.CharField(max_length=50)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    client_id = models.UUIDField(null=True, blank=True)
    address_id = models.UUIDField(null=True, blank=True)
    conversation_id = models.UUIDField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'order'


class OrderLineModel(models.Model):
    id = models.UUIDField(primary_key=True)
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="lines")
    product_id = models.UUIDField()
    amount = models.IntegerField()  # mapped to quantity in Domain
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_id = models.UUIDField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'order_line'


class AppliedCouponModel(models.Model):
    id = models.UUIDField(primary_key=True)
    order = models.ForeignKey(OrderModel, on_delete=models.CASCADE, related_name="applied_coupons")
    coupon_id = models.UUIDField(null=True, blank=True)
    coupon_code = models.CharField(max_length=100)
    type = models.CharField(max_length=50)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    available_uses = models.IntegerField()
    date_of_expiration = models.DateTimeField(null=True, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'applied_coupon'
