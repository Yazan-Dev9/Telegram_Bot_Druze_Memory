import datetime


class SpamFilter:
    def __init__(self, threshold=3, time_window=5):
        self.threshold = threshold
        self.time_window = time_window
        self.user_messages = {}

    def is_spam(self, message):
        user_id = message.from_user.id
        now = message.date
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []

        recent_messages = [
            msg_time
            for msg_time in self.user_messages[user_id]
            if now - msg_time < datetime.timedelta(seconds=self.time_window)
        ]

        recent_messages.append(now)
        self.user_messages[user_id] = recent_messages

        if len(recent_messages) > self.threshold:
            return True
        else:
            return False


spam_filter = SpamFilter()
