"""
Схема валидации данных для AI-ассистента LUMI Beauty. 
Обеспечивает строгую структуру ответов и предотвращает галлюцинации LLM.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

class LumiResponseSchema(BaseModel):
    """
    Основная модель валидации ответов (JSON) от нейросети.
    Позволяет типизировать полученные данные и безопасно использовать их в бизнес-логике.
    """
    
    intent: str = Field(
        ..., 
        description="Классификация намерений: price_check, booking, location, general"
    )
    
    service: Optional[str] = Field(
        default=None, 
        description="Название услуги (например, 'manicure' или 'design')"
    )
    
    cost_kzt: Optional[int] = Field(
        default=None, 
        description="Цена за услугу согласно прайс-листу (в KZT)"
    )
    
    duration: Optional[str] = Field(
        default=None, 
        description="Длительность сеанса (например, '90 min')"
    )
    
    message_to_client: str = Field(
        ..., 
        description="Финальный ответ, который будет отправлен текущему клиенту"
    )
    
    confidence_score: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Метрика уверенности: от 0.0 до 1.0 (для D2C мониторинга)"
    )
    
    is_ready_for_human: bool = Field(
        default=False, 
        description="Флаг перевода на администратора при сложной ситуации"
    )
    
    created_at: datetime = Field(
        default_factory=datetime.now, 
        description="Время обработки и генерации ответа системой"
    )
