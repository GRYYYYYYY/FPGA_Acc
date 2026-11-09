"""External routing callback for a single owned persistent timing session."""
import json
import os
from pathlib import Path
import socket
import sys

if __name__ == '__main__':
    epoch, source, target = sys.argv[1:]
    request = dict(epoch=int(epoch), input=str(Path(source).resolve()), output=str(Path(target).resolve()))
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as channel:
        channel.connect(os.environ['PERSISTROUTE_TIMING_SOCKET'])
        channel.sendall((json.dumps(request)+'\n').encode())
        with channel.makefile('rb') as stream:
            response=json.loads(stream.readline(65536))
    if response.get('status') != 'ok':
        raise RuntimeError(response)
