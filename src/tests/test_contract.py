import pytest
from src.common.contract import (
    validate_detection, validate_tracked_object,
    validate_event, validate_stats, validate_config,
)
from src.common.errors import ContractError


def test_valid_detection_ok():
    validate_detection({"cls": "person", "bbox": [0, 0, 10, 20], "conf": 0.9})


@pytest.mark.parametrize("bad", [
    {"cls": "cat", "bbox": [0, 0, 10, 20], "conf": 0.9},          # неизвестный класс
    {"cls": "person", "bbox": [0, 0, 10], "conf": 0.9},            # короткий bbox
    {"cls": "person", "bbox": [10, 0, 0, 20], "conf": 0.9},        # x1 > x2
    {"cls": "person", "bbox": [0, 0, 10, 20], "conf": 1.5},        # conf вне [0,1]
    {"cls": "person", "bbox": [0, 0, 10, 20]},                     # нет conf
])
def test_bad_detection_raises(bad):
    with pytest.raises(ContractError):
        validate_detection(bad)


def test_person_requires_track_id():
    with pytest.raises(ContractError):
        validate_tracked_object({"cls": "person", "bbox": [0, 0, 1, 1], "conf": 0.5})


def test_helmet_must_not_have_track_id():
    with pytest.raises(ContractError):
        validate_tracked_object(
            {"cls": "helmet", "bbox": [0, 0, 1, 1], "conf": 0.5, "track_id": 3}
        )


def test_bad_timestamp_raises():
    with pytest.raises(ContractError):
        validate_event({
            "track_id": 1, "event_type": "helmet_off",
            "frame": 10, "timestamp": "вчера", "confidence": 0.9,
        })


def test_unknown_event_type_raises():
    with pytest.raises(ContractError):
        validate_event({
            "track_id": 1, "event_type": "helmet_down",  # опечатка
            "frame": 10, "timestamp": "2026-11-24T12:00:00", "confidence": 0.9,
        })


def test_stats_empty_db_is_valid():
    validate_stats({
        "total_persons": 0, "persons_without_helmet": 0,
        "persons_without_vest": 0, "total_events": 0,
    })


def test_config_missing_section_raises():
    with pytest.raises(ContractError):
        validate_config({"detection": {}, "tracking": {}, "database": {}})