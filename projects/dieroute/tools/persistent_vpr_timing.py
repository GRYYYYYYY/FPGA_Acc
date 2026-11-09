"""One initialized VPR process serving serialized timing requests over typed FIFOs."""
import csv
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import select
import shutil
import struct
import subprocess
import tempfile
import time


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class PersistentTimingSession:
    def __init__(self,binary,environment,adapter,tasks,directory):
        self.directory=Path(directory).resolve()
        self.directory.mkdir(mode=0o700,exist_ok=False)
        self.process=None
        self.request_fd=self.response_fd=None
        self.buffer=b''
        self.sequence=0
        self.pending=False
        self.stopped=False
        self.receipts=(self.directory/'receipts.jsonl').open('w')
        self.log=(self.directory/'native.log').open('w')
        self.started_ns=time.monotonic_ns()
        self.binary=Path(binary).resolve()
        self.environment={k:v for k,v in environment.items() if k.startswith('PERSISTROUTE_')}
        self.environment['PERSISTROUTE_VPR_BIN']=str(self.binary)
        self.adapter=Path(adapter).resolve()
        self.tasks=Path(tasks).resolve()
        raw=list(struct.iter_unpack('<IIIIHHIII',self.tasks.read_bytes()))
        self.identities={r[0]:(r[1],r[2],r[3]) for r in raw}
        assert len(self.identities)==len(raw) and raw
        spec=importlib.util.spec_from_file_location('frozen_vpr_timing_util',self.adapter)
        utility=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(utility)
        paths={name:Path(self.environment[name]).resolve() for name in utility.REQUIRED[:-1]}
        assert all(p.is_file() for p in paths.values())
        utility._validate_placement_identity(paths['PERSISTROUTE_VPR_ROUTE'],paths['PERSISTROUTE_VPR_PLACE'])
        work=self.directory/'native_work'
        work.mkdir()
        private={}
        for name in ('NET','PLACE','ROUTE'):
            source=paths['PERSISTROUTE_VPR_'+name]
            target=work/source.name
            shutil.copy2(source,target)
            private[name]=target
        utility._normalize_private_identity_headers(private['NET'],private['PLACE'],private['ROUTE'])
        command=[str(self.binary),str(paths['PERSISTROUTE_VPR_ARCH']),str(paths['PERSISTROUTE_VPR_CIRCUIT']),
                 '--analysis','--net_file',private['NET'].name,'--place_file',private['PLACE'].name,
                 '--route_file',private['ROUTE'].name,'--route_chan_width',self.environment['PERSISTROUTE_VPR_CHAN_WIDTH'],
                 '--timing_report_npaths','1']
        extra_sources=set()
        for key,flag in [('PERSISTROUTE_VPR_DEVICE','--device'),('PERSISTROUTE_VPR_CONSTRAINTS','--read_vpr_constraints'),
                         ('PERSISTROUTE_VPR_RR_GRAPH','--read_rr_graph')]:
            if self.environment.get(key):
                if key!='PERSISTROUTE_VPR_DEVICE':
                    source=Path(self.environment[key]).resolve()
                    assert source.is_file()
                    extra_sources.add(source)
                command.extend([flag,self.environment[key]])
        if self.environment.get('PERSISTROUTE_VPR_SDC'):
            original=Path(self.environment['PERSISTROUTE_VPR_SDC']).resolve()
            extra_sources.add(original)
            sdc=work/original.name
            shutil.copy2(original,sdc)
            command.extend(['--sdc_file',sdc.name])
        self.ipc=tempfile.TemporaryDirectory(prefix='dieroute_sta_',dir='/tmp')
        self.request_path=Path(self.ipc.name)/'requests.fifo'
        self.response_path=Path(self.ipc.name)/'responses.fifo'
        os.mkfifo(self.request_path,0o600)
        os.mkfifo(self.response_path,0o600)
        self.request_fd=os.open(self.request_path,os.O_RDWR|os.O_CLOEXEC)
        self.response_fd=os.open(self.response_path,os.O_RDONLY|os.O_NONBLOCK|os.O_CLOEXEC)
        env={k:v for k,v in os.environ.items() if not k.startswith(('DIEROUTE_','PERSISTROUTE_'))}
        env.update(self.environment)
        env.pop('PERSISTROUTE_VPR_TIMING_INPUT',None)
        env.pop('PERSISTROUTE_VPR_TIMING_OUTPUT',None)
        env['PERSISTROUTE_VPR_TIMING_REQUEST_FIFO']=str(self.request_path)
        env['PERSISTROUTE_VPR_TIMING_RESPONSE_FIFO']=str(self.response_path)
        self.protected=set(paths.values())|extra_sources|{self.binary,self.adapter,self.tasks,self.request_path,self.response_path,self.directory/'native.log'}
        self._record(dict(event='session_start',command=command,cwd=str(work),
                          binary_sha256=sha(self.binary),tasks_sha256=sha(self.tasks),adapter_sha256=sha(self.adapter),
                          input_sha256={str(p):sha(p) for p in set(paths.values())|extra_sources}))
        self.process=subprocess.Popen(command,cwd=work,env=env,stdout=self.log,stderr=subprocess.STDOUT)
        try:
            assert self.read_response()=='READY\t1','Invalid native timing readiness frame'
        except BaseException:
            self.abort()
            raise
        self.ready_ns=time.monotonic_ns()
        self._record(dict(event='engine_ready',pid=self.process.pid,
                          process_start_ticks=Path('/proc',str(self.process.pid),'stat').read_text().split(')')[-1].split()[19],
                          ready_frame='READY\t1',startup_ns=self.ready_ns-self.started_ns))

    def _record(self,row):
        self.receipts.write(json.dumps(dict(monotonic_ns=time.monotonic_ns(),**row))+'\n')
        self.receipts.flush()

    def write_frame(self,text):
        assert self.process.poll() is None
        encoded=text.encode('utf-8')
        assert encoded.endswith(b'\n') and len(encoded)<4096
        assert os.write(self.request_fd,encoded)==len(encoded)

    def read_response(self):
        # A live engine is not declared failed merely because observation takes time.
        while b'\n' not in self.buffer:
            ready,_,_=select.select([self.response_fd],[],[],0.25)
            if ready:
                chunk=os.read(self.response_fd,4096)
                if chunk:
                    self.buffer+=chunk
                    continue
            if self.process.poll() is not None:
                raise RuntimeError(f'Native timing process exited {self.process.returncode}; see {self.directory / "native.log"}')
            if ready:
                time.sleep(0.01)
        line,self.buffer=self.buffer.split(b'\n',1)
        return line.decode('ascii')

    def analyze(self,epoch,input_csv,output_csv):
        assert not self.stopped and not self.pending and type(epoch) is int and 0<=epoch<=0xffffffff
        source,target=Path(input_csv).resolve(),Path(output_csv).resolve()
        assert source.is_file() and source!=target and target not in self.protected and not target.exists()
        assert not any(c in str(p) for p in (source,target) for c in ('\t','\n','\r'))
        before=sha(source)
        with source.open() as stream:
            reader=csv.DictReader(stream)
            assert reader.fieldnames==['iteration','task_id','net_id','source','sink','routed','delay_ps','criticality_q']
            rows=[{k:int(v) for k,v in r.items()} for r in reader]
        ids=[r['task_id'] for r in rows]
        assert len(ids)==len(self.identities) and len(set(ids))==len(ids) and set(ids)==set(self.identities)
        for r in rows:
            assert r['iteration']==epoch and self.identities[r['task_id']]==(r['net_id'],r['source'],r['sink'])
            assert r['routed'] in (0,1) and 0<=r['delay_ps']<=0xffffffffffffffff and 0<=r['criticality_q']<=65535
        target.parent.mkdir(parents=True,exist_ok=True)
        seq=self.sequence
        begin=time.monotonic_ns()
        self.pending=True
        self.write_frame(f'ANALYZE\t{seq}\t{source}\t{target}\n')
        response=self.read_response().split('\t')
        assert len(response)==3 and response[0]=='DONE' and int(response[1])==seq and int(response[2])>=0
        assert sha(source)==before and target.is_file()
        with target.open() as stream:
            reader=csv.DictReader(stream)
            assert reader.fieldnames==['task_id','criticality_q','delay_ps','slack_ps','critical_path_delay_ps']
            actual=[{k:int(v) for k,v in r.items()} for r in reader]
        assert [r['task_id'] for r in actual]==ids
        assert len({r['critical_path_delay_ps'] for r in actual})==1
        assert all(0<=r['criticality_q']<=65535 and 0<=r['delay_ps']<=0xffffffffffffffff for r in actual)
        self.sequence+=1
        self.pending=False
        receipt=dict(event='timing_response',sequence=seq,epoch=epoch,input=str(source),output=str(target),
                     input_sha256=before,output_sha256=sha(target),rows=len(actual),
                     native_elapsed_us=int(response[2]),request_roundtrip_ns=time.monotonic_ns()-begin)
        self._record(receipt)
        return receipt

    def stop(self):
        assert not self.stopped and not self.pending
        self.write_frame(f'STOP\t{self.sequence}\n')
        assert self.read_response()==f'STOPPED\t{self.sequence}'
        code=self.process.wait()
        self.stopped=True
        self._record(dict(event='session_stop',requests=self.sequence,returncode=code,
                          lifetime_ns=time.monotonic_ns()-self.started_ns))
        self._close_files()
        assert code==0,code

    def _close_files(self):
        for name in ('request_fd','response_fd'):
            fd=getattr(self,name,None)
            if fd is not None:
                os.close(fd)
                setattr(self,name,None)
        self.log.close()
        self.receipts.close()
        if hasattr(self,'ipc'):
            self.ipc.cleanup()

    def abort(self):
        # Used only after an actual failed fixture/assertion or explicit cancellation.
        if self.process is not None and self.process.poll() is None:
            self.process.terminate()
            self.process.wait()
        if not self.receipts.closed:
            self._record(dict(event='session_aborted_after_failure',returncode=None if self.process is None else self.process.returncode))
        self.stopped=True
        self._close_files()
