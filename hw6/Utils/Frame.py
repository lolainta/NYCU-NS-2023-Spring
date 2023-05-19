import struct


class Frame:
    max_payload_size = 16384  # 2^14

    def __init__(
        self, length=0, type=0, flags=0, r=0, stream_id=0, payload=b""
    ) -> None:
        self.length = length  # (24)
        self.type = type  # (8)
        self.flags = flags  # (8)
        self.r = r  # (1)
        self.stream_id = stream_id  # (31)
        self.payload = payload

    def to_bytes(self):
        return struct.pack(
            f"!LBL{self.length}s",
            (self.length << 8) | self.type,
            self.flags,
            (self.r << 31) | self.stream_id,
            self.payload,
        )


def create_data_frame(stream_id, payload, end_stream=False):
    if len(payload) > Frame.max_payload_size:  # 2^24-1
        raise "payload can't larger than 2^24-1"
    return Frame(
        length=len(payload),
        type=0,
        flags=end_stream,
        stream_id=stream_id,
        payload=payload,
    )


def create_headers_frame(stream_id, payload, end_stream=False):
    if len(payload) > Frame.max_payload_size:  # 2^24-1
        raise "payload can't larger than 2^24-1"
    return Frame(
        length=len(payload),
        type=1,
        flags=end_stream,
        stream_id=stream_id,
        payload=payload,
    )


def bytes_to_frame(data):
    (length_type,) = struct.unpack(f"!L", data[:4])
    length = length_type >> 8
    type, flags, r_stream_id, payload = struct.unpack(f"!BBL{length}s", data[3:])
    return Frame(
        length=length,
        type=type,
        flags=flags,
        r=r_stream_id >> 31,
        stream_id=r_stream_id & ((1 << 31) - 1),
        payload=payload,
    )


def bytes_to_frames(data):
    frames = []
    remain_bytes = b""
    while len(data) > 0:
        (length_type,) = struct.unpack(f"!L", data[:4])
        length = length_type >> 8
        if 9 + length <= len(data):
            type, flags, r_stream_id, payload = struct.unpack(
                f"!BBL{length}s", data[3 : 9 + length]
            )
            frame = Frame(
                length=length,
                type=type,
                flags=flags,
                r=r_stream_id >> 31,
                stream_id=r_stream_id & ((1 << 31) - 1),
                payload=payload,
            )
            frames.append(frame)
            data = data[9 + length :]
        else:
            remain_bytes = data
            break
    return frames, remain_bytes


if __name__ == "__main__":
    f1 = create_headers_frame(1, "aaa".encode())
    f2 = create_headers_frame(1, "bbb".encode())
    fs = bytes_to_frames(f1.to_bytes() + f2.to_bytes())
    for f in fs:
        print(f.payload)
