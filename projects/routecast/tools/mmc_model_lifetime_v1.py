"""Serial setup/round/export ownership for the frozen two-round MMC model.

The reference body and outputs are retained. This exposes round boundaries for
lifetime validation; it does not reuse a model across different placements.
"""
import ast,hashlib,json,time
from pathlib import Path
from dataclasses import dataclass
from types import MappingProxyType
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
SOURCE=R/'tools/run_mmc_native_cached_feedback_v1_2026_10_18.py'
SOURCE_SHA='abe4ca4b43d588230efec87ad51318248052ca1d4c174a3128cbc915e1331f1e'

@dataclass(frozen=True,slots=True)
class Ticket:
    generation:int
    round_index:int
    file:str|None
    digest:str|None

class Controller:
    def __init__(self,generator):
        self._generator=generator;self.current=None;self.phase='SETTING_UP';self.next_round=0;self._busy=False
        self.costs=[];tick=time.perf_counter()
        try:
            event=next(generator)
            if event['kind']!='ready':raise ValueError('missing ready boundary')
            self._bindings=dict(event['bindings']);self._resources=event['resources'];self.phase='ACTIVE';self.current=Ticket(0,-1,None,None)
        except BaseException:
            self.close();raise
        self.costs.append({'stage':'setup','seconds':time.perf_counter()-tick})
    def _ticket(self,ticket):
        if self.phase!='ACTIVE' or ticket is not self.current or self._busy:raise RuntimeError('stale/closed/busy model ticket')
    def _guard(self):
        if not all(sha(p)==h for p,h in self._bindings.items()):raise ValueError('model input binding changed')
    def step(self,ticket,round_index):
        self._ticket(ticket)
        if type(round_index) is not int or round_index!=self.next_round or round_index>=2:raise ValueError('round order')
        tick=time.perf_counter();self._busy=True
        try:
            self._guard();event=next(self._generator)
            if event['kind']!='round' or event['index']!=round_index or event['resources']!=self._resources:raise ValueError('boundary/owner mismatch')
            path=event['file'];self.current=Ticket(ticket.generation+1,round_index,path,sha(path));self.next_round+=1
        except BaseException:
            self.close();raise
        finally:self._busy=False
        self.costs.append({'stage':f'round{round_index}_with_input_guard','seconds':time.perf_counter()-tick})
        return self.current
    def read_state(self,ticket):
        self._ticket(ticket)
        if ticket.file is None:raise ValueError('no completed round')
        raw=Path(ticket.file).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=ticket.digest:raise ValueError('state export changed')
        return json.loads(raw)
    def export(self,ticket):
        self._ticket(ticket)
        if self.next_round!=2:raise ValueError('unfinished rounds')
        tick=time.perf_counter();self._busy=True
        try:
            self._guard()
            try:next(self._generator)
            except StopIteration as done:result=done.value
            else:raise ValueError('unexpected extra round')
            self.phase='EXPORTED';self.current=None
        except BaseException:
            self.close();raise
        finally:self._busy=False
        self.costs.append({'stage':'final_export_with_input_guard','seconds':time.perf_counter()-tick})
        return MappingProxyType(dict(result))
    def close(self):
        try:self._generator.close()
        finally:self.phase='CLOSED';self.current=None

class Model(Controller):
    def __init__(self,*args):
        if sha(SOURCE)!=SOURCE_SHA:raise ValueError('reference model source changed')
        tree=ast.parse(SOURCE.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='predict')
        loop=next(n for n in fn.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='round_index')
        if ast.unparse(loop.iter)!='range(2)':raise ValueError('reference round schedule changed')
        resource="(id(search),id(criticality_graph))"
        loop.body.extend(ast.parse("assert context.active is None\nyield {'kind':'round','index':round_index,'file':str(file),'resources':"+resource+"}").body)
        i=fn.body.index(loop);fn.body[i:i]=ast.parse("yield {'kind':'ready','bindings':bindings,'resources':"+resource+"}").body
        original_body=fn.body
        final=ast.parse("if search is not None: search.close()\nif criticality_graph is not None: criticality_graph.close()\n_cleanup_report(search is None or search.closed,criticality_graph is None or criticality_graph.closed)").body
        fn.body=ast.parse('search=None\ncriticality_graph=None').body+[ast.Try(body=original_body,handlers=[],orelse=[],finalbody=final)]
        ast.fix_missing_locations(tree);self.cleanup={'calls':0,'search_closed':False,'graph_closed':False}
        def cleanup(a,b):self.cleanup.update(calls=self.cleanup['calls']+1,search_closed=a,graph_closed=b)
        ns={'__file__':str(SOURCE),'__name__':'mmc_lifetime_original','_cleanup_report':cleanup}
        self.transformed_ast_sha256=hashlib.sha256(ast.dump(tree,include_attributes=False).encode()).hexdigest()
        exec(compile(tree,str(SOURCE),'exec'),ns)
        super().__init__(ns['predict'](*args))
