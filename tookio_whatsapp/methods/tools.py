import frappe
import json

def check_inventory(item_name="", shop_name=None):
    """
    Check the inventory level of an item.
    """
    filters = {}
    if shop_name:
        filters['shop_name'] = ["like", f"%{shop_name}%"]
        
    try:
        stocks = frappe.get_all("Product", filters=filters, fields=["name", "item_name", "shop", "shop_name", "stock_quantity", "price"])
        
        matches = []
        if item_name:
            search_terms = [t.strip().lower() for t in item_name.replace(" and ", ",").split(",") if t.strip()]
            for s in stocks:
                for term in search_terms:
                    if term in s.item_name.lower():
                        matches.append(s)
                        break
        else:
            matches = stocks
                    
        if not matches:
            if item_name:
                return f"I couldn't find any products matching '{item_name}'."
            else:
                return f"I couldn't find any products in your shop(s)."
        
        lines = []
        for match in matches:
            shop_display = match.shop_name or match.shop
            lines.append(f"- {match.item_name} in {shop_display}: {match.stock_quantity} units available (Price: {match.price})")
        return "\n".join(lines)
    except Exception as e:
        frappe.log_error("check_inventory error", str(e))
        return f"Error checking inventory: {str(e)}"


def create_quick_sale(items=None, shop_name=None, customer_name="Walk-in Customer", customer_phone_number="", item_name=None, quantity=1, payment_method="Cash", delivery_location=""):
    """
    Create a quick Sale Invoice for multiple products.
    """
    try:
        # Fallback if Gemini passes item_name instead of items array
        if not items and item_name:
            items = [{"item_name": item_name, "quantity": quantity}]
            
        if not items:
            return "Error: No items provided for the sale. Please specify the products and try again."
            
        invoice_items = []
        total = 0
        
        for item in items:
            it_name = item.get("item_name")
            qty = item.get("quantity", 1)
            
            # Find the product
            products = frappe.get_all("Product", filters={"item_name": ["like", f"%{it_name}%"]}, fields=["name", "item_name", "price"])
            if not products:
                return f"I couldn't find a product matching '{it_name}'. Sale aborted."
                
            product = products[0]
            price = product.price or 0
            
            invoice_items.append({
                "product": product.name,
                "product_name": product.item_name,
                "quantity": qty,
                "price": price
            })
            total += (price * qty)
            
        # Resolve shop_name to Shop ID
        shops = frappe.get_all("Shop", filters={"shop_name": shop_name}, fields=["name"])
        if not shops:
            return f"Error: Could not find a shop named '{shop_name}'."
        shop_id = shops[0].name
            
        # Create Sales Invoice in tookio_shop
        invoice = frappe.get_doc({
            "doctype": "Sale Invoice",
            "shop": shop_id,
            "customer_name": customer_name,
            "customer_phone_number": customer_phone_number,
            "payment_method": payment_method,
            "delivery_location": delivery_location,
            "total": total,
            "items": invoice_items
        })
        invoice.insert(ignore_permissions=True)
        item_strings = [f"{i.get('quantity')}x {i.get('product_name')}" for i in invoice_items]
        return f"Success! Created Draft Sale Invoice {invoice.name} at {shop_name} for {customer_name} totaling {total}. Products: {', '.join(item_strings)}."
    except Exception as e:
        frappe.log_error("create_quick_sale error", str(e))
        return f"Error creating sale: {str(e)}"


def get_gemini_tools():
    """
    Returns the Gemini function declarations for the tools.
    """
    return [
        {
            "functionDeclarations": [
                {
                    "name": "check_inventory",
                    "description": "Check the available inventory/stock levels for products. Leave item_name blank to list all products. If the merchant manages multiple shops, provide the shop name.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "item_name": {
                                "type": "STRING",
                                "description": "The name or partial name of the product to check. Leave empty to retrieve a full list of all products."
                            },
                            "shop_name": {
                                "type": "STRING",
                                "description": "The specific shop/company name to check inventory in. Optional if they only have one shop."
                            }
                        }
                    }
                },
                {
                    "name": "create_quick_sale",
                    "description": "Draft a quick Sale Invoice when a customer makes a purchase. Can include multiple items.",
                    "parameters": {
                        "type": "OBJECT",
                        "properties": {
                            "items": {
                                "type": "ARRAY",
                                "description": "The list of items being sold. Use this for multiple items.",
                                "items": {
                                    "type": "OBJECT",
                                    "properties": {
                                        "item_name": {"type": "STRING"},
                                        "quantity": {"type": "INTEGER"}
                                    },
                                    "required": ["item_name", "quantity"]
                                }
                            },
                            "item_name": {
                                "type": "STRING",
                                "description": "Fallback: Use this if selling only one type of item."
                            },
                            "quantity": {
                                "type": "INTEGER",
                                "description": "Fallback: Use this if selling only one type of item."
                            },
                            "shop_name": {
                                "type": "STRING",
                                "description": "The specific shop/company name where the sale occurred. Required."
                            },
                            "customer_name": {
                                "type": "STRING",
                                "description": "The name of the customer buying the products."
                            },
                            "customer_phone_number": {
                                "type": "STRING",
                                "description": "The phone number of the customer."
                            },
                            "payment_method": {
                                "type": "STRING",
                                "description": "The payment method used (e.g., Cash, M-Pesa). Default is Cash."
                            },
                            "delivery_location": {
                                "type": "STRING",
                                "description": "The location where the items should be delivered."
                            }
                        },
                        "required": ["shop_name"]
                    }
                }
            ]
        }
    ]
