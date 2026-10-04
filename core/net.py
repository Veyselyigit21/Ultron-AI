"""Hafif internet bağlantısı kontrolü (önbellekli)."""
import socket
import time

_cache = [0.0, True]


def is_online(max_age: float = 15.0) -> bool:
    now = time.time()
    if now - _cache[0] < max_age:
        return _cache[1]
    ok = False
    for host in (("1.1.1.1", 443), ("8.8.8.8", 53)):
        try:
            socket.create_connection(host, timeout=1.0).close()
            ok = True
            break
        except OSError:
            continue
    _cache[0], _cache[1] = now, ok
    return ok


def mark(online: bool) -> None:
    _cache[0], _cache[1] = time.time(), online
