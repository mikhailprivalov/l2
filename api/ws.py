from laboratory.settings import WS_BASE, WS_PORT, WS_ENABLED


def emit(name, data=None):
    if not WS_ENABLED:
        return
    try:
        if data is None:
            data = {}
        from socketIO_client_nexus import SocketIO

        with SocketIO(WS_BASE, WS_PORT, wait_for_connection=False) as socketIO:
            socketIO.emit(name, data)
    except:
        pass
