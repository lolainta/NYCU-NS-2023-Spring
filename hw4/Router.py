from heapq import heappush, heappop
from copy import deepcopy


class Router():
    def __init__(self, id: int, link_state: list) -> None:
        self.id = id
        self.sz = len(link_state)
        self.neighbors = [i for i in range(len(link_state))
                          if link_state[i] != 999 and i != self.id
                          ]


class OSPFRouter(Router):
    def __init__(self, id: int, link_state: list) -> None:
        super().__init__(id, link_state)
        self.map = [[]]*self.sz
        self.map[id] = link_state

    def solve(self) -> list:
        ret = [999]*self.sz
        pq = list()
        heappush(pq, (0, self.id))
        while len(pq) != 0:
            top = heappop(pq)
            if ret[top[1]] == 999:
                ret[top[1]] = top[0]
            for neid in [i for i, dis in enumerate(self.map[top[1]]) if dis != 999]:
                if ret[neid] == 999:
                    heappush(pq, (top[0]+self.map[top[1]][neid], neid))
        return ret


class RIPRouter(Router):
    def __init__(self, id: int, link_state: list) -> None:
        super().__init__(id, link_state)
        self.map = [[999 for _ in range(self.sz)] for _ in range(self.sz)]
        self.map[self.id] = link_state
        self.changed = True

    def update(self, src: int, vector: list):
        assert src != self.id
        self.map[src] = deepcopy(vector)

    def commit(self):
        self.changed = False
        for i in range(self.sz):
            for j in range(self.sz):
                if self.map[self.id][i] > self.map[self.id][j]+self.map[j][i]:
                    self.map[self.id][i] = \
                        self.map[self.id][j] + self.map[j][i]
                    self.changed = True
