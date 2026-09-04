import numpy as np
from app.cv.tracker import Track
import cv2

conveyor_roi = np.array([
    [0, 360],
    [310, 28],
    [484, 65],
    [315, 360],
], dtype=np.int32)

def get_forward_vector(roi):
    top_center = np.array([(roi[1][0] + roi[2][0]) / 2, (roi[1][1] + roi[2][1]) / 2], dtype = float)

    bottom_center = np.array([(roi[0][0] + roi[3][0]) / 2, (roi[0][1] + roi[3][1]) / 2], dtype = float)

    vector = top_center - bottom_center
    return vector / np.linalg.norm(vector)

forward_vector = get_forward_vector(conveyor_roi)

class AnomalyMonitor:
    def __init__(self, motion_window = 10, movement_threshold = 0.2, reverse_confirm_sec = 0.5, stop_confirm_sec = 2.0):
        self.anomalies = []
        self.active = {}

        self.motion_window = motion_window
        self.movement_threshold = movement_threshold

        self.reverse_confirm_sec = reverse_confirm_sec
        self.stop_confirm_sec = stop_confirm_sec

        self.reverse_frames = 0
        self.stopped_frames = 0


    def get_motion_state(self, track, forward_vector):
        window = self.motion_window

        if len(track.history) < window + 1:
            return None

        prev = np.array(track.history[-window - 1], dtype = float)
        curr = np.array(track.history[-1], dtype = float)

        movement = curr - prev
        speed = (np.linalg.norm(movement) / window)
        projection = (np.dot(movement, forward_vector) / window)

        if speed < self.movement_threshold:
            return "stationary"

        if projection > 0:
            return "forward"

        return "reverse"

    def activate(self, name, frame_index, fps):
        if name in self.active:
            return

        anomaly = {
            "type": name,
            "start_frame": frame_index,
            "start_time": frame_index / fps,
            "end_frame": None,
            "end_time": None
        }

        self.active[name] = anomaly
        self.anomalies.append(anomaly)

    def resolve(self, name, frame_index, fps):
        if name not in self.active:
            return

        anomaly = self.active[name]

        anomaly['end_frame'] = frame_index
        anomaly['end_time'] = frame_index / fps

        del self.active[name]

    def update_motion(self, tracks, forward_vector, frame_index, fps):
        states = []

        for track in tracks:
            if not track.confirmed:
                continue

            state = self.get_motion_state(track, forward_vector)

            if state is None:
                continue

            if state in ("forward", "reverse"):
                track.moving = True

            if state == "stationary" and not track.moving:
                continue

            states.append(state)

        if len(states) == 0:
            return

        forward_count = states.count("forward")
        reverse_count = states.count("reverse")
        stationary_count = states.count("stationary")

        total = len(states)

        is_reverse = (reverse_count > forward_count and reverse_count > stationary_count)

        if is_reverse:
            self.reverse_frames += 1
        else:
            self.reverse_frames = 0

        reverse_confirm = int(self.reverse_confirm_sec * fps)

        if self.reverse_frames >= reverse_confirm:
            self.activate("conveyor reverse", frame_index, fps)

        is_forward = (forward_count > reverse_count and forward_count > stationary_count)

        if ("conveyor reverse" in self.active and is_forward):
            self.resolve("conveyor reverse", frame_index, fps)

        is_stopped = (stationary_count == total)

        if is_stopped:
            self.stopped_frames += 1
        else:
            self.stopped_frames = 0

        stop_confirm = int(self.stop_confirm_sec * fps)

        if self.stopped_frames >= stop_confirm:
            self.activate("conveyor stopped", frame_index, fps)

        is_moving = (forward_count > 0 or reverse_count > 0)

        if ("conveyor stopped" in self.active and is_moving):
            self.resolve("conveyor stopped", frame_index, fps)