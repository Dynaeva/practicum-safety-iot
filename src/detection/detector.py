def detect(frame) -> list[dict]:
    """Заглушка -> заменить на YOLO

    Возвращает список объектов по контракту:
    {"cls": "person" | "helmet" | "vest",
     "bbox": [x1, y1, x2, y2],
     "conf": float}
    """
    return []

# from src.common.contract import validate_detections

# def detect(frame) -> list[dict]:
#     results = [...]  # YOLO
#     validate_detections(results)   # <-- падает здесь, а не в трекинге
#     return results