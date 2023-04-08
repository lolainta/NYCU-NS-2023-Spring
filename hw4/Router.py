from heapq import heappush, heappop


class OSPFRouter():
    def __init__(self, id: int, link_state: list) -> None:
        self.id = id
        self.sz = len(link_state)
        self.map = [[]]*self.sz
        self.map[id] = link_state
        self.neighbors = [i for i in range(len(link_state))
                          if link_state[i] != 999 and i != self.id
                          ]

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
