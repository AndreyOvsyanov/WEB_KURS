"""
    Здесь будут содержаться необходимые плагины для поддержки бизнес-логики
"""
class Status:
    """
        Статус заявки, который может быть
    """
    DELETED = "Удалён"
    ON_DELETED = "На удалении"
    CURRENT = "Действующий"
    UNDER_CONSIDERATION = "На рассмотрении"