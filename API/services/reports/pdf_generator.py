"""
PDF Report Generator Service.
Generates PDF reports and receipts using ReportLab.
"""

import io
from datetime import datetime, date
from decimal import Decimal
from typing import List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, 
    Spacer, PageBreak, Image
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from sqlalchemy.orm import Session
from sqlalchemy import func
from utils.helpers import get_tashkent_datetime_str, get_tashkent_date_str

from database.models import (
    Sale, SaleItem, Product, Customer, Stock, 
    StockMovement, Payment, Warehouse
)


class PDFReportGenerator:
    """PDF report generator with professional formatting."""
    
    # Colors
    PRIMARY_COLOR = colors.HexColor('#4472C4')
    HEADER_BG = colors.HexColor('#4472C4')
    ALT_ROW_BG = colors.HexColor('#F2F2F2')
    
    def __init__(self, db: Session):
        self.db = db
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            textColor=self.PRIMARY_COLOR,
            spaceAfter=20,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.grey,
            spaceAfter=15,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=self.PRIMARY_COLOR,
            spaceBefore=15,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyName',
            parent=self.styles['Normal'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=5
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReceiptText',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_CENTER
        ))
    
    def _create_table_style(self, has_header: bool = True) -> TableStyle:
        """Create standard table style."""
        style_commands = [
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]
        
        if has_header:
            style_commands.extend([
                ('BACKGROUND', (0, 0), (-1, 0), self.HEADER_BG),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, self.ALT_ROW_BG]),
            ])
        
        return TableStyle(style_commands)
    
    def generate_receipt(self, sale_id: int) -> bytes:
        """
        Generate sale receipt (chek) PDF.
        Thermal printer compatible (80mm width).
        """
        sale = self.db.query(Sale).filter(Sale.id == sale_id).first()
        if not sale:
            raise ValueError("Sotuv topilmadi")
        
        buffer = io.BytesIO()
        
        # 80mm receipt width
        page_width = 80 * mm
        page_height = 297 * mm
        
        doc = SimpleDocTemplate(
            buffer,
            pagesize=(page_width, page_height),
            leftMargin=5*mm,
            rightMargin=5*mm,
            topMargin=10*mm,
            bottomMargin=10*mm
        )
        
        elements = []
        
        # Company header
        elements.append(Paragraph("<b>METALL BASA</b>", self.styles['CompanyName']))
        elements.append(Paragraph("Qurilish mollari do'koni", self.styles['ReceiptText']))
        elements.append(Paragraph("Tel: +998 90 123 45 67", self.styles['ReceiptText']))
        elements.append(Spacer(1, 5*mm))
        
        # Separator
        elements.append(Paragraph("=" * 32, self.styles['ReceiptText']))
        elements.append(Spacer(1, 3*mm))
        
        # Sale info
        info_style = ParagraphStyle('info', parent=self.styles['Normal'], fontSize=9, alignment=TA_LEFT)
        elements.append(Paragraph(f"<b>Chek:</b> {sale.sale_number}", info_style))
        elements.append(Paragraph(f"<b>Sana:</b> {sale.created_at.strftime('%d.%m.%Y %H:%M')}", info_style))
        elements.append(Paragraph(f"<b>Sotuvchi:</b> {sale.seller.first_name} {sale.seller.last_name}", info_style))
        if sale.customer:
            elements.append(Paragraph(f"<b>Mijoz:</b> {sale.customer.name}", info_style))
        elements.append(Spacer(1, 3*mm))
        
        # Separator
        elements.append(Paragraph("-" * 32, self.styles['ReceiptText']))
        elements.append(Spacer(1, 2*mm))
        
        # Items
        items_data = []
        for item in sale.items:
            name = item.product.name
            if len(name) > 20:
                name = name[:18] + '..'
            qty_price = f"{item.quantity} x {item.unit_price:,.0f}"
            total = f"{item.total_price:,.0f}"
            items_data.append([name, ''])
            items_data.append([qty_price, total])
        
        if items_data:
            items_table = Table(items_data, colWidths=[45*mm, 20*mm])
            items_table.setStyle(TableStyle([
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(items_table)
        
        elements.append(Spacer(1, 2*mm))
        elements.append(Paragraph("-" * 32, self.styles['ReceiptText']))
        elements.append(Spacer(1, 2*mm))
        
        # Totals
        totals_style = ParagraphStyle('totals', parent=self.styles['Normal'], fontSize=9, alignment=TA_RIGHT)
        
        if sale.discount_amount > 0:
            elements.append(Paragraph(f"Summa: {sale.subtotal:,.0f} so'm", totals_style))
            elements.append(Paragraph(f"Chegirma ({sale.discount_percent:.1f}%): -{sale.discount_amount:,.0f} so'm", totals_style))
        
        total_style = ParagraphStyle('total', parent=self.styles['Normal'], fontSize=12, alignment=TA_RIGHT)
        elements.append(Paragraph(f"<b>JAMI: {sale.total_amount:,.0f} so'm</b>", total_style))
        elements.append(Spacer(1, 2*mm))
        
        elements.append(Paragraph(f"To'langan: {sale.paid_amount:,.0f} so'm", totals_style))
        
        if sale.debt_amount > 0:
            elements.append(Paragraph(f"<b>QARZ: {sale.debt_amount:,.0f} so'm</b>", totals_style))
        else:
            change = sale.paid_amount - sale.total_amount
            if change > 0:
                elements.append(Paragraph(f"Qaytim: {change:,.0f} so'm", totals_style))
        
        elements.append(Spacer(1, 5*mm))
        elements.append(Paragraph("=" * 32, self.styles['ReceiptText']))
        elements.append(Spacer(1, 3*mm))
        
        # Footer
        elements.append(Paragraph("Xaridingiz uchun rahmat!", self.styles['ReceiptText']))
        elements.append(Paragraph(get_tashkent_datetime_str(), self.styles['ReceiptText']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_sales_report(
        self,
        start_date: date,
        end_date: date,
        warehouse_id: int = None
    ) -> bytes:
        """Generate sales report PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # Title
        elements.append(Paragraph("SOTUVLAR HISOBOTI", self.styles['CustomTitle']))
        elements.append(Paragraph(
            f"Davr: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}",
            self.styles['CustomSubtitle']
        ))
        
        # Query sales
        query = self.db.query(Sale).filter(
            Sale.sale_date >= start_date,
            Sale.sale_date <= end_date,
            Sale.is_cancelled == False
        )
        if warehouse_id:
            query = query.filter(Sale.warehouse_id == warehouse_id)
        
        sales = query.order_by(Sale.sale_date).all()
        
        # Summary section
        elements.append(Paragraph("UMUMIY MA'LUMOTLAR", self.styles['SectionHeader']))
        
        total_amount = sum(s.total_amount for s in sales)
        total_paid = sum(s.paid_amount for s in sales)
        total_debt = sum(s.debt_amount for s in sales)
        total_discount = sum(s.discount_amount for s in sales)
        
        summary_data = [
            ["Ko'rsatkich", "Qiymat"],
            ["Sotuvlar soni", str(len(sales))],
            ["Jami summa", f"{total_amount:,.0f} so'm"],
            ["Chegirmalar", f"{total_discount:,.0f} so'm"],
            ["To'langan", f"{total_paid:,.0f} so'm"],
            ["Qarzga", f"{total_debt:,.0f} so'm"],
        ]
        
        summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
        summary_table.setStyle(self._create_table_style())
        elements.append(summary_table)
        elements.append(Spacer(1, 1*cm))
        
        # Sales list
        elements.append(Paragraph("SOTUVLAR RO'YXATI", self.styles['SectionHeader']))
        
        sales_data = [["№", "Sana", "Chek №", "Mijoz", "Summa", "Qarz"]]
        for i, sale in enumerate(sales[:100], 1):  # Limit for PDF
            customer_name = sale.customer.name if sale.customer else "-"
            if len(customer_name) > 20:
                customer_name = customer_name[:18] + ".."
            sales_data.append([
                str(i),
                sale.sale_date.strftime('%d.%m.%Y'),
                sale.sale_number,
                customer_name,
                f"{sale.total_amount:,.0f}",
                f"{sale.debt_amount:,.0f}" if sale.debt_amount > 0 else "-"
            ])
        
        sales_table = Table(sales_data, colWidths=[1*cm, 2.5*cm, 3*cm, 4.5*cm, 3*cm, 2.5*cm])
        sales_table.setStyle(self._create_table_style())
        elements.append(sales_table)
        
        if len(sales) > 100:
            elements.append(Paragraph(
                f"... va yana {len(sales) - 100} ta sotuv",
                self.styles['Normal']
            ))
        
        # Footer
        elements.append(Spacer(1, 1*cm))
        footer_style = ParagraphStyle('footer', parent=self.styles['Normal'], fontSize=8, textColor=colors.grey)
        elements.append(Paragraph(
            f"Hisobot yaratilgan: {get_tashkent_datetime_str()}",
            footer_style
        ))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_debtors_report(self) -> bytes:
        """Generate debtors report PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=2*cm,
            rightMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        elements.append(Paragraph("QARZDORLAR HISOBOTI", self.styles['CustomTitle']))
        elements.append(Paragraph(
            f"Sana: {get_tashkent_date_str()}",
            self.styles['CustomSubtitle']
        ))
        
        # Query
        debtors = self.db.query(Customer).filter(
            Customer.is_deleted == False,
            Customer.current_debt > 0
        ).order_by(Customer.current_debt.desc()).all()
        
        total_debt = sum(d.current_debt for d in debtors)
        
        # Summary
        elements.append(Paragraph("UMUMIY MA'LUMOTLAR", self.styles['SectionHeader']))
        summary_data = [
            ["Ko'rsatkich", "Qiymat"],
            ["Jami qarzdorlar", str(len(debtors))],
            ["Jami qarz summasi", f"{total_debt:,.0f} so'm"],
        ]
        summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
        summary_table.setStyle(self._create_table_style())
        elements.append(summary_table)
        elements.append(Spacer(1, 1*cm))
        
        # Debtors list
        elements.append(Paragraph("QARZDORLAR RO'YXATI", self.styles['SectionHeader']))
        
        debtors_data = [["№", "Mijoz", "Telefon", "Qarz summasi"]]
        for i, debtor in enumerate(debtors, 1):
            name = debtor.name
            if len(name) > 25:
                name = name[:23] + ".."
            debtors_data.append([
                str(i),
                name,
                debtor.phone,
                f"{debtor.current_debt:,.0f} so'm"
            ])
        
        debtors_table = Table(debtors_data, colWidths=[1*cm, 6*cm, 4*cm, 4*cm])
        debtors_table.setStyle(self._create_table_style())
        elements.append(debtors_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
    
    def generate_stock_report(self, warehouse_id: int = None) -> bytes:
        """Generate stock report PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=1.5*cm,
            rightMargin=1.5*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        elements.append(Paragraph("OMBOR QOLDIQLARI", self.styles['CustomTitle']))
        elements.append(Paragraph(
            f"Sana: {get_tashkent_datetime_str()}",
            self.styles['CustomSubtitle']
        ))
        
        # Query
        query = self.db.query(Stock).join(Product).filter(
            Product.is_deleted == False,
            Stock.quantity > 0
        )
        if warehouse_id:
            query = query.filter(Stock.warehouse_id == warehouse_id)
        
        stocks = query.order_by(Product.name).all()
        
        total_value = sum(s.quantity * s.average_cost for s in stocks)
        
        # Summary
        elements.append(Paragraph("UMUMIY MA'LUMOTLAR", self.styles['SectionHeader']))
        summary_data = [
            ["Ko'rsatkich", "Qiymat"],
            ["Jami tovarlar", str(len(stocks))],
            ["Jami qiymat", f"{total_value:,.0f} so'm"],
        ]
        summary_table = Table(summary_data, colWidths=[8*cm, 6*cm])
        summary_table.setStyle(self._create_table_style())
        elements.append(summary_table)
        elements.append(Spacer(1, 1*cm))
        
        # Stock list
        elements.append(Paragraph("TOVARLAR RO'YXATI", self.styles['SectionHeader']))
        
        stock_data = [["№", "Tovar", "Miqdor", "Narx", "Qiymat"]]
        for i, stock in enumerate(stocks[:100], 1):
            name = stock.product.name
            if len(name) > 30:
                name = name[:28] + ".."
            value = stock.quantity * stock.average_cost
            stock_data.append([
                str(i),
                name,
                f"{stock.quantity:,.1f}",
                f"{stock.average_cost:,.0f}",
                f"{value:,.0f}"
            ])
        
        stock_table = Table(stock_data, colWidths=[1*cm, 7*cm, 2.5*cm, 3*cm, 3.5*cm])
        stock_table.setStyle(self._create_table_style())
        elements.append(stock_table)
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
