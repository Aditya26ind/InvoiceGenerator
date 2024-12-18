import ast
from datetime import datetime
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth.models import User
from .models import InvoiceNumber, client , invoice , Item

#report imports

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from decimal import Decimal
from django.conf import settings
import os
from datetime import datetime
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph



# Create your views here.

class createUserView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        # Suggestion: Add more robust validation
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not all([username, email, password]):
            return Response({'message': 'Missing required fields'}, status=400)
        
        try:
            if User.objects.filter(email=email).exists():
                return Response({'message': 'Email already exists'}, status=400)
            
            user = User.objects.create_user(
                username=username, 
                email=email, 
                password=password
            )
            return Response({
                'message': 'User created', 
                'user_id': user.id
            }, status=201)
        except Exception as e:
            return Response({'message': str(e)}, status=400)

class GenerateInvoicesView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    def post(self, request, *args, **kwargs):
        
        user=request.user
        name = request.user.username  
        email = request.user.email    
        
        # Use request.data for DRF, not request.POST
        address=request.data.get('address', '')
        city=request.data.get('city', '')
        state=request.data.get('state', '')
        zip_code=request.data.get('zip_code', '')
        descriptions = request.data.get('description',[]) # should be in array ['abc','def]
        quantities = request.data.get('quantity',[]) #['2','3]
        unit_prices = request.data.get('unit_price',[]) #['2','3']
        
        if not descriptions or not quantities or not unit_prices:
            return Response({'message': 'Missing required fields'}, status=400)
        try:
            # Create client
            
            client_obj = client.objects.create(
                name=name,
                email=email,
                address=address,
                city=city,
                state=state,
                zip_code=zip_code
            )
            
            items=[]
            itemsOnlyTopass = []
            for item in range(len(descriptions)):
                itemObjs = Item(
                    client=client_obj,
                    description=descriptions[item], 
                    unit_price=unit_prices[item],
                    quantity=quantities[item]
                )
                itemsOnlyTopass.append([descriptions[item],unit_prices[item],quantities[item]])
                items.append(itemObjs)
            allItems=Item.objects.bulk_create(items)
            
            
            
            
            total=0
            for item in allItems:
                total+=item.quantity*item.unit_price
                
            invoice_number=self.generate_invoice_number('INV')
            invoice_obj = invoice.objects.create(
                client=client_obj,
                invoice_number=invoice_number,
                date=datetime.now(),
                total_amount=total,
                createdAt=datetime.now(),
                status='draft',
                items=str(items)
                
            )
            
            path=self.generateInvoicePDF(user,invoice_obj,itemsOnlyTopass)
            file_url = request.build_absolute_uri(settings.MEDIA_URL + path)
            print(file_url)
            print("BASE_DIR",settings.BASE_DIR)
            
            return Response({'message': 'Invoice created successfully', 'invoice_number': invoice_number,'path':file_url}, status=201)
        
        except Exception as e:
            return Response({'message': str(e)}, status=400)
            
    def generate_invoice_number(self, prefix):
        # Ensure prefix is a string
        prefix = str(prefix)
        
        # Get the latest invoice number for the given prefix
        last_invoice = InvoiceNumber.objects.filter(prefix=prefix).order_by('-id').first()

        if last_invoice:
            next_number = last_invoice.number + 1
        else:
            next_number = 1

        # Create a new InvoiceNumber record
        InvoiceNumber.objects.create(prefix=prefix, number=next_number)

        return f"{prefix}-{next_number:04d}"
    
    def generateInvoicePDF(self, user, invoice_obj, items):

        # Prepare invoice data
        processed_items = []
        for item in items:
            processed_items.append({
                'description': str(item[0]) if hasattr(item, '__getitem__') else str(item.description),
                'quantity': int(item[1]) if hasattr(item, '__getitem__') else int(item.quantity),
                'unit_price': float(item[2]) if hasattr(item, '__getitem__') else float(item.unit_price)
            })
        
        data = {
            'invoice_number': invoice_obj.invoice_number,
            'client_name': invoice_obj.client.name,
            'client_email': invoice_obj.client.email,
            'client_address': invoice_obj.client.address,
            'invoice_date': invoice_obj.date,
            'items': processed_items,
            'total_amount': invoice_obj.total_amount
        }
        
        # Ensure invoice directory exists
        print(settings.MEDIA_ROOT)
        invoice_dir = os.path.join(settings.MEDIA_ROOT, 'invoices')
        os.makedirs(invoice_dir, exist_ok=True)
        # Generate unique filename
        filename = f"invoice_{data['invoice_number']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        filepath = os.path.join(invoice_dir, filename)
        # relative_path = os.path.relpath(filepath, settings.MEDIA_ROOT)
        
        # Create PDF document
        
        doc = SimpleDocTemplate(filepath, pagesize=letter)
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Company Header
        company_details = [
            [Paragraph('Your Company Name', styles['Heading3'])],
            [Paragraph('123 Business Street', styles['Normal'])],
            [Paragraph('City, State ZIP', styles['Normal'])],
            [Paragraph('Contact: (555) 123-4567', styles['Normal'])],
            [Paragraph('Email: contact@yourcompany.com', styles['Normal'])]
        ]
        company_table = Table(company_details, colWidths=[4*inch])
        company_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
        ]))
        elements.append(company_table)
        
        # Invoice Header
        invoice_header = [
            [Paragraph('INVOICE', styles['Title'])],
            [Paragraph(f'Invoice Number: {data["invoice_number"]}', styles['Normal'])],
            [Paragraph(f'Date: {data["invoice_date"].strftime("%B %d, %Y")}', styles['Normal'])]
        ]
        invoice_header_table = Table(invoice_header, colWidths=[4*inch])
        invoice_header_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (0,0), 16),
        ]))
        elements.append(invoice_header_table)
        
        # Client Details
        
        client_details = [
            [Paragraph('Bill To:', styles['Heading4'])],
            [Paragraph(data['client_name'], styles['Normal'])],
            [Paragraph(data['client_email'], styles['Normal'])],
            [Paragraph(data['client_address'], styles['Normal'])]
        ]
        client_table = Table(client_details, colWidths=[4*inch])
        client_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
        ]))
        elements.append(client_table)
        
        # Invoice Items
        
        items_data = [
            [Paragraph('Description', styles['Heading4']), 
            Paragraph('Quantity', styles['Heading4']), 
            Paragraph('Unit Price', styles['Heading4']), 
            Paragraph('Total', styles['Heading4'])]
        ]
        
        
        for item in data['items']:
            items_data.append([
                Paragraph(item['description'], styles['Normal']), 
                Paragraph(str(item['quantity']), styles['Normal']), 
                Paragraph(f"${item['unit_price']:.2f}", styles['Normal']), 
                Paragraph(f"${item['quantity'] * item['unit_price']:.2f}", styles['Normal'])
            ])
        
        # Add total row
        items_data.append([
            Paragraph('', styles['Normal']), 
            Paragraph('', styles['Normal']), 
            Paragraph('Total:', styles['Heading4']), 
            Paragraph(f"${data['total_amount']:.2f}", styles['Heading4'])
        ])
        
        items_table = Table(items_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,0), 12),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-2), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        elements.append(items_table)
        
        # Payment Instructions
        payment_details = [
            [Paragraph('Payment Instructions:', styles['Heading4'])],
            [Paragraph('Please make payment within 30 days', styles['Normal'])],
            [Paragraph('Bank: Your Bank Name', styles['Normal'])],
            [Paragraph('Account Number: XXXXXXXX', styles['Normal'])],
            [Paragraph('Routing Number: YYYYYYY', styles['Normal'])]
        ]
        payment_table = Table(payment_details, colWidths=[4*inch])
        payment_table.setStyle(TableStyle([
            ('FONTNAME', (0,0), (0,0), 'Helvetica-Bold'),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        elements.append(payment_table)
        
        # Build PDF
        try:
            doc.build(elements)
            relative_path = os.path.relpath(filepath, settings.MEDIA_ROOT)
            return relative_path
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return None