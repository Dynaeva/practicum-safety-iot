""" !!! БЕЗ ПРОВЕРКИ НА ПРАВИЛЬНОСТЬ КОНТРАКТОВ !!! """

import argparse

import cv2

from src.detection.detector import detect
from src.tracking.tracker import track
from src.db.database import init_db, save_events


def build_events(objects: list[dict], frame_idx: int) -> list[dict]:
    """Заглушка: Ксюша заменит на реальную логику событий."""
    return []


def draw(frame, objects: list[dict]):
    for obj in objects:
        x1, y1, x2, y2 = map(int, obj["bbox"])
        color = (0, 255, 0) if obj["cls"] == "person" else (0, 165, 255)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = obj["cls"]
        if "track_id" in obj:
            label += f' #{obj["track_id"]}'
        cv2.putText(frame, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)


def run(video_path: str, show: bool = True):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise FileNotFoundError(f"Не удалось открыть видео: {video_path}")

    init_db()
    frame_idx = 0

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        detections = detect(frame)               # список dict по контракту
        tracked = track(detections, frame_idx)   # + track_id у person
        events = build_events(tracked, frame_idx)
        save_events(events)

        if show:
            draw(frame, tracked)
            cv2.imshow("PPE detection", frame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        frame_idx += 1

    cap.release()
    cv2.destroyAllWindows()
    print(f"Готово. Обработано кадров: {frame_idx}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, help="путь к видео")
    parser.add_argument("--no-show", action="store_true", help="без окна")
    args = parser.parse_args()

    run(args.video, show=not args.no_show)