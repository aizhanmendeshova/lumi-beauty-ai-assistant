"""
Configuration Module for LUMI Beauty AI Assistant.
Enterprise-grade settings, structured for scalability and maintainability.
"""

import os
from dotenv import load_dotenv

# =============================================================================
# ENVIRONMENT INITIALIZATION
# =============================================================================
# Load environment variables from .env file securely
load_dotenv()

# =============================================================================
# GLOBAL AI MODEL SETTINGS
# =============================================================================
MODEL_NAME = "gemini-2.5-flash"

# Controls randomness: 0.2 ensures high stability and predictable responses
TEMPERATURE = 0.2 

# =============================================================================
# FINOPS: COST TRACKING & OPTIMIZATION
# =============================================================================
# Cost metrics per 1 Million tokens (Base currency: USD)
COST_PER_1M_INPUT = 0.075
COST_PER_1M_OUTPUT = 0.30

# =============================================================================
# BUSINESS LOGIC: LUMI BEAUTY CONSTANTS
# =============================================================================
ADDRESS = "Алматы, пр. Достык 105"

# Aktual'nyy prays-list salona (Currency: KZT)
SERVICES = {
    "manicure_no_polish": 6000,
    "manicure_gel_strengthening": 8000,
    "nail_extension": "8000-15000",
    "nail_architecture": "3000-4000",
    "extension_correction": "8000-15000",
    "design_french": 1500,
    "design_rub": "1500-2000",
    "design_cat_eye": 1500,
    "removal_extension": 1500,
    "removal_gel": 1000,
    "pedicure_no_polish": 7000,
    "pedicure_gel": 10000
}

# Формируем читабельный прайс-лист для ИИ
SERVICES_LIST = "\n".join([f"- {name}: {price} ₸" for name, price in SERVICES.items()])

# Core directive for AI behavior and JSON serialization
SYSTEM_PROMPT = f"""
Ты — AI-администратор салона LUMI Beauty. Твоя задача — анализировать сообщения клиентов и возвращать ответ в формате JSON.

📋 НАШ АКТУАЛЬНЫЙ ПРАЙС-ЛИСТ (Оказываем ТОЛЬКО эти услуги):
{SERVICES_LIST}

🚨 СТРОГИЕ ПРАВИЛА (ЗАПРЕТ НА ГАЛЛЮЦИНАЦИИ):
- Ты должен предлагать ТОЛЬКО те услуги, которые есть в прайс-листе выше!
- Если клиент просит ресницы, брови, стрижки, макияж или любые другие услуги, которых нет в списке, вежливо извинись и ответь, что вы занимаетесь ИСКЛЮЧИТЕЛЬНО ногтями (маникюр и педикюр) и дизайном. Никогда не придумывай услуги!

Логика:
- Если клиент просит услугу с диапазоном цен (например, архитектура), указывай вилку цен в тексте ответа (message_to_client).
- Если клиент просит несколько услуг, обязательно суммируй фиксированные цены (если есть точные значения, например 6000 + 1500), и передавай это в cost_kzt.

Ответ должен быть строго по схеме LumiResponseSchema из beauty_models.py.

Требования к JSON-ответу:
ИИ должен всегда возвращать:
{{
  "intent": "<тип запроса: price_check, booking, location, general>",
  "service": "<название услуги или null>",
  "cost_kzt": <итоговая сумма (число) или null, если цену посчитать точно нельзя из-за вилки>,
  "message_to_client": "<вежливый текст для клиента с эмодзи ✨💅>",
  "confidence_score": <вероятность от 0.0 до 1.0>
}}
"""
