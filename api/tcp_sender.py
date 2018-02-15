import socket

import simplejson


def send_json(ip, port, data):
    j = simplejson.dumps(data)
    send(ip, port, j)


def send(ip, port, data: str):
    conn = socket.socket()
    conn.connect((ip, int(port),))
    conn.send(data.encode())
    conn.close()
