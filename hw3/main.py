from protocols import aloha, slotted_aloha, csma, csma_cd
from setting import Setting
import matplotlib.pyplot as plt
import os

SEED = 4


def main():
    conf = Setting(host_num=3,
                   total_time=100,
                   packet_num=4,
                   max_colision_wait_time=20,
                   p_resend=0.3,
                   packet_size=3,
                   link_delay=1,
                   seed=SEED)

    print('Question 0')
    print(f'aloha:')
    success_rate, idle_rate, collision_rate = aloha(conf, True)
    print(f'aloha: {success_rate=}, {idle_rate=}, {collision_rate=}')
    print()
    print(f'slotted_aloha:')
    success_rate, idle_rate, collision_rate = slotted_aloha(conf, True)
    print(f'slotted_aloha: {success_rate=}, {idle_rate=}, {collision_rate=}')
    print()
    print(f'csma:')
    success_rate, idle_rate, collision_rate = csma(conf, True)
    print(f'csma: {success_rate=}, {idle_rate=}, {collision_rate=}')
    print()
    print(f'csma_cd:')
    success_rate, idle_rate, collision_rate = csma_cd(conf, True)
    print(f'csma_cd: {success_rate=}, {idle_rate=}, {collision_rate=}')

    os.makedirs('results', exist_ok = True)

    print('Question 1')
    host_num_list = [2, 3, 4, 6]
    packet_num_list = [2400//hnum for hnum in host_num_list]
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for h, p in zip(host_num_list, packet_num_list):
        conf = Setting(host_num=h, packet_num=p,
                       max_colision_wait_time=20, p_resend=0.3, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, host_num_list, 'q1', 'Host Num')

    print('Question 3')
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for h, p in zip(host_num_list, packet_num_list):
        conf = Setting(host_num=h, packet_num=p, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, host_num_list, 'q3', 'Host Num')

    print('Question 4')
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for c in range(1, 31, 1):
        print(f'{c=}', end='\r')
        conf = Setting(c=c, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, range(1, 31, 1), 'q4', 'Coefficient')

    print('Question 5')
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for p in range(100, 1050, 50):
        print(f'{p=}', end='\r')
        conf = Setting(packet_num=p, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, range(100, 1050, 50), 'q5', 'Packet Num')

    print('Question 6')
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for h in range(1, 20):
        print(f'{h=}', end='\r')
        conf = Setting(host_num=h, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, range(1, 20), 'q6', 'Host Num')

    print('Question 7')
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for sz in range(1, 20):
        print(f'{sz=}', end='\r')
        conf = Setting(packet_size=sz, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, range(1, 20), 'q7', 'Packet Size')

    print('Question 8')
    link_delay_list = [0, 1, 2, 3]
    packet_size_list = [7-2*l for l in link_delay_list]
    succ, idle, coli = [[[] for _ in range(4)] for _ in range(3)]
    for l, sz in zip(link_delay_list, packet_size_list):
        conf = Setting(link_delay=l, packet_size=sz, seed=SEED)
        run(succ, idle, coli, conf)
    plot(succ, idle, coli, link_delay_list, 'q8', 'Link Delay')


def run(succ: list[list], idle: list[list], coli: list[list], conf: Setting) -> None:
    scc, idl, col = aloha(conf, False)
    succ[0].append(scc)
    idle[0].append(idl)
    coli[0].append(col)
    scc, idl, col = slotted_aloha(conf, False)
    succ[1].append(scc)
    idle[1].append(idl)
    coli[1].append(col)
    scc, idl, col = csma(conf, False)
    succ[2].append(scc)
    idle[2].append(idl)
    coli[2].append(col)
    scc, idl, col = csma_cd(conf, False)
    succ[3].append(scc)
    idle[3].append(idl)
    coli[3].append(col)


def plot(succ: list[list], idle: list[list], coli: list[list], x, prefix: str, influence: str):
    # print(succ, idle, coli, sep='\n')

    fig, ax = plt.subplots()

    # Success
    for i in range(4):
        ax.plot(x, succ[i], marker=10)
    ax.set_title(f'Infulence of {influence}')
    ax.set_ylabel('Success Rate')
    ax.set_xlabel(influence)
    ax.legend(['aloha', 'slotted aloha', 'csma', 'csma/cd'])
    fig.savefig(f'results/{prefix}_success.png')

    # Idle
    ax.cla()
    for i in range(4):
        ax.plot(x, idle[i], marker=10)
    ax.set_title(f'Infulence of {influence}')
    ax.set_ylabel('Idle Rate')
    ax.set_xlabel(influence)
    ax.legend(['aloha', 'slotted aloha', 'csma', 'csma/cd'])
    fig.savefig(f'results/{prefix}_idle.png')

    # Collision
    ax.cla()
    for i in range(4):
        ax.plot(x, coli[i], marker=10)
    ax.set_title(f'Infulence of {influence}')
    ax.set_ylabel('Collision Rate')
    ax.set_xlabel(influence)
    ax.legend(['aloha', 'slotted aloha', 'csma', 'csma/cd'])
    fig.savefig(f'results/{prefix}_collision.png')


if __name__ == '__main__':
    main()
