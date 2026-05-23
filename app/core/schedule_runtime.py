from datetime import datetime


class ScheduleRuntime:
    def __init__(self, schedules=None):
        self.schedules = schedules or []

    def is_allowed(self, current_time=None):
        current_time = current_time or datetime.now().strftime('%H:%M')

        if not self.schedules:
            return True

        for schedule in self.schedules:
            start = schedule.get('start')
            end = schedule.get('end')

            if start <= current_time <= end:
                return True

        return False
