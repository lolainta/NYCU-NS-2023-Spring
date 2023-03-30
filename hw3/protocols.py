from setting import Setting
from enum import Enum, auto
import random


def show_log(pkts, hist):
    print('idx:', end='')
    for i, _ in enumerate(hist[0]):
        print(f'{i//10}', end='')
    print()
    print('idx:', end='')
    for i, _ in enumerate(hist[0]):
        print(f'{i%10}', end='')
    print()

    for idx, h in enumerate(hist):
        print(f'h{idx}:', ''.join(['V' if t in pkts[idx] else ' '
                                   for t in range(len(hist[0]))]))
        print(f'h{idx}:', ''.join(h))


class State(Enum):
    IDLE = auto()
    START = auto()
    SEND = auto()
    DETECTED = auto()
    STOP = auto()
    WAIT = auto()


class Host():
    def __init__(self, pkts: list, link_delay: int = 0) -> None:
        self.history: list[str] = list()
        self.histat: list[State] = list()
        self.state: State = State.IDLE
        self.pkts: list = pkts
        self.queue: int = 0
        self.sending: int = 0
        self.detect: bool = False
        self.wait: int = 0
        self.finished: int = 0
        self.delay = link_delay

    def commit(self) -> None:
        self.histat.append(self.state)
        self.history.append(self._s2s(self.state))

    def delayed_state(self) -> State:
        if len(self.histat) < self.delay:
            return State.IDLE
        return self.histat[-self.delay]

    @staticmethod
    def _s2s(state: State) -> str:
        if state in [State.IDLE, State.WAIT]:
            return '.'
        elif state == State.START:
            return '<'
        elif state == State.SEND:
            return '-'
        elif state == State.DETECTED:
            return '|'
        elif state == State.STOP:
            return '>'
        else:
            assert False, "Unknown state"


def analyse(conf: Setting, hist: list):
    n, m = len(hist[0]), len(hist)
    idle = sum([all([hist[h][t] == '.' for h in range(m)]) for t in range(n)])
    suc = sum([hist[h][t] == '>' for h in range(m)
              for t in range(n)])*conf.packet_time

    col = conf.total_time-idle-suc
    return suc/conf.total_time, idle/conf.total_time, col/conf.total_time


def decision(conf: Setting, hosts: list[Host], t: int):
    for host in hosts:
        if t in host.pkts:
            host.queue += 1
        if host.state == State.WAIT:
            assert host.queue > 0
            host.wait -= 1
            if host.wait == 0:
                host.state = State.START
                host.sending = conf.packet_time-1
                host.detect = False
        elif host.state == State.IDLE:
            if host.queue > 0:
                host.state = State.START
                host.sending = conf.packet_time-1
                host.detect = False
        elif host.state == State.START:
            host.state = State.SEND
        elif host.state == State.SEND:
            host.sending -= 1
            if host.sending == 1:
                host.state = State.STOP
        elif host.state == State.DETECTED:
            host.wait = random.randint(
                0, conf.max_colision_wait_time)
            if host.wait == 0:
                host.state = State.START
                host.sending = conf.packet_time-1
                host.detect = False
            else:
                host.state = State.WAIT
        elif host.state == State.STOP:
            host.queue -= 1
            if host.queue > 0:
                host.state = State.START
                host.sending = conf.packet_time-1
                host.detect = False
            else:
                host.state = State.IDLE
        else:
            assert False, 'Unknown state'


def aloha(setting: Setting, show_history=False):
    pkts = setting.gen_packets()
    # print(pkts)
    hosts = [Host(pkt) for pkt in pkts]
    for t in range(setting.total_time):
        decision(setting, hosts, t)
        for host in hosts:
            if host.state in [State.START, State.SEND, State.STOP]:
                for nei in hosts:
                    if nei != host:
                        nei.detect = True

        for host in hosts:
            if host.state == State.STOP:
                if host.detect == True:
                    host.state = State.DETECTED

        # print(f'{t=}', end='\t')
        for host in hosts:
            # print(f'{host.state:15}', end='')
            host.commit()
        # print()

    history = [host.history for host in hosts]
    if show_history:
        show_log(pkts, history)

    return analyse(setting, history)


def slotted_aloha(setting: Setting, show_history=False):
    pkts = setting.gen_packets()
    # print(pkts)
    hosts = [Host(pkt) for pkt in pkts]
    for t in range(setting.total_time):
        decision(setting, hosts, t)

        for host in hosts:
            if host.state == State.STOP:
                if host.detect == True:
                    host.state = State.DETECTED
            elif host.state == State.START:
                if t % setting.packet_time != 0:
                    host.state = State.WAIT
                    host.wait = (setting.packet_time-t) % setting.packet_time

        for host in hosts:
            if host.state in [State.START, State.SEND, State.STOP]:
                for nei in hosts:
                    if nei != host:
                        nei.detect = True
        # print(f'{t=}', end='\t')
        for host in hosts:
            # print(f'{host.state:15}', end='')
            host.commit()
        # print()

    history = [host.history for host in hosts]
    if show_history:
        show_log(pkts, history)

    return analyse(setting, history)


def csma(setting: Setting, show_history=False):
    pkts = setting.gen_packets()
    # print(pkts)
    hosts = [Host(pkt, setting.link_delay) for pkt in pkts]
    for t in range(setting.total_time):
        decision(setting, hosts, t)
        for host in hosts:
            if host.state == State.STOP:
                if host.detect == True:
                    host.state = State.DETECTED
            elif host.state == State.START:
                for nei in hosts:
                    if nei != host:
                        if nei.delayed_state() in [State.START, State.SEND]:
                            host.wait = random.randint(
                                1, setting.max_colision_wait_time)
                            host.state = State.WAIT
                            # print(f'{t=} {host=} detected {host.wait=}')

        for host in hosts:
            if host.state in [State.START, State.SEND, State.STOP]:
                for nei in hosts:
                    if nei != host:
                        nei.detect = True

        # print(f'{t=}', end='\t')
        for host in hosts:
            # print(f'{host.state:15}', end='')
            host.commit()
        # print()

    history = [host.history for host in hosts]
    if show_history:
        show_log(pkts, history)

    return analyse(setting, history)


def csma_cd(setting: Setting, show_history=False):
    pkts = setting.gen_packets()
    # print(pkts)
    hosts = [Host(pkt, setting.link_delay) for pkt in pkts]
    for t in range(setting.total_time):
        decision(setting, hosts, t)
        for host in hosts:
            if host.state == State.STOP:
                if host.detect == True:
                    host.state = State.DETECTED
            elif host.state == State.START:
                for nei in hosts:
                    if nei != host:
                        if nei.delayed_state() in [State.START, State.SEND]:
                            host.wait = random.randint(
                                1, setting.max_colision_wait_time)
                            host.state = State.WAIT
                            # print(f'{t=} {host=} detected {host.wait=}')
            elif host.state == State.SEND:
                for nei in hosts:
                    if nei != host and nei.delayed_state() in [State.START, State.SEND, State.STOP]:
                        host.state = State.DETECTED
                        host.sending = 0
                        host.detect = False
                pass

        for host in hosts:
            if host.state in [State.START, State.SEND, State.STOP]:
                for nei in hosts:
                    if nei != host:
                        nei.detect = True

        # print(f'{t=}', end='\t')
        for host in hosts:
            # print(f'{host.state:15}', end='')
            host.commit()
        # print()

    history = [host.history for host in hosts]
    if show_history:
        show_log(pkts, history)

    return analyse(setting, history)
