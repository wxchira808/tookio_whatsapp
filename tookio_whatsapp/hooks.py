app_name = "tookio_whatsapp"
app_title = "Tookio Whatsapp"
app_publisher = "Tookio"
app_description = "Whatsapp intergration for Frappe and N8N"
app_email = "tookiosolutions@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "tookio_whatsapp",
# 		"logo": "/assets/tookio_whatsapp/logo.png",
# 		"title": "Tookio Whatsapp",
# 		"route": "/tookio_whatsapp",
# 		"has_permission": "tookio_whatsapp.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/tookio_whatsapp/css/tookio_whatsapp.css"
# app_include_js = "/assets/tookio_whatsapp/js/tookio_whatsapp.js"

# include js, css files in header of web template
# web_include_css = "/assets/tookio_whatsapp/css/tookio_whatsapp.css"
# web_include_js = "/assets/tookio_whatsapp/js/tookio_whatsapp.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "tookio_whatsapp/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "tookio_whatsapp/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "tookio_whatsapp.utils.jinja_methods",
# 	"filters": "tookio_whatsapp.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "tookio_whatsapp.install.before_install"
# after_install = "tookio_whatsapp.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "tookio_whatsapp.uninstall.before_uninstall"
# after_uninstall = "tookio_whatsapp.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "tookio_whatsapp.utils.before_app_install"
# after_app_install = "tookio_whatsapp.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "tookio_whatsapp.utils.before_app_uninstall"
# after_app_uninstall = "tookio_whatsapp.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "tookio_whatsapp.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"tookio_whatsapp.tasks.all"
# 	],
# 	"daily": [
# 		"tookio_whatsapp.tasks.daily"
# 	],
# 	"hourly": [
# 		"tookio_whatsapp.tasks.hourly"
# 	],
# 	"weekly": [
# 		"tookio_whatsapp.tasks.weekly"
# 	],
# 	"monthly": [
# 		"tookio_whatsapp.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "tookio_whatsapp.install.before_tests"

# Extend DocType Class
# ------------------------------
#
# Specify custom mixins to extend the standard doctype controller.
# extend_doctype_class = {
# 	"Task": "tookio_whatsapp.custom.task.CustomTaskMixin"
# }

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "tookio_whatsapp.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "tookio_whatsapp.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["tookio_whatsapp.utils.before_request"]
# after_request = ["tookio_whatsapp.utils.after_request"]

# Job Events
# ----------
# before_job = ["tookio_whatsapp.utils.before_job"]
# after_job = ["tookio_whatsapp.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"tookio_whatsapp.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

