import socket
import struct
import time
from collections import deque

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to a specific address and port
server_address = ('localhost', 10000)
sock.bind(server_address)

# Initialize the sliding window
window_size = 10
window_start = 0
window_end = window_start + window_size

# Keep track of the packets that have been acknowledged
acknowledged_packets = set()

# Initialize a queue for retransmission
retransmission_queue = deque()

# Set a timeout for retransmission
timeout = 0.5

# Set a threshold for congestion control
congestion_threshold = 0.8

# Keep track of the number of retransmissions
retransmissions = 0

# Keep track of the number of packets sent
packets_sent = 0

while True:
    # Wait for data from a client
    print('waiting for data')
    data, client_address = sock.recvfrom(1024)

    # Extract the packet number and payload
    packet_number, = struct.unpack('!I', data[:4])
    payload = data[4:]

    # Check if the packet is within the current window
    if packet_number >= window_start and packet_number < window_end:
        # Send an acknowledgement for the packet
        ack = struct.pack('!I', packet_number)
        sock.sendto(ack, client_address)

        # Add the packet to the acknowledged set
        acknowledged_packets.add(packet_number)

        # Check if all packets in the window have been acknowledged
        if len(acknowledged_packets) == window_size:
            # Move the window forward
            window_start = window_end
            window_end += window_size

            # Clear the acknowledged set
            acknowledged_packets.clear()

    else:
        # Send a negative acknowledgement for the packet
        nack = struct.pack('!I', -1)
        sock.sendto(nack, client_address)

        # Add the packet to the retransmission queue
        retransmission_queue.append((time.time(), packet_number, payload))

    # Check for retransmission
    while len(retransmission_queue) > 0:
        timestamp, packet_number, payload = retransmission_queue[0]

        # Check if the packet has timed out
        if time.time() - timestamp > timeout:
            # Send the packet again
            sock.sendto(payload, client_address)

            # Update the timestamp
            retransmission_queue[0] = (time.time(), packet_number, payload)

            # Increase the number of retransmissions
            retransmissions += 1

            # Check for congestion
            if retransmissions / packets_sent > congestion_threshold:
                # Reduce the window size
                window_size = window_size // 2
                window_end = window_size
