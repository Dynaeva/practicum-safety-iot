"""Контракты данных между модулями.

Каждый модуль обязан возвращать данные строго в этом формате.
Изменение формата — только через согласование в чате и правку этого файла.
"""

from __future__ import annotations
from datetime import datetime
from typing import Literal, TypedDict
from .errors import ContractError

# 1. ДЕТЕКЦИЯ

DetectionClass = Literal["person", "helmet", "vest"]
VALID_DETECTION_CLASSES: set[str] = {"person", "helmet", "vest"}


class Detection(TypedDict):
    cls: DetectionClass
    bbox: list[float]   # [x1, y1, x2, y2] в пикселях
    conf: float         # 0.0 .. 1.0


def _check_bbox(bbox: object) -> None:
    if not isinstance(bbox, (list, tuple)):
        raise ContractError(f"bbox должен быть списком, получено: {type(bbox).__name__}")
    if len(bbox) != 4:
        raise ContractError(f"bbox должен содержать 4 числа, получено: {len(bbox)}")
    for v in bbox:
        if not isinstance(v, (int, float)):
            raise ContractError(f"bbox: все элементы должны быть числами, получено: {v!r}")
        if v < 0:
            raise ContractError(f"bbox: координаты не могут быть отрицательными: {v}")
    x1, y1, x2, y2 = bbox
    if x1 >= x2 or y1 >= y2:
        raise ContractError(f"bbox: нарушен порядок (x1<x2, y1<y2): {bbox}")


def _check_conf(conf: object) -> None:
    if not isinstance(conf, (int, float)):
        raise ContractError(f"conf должен быть числом, получено: {type(conf).__name__}")
    if not 0.0 <= float(conf) <= 1.0:
        raise ContractError(f"conf должен быть в [0, 1], получено: {conf}")


def validate_detection(obj: dict) -> None:
    if not isinstance(obj, dict):
        raise ContractError(f"детекция должна быть dict, получено: {type(obj).__name__}")
    if "cls" not in obj or "bbox" not in obj or "conf" not in obj:
        raise ContractError(f"в детекции не хватает обязательных ключей cls/bbox/conf: {obj}")
    if obj["cls"] not in VALID_DETECTION_CLASSES:
        raise ContractError(
            f"неизвестный класс '{obj['cls']}'. Допустимо: {VALID_DETECTION_CLASSES}"
        )
    _check_bbox(obj["bbox"])
    _check_conf(obj["conf"])


def validate_detections(objects: list[dict]) -> None:
    if not isinstance(objects, list):
        raise ContractError(f"детекции должны быть list, получено: {type(objects).__name__}")
    for i, obj in enumerate(objects):
        try:
            validate_detection(obj)
        except ContractError as e:
            raise ContractError(f"детекция[{i}]: {e}") from e

# 2. ТРЕКИНГ

class TrackedObject(TypedDict, total=False):
    cls: DetectionClass
    bbox: list[float]
    conf: float
    track_id: int       # обязателен только для cls == "person"


def validate_tracked_object(obj: dict) -> None:
    validate_detection(obj)  # трекинг обязан сохранить все поля детекции

    if obj["cls"] == "person":
        if "track_id" not in obj:
            raise ContractError(f"у person отсутствует track_id: {obj}")
        if not isinstance(obj["track_id"], int) or obj["track_id"] < 0:
            raise ContractError(f"track_id должен быть int >= 0: {obj['track_id']!r}")
    else:
        if "track_id" in obj:
            raise ContractError(
                f"track_id допустим только у person, а у {obj['cls']}: {obj['track_id']}"
            )


def validate_tracked_objects(objects: list[dict]) -> None:
    if not isinstance(objects, list):
        raise ContractError(f"трекинг-объекты должны быть list, получено: {type(objects).__name__}")
    for i, obj in enumerate(objects):
        try:
            validate_tracked_object(obj)
        except ContractError as e:
            raise ContractError(f"tracked[{i}]: {e}") from e

# 3. СОБЫТИЯ (логика -> БД -> дашборд)

EventType = Literal[
    "person_appeared",
    "person_left",
    "helmet_on",
    "helmet_off",
    "vest_on",
    "vest_off",
]
VALID_EVENT_TYPES: set[str] = {
    "person_appeared", "person_left",
    "helmet_on", "helmet_off",
    "vest_on", "vest_off",
}

# какие события относятся к person, а какие — к конкретному СИЗ
PERSON_EVENTS = {"person_appeared", "person_left"}
HELMET_EVENTS = {"helmet_on", "helmet_off"}
VEST_EVENTS = {"vest_on", "vest_off"}


class Event(TypedDict):
    track_id: int
    event_type: EventType
    frame: int
    timestamp: str      # ISO 8601, например "2026-11-24T12:34:56"
    confidence: float   # 0.0 .. 1.0


def _check_iso_timestamp(ts: object) -> None:
    if not isinstance(ts, str):
        raise ContractError(f"timestamp должен быть str (ISO 8601), получено: {type(ts).__name__}")
    try:
        datetime.fromisoformat(ts)
    except ValueError as e:
        raise ContractError(f"timestamp не парсится как ISO 8601: {ts!r} ({e})") from e


