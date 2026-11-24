def init_db():
    """Заглушка -> создать таблицы."""
    pass


def save_events(events: list[dict]):
    """Заглушка -> реализовать запись событий в SQLite."""
    pass

# from src.common.contract import validate_events

# def save_events(events):
#     validate_events(events)   # защита от прямых вызовов и тестов
#     with sqlite3.connect(DB_PATH) as conn:
#         ...