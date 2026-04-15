"""
LUMI Beauty: Operations & FinOps Manager
Модуль для мониторинга финансового учета затрат на LLM и качества ответов (D2C).
"""

import logging
from datetime import datetime
from config import COST_PER_1M_INPUT, COST_PER_1M_OUTPUT

# Настраиваем базовый логгер Python для записи в файл
LOG_FILE = "lumi_business.log"
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="[%(asctime)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Курс валют для конвертации токенов (USD) в тенге
USD_TO_KZT = 500.0

def log_lumi_transaction(input_tokens: int, output_tokens: int, confidence_score: float, intent: str):
    """
    Логирует каждую транзакцию (запрос-ответ) в единый текстовый файл.
    Рассчитывает фактические затраты студии в тенге и оценивает риски галлюцинаций.
    
    :param input_tokens: Количество входящих токенов (Prompt)
    :param output_tokens: Количество сгенерированных токенов (Completion)
    :param confidence_score: Метрика уверенности ИИ из JSON ответа
    :param intent: Классифицированное намерение клиента (например, booking)
    :return: dict с результатами расчета
    """
    
    # 1. FinOps: Рассчитываем цены сессии
    cost_usd = (input_tokens / 1_000_000 * COST_PER_1M_INPUT) + (output_tokens / 1_000_000 * COST_PER_1M_OUTPUT)
    cost_kzt = cost_usd * USD_TO_KZT
    
    # 2. D2C: Проверяем стабильность ответа
    d2c_status = "SAFE" if confidence_score > 0.7 else "REVIEW_REQUIRED"
    
    # 3. Формируем подробную строку для записи
    log_message = (
        f"INTENT: {intent:<12} | "
        f"TOKENS: {input_tokens} in / {output_tokens} out | "
        f"COST: {cost_kzt:.4f} ₸ ({cost_usd:.6f} $) | "
        f"CONFIDENCE: {confidence_score:.2f} -> [{d2c_status}]"
    )
    
    # Записываем в файл (таймстемп добавится автоматически благодаря basicConfig)
    logging.info(log_message)
    
    return {
        "cost_kzt": cost_kzt,
        "d2c_status": d2c_status
    }
