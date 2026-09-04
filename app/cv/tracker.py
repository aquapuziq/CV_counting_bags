import numpy as np
import cv2

conveyor_roi = np.array([
    [0, 360],
    [310, 28],
    [484, 65],
    [315, 360],
], dtype=np.int32)

def interpolate(p1, p2, coeff):
    x = p1[0] + (p2[0] - p1[0]) * coeff
    y = p1[1] + (p2[1] - p1[1]) * coeff

    return int(x), int(y)

line_pos_coeff = 0.35

left_point = interpolate(conveyor_roi[1], conveyor_roi[0], line_pos_coeff)
right_point = interpolate(conveyor_roi[2], conveyor_roi[3], line_pos_coeff)

counting_line = (left_point, right_point)


def bbox_iou(bbox1, bbox2):
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    inter_width = max(0, x2 - x1)
    inter_height = max(0, y2 - y1)

    area1 = max(0, bbox1[2] - bbox1[0]) * max(0, bbox1[3] - bbox1[1])
    area2 = max(0, bbox2[2] - bbox2[0]) * max(0, bbox2[3] - bbox2[1])

    intersection = inter_width * inter_height
    union = area1 + area2 - intersection

    if union == 0:
        return 0.0

    return intersection / union


class Track:
    def __init__(self, track_id, bbox, score):
        self.id = track_id
        self.bbox = np.array(bbox, dtype=float)
        self.score = float(score)

        self.hits = 1
        self.missed = 0
        self.age = 1
        self.confirmed = False
        self.history = [self.center()]

        self.last_side = None
        self.moving = False

    def center(self):
        x1, y1, x2, y2 = self.bbox

        return (float((x1 + x2) / 2), float((y1 + y2) / 2))

    def update(self, bbox, score):
        self.bbox = np.array(bbox, dtype=float)
        self.score = float(score)

        self.hits += 1
        self.missed = 0
        self.age += 1
        self.history.append(self.center())

    def mark_missed(self):
        self.missed += 1
        self.age += 1


class IoUTracker:
    def __init__(self, iou_threshold=0.3, max_missed=3, min_hits=3):
        self.iou_threshold = iou_threshold
        self.max_missed = max_missed
        self.min_hits = min_hits

        self.tracks = []
        self.next_id = 1

    def create_track(self, detection):
        track = Track(track_id=self.next_id, bbox=detection['bbox'], score=detection['score'])

        self.next_id += 1
        self.tracks.append(track)

    def update(self, detections):
        if len(self.tracks) == 0:
            for detection in detections:
                self.create_track(detection)

            self.update_accepted()
            return self.tracks

        if len(detections) == 0:
            for track in self.tracks:
                track.mark_missed()

            self.remove_dead_tracks()
            self.update_accepted()
            return self.tracks

        iou_matrix = np.zeros((len(self.tracks), len(detections)), dtype=float)

        for track_index, track in enumerate(self.tracks):
            for detection_index, detection in enumerate(detections):
                iou_matrix[track_index, detection_index] = bbox_iou(track.bbox, detection['bbox'])

        matched_tracks = set()
        matched_detections = set()

        while True:
            track_index, detection_index = np.unravel_index(np.argmax(iou_matrix), iou_matrix.shape)

            best_iou = iou_matrix[track_index, detection_index]
            if best_iou < self.iou_threshold:
                break

            track = self.tracks[track_index]
            detection = detections[detection_index]

            track.update(detection['bbox'], detection['score'])

            matched_tracks.add(track_index)
            matched_detections.add(detection_index)

            iou_matrix[track_index, :] = -1
            iou_matrix[:, detection_index] = -1

        for track_index, track in enumerate(self.tracks):
            if track_index not in matched_tracks:
                track.mark_missed()

        for detection_index, detection in enumerate(detections):
            if detection_index not in matched_detections:
                self.create_track(detection)

        self.remove_dead_tracks()
        self.update_accepted()

        return self.tracks

    def remove_dead_tracks(self):
        self.tracks = [track for track in self.tracks if track.missed <= self.max_missed]

    def update_accepted(self):
        for track in self.tracks:
            if track.hits >= self.min_hits:
                track.confirmed = True

