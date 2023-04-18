from Router import OSPFRouter, RIPRouter


def run_ospf(link_cost: list) -> tuple[list, list]:
    sz = len(link_cost)
    routers = [OSPFRouter(i, link_cost[i]) for i in range(sz)]
    hist = list()
    while any([any([len(ls) == 0 for ls in router.map]) for router in routers]):
        # print('Round Start')
        rhist = list()
        for i in range(sz):
            roundRouters = [
                router for router in routers if len(router.map[i]) != 0
            ]
            for router in roundRouters:
                for neid in router.neighbors:
                    nei = routers[neid]
                    if len(nei.map[i]) == 0:
                        nei.map[i] = router.map[i]
                        rhist.append((router.id, i, nei.id))
        rhist = sorted(rhist)
        hist.extend(rhist)
    return ([routers[i].solve() for i in range(sz)], hist)


def run_rip(link_cost: list) -> tuple[list, list]:
    sz = len(link_cost)
    routers = [RIPRouter(i, link_cost[i]) for i in range(sz)]
    hist = list()
    while any([router.changed for router in routers]):
        # print('Round Start')
        roundRouter = [router for router in routers if router.changed]
        for router in roundRouter:
            for neid in router.neighbors:
                nei = routers[neid]
                nei.update(router.id, router.map[router.id])
                hist.append((router.id, nei.id))
        for router in routers:
            router.commit()
    return ([router.map[router.id] for router in routers], hist)


def check(link_cost: list):
    sz = len(link_cost)
    for i in range(sz):
        assert sz == len(
            link_cost[i]), f'ERROR: Data length invalid {link_cost}'
        for j in range(sz):
            assert link_cost[i][j] == link_cost[j][
                i], f'ERROR: Data not symmetric on [{i}][{j}]'


def main():
    mini_data = [
        [
            [0, 2, 5, 1, 999, 999],
            [2, 0, 3, 2, 999, 999],
            [5, 3, 0, 3, 1, 5],
            [1, 2, 3, 0, 1, 999],
            [999, 999, 1, 1, 0, 2],
            [999, 999, 5, 999, 2, 0]
        ]
    ]
    mini_ospf = (
        [
            [0, 2, 3, 1, 2, 4],
            [2, 0, 3, 2, 3, 5],
            [3, 3, 0, 2, 1, 3],
            [1, 2, 2, 0, 1, 3],
            [2, 3, 1, 1, 0, 2],
            [4, 5, 3, 3, 2, 0]
        ],
        [
            (0, 0, 1), (0, 0, 2), (0, 0, 3),
            (1, 1, 0), (1, 1, 2), (1, 1, 3),
            (2, 2, 0), (2, 2, 1), (2, 2, 3), (2, 2, 4), (2, 2, 5),
            (3, 3, 0), (3, 3, 1), (3, 3, 2), (3, 3, 4),
            (4, 4, 2), (4, 4, 3), (4, 4, 5),
            (5, 5, 2), (5, 5, 4),
            (2, 0, 4), (2, 0, 5),
            (2, 1, 4), (2, 1, 5),
            (2, 3, 5),
            (2, 4, 0), (2, 4, 1),
            (2, 5, 0), (2, 5, 1), (2, 5, 3)
        ]
    )
    mini_rip = (
        [
            [0, 2, 3, 1, 2, 4],
            [2, 0, 3, 2, 3, 5],
            [3, 3, 0, 2, 1, 3],
            [1, 2, 2, 0, 1, 3],
            [2, 3, 1, 1, 0, 2],
            [4, 5, 3, 3, 2, 0]
        ],
        [
            (0, 1), (0, 2), (0, 3),
            (1, 0), (1, 2), (1, 3),
            (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
            (3, 0), (3, 1), (3, 2), (3, 4),
            (4, 2), (4, 3), (4, 5),
            (5, 2), (5, 4),
            (0, 1), (0, 2), (0, 3),
            (1, 0), (1, 2), (1, 3),
            (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
            (3, 0), (3, 1), (3, 2), (3, 4),
            (4, 2), (4, 3), (4, 5),
            (5, 2), (5, 4),
            (0, 1), (0, 2), (0, 3),
            (1, 0), (1, 2), (1, 3),
            (2, 0), (2, 1), (2, 3), (2, 4), (2, 5),
            (5, 2), (5, 4)
        ]
    )
    assert mini_ospf == run_ospf(mini_data[0]), 'OSPF Failed on mini_data'
    assert mini_rip == run_rip(mini_data[0]), 'RIP Failed on mini_data'

if __name__ == '__main__':
    main()