def validate_event(ev: dict) -> None:
    if not isinstance(ev, dict):
        raise ContractError(f"событие должно быть dict, получено: {type(ev).__name__}")
    required = {"track_id", "event_type", "frame", "timestamp", "confidence"}
    missing = required - ev.keys()
    if missing:
        raise ContractError(f"в событии не хватает полей: {missing}")
    if ev["event_type"] not in VALID_EVENT_TYPES:
        raise ContractError(
            f"неизвестный event_type '{ev['event_type']}'. Допустимо: {VALID_EVENT_TYPES}"
        )
    if not isinstance(ev["track_id"], int) or ev["track_id"] < 0:
        raise ContractError(f"track_id должен быть int >= 0: {ev['track_id']!r}")
    if not isinstance(ev["frame"], int) or ev["frame"] < 0:
        raise ContractError(f"frame должен быть int >= 0: {ev['frame']!r}")
    _check_iso_timestamp(ev["timestamp"])
    _check_conf(ev["confidence"])


def validate_events(events: list[dict]) -> None:
    if not isinstance(events, list):
        raise ContractError(f"события должны быть list, получено: {type(events).__name__}")
    for i, ev in enumerate(events):
        try:
            validate_event(ev)
        except ContractError as e:
            raise ContractError(f"event[{i}]: {e}") from e


# 4. РЕЗУЛЬТАТЫ ЗАПРОСОВ БД (БД -> дашборд)

class Stats(TypedDict):
    total_persons: int
    persons_without_helmet: int
    persons_without_vest: int
    total_events: int


def validate_stats(stats: dict) -> None:
    if not isinstance(stats, dict):
        raise ContractError(f"stats должен быть dict, получено: {type(stats).__name__}")
    required = {"total_persons", "persons_without_helmet",
                "persons_without_vest", "total_events"}
    missing = required - stats.keys()
    if missing:
        raise ContractError(f"в stats не хватает полей: {missing}")
    for key in required:
        if not isinstance(stats[key], int) or stats[key] < 0:
            raise ContractError(f"stats['{key}'] должен быть int >= 0: {stats[key]!r}")


class HourlyCount(TypedDict):
    hour: str      # "2026-11-24 12:00"
    count: int


def validate_hourly_counts(rows: list[dict]) -> None:
    if not isinstance(rows, list):
        raise ContractError(f"hourly_counts должен быть list, получено: {type(rows).__name__}")
    for i, row in enumerate(rows):
        if "hour" not in row or "count" not in row:
            raise ContractError(f"hourly_counts[{i}]: нужны ключи hour и count: {row}")
        if not isinstance(row["hour"], str):
            raise ContractError(f"hourly_counts[{i}].hour должен быть str: {row['hour']!r}")
        if not isinstance(row["count"], int) or row["count"] < 0:
            raise ContractError(f"hourly_counts[{i}].count должен быть int >= 0: {row['count']!r}")

# 5. КОНФИГ (config.yaml -> код)

def _require_keys(d: dict, keys: set[str], where: str) -> None:
    missing = keys - d.keys()
    if missing:
        raise ContractError(f"config[{where}]: отсутствуют ключи {missing}")


def validate_config(cfg: dict) -> None:
    if not isinstance(cfg, dict):
        raise ContractError(f"config должен быть dict, получено: {type(cfg).__name__}")

    _require_keys(cfg, {"detection", "tracking", "database", "video"}, "root")

    det = cfg["detection"]
    _require_keys(det, {"model_path", "conf_threshold", "classes"}, "detection")
    if not isinstance(det["model_path"], str) or not det["model_path"]:
        raise ContractError("config[detection].model_path: непустая строка")
    if not isinstance(det["conf_threshold"], (int, float)) \
       or not 0.0 <= det["conf_threshold"] <= 1.0:
        raise ContractError("config[detection].conf_threshold: число в [0, 1]")
    if not isinstance(det["classes"], list) or not det["classes"]:
        raise ContractError("config[detection].classes: непустой список")
    for c in det["classes"]:
        if c not in VALID_DETECTION_CLASSES:
            raise ContractError(
                f"config[detection].classes: неизвестный класс {c!r}, "
                f"допустимо {VALID_DETECTION_CLASSES}"
            )

    trk = cfg["tracking"]
    _require_keys(trk, {"overlap_threshold"}, "tracking")
    if not isinstance(trk["overlap_threshold"], (int, float)) \
       or not 0.0 <= trk["overlap_threshold"] <= 1.0:
        raise ContractError("config[tracking].overlap_threshold: число в [0, 1]")

    db = cfg["database"]
    _require_keys(db, {"path"}, "database")
    if not isinstance(db["path"], str) or not db["path"]:
        raise ContractError("config[database].path: непустая строка")

    vid = cfg["video"]
    _require_keys(vid, {"output_dir"}, "video")
    if not isinstance(vid["output_dir"], str) or not vid["output_dir"]:
        raise ContractError("config[video].output_dir: непустая строка")