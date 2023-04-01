import random


class Setting():
    def __init__(self,
                 host_num: int = 3,
                 total_time: int = 10000,
                 packet_num: int = 500,
                 packet_size: int = 5,
                 max_colision_wait_time: None | int = None,
                 p_resend: None | float = None,
                 c: int = 8,
                 link_delay: int = 1,
                 seed: int | None = None
                 ) -> None:
        self.host_num = host_num
        self.total_time = total_time
        self.packet_num = packet_num
        self.packet_time = packet_size + 2*link_delay
        self.max_colision_wait_time = self.packet_time * \
            c if max_colision_wait_time is None else max_colision_wait_time
        self.p_resend = 1/c if p_resend is None else p_resend
        self.link_delay = link_delay
        if seed is None:
            self.seed = random.randint(1, 10000)
            print(f'Use randomn seed {self.seed}')
        else:
            self.seed = seed

    def gen_packets(self):
        random.seed(self.seed)
        packets = [[]]*self.host_num
        for i in range(self.host_num):
            packets[i] = random.sample(
                range(1, self.total_time-self.packet_time), self.packet_num)
            packets[i].sort()
        return packets
