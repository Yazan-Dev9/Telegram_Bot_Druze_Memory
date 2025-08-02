import datetime


class DateValidator:
    @staticmethod
    def validate_date(date_text):
        try:
            datetime.datetime.strptime(date_text, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    @staticmethod
    def is_future_date(date_text):
        if not DateValidator.validate_date(date_text):
            return False
        try:
            date = datetime.datetime.strptime(date_text, "%Y-%m-%d").date()
            today = datetime.date.today()
            return date > today
        except ValueError:
            return False
