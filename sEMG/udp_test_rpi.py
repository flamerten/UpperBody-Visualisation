import socket
import sys
from struct import unpack

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Bind the socket to the port
host, port = '0.0.0.0', 65000
server_address = (host, port)

print(f'Starting UDP server on {host} port {port}')
sock.bind(server_address)

while True:
    # Wait for message
    try:
        conn, addr = sock.accept()
        conn.setblocking(0)
        message, address = sock.recvfrom(4096)
        reading = unpack('i', message)
        print(reading,"recieved")
    except:
        pass