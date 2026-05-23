class Scheduler:
    def __init__(self):
        self.schedules = []

    def register(self, schedule):
        self.schedules.append(schedule)
