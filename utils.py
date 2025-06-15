# utils.py
import logging
from datetime import datetime
import pytz
from config import OPEN_HOUR, CLOSE_HOUR, TIMEZONE

logger = logging.getLogger(__name__)

def is_cafe_open():
    """Проверяет, открыто ли кафе в данный момент."""
    try:
        tz = pytz.timezone(TIMEZONE)
        now = datetime.now(tz)
        return OPEN_HOUR <= now.hour < CLOSE_HOUR
    except pytz.UnknownTimeZoneError:
        logger.error(f"Неизвестный часовой пояс: {TIMEZONE}. Проверьте config.py.")
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке времени: {e}")
        return True

def get_closed_message():
    """Возвращает стандартное сообщение о том, что кафе закрыто."""
    return f"🌙 Кафе закрыто.\nМы работаем ежедневно с {OPEN_HOUR}:00 до {CLOSE_HOUR}:00."