"""
Iris Nova - Main Configuration
"""

from core.env import Env


# =====================
# Bot Identity
# =====================

BOT_NAME = "Iris Nova"

PREFIX = "!"

VERSION = "1.0.0"


# =====================
# Owner
# =====================

OWNER_ID = Env.OWNER_ID or 1525548792567431184


# =====================
# Features
# =====================

SETTINGS = {

    "AI_ENABLED": False,

    "LOGGING_ENABLED": True,

    "WELCOME_ENABLED": True,

    "SLASH_COMMANDS_ENABLED": True,

    "AUTO_LOADER_ENABLED": True

}


# =====================
# Database
# =====================

DATABASE = {

    "TYPE": "sqlite",

    "FILE": "iris.db"

}


# =====================
# Development
# =====================

DEBUG = True