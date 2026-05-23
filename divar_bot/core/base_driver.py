class BaseDriver:
    def connect(self):
        raise NotImplementedError

    def extract(self):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError
