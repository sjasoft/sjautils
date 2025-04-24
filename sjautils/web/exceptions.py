
class GenericWebException(Exception):
    def __init__(self, response, original_exception=None, special_processing=None):
        self.response = response
        self.original_exception = original_exception
        self._special_processing = special_processing
        super().__init__(self._message())

    def get_reason(self):
        attr_names = ["reason", "reason_phrase"]
        for attr in attr_names:
            if hasattr(self.response, attr):
                return getattr(self.response, attr)

    def reason_string(self):
        base = self.get_reason()
        return self._special_processing(base) if self._special_processing else base

    def _message(self):
        base_str = f'got exception {self.original_exception}' if self.original_exception else self.reason_string()
        return f'Web request exception: {base_str}'
