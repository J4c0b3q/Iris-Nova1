class Cache:

    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key, default=None):
        return self.data.get(key, default)

    def delete(self, key):
        self.data.pop(key, None)

    def clear(self):
        self.data.clear()

    def has(self, key):
        return key in self.data

    def size(self):
        return len(self.data)