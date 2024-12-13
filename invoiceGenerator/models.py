from django.db import models

# Create your models here.

class client(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    address = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=100)

class invoice(models.Model):
    INVOICE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
    ]
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(client, on_delete=models.CASCADE)
    invoice_number = models.CharField(max_length=50, unique=True)
    date = models.DateField()
    createdAt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=INVOICE_STATUS_CHOICES, default='draft')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    items = models.TextField(blank=True, null=True)
    


class Item(models.Model):
    """Stores individual line items for an invoice"""
    id = models.AutoField(primary_key=True)
    client = models.ForeignKey(client, related_name='client', on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quantity = models.IntegerField()
    def save(self, *args, **kwargs):
        if not self.total_amount:
            self.total_amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def clean(self):
        self.total_amount = self.quantity * self.unit_price


class InvoiceNumber(models.Model):
    id = models.AutoField(primary_key=True)
    prefix = models.CharField(max_length=10)
    number = models.IntegerField()

    