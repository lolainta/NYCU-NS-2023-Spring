from protocols import aloha, slotted_aloha, csma
from setting import Setting


def main():
    conf = Setting(host_num=3,
                   total_time=100,
                   packet_num=4,
                   max_colision_wait_time=20,
                   p_resend=0.3,
                   packet_size=3,
                   link_delay=1,
                   seed=4)

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


if __name__ == '__main__':
    main()
