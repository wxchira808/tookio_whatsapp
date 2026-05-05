app_name = "tookio_whatsapp"
app_title = "Tookio Whatsapp"
app_publisher = "Tookio"
app_description = "WhatsApp Business Cloud API integration for Frappe - AI customer service automation"
app_email = "tookiosolutions@gmail.com"
app_license = "mit"
app_version = "0.0.1"

# Installation
after_install = "tookio_whatsapp.install.after_install"

fixtures = []

# Webhook routes
api_endpoints = {
	"tookio_whatsapp.methods.whatsapp_webhook.webhook": ["webhook"]
}
