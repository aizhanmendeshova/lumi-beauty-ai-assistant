import os
from dotenv import load_dotenv

load_dotenv() # Эта строка загружает твой ключ из файла .env

import lumi_ops_manager
import streamlit as st
import os
import json
from google import genai
from google.genai import types
from pydantic import ValidationError

# Импортируем наши модули
from config import (
    MODEL_NAME, TEMPERATURE, SYSTEM_PROMPT, SERVICES,
    COST_PER_1M_INPUT, COST_PER_1M_OUTPUT
)
from beauty_models import LumiResponseSchema

# -----------------------------------------------------------------------------
# 1. UI SETUP AND DESIGN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="LUMI Beauty AI",
    page_icon="💅",
    layout="wide"
)

# Кастомный CSS для создания премиального (дорогого) визуала
st.markdown("""
<style>
    /* Нежно-розовый градиентный фон */
    .stApp {
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%);
        font-family: 'Helvetica Neue', sans-serif;
    }
    
    /* Округление чат-контейнеров (пузырьки) */
    .stChatMessage {
        border-radius: 20px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        background-color: rgba(255, 255, 255, 0.6);
    }

    /* Настройка заголовка */
    h1 {
        color: #C71585;
        font-weight: 300;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* Стилизация карточек в Sidebar */
    .service-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 10px;
        margin-bottom: 10px;
        border-left: 4px solid #FF69B4;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .service-title { font-weight: bold; color: #333; }
    .service-price { color: #FF1493; font-weight: 500; font-size: 0.9em; }
</style>
""", unsafe_allow_html=True)

st.title("LUMI Beauty | Интеллектуальный ассистент ✨")

# -----------------------------------------------------------------------------
# 2. STATE MANAGEMENT (Память ИИ и Аналитика)
# -----------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
    # Приветственное сообщение
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Здравствуйте! Я LUMI ✨ Ваш персональный AI-администратор студии красоты. Чем могу помочь?",
        "intent": "general"
    })

if "total_cost_usd" not in st.session_state:
    st.session_state.total_cost_usd = 0.0

if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = 1.0

# -----------------------------------------------------------------------------
# 3. SIDEBAR (Гордость - FinOps, D2C и Прайс)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 💅 LUMI Studio")
    st.caption("Админ-панель AI")
    st.divider()
    
    # D2C (Мониторинг уверенности)
    st.markdown("### 📊 Уверенность (D2C)")
    confidence = st.session_state.last_confidence
    st.progress(confidence)
    st.caption(f"Уверенность LLM: {confidence:.2f}/1.0")
    if confidence < 0.6:
        st.warning("⚠️ Низкая уверенность. Рекомендуется контроль менеджера!")
    st.divider()
    
    # FinOps (Расчет цены сессии)
    usd_to_kzt = 500 # Примерный курс
    st.markdown("### 💰 FinOps Metrics")
    cost_kzt = st.session_state.total_cost_usd * usd_to_kzt
    st.metric(label="Стоимость сессии (AI Token Cost)", value=f"{cost_kzt:.2f} ₸", delta=f"{st.session_state.total_cost_usd:.4f} $")
    st.divider()
    
    # Прайс-лист салона
    st.markdown("### 📋 Услуги и цены")
    for srv_name, srv_price in SERVICES.items():
        st.markdown(
            f"""
            <div class="service-card">
                <div class="service-title">{srv_name.replace('_', ' ').capitalize()}</div>
                <div class="service-price">{srv_price} ₸</div>
            </div>
            """, 
            unsafe_allow_html=True
        )

# -----------------------------------------------------------------------------
# 4. CHAT FUNCTIONALITY & API INTEGRATION
# -----------------------------------------------------------------------------
# Инициализация нового клиента Google GenAI (согласно v1.0.0+)
# Ожидает, что GEMINI_API_KEY подтянется из .env (через config)
try:
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)
except Exception as e:
    st.error(f"Ошибка подключения Gemini API: Убедитесь, что GEMINI_API_KEY в .env задан. Текст: {e}")
    st.stop()

