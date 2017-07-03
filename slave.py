#!/usr/bin/env python3

import json
import logging
import os
import socket
import struct
import subprocess
import sys


def ipc_command(ipc: open, command: [object]) -> object:
    req_id = ipc_command.request_id
    ipc_command.request_id += 1
    line = '{"command":%s,"request_id":%d}\n' % (json.dumps(command), req_id)
    # logging.info('>> %s' % line.strip())
    ipc.write(line)
    ipc.flush()
    for line in ipc:
        # logging.info('<< %s' % line.strip())
        obj = json.loads(line)
        if 'err' in obj and obj['error'] != 'success':
            logging.error('mpv error: %r' % obj['error'])
        if obj.get('request_id') == req_id:
            return obj.get('data')


ipc_command.request_id = 0


def clamp(value: float, low: float, high: float) -> float:
    return min(max(value, low), high)


def main(argv: [str]) -> int:
    logging.basicConfig(level=logging.INFO)
    if len(argv) < 4:
        sys.stdout.write('Usage: ./slave.py bind port media_file [mpv_args ...]\n\n')
        return 1
    logging.info("Setting listening address to '%s:%s" % (argv[1], argv[2]))
    addr = (argv[1], int(argv[2]))
    logging.info("Setting media file to '%s'" % argv[3])
    media = argv[3]
    mpv_args = argv[4:]

    logging.info("Listening on '%s:%s'" % (argv[1], argv[2]))
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(addr)
    ipc_path = '/tmp/mpv-%d.sock' % os.getpid()
    logging.info('Starting mpv on %s' % ipc_path)
    subprocess.Popen([
        'mpv', '--idle=yes', '--input-ipc-server=' + ipc_path
    ] + mpv_args)
    ipc = None

    while True:
        buf, master = sock.recvfrom(8)
        target, = struct.unpack('!d', buf)
        if ipc is None:
            if os.path.exists(ipc_path):
                ipc_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                ipc_sock.connect(ipc_path)
                os.unlink(ipc_path)
                ipc = ipc_sock.makefile('rw')
                ipc_command(ipc, ['set_property', 'audio-pitch-correction', 'yes'])
                ipc_command(ipc, ['set_property', 'hr-seek', 'yes'])
                ipc_command(ipc, ['set_property', 'keep-open', 'yes'])
                ipc_command(ipc, ['loadfile', media, 'replace'])
            else:
                logging.error('IPC socket not ready, retrying')
                continue
        if target == 0.0:
            ipc_command(ipc, ['set_property', 'speed', 1])
            ipc_command(ipc, ['set_property', 'time-pos', 0])
            ipc_command(ipc, ['set_property', 'pause', 'no'])
        else:
            pos = ipc_command(ipc, ['get_property', 'time-pos'])
            if pos is not None and -3 < target - pos < 3:
                ipc_command(ipc, ['set_property', 'speed', clamp(target - pos + 1, 0.5, 2)])
            else:
                ipc_command(ipc, ['set_property', 'speed', 1])
                ipc_command(ipc, ['set_property', 'time-pos', target])

    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
