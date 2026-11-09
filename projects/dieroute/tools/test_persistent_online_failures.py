"""Actual unchanged C++ router must fail on rejected, malformed or disconnected timing service."""
import argparse,json,os
from pathlib import Path
import shlex,socket,subprocess,sys,tempfile,threading
from persistent_vpr_timing import sha

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('pair',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    pair=a.pair.resolve();out=a.output.resolve();out.mkdir(exist_ok=False)
    m=json.loads(pair.read_text());mode,=m['modes'];step=next(x for x in m['steps'] if x['label']==mode+'_0')
    client=Path(__file__).with_name('persistent_timing_client.py').resolve();results=[]
    for name,response in [('rejected',b'{"status":"error","error":"injected engine failure"}\n'),('malformed',b'not-json\n'),('disconnected',b'')]:
        directory=out/name;directory.mkdir();observations=[]
        with tempfile.TemporaryDirectory(prefix='dieroute_fault_') as temp:
            with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as server:
                address=str(Path(temp)/'test.sock');server.bind(address);server.listen(1);server.settimeout(.25)
                finished=threading.Event()
                def serve():
                    while not finished.is_set():
                        try:connection,_=server.accept()
                        except socket.timeout:continue
                        with connection:
                            with connection.makefile('rb') as stream:observations.append(json.loads(stream.readline(65536)))
                            if response:connection.sendall(response)
                        return
                thread=threading.Thread(target=serve);thread.start()
                env={k:v for k,v in os.environ.items() if not k.startswith(('PERSISTROUTE_','DIEROUTE_'))};env.update(step['routing_environment']);env['PERSISTROUTE_TIMING_SOCKET']=address;env['PERSISTROUTE_TIMING_COMMAND']=shlex.join([sys.executable,str(client)])
                command=list(step['command']);command[3]=str(directory/'route')
                try:
                    with (directory/'routing.log').open('w') as log:r=subprocess.run(command,cwd=step['cwd'],env=env,stdout=log,stderr=subprocess.STDOUT)
                finally:finished.set();thread.join()
        assert r.returncode!=0 and len(observations)==1 and observations[0]['epoch']==0
        assert 'timing analyzer failed for iteration 0' in (directory/'routing.log').read_text()
        assert not (directory/'route.json').exists() and not (directory/'route.timing_iteration_0.output.csv').exists()
        results.append(dict(name=name,returncode=r.returncode,requests=observations,log_sha256=sha(directory/'routing.log'),no_final_success=True,no_timing_output=True))
    (out/'audit.json').write_text(json.dumps(dict(status='actual_router_rejects_three_socket_service_failures',cases=results,source_sha256={str(p):sha(p) for p in [pair,client,Path(__file__).resolve(),Path(step['command'][0])]},scope='Failure propagation from external timing client into actual unchanged C++ router;not native engine failure injection or performance evidence',board_result=False,research_complete=False),indent=2)+'\n')
