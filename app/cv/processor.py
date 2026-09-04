from app.cv.draw import draw_detection
from app.cv.tracker import IoUTracker, counting_line, conveyor_roi
from app.cv.counter import LineCounter
from app.cv.monitor import AnomalyMonitor, forward_vector
import cv2
from pathlib import Path
from mmdet.apis import inference_detector


def process_video(video_path, out_path, model, threshold=0.36, max_frames=None):
    cap = cv2.VideoCapture(str(video_path))

    if not cap.isOpened():
        raise RuntimeError("failed to open video:", video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    frames_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"FPS: {fps}")
    print(f"Res: {width}x{height}")
    print(f"Frames: {frames_count}")

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(out_path), fourcc, fps, (width, height))

    if not writer.isOpened():
        cap.release()
        raise RuntimeError("failed to create video", out_path)

    tracker = IoUTracker(iou_threshold=0.3, max_missed=3, min_hits=3)

    frame_index = 0
    counter = LineCounter(counting_line)
    monitor = AnomalyMonitor()

    while True:
        ret, frame = cap.read()

        if not ret:
            break

        if max_frames is not None and frame_index >= max_frames:
            break

        result = inference_detector(model, frame)
        annotation, track_detections = draw_detection(frame, result, conveyor_roi, threshold=threshold)
        tracks = tracker.update(track_detections)
        monitor.update_motion(tracks, forward_vector, frame_index, fps)

        for track in tracks:
            if not track.confirmed:
                continue

            x1, y1, x2, y2 = track.bbox.astype(int)

            counter.update(track)

            cv2.putText(annotation, f"ID {track.id}", (x1, y2 + 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        cv2.putText(annotation, f"Bags count: {counter.count}",
                    (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        for anomaly_name in monitor.active:
            cv2.putText(annotation, f"ANOMALY: {anomaly_name}",
                        (360, 300), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        writer.write(annotation)
        frame_index += 1

    cap.release()
    writer.release()
    print("done")

    return {
        "count": counter.count,
        "anomalies": monitor.anomalies
    }