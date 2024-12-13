from django.contrib import admin
from django.urls import path
from invoiceGenerator import views

urlpatterns = [
    path('user/',views.createUserView.as_view(), name='user'),
    path('generate/', views.GenerateInvoicesView.as_view(), name='invoice'),
       
]