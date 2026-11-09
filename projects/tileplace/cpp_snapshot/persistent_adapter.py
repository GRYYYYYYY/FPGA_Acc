"""Native host adapter with persistent C++ placement/feedback state checks."""
import subprocess
from compare_proposals import TilePlaceV2Engine,payload,parse

class SavedPlacement(dict):
    pass

class PersistentCppEngine(TilePlaceV2Engine):
    binary=None
    checks=[]
    instances=[]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._server=subprocess.Popen([str(self.binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        self._snapshot_number=0
        self.instances.append(self)
        self._send(payload(self,0)+' '.join(map(str,[len(self.focus_blocks),*sorted(self.focus_blocks)])))
        if self._line()!='READY':raise RuntimeError('C++ state initialization failed')
        self._verify_layout()
    def _send(self,text):
        self._server.stdin.write(text+'\n');self._server.stdin.flush()
    def _line(self):
        result=self._server.stdout.readline().strip()
        if not result or result.startswith('ERROR '):raise RuntimeError('C++ state response: '+result)
        return result
    def _ok(self,text):
        self._send(text)
        if self._line()!='OK':raise RuntimeError('C++ state acknowledgement differs')
    def _verify_layout(self):
        self._send('DUMP');count=int(self._line());positions={}
        for _ in range(count):
            row=list(map(int,self._line().split()));positions[row[0]]=tuple(row[1:])
        if self._line()!='END' or positions!=self.positions:raise RuntimeError('persistent C++ layout differs')
    def _sync_feedback(self):
        values=[len(self.pressure_q16),len(self.path_edges_q16),len(self.focus_blocks)]
        for edge,weight in self.pressure_q16.items():values.extend([*edge,weight])
        for edge,weight in self.path_edges_q16.items():values.extend([*edge,weight])
        values.extend(sorted(self.focus_blocks))
        self._ok('FEEDBACK '+' '.join(map(str,values)))
    @TilePlaceV2Engine.pressure_q16.setter
    def pressure_q16(self,values):
        TilePlaceV2Engine.pressure_q16.fset(self,values)
        if hasattr(self,'_server'):self._sync_feedback()
    def update_timing_feedback(self,feedback):
        super().update_timing_feedback(feedback)
        if hasattr(self,'_server'):self._sync_feedback()
    def snapshot(self):
        saved=SavedPlacement(super().snapshot());self._snapshot_number+=1
        saved.server_snapshot=self._snapshot_number
        self._ok(f'SAVE {saved.server_snapshot}')
        return saved
    def restore(self,positions):
        if not isinstance(positions,SavedPlacement):raise RuntimeError('unbound C++ snapshot')
        self._ok(f'RESTORE {positions.server_snapshot}')
        super().restore(positions)
        self._verify_layout()
    def apply(self,transactions):
        transactions=list(transactions)
        changes={id:p for t in transactions for id,p in t.trial.items()}
        values=[len(changes)]
        for id,p in sorted(changes.items()):values.extend([id,*p])
        self._ok('APPLY '+' '.join(map(str,values)))
        super().apply(transactions);self._verify_layout()
    def propose_color(self,color,forbidden_ids=None):
        forbidden=forbidden_ids or set()
        reference,stats=super().propose_color(color,forbidden)
        values=[color,len(forbidden)]
        for kind,units,trial in sorted(forbidden):
            values.extend([kind,len(units)])
            for unit in units:values.extend([len(unit),*unit])
            values.append(len(trial))
            for id,p in trial:values.extend([id,*p])
        self._send('COLOR '+' '.join(map(str,values)))
        count=int(self._line());rows=[self._line() for _ in range(count)]
        if self._line()!='END':raise RuntimeError('C++ color framing differs')
        actual=parse('\n'.join(rows));expected=sorted((t.transaction_id,t.score_q20) for t in reference)
        if actual!=expected:raise RuntimeError(f'persistent C++ selection differs at color {color}')
        self._verify_layout()
        self.checks.append({'color':color,'selected':len(actual),'forbidden':len(forbidden),
                            'pressure_edges':len(self.pressure_q16),'timing_edges':len(self.path_edges_q16)})
        by_id={t.transaction_id:t for t in reference}
        return [by_id[identity] for identity,score in sorted(actual,key=lambda row:(row[1],row[0]))],stats
    def close(self):
        if self._server.poll() is None:
            try:self._ok('QUIT');self._server.wait(timeout=10)
            finally:
                if self._server.poll() is None:self._server.kill();self._server.wait()
