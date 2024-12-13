from .models import client, invoice, Item
from rest_framework import serializers
from django.contrib.auth.models import User


class UserSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields= ('username','email', 'password')
        write_only = ('password')
    

class InvoiceItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ('description', 'quantity', 'unit_price', 'total_price')

class clientSerializer(serializers.ModelSerializer):
    class Meta:
        model = client
        fields = ('name', 'email', 'address', 'city', 'state', 'zip_code')
        
class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    client = clientSerializer()

    class Meta:
        model = invoice
        fields = ('client','invoice_number', 'date', 'total_amount', 'createdAt', 'status', 'items')

