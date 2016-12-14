#!/usr/bin/env python3

import logging
import socket
import struct
import sys
import time

def broadcast_pos(sock: socket.socket, pos: float, clients: [(str, int)]) -> [int]:
    data = struct.pack('!d', pos)
    sent = []
    for client in clients:
        sent.append(sock.sendto(data, client))
    for client, written in zip(clients, sent):
        if written != 8:
            logging.error("Cannot send to '%s:%d'" % client)
    return sent

def main(argv: [str]) -> int:
    logging.basicConfig(level=logging.INFO)
    if len(argv) < 3:
        sys.stdout.write('Usage: ./master.py length client1 port1 [client2 port2 ...]\n\n')
        return 1
    logging.info("Setting length to '%s'" % argv[1])
    length = float(argv[1])
    clients = []
    for addr, port in zip(argv[2::2], argv[3::2]):
        logging.info("Adding client '%s:%s'" % (addr, port))
        clients.append((addr, int(port)))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    
    while True:  # Loop playback
        start_time = time.monotonic()
        pos = 0
        broadcast_pos(sock, 0, clients)
        logging.info('Position: 0.000000000')
        while pos < length:
            time.sleep(1)
            pos = time.monotonic() - start_time
            broadcast_pos(sock, pos, clients)
            logging.info('Position: %.9f' % pos)

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv))
