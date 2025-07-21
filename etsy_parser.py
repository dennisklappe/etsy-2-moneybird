#!/usr/bin/env python3
import PyPDF2
import requests
import os
from typing import Dict, Optional
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration from environment variables
API_TOKEN = os.getenv('MONEYBIRD_API_TOKEN')
ADMIN_ID = os.getenv('MONEYBIRD_ADMIN_ID')
TAX_RATE_ID = os.getenv('TAX_RATE_ID')
LEDGER_ACCOUNT_ID = os.getenv('LEDGER_ACCOUNT_ID')
PROJECT_ID = os.getenv('PROJECT_ID')
DOCUMENT_STYLE_ID = os.getenv('DOCUMENT_STYLE_ID')

# Validate required environment variables
required_env_vars = [
    'MONEYBIRD_API_TOKEN', 'MONEYBIRD_ADMIN_ID', 'TAX_RATE_ID', 
    'LEDGER_ACCOUNT_ID', 'PROJECT_ID', 'DOCUMENT_STYLE_ID'
]

for var in required_env_vars:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")

def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF file"""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def parse_contact_info(pdf_text: str) -> Dict[str, str]:
    """Parse contact information from Etsy invoice PDF text"""
    contact_info = {}
    
    # Find email
    lines = pdf_text.split('\n')
    email = ""
    for line in lines[:5]:  # Check first few lines
        if "(" in line and "@" in line and ")" in line:
            # Extract email
            start = line.find("(") + 1
            end = line.find(")")
            if start > 0 and end > start:
                email = line[start:end].strip()
            break
    
    # Find the "Deliver to" section
    deliver_to_index = -1
    
    for i, line in enumerate(lines):
        if "Deliver to" in line:
            deliver_to_index = i
            break
    
    if deliver_to_index == -1:
        raise ValueError("Could not find 'Deliver to' section in PDF")
    
    # Extract contact info from the lines following "Deliver to"
    try:
        # Name is usually on the next line after "Deliver to"
        full_name = lines[deliver_to_index + 1].strip()
        name_parts = full_name.split(' ')
        firstname = name_parts[0] if name_parts else ""
        lastname = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ""
        
        # Address is on the line after name
        address1 = lines[deliver_to_index + 2].strip()
        
        # Zipcode and city on next line
        zipcode_city_line = lines[deliver_to_index + 3].strip()
        zipcode_city_parts = zipcode_city_line.split(' ')
        zipcode = zipcode_city_parts[0] if zipcode_city_parts else ""
        city = ' '.join(zipcode_city_parts[1:]) if len(zipcode_city_parts) > 1 else ""
        
        # Country on next line
        country_line = lines[deliver_to_index + 4].strip()
        
        # Map country names to ISO codes
        country_mapping = {
            "Germany": "DE",
            "Netherlands": "NL",
            "Austria": "AT",
            "Belgium": "BE",
            "France": "FR",
            "Italy": "IT",
            "Spain": "ES",
            "Portugal": "PT",
            "Switzerland": "CH",
            "Luxembourg": "LU",
            "Denmark": "DK",
            "Sweden": "SE",
            "Norway": "NO",
            "Finland": "FI",
            "Ireland": "IE",
            "Poland": "PL",
            "Czech Republic": "CZ",
            "Slovakia": "SK",
            "Hungary": "HU",
            "Slovenia": "SI",
            "Croatia": "HR",
            "Romania": "RO",
            "Bulgaria": "BG",
            "Greece": "GR",
            "Cyprus": "CY",
            "Malta": "MT",
            "Estonia": "EE",
            "Latvia": "LV",
            "Lithuania": "LT",
            "United Kingdom": "GB",
            "United States": "US",
            "Canada": "CA",
            "Australia": "AU",
            "New Zealand": "NZ",
            "Japan": "JP",
            "South Korea": "KR",
            "Singapore": "SG",
            "Hong Kong": "HK",
            "Taiwan": "TW",
            "Thailand": "TH",
            "Malaysia": "MY",
            "Philippines": "PH",
            "Indonesia": "ID",
            "Vietnam": "VN",
            "India": "IN",
            "Brazil": "BR",
            "Mexico": "MX",
            "Argentina": "AR",
            "Chile": "CL",
            "Colombia": "CO",
            "Peru": "PE",
            "South Africa": "ZA",
            "Israel": "IL",
            "Turkey": "TR",
            "Russia": "RU",
            "Ukraine": "UA",
            "China": "CN"
        }
        
        # Find matching country
        country_code = None
        for country_name, code in country_mapping.items():
            if country_name in country_line:
                country_code = code
                break
        
        # Fallback to first two characters if no match found
        if not country_code:
            country_code = country_line[:2].upper()
        
        contact_info = {
            "company_name": "",
            "firstname": firstname.capitalize(),
            "lastname": lastname,
            "address1": address1,
            "zipcode": zipcode,
            "city": city,
            "country": country_code,
            "email": email
        }
        
    except IndexError as e:
        raise ValueError(f"Error parsing contact info: {e}")
    
    return contact_info

def parse_invoice_details(pdf_text: str) -> Dict[str, any]:
    """Parse invoice details from Etsy PDF"""
    lines = pdf_text.split('\n')
    invoice_details = {}
    
    # Extract order number
    order_line = lines[0] if lines else ""
    if "Order #" in order_line:
        invoice_details["order_number"] = order_line.replace("Order #", "").strip()
    
    # Extract order date
    for line in lines:
        if "Order date" in line:
            # Find next line with date
            idx = lines.index(line)
            if idx + 1 < len(lines):
                date_str = lines[idx + 1].strip()
                # Convert date format from "21 Jun, 2025" to "2025-06-21"
                try:
                    date_obj = datetime.strptime(date_str, "%d %b, %Y")
                    invoice_details["invoice_date"] = date_obj.strftime("%Y-%m-%d")
                except:
                    invoice_details["invoice_date"] = date_str
            break
    
    # Parse products and prices
    products = []
    # Look for the pattern "2 items" or "1 item" first to find product section
    product_section_start = -1
    for i, line in enumerate(lines):
        if " item" in line and any(char.isdigit() for char in line):
            product_section_start = i
            break
    
    if product_section_start >= 0:
        # Look for lines with "SKU:" and then find the quantity/price line
        for i in range(product_section_start, min(len(lines), product_section_start + 10)):
            if "SKU:" in lines[i]:
                # Look for quantity/price pattern in surrounding lines
                for check_line_idx in range(max(0, i-2), min(len(lines), i+3)):
                    check_line = lines[check_line_idx].strip()
                    if " x €" in check_line:
                        # Product name before SKU
                        product_name = ""
                        for j in range(max(0, i-3), i):
                            line_text = lines[j].strip()
                            if line_text and "via PostNL" not in line_text and "Tracking" not in line_text and "SKU:" not in line_text:
                                # Clean up the line to remove trailing digits that got merged
                                clean_line = line_text
                                if clean_line.endswith('2 items') or clean_line.endswith('1 item'):
                                    clean_line = clean_line.rsplit(' items', 1)[0].strip()
                                    if clean_line.endswith((' 1', ' 2', ' 3', ' 4', ' 5', ' 6', ' 7', ' 8', ' 9')):
                                        clean_line = clean_line.rsplit(' ', 1)[0].strip()
                                
                                if product_name:
                                    product_name += " " + clean_line
                                else:
                                    product_name = clean_line
                        
                        # Extract quantity and price - handle "SKU: 123 x €11.95" format
                        if "SKU:" in check_line:
                            # Extract the part after SKU number
                            sku_parts = check_line.split(" x €")
                            if len(sku_parts) == 2:
                                price = float(sku_parts[1].strip())
                                # Get quantity from context
                                quantity = 2 if "2 items" in pdf_text else 1
                                products.append({
                                    "name": product_name.strip(),
                                    "quantity": quantity,
                                    "price": price
                                })
                                break
                        else:
                            parts = check_line.split(" x €")
                            if len(parts) == 2:
                                try:
                                    quantity = int(parts[0].strip())
                                    price = float(parts[1].strip())
                                    products.append({
                                        "name": product_name.strip(),
                                        "quantity": quantity,
                                        "price": price
                                    })
                                    break
                                except ValueError:
                                    pass
                        break
    
    invoice_details["products"] = products
    
    # Extract delivery cost
    for line in lines:
        if "Delivery total" in line:
            parts = line.split("€")
            if len(parts) > 1:
                try:
                    invoice_details["delivery_cost"] = float(parts[1].strip())
                except:
                    pass
            break
    
    return invoice_details

def find_or_create_contact(contact_info: Dict[str, str]) -> Optional[Dict]:
    """Find existing contact or create new one"""
    customer_id = f"{contact_info['firstname']}-{contact_info['lastname']}-{contact_info['zipcode']}"
    
    # Try to find existing contact
    url = f"https://moneybird.com/api/v2/{ADMIN_ID}/contacts"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}", 
        "Content-Type": "application/json",
        "User-Agent": "etsy-2-moneybird/1.0"
    }
    
    try:
        response = requests.get(url, headers=headers, params={"query": customer_id})
        response.raise_for_status()
        contacts = response.json()
        for contact in contacts:
            if contact.get("customer_id") == customer_id:
                return contact
    except:
        pass
    
    # Create new contact
    contact_data = {
        "contact": {
            "company_name": contact_info.get("company_name", ""),
            "firstname": contact_info["firstname"],
            "lastname": contact_info["lastname"],
            "address1": contact_info["address1"],
            "zipcode": contact_info["zipcode"],
            "city": contact_info["city"],
            "country": contact_info["country"],
            "email": contact_info.get("email", ""),
            "customer_id": customer_id
        }
    }
    
    headers.update({"User-Agent": "etsy-2-moneybird/1.0"})
    try:
        response = requests.post(url, headers=headers, json=contact_data)
        response.raise_for_status()
        return response.json()
    except:
        return None

def create_invoice(contact_id: str, invoice_details: Dict) -> Optional[Dict]:
    """Create invoice in Moneybird"""
    url = f"https://moneybird.com/api/v2/{ADMIN_ID}/sales_invoices"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}", 
        "Content-Type": "application/json",
        "User-Agent": "etsy-2-moneybird/1.0"
    }
    
    # Prepare invoice lines
    details_attributes = []
    
    # Add product lines
    for product in invoice_details.get("products", []):
        details_attributes.append({
            "description": product["name"],
            "amount": str(product["quantity"]),
            "price": str(product["price"]),
            "tax_rate_id": TAX_RATE_ID,
            "ledger_account_id": LEDGER_ACCOUNT_ID,
            "project_id": PROJECT_ID,
            "_destroy": False
        })
    
    # Add shipping line
    if invoice_details.get("delivery_cost"):
        details_attributes.append({
            "description": "Shipping",
            "amount": "1",
            "price": str(invoice_details["delivery_cost"]),
            "tax_rate_id": TAX_RATE_ID,
            "ledger_account_id": LEDGER_ACCOUNT_ID,
            "project_id": PROJECT_ID,
            "_destroy": False
        })
    
    invoice_data = {
        "sales_invoice": {
            "contact_id": contact_id,
            "reference": invoice_details.get("order_number", ""),
            "invoice_date": invoice_details.get("invoice_date", ""),
            "document_style_id": DOCUMENT_STYLE_ID,
            "prices_are_incl_tax": True,  # Prices include BTW
            "details_attributes": details_attributes,
            "source": "etsy-2-moneybird",
            "source_url": "https://github.com/dennisklappe/etsy-2-moneybird"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=invoice_data)
        response.raise_for_status()
        return response.json()
    except:
        return None

def mark_invoice_paid(invoice_id: str, invoice_details: Dict) -> bool:
    """Mark invoice as sent and paid"""
    headers = {
        "Authorization": f"Bearer {API_TOKEN}", 
        "Content-Type": "application/json",
        "User-Agent": "etsy-2-moneybird/1.0"
    }
    
    # First mark as sent
    sent_url = f"https://moneybird.com/api/v2/{ADMIN_ID}/sales_invoices/{invoice_id}/send_invoice"
    send_data = {"sales_invoice_sending": {"delivery_method": "Manual"}}
    
    try:
        response = requests.patch(sent_url, headers=headers, json=send_data)
        response.raise_for_status()
    except:
        return False
    
    # Calculate total amount
    total_amount = sum([p['quantity'] * p['price'] for p in invoice_details['products']]) + invoice_details.get('delivery_cost', 0)
    
    # Mark as paid
    paid_url = f"https://moneybird.com/api/v2/{ADMIN_ID}/sales_invoices/{invoice_id}/payments"
    payment_data = {
        "payment": {
            "payment_date": invoice_details.get("invoice_date", ""),
            "price": str(total_amount),
            "description": f"Payment received of €{total_amount:.2f} via etsy-2-moneybird"
        }
    }
    
    try:
        response = requests.post(paid_url, headers=headers, json=payment_data)
        response.raise_for_status()
        return True
    except:
        return False

def process_etsy_pdf(pdf_path: str) -> Dict[str, any]:
    """Main function to process an Etsy PDF and create invoice"""
    try:
        # Extract text from PDF
        pdf_text = extract_text_from_pdf(pdf_path)
        
        # Parse contact and invoice details
        contact_info = parse_contact_info(pdf_text)
        invoice_details = parse_invoice_details(pdf_text)
        
        # Find or create contact
        contact = find_or_create_contact(contact_info)
        if not contact:
            return {"success": False, "error": "Failed to create contact"}
        
        # Create invoice
        invoice = create_invoice(str(contact["id"]), invoice_details)
        if not invoice:
            return {"success": False, "error": "Failed to create invoice"}
        
        # Mark as sent and paid
        invoice_id = str(invoice["id"])
        if not mark_invoice_paid(invoice_id, invoice_details):
            return {"success": False, "error": "Failed to mark invoice as paid"}
        
        # Calculate total
        total_amount = sum([p['quantity'] * p['price'] for p in invoice_details['products']]) + invoice_details.get('delivery_cost', 0)
        
        return {
            "success": True,
            "contact_name": f"{contact_info['firstname']} {contact_info['lastname']}",
            "order_number": invoice_details.get("order_number", ""),
            "total_amount": total_amount,
            "invoice_id": invoice_id,
            "contact_id": contact["id"]
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}