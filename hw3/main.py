from protocols import aloha, slotted_aloha, csma, csma_cd
from setting import Setting
import matplotlib.pyplot as plt

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

    host_num_list = [2, 3, 4, 6]
    packet_num_list = [2400//hnum for hnum in host_num_list]

    succ, idle, coli = [[[] for _ in range(4)] for __ in range(3)]

    for h, p in zip(host_num_list, packet_num_list):
        conf = Setting(host_num=h, packet_num=p,
                       max_colision_wait_time=20, p_resend=0.3, seed=SEED)
        run(succ, idle, coli, conf)

    plot(succ, idle, coli, host_num_list)


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


def plot(succ: list[list], idle: list[list], coli: list[list], x: list):
    # print(succ, idle, coli, sep='\n')

    fig, ax = plt.subplots()

    # Success
    for i in range(4):
        ax.plot(x, succ[i])
    ax.set_title('Infulence of Host Num')
    ax.set_ylabel('Success Rate')
    ax.set_xlabel('Host Num')
    ax.legend(['aloha', 'slotted aloha', 'csma', 'csma/cd'])
    fig.savefig('success.png')

    # Idle
    ax.cla()
    for i in range(4):
        ax.plot(x, idle[i])
    ax.set_title('Infulence of Host Num')
    ax.set_ylabel('Idle Rate')
    ax.set_xlabel('Host Num')
    ax.legend(['aloha', 'slotted aloha', 'csma', 'csma/cd'])
    fig.savefig('idle.png')

    # Collision
    ax.cla()
    for i in range(4):
        ax.plot(x, coli[i])
    ax.set_title('Infulence of Host Num')
    ax.set_ylabel('Collision Rate')
    ax.set_xlabel('Host Num')
    ax.legend(['aloha', 'slotted aloha', 'csma', 'csma/cd'])
    fig.savefig('collision.png')


if __name__ == '__main__':
    main()
