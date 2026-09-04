from app.cv.tracker import Track
import cv2

class LineCounter:
    def __init__(self, line):
        self.line = line
        self.count = 0

    def point_side(self, point):
        x, y = point
        (x1, y1), (x2, y2) = self.line

        value = ((x2 - x1) * (y - y1) - (y2 - y1) * (x - x1))

        if value > 0:
            return 1
        elif value < 0:
            return -1
        else:
            return 0

    def update(self, track):
        curr_side = self.point_side(track.center())

        if curr_side == 0:
            return None

        if track.last_side is None:
            track.last_side = curr_side
            return None

        if track.last_side == 1 and curr_side == -1:
            self.count += 1

        if track.last_side == -1 and curr_side == 1:
            self.count -= 1

        track.last_side = curr_side