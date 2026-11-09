"""Run unchanged native router with one cold-started persistent timing engine."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import socket
import subprocess
import sys
import tempfile
import threading
import time
sys.path.insert(1,'/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/dieroute/work/sb3_fixed_feedback_pair_20261015/native_tools')
from persistent_vpr_timing import PersistentTimingSession, sha

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('pair',type=Path)
    parser.add_argument('build',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    pair,build,output=[p.resolve() for p in (args.pair,args.build,args.output)]
    output.mkdir(exist_ok=False)
    manifest=json.loads(pair.read_text())
    mode,=manifest['modes']
    step=next(s for s in manifest['steps'] if s['label']==mode+'_0')
    audit=json.loads((build/'build_dependency_audit.json').read_text())
    binary=Path(audit['binary'])
    assert sha(binary)==audit['binary_sha256']
    environment={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))}
    environment.update(step['routing_environment'])
    environment['PERSISTROUTE_VPR_BIN']=str(binary)
    adapter=pair.parent/'source/persistroute/tools/vpr_timing_analyzer.py'
    client=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/dieroute/work/sb3_fixed_feedback_pair_20261015/native_tools/persistent_timing_client.py').resolve()
    command=list(step['command']);command[3]=str(output/'route')
    errors=[]
    requests=[]
    stopped=threading.Event()
    process=None
    session=None
    begin=time.monotonic_ns()
    report=dict(status='starting',command=command,source_sha256={str(p):sha(p) for p in [pair,binary,adapter,client,Path(__file__).resolve(),Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/dieroute/work/sb3_fixed_feedback_pair_20261015/native_tools/persistent_vpr_timing.py'),Path(command[0])]},board_result=False,research_complete=False)
    (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    try:
        session=PersistentTimingSession(binary,environment,adapter,pair.parent/'input.tasks',output/'timing_session')
        with tempfile.TemporaryDirectory(prefix='dieroute_online_',dir='/tmp') as temporary:
            address=str(Path(temporary)/'timing.sock')
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
                server.bind(address);os.chmod(address,0o600);server.listen(1);server.settimeout(.25)
                environment['PERSISTROUTE_TIMING_SOCKET']=address
                environment['PERSISTROUTE_TIMING_COMMAND']=shlex.join([sys.executable,str(client)])
                def serve():
                    while not stopped.is_set():
                        try:
                            connection,_=server.accept()
                        except socket.timeout:
                            continue
                        with connection:
                            try:
                                with connection.makefile('rb') as stream:
                                    frame=stream.readline(65536)
                                assert frame.endswith(b'\n') and len(frame)<65536
                                request=json.loads(frame)
                                assert set(request)=={'epoch','input','output'}
                                receipt=session.analyze(request['epoch'],request['input'],request['output'])
                                requests.append(receipt)
                                connection.sendall(b'{"status":"ok"}\n')
                            except BaseException as error:
                                errors.append(repr(error))
                                try: connection.sendall((json.dumps(dict(status='error',error=repr(error)))+'\n').encode())
                                except OSError: pass
                                return
                thread=threading.Thread(target=serve)
                thread.start()
                try:
                    with (output/'routing.log').open('w') as log:
                        process=subprocess.Popen(command,cwd=step['cwd'],env=environment,stdout=log,stderr=subprocess.STDOUT)
                        fields=Path('/proc',str(process.pid),'stat').read_text().rsplit(')',1)[1].split()
                        launch={'pid':process.pid,'start_ticks':fields[19],'started_ns':time.time_ns(),'command':command,'cwd':step['cwd'],'router_binary_sha256':sha(Path(command[0])),'pair_sha256':sha(pair)}
                        (output/'router_process_launch.json').write_text(json.dumps(launch,indent=2)+'\n')
                        report.update(status='routing',pid=process.pid)
                        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
                        code=process.wait()
                        (output/'router_process_terminal.json').write_text(json.dumps({**launch,'returncode':code,'ended_ns':time.time_ns()},indent=2)+'\n')
                finally:
                    stopped.set();thread.join()
                assert code in (0,3) and not errors,(code,errors)
                session.stop()
        report.update(status=('online_router_completed_equivalence_audit_required' if code==0 else 'online_router_exit3_retained_orderly_session_stop_requires_capacity_classification'),raw_parent_legal_exit=(code==0),returncode=code,requests=len(requests),cold_start_through_shutdown_ns=time.monotonic_ns()-begin,request_receipts=requests)
    except BaseException as error:
        report.update(status='failed',error=repr(error),server_errors=errors)
        if process is not None and process.poll() is None:
            process.terminate();process.wait()
        raise
    finally:
        if session is not None and not session.stopped: session.abort()
        (output/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')

    sys.exit(code)
