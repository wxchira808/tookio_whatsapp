from .message_processor import _send_whatsapp_message


def send_test():
    # test payload — edit phone / token if needed
    phone_number_id = "1016347674905044"
    to_phone = "254732662420"
    text = "Test from Tookio (server-side helper) — ignore."
    access_token = "EAATquDH2lFMBRV6x61H9J4Y7wD0ZBZBDOTZBTZCYFNWdPt1a1wEypp1pxBZBlUI2fF7KQTotYWoQBvCfxb4jfZArRvTlZALKrbIs7k8qjPct71EwmKuHKioLaVypvA6IAwxIS0sZArsqPfLKrcXpqADlJKkmVRkVUL3p8q7cbkZAmTJ3NRyX4q3Law9lKDxjBjyhNEQZDZD"

    return _send_whatsapp_message(phone_number_id, to_phone, text, access_token)
