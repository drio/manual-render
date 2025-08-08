"""
Compute frames per second logic
"""

import time


class FPSCounter:
    def __init__(self):
        self.frame_count = 0
        self.last_time = time.time()
        self.current_fps = 0

    def update(self):
        self.frame_count += 1
        current_time = time.time()

        if current_time - self.last_time >= 1.0:
            self.current_fps = self.frame_count / (current_time - self.last_time)
            self.frame_count = 0
            self.last_time = current_time
            return True
        return False

    def get_fps(self):
        return self.current_fps
