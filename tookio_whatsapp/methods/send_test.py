from .message_processor import _send_whatsapp_message


def send_test():
    phone_number_id = "1016347674905044"
    to_phone = "254732662420"
    text = "Test from Tookio (server-side helper) — ignore."
    access_token = "EAATquDH2lFMBRV6x61H9J4Y7wD0ZBZBDOTZBTZCYFNWdPt1a1wEypp1pxBZBlUI2fF7KQTotYWoQBvCfxb4jfZArRvTlZALKrbIs7k8qjPct71EwmKuHKioLaVypvA6IAwxIS0sZArsqPfLKrcXpqADlJKkmVRkVUL3p8q7cbkZAmTJ3NRyX4q3Law9lKDxjBjyhNEQZDZD"

    return _send_whatsapp_message(phone_number_id, to_phone, text, access_token)


def verify_handoff_doctypes():
    import frappe
    
    results = {}
    try:
        results["business"] = bool(frappe.get_meta("Business"))
    except:
        results["business"] = False
    
    try:
        results["handoff"] = bool(frappe.get_meta("WhatsApp Handoff"))
    except:
        results["handoff"] = False
    
    try:
        results["conversation_has_business"] = bool(frappe.get_meta("WhatsApp Conversation").get_field("business"))
    except:
        results["conversation_has_business"] = False
    
    return results
