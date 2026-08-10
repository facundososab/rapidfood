from django.db import models


class ClientModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = "client"
        managed = False  # Prisma es dueño de la tabla


class ClientAddressModel(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    client = models.ForeignKey(
        ClientModel, on_delete=models.CASCADE, db_column="client_id", related_name="addresses"
    )
    street = models.CharField(max_length=255)
    street_number = models.CharField(max_length=50)
    floor = models.CharField(max_length=20, null=True, blank=True)
    apartment = models.CharField(max_length=20, null=True, blank=True)
    city = models.CharField(max_length=100)
    province = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7)
    longitude = models.DecimalField(max_digits=10, decimal_places=7)
    delivery_instructions = models.TextField(null=True, blank=True)
    label = models.CharField(max_length=50, null=True, blank=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "client_address"
        managed = False  # Prisma es dueño de la tabla
