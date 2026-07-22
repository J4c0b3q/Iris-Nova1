"""
Global configuration for Iris.
Tutaj NIE przechowujemy sekretów.
"""

BOT_NAME = "Iris"
VERSION = "1.0.0"
PREFIX = "!"

OWNER_ID = 0

SETTINGS = {
    "AI_ENABLED": False,
    "LOGGING_ENABLED": True,
    "WELCOME_ENABLED": True,
}

MODULES = {
    "AI": True,
    "MODERATION": True,
    "OWNER": True,
    "SYSTEM": True,
    "UTILITY": True,
}