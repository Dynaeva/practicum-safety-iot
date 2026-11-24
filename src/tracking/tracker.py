def track(objects: list[dict], frame_idx: int) -> list[dict]:
    """Заглушка -> добавитт ByteTrack и track_id для person"""
    return objects

# from src.common.contract import validate_detections, validate_tracked_objects

# def track(objects, frame_idx):
#     validate_detections(objects)        # на входе — контракт детекции
#     result = [...]                       # ByteTrack + track_id
#     validate_tracked_objects(result)    # на выходе — контракт трекинга
#     return result