# Рендер истории сообщений
for index, msg in enumerate(st.session_state.messages):
    avatar = "💅" if msg["role"] == "assistant" else "💬"
    with st.chat_message(msg["role"], avatar=avatar):
        st.write(msg["content"])
        
        # Если ответ от ассистента - показываем лейблы для отладки
        if msg["role"] == "assistant" and index > 0:
            cols = st.columns(3)
            with cols[0]:
                st.caption(f"Intent: `{msg.get('intent', 'unknown')}`")
            with cols[1]:
                if msg.get("cost_kzt"):
                    st.caption(f"Price: `{msg['cost_kzt']} ₸`")
            with cols[2]:
                if msg.get("needs_human"):
                    st.caption(f"🚨 Требуется человек")

# Ввод пользователя
user_input = st.chat_input("Напишите LUMI...")

if user_input:
    # 1. Показываем сообщение клиента
    with st.chat_message("user", avatar="💬"):
        st.write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 2. Формируем контекст для модели
    contents = []
    for msg in st.session_state.messages:
        # Для Gemini валидные роли: 'user' и 'model'
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))
        
    # 3. Отправляем запрос с использованием спиннера
    with st.chat_message("assistant", avatar="💅"):
        with st.spinner('LUMI анализирует ваш запрос ✨...'):
            try:
                # Настраиваем конфигурацию (Structured Output)
                config = types.GenerateContentConfig(
                   system_instruction=SYSTEM_PROMPT,    # Должно быть строго system_instruction
                   temperature=TEMPERATURE,
                   response_mime_type="application/json", # Должно быть строго response_mime_type
                 response_schema=LumiResponseSchema,     # Должно быть строго response_schema
                )
                
                # Запрос к LLM ресурсам
                response = client.models.generate_content(
                  model=MODEL_NAME,
                  contents=contents,
                  config=config
                )
                
                # FinOps - рассчитываем потраченные токены на лету!
                if response.usage_metadata:
                    in_tokens = response.usage_metadata.prompt_token_count
                    out_tokens = response.usage_metadata.candidates_token_count
                    
                    session_cost = (in_tokens / 1_000_000 * COST_PER_1M_INPUT) + (out_tokens / 1_000_000 * COST_PER_1M_OUTPUT)
                    st.session_state.total_cost_usd += session_cost
                
                # Парсим ответ через нашу Pydantic модель
                result_json = response.text
                ai_data = LumiResponseSchema.model_validate_json(result_json)
                
                # Сохраняем метрику D2C
                st.session_state.last_confidence = ai_data.confidence_score
                lumi_ops_manager.log_lumi_transaction(
                   input_tokens=in_tokens,
                   output_tokens=out_tokens,
                   confidence_score=ai_data.confidence_score,
                   intent=ai_data.intent
                )

                # Выводим ответ клиенту
                st.write(ai_data.message_to_client)
                
                # Рендер отладки и тэгов
                cols = st.columns(3)
                with cols[0]:
                    st.caption(f"Intent: `{ai_data.intent}`")
                with cols[1]:
                    if ai_data.cost_kzt:
                        st.caption(f"Price: `{ai_data.cost_kzt} ₸`")
                with cols[2]:
                    if ai_data.is_ready_for_human:
                        st.caption(f"🚨 Требуется человек")
                        
                # Сохраняем в память
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": ai_data.message_to_client,
                    "intent": ai_data.intent,
                    "cost_kzt": ai_data.cost_kzt,
                    "needs_human": ai_data.is_ready_for_human
                })
                
                # Принудительно перезагружаем UI для обновления метрик Sidebar
                st.rerun()

            except ValidationError as ve:
                st.error("Ошибка валидации схемы ответа (галлюцинация предотвращена!).")
                st.exception(ve)
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    st.warning("⏳ Бесплатный лимит запросов Google исчерпан (слишком частые сообщения). Пожалуйста, подождите 10-15 секунд и попробуйте снова!")
                elif "503" in error_str or "UNAVAILABLE" in error_str:
                    st.warning("🔄 Серверы Google Gemini сейчас сильно перегружены запросами со всего мира. Пожалуйста, просто нажмите кнопку отправки еще раз через пару секунд!")
                else:
                    st.error(f"Случилась непредвиденная ошибка на сервере LUMI: {e}")
