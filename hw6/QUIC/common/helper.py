class Pointer:
    def __init__(self, v=0) -> None:
        self.v = v

    def __add__(self, other):
        self.v += other
        return self.v

    def lookahead(self, v):
        return self.v + v

class HeapNode:
    def __init__(self, k, v) -> None:
        self.k = k
        self.v = v

    def __lt__(self, other) -> bool:
        return self.k < other.k

    def __gt__(self, other) -> bool:
        return self.k > other.k

    def __eq__(self, other) -> bool:
        return self.k == other.k and self.v == other.v

class Buffer:
    def __init__(self, size) -> None:
        self.size = size
        self._buf = []

    def get_buf(self):
        return self._buf

    def is_full(self):
        return len(self._buf) == self.size

    def get_size(self):
        return self.size

    def double_size(self):
        self.size += self.size

    def halve_size(self):
        self.size = self.size // 2

    def add_size(self):
        self.size += 1