"""Frozen reference engine plus optional scalar memo; observational AST only in correctness mode."""
import ast,sys,os,json,hashlib,time,types,cProfile,pstats,resource
from pathlib import Path
D=Path(__file__).resolve().parent;A=D.parent/'phase2_A';S=A/'source';sys.path.insert(0,str(S));sys.path.insert(0,str(D))
from reuse import Memo
arm=os.environ['REUSE_ARM'];mode=os.environ['REUSE_MODE'];observe=mode=='correctness';w=Path(os.environ['REUSE_OUTPUT']);started=time.monotonic()
counts={};chunks=[];h=hashlib.sha256();n=0;examples=[]
def clean(x):
 if hasattr(x,'audit'):return x.audit()
 if isinstance(x,dict):return [[clean(k),clean(v)] for k,v in sorted(x.items(),key=lambda kv:repr(kv[0]))]
 if isinstance(x,(set,frozenset)):return sorted((clean(v) for v in x),key=repr)
 if isinstance(x,(list,tuple)):return [clean(v) for v in x]
 if isinstance(x,(str,int,float,bool)) or x is None:return x
 return type(x).__name__
fields={'unit','target_root','second_target','direct','owners','other','third','trial','changed_blocks','kind','units','before','after','deltas','normalized','score','candidate','transaction','candidates','best','old','proposals','accepted','reserved_sites','reserved_nets','reserved_units','forbidden_ids','color','positions','target','block_id'}
def event(label,loc):
 global n,h
 record=[label,{k:clean(v) for k,v in loc.items() if k in fields and k not in {'positions','candidate'}}]
 # Candidate coordinates are fully determined by recorded trial and position transitions.
 payload=json.dumps(record,sort_keys=True,separators=(',',':')).encode();h.update(payload+b'\n');n+=1;counts[label]=counts.get(label,0)+1
 if len(examples)<12:examples.append(record)
 if n%4096==0:chunks.append({'end':n,'sha256':h.hexdigest()});h=hashlib.sha256()
class Observer(ast.NodeTransformer):
 def visit_FunctionDef(self,node):
  names={'_transactions_for_unit','_make_transaction','_valid_trial','_guard_ok','propose_color','apply','restore','update_timing_feedback'}
  if node.name not in names:return node
  name=node.name
  def block(body):
   out=[]
   for s in body:
    # Capture every decision/return and resulting assignments, including discarded scores.
    if isinstance(s,(ast.If,ast.For,ast.While)):
     s.body=block(s.body);s.orelse=block(s.orelse)
    label=f'{name}:{s.lineno}:{type(s).__name__}'
    call=ast.Expr(ast.Call(ast.Name('_observe',ast.Load()),[ast.Constant(label),ast.Call(ast.Name('locals',ast.Load()),[],[])],[]))
    if isinstance(s,(ast.Return,ast.Continue,ast.If,ast.For)):out.extend([call,s])
    elif isinstance(s,(ast.Assign,ast.AugAssign)) and any(isinstance(t,ast.Name) and t.id in {'trial','before','after','deltas','normalized','score','candidates','best','proposals','direct'} for t in ast.walk(s)):out.extend([s,call])
    else:out.append(s)
   return out
  node.body=block(node.body);return node
source=(S/'tileplace_v2.py').read_text();tree=ast.parse(source)
if observe:tree=Observer().visit(tree);ast.fix_missing_locations(tree)
m=types.ModuleType('tileplace_v2');m.__file__=str(S/'tileplace_v2.py');m._observe=event;sys.modules['tileplace_v2']=m;exec(compile(tree,m.__file__,'exec'),m.__dict__)
E=m.TilePlaceV2Engine;original=E._connection_congestion;setter=E.pressure_q16.fset;engines=[]
def pressure(self,values):
 if not hasattr(self,'memo'):self.memo=Memo();engines.append(self)
 self.memo.reset();setter(self,values)
E.pressure_q16=property(E.pressure_q16.fget,pressure)
if arm=='R1':
 def connection(self,s,t,p):return self.memo.get(self,s,t,p,original,observe)
 E._connection_congestion=connection
elif observe:
 def connection(self,s,t,p):
  a,b=p[s],p[t];key=(self.memo.version,a[0],a[1],b[0],b[1]);self.memo.seen.add(key);self.memo.roles['before' if p is self.positions else 'candidate']+=1;self.memo.stats['queries']+=1
  return original(self,s,t,p)
 E._connection_congestion=connection
import run_tileplace_v2 as runner
# Observe terminal acceptance after feedback replacement; recursive trials are journalled individually.
class Journal(list):
 def append(self,item):
  item=dict(item);item['completed_elapsed_s']=time.monotonic()-started
  super().append(item)
init=runner.RoutedSearch.__init__
def init_search(self,*a,**kw):init(self,*a,**kw);self.trials=Journal()
runner.RoutedSearch.__init__=init_search
prof=cProfile.Profile() if observe else None
try:
 if prof:
  propose=E.propose_color
  def first_profile(self,*a,**kw):
   if getattr(self,'_profiled',False):return propose(self,*a,**kw)
   self._profiled=True;prof.enable()
   try:return propose(self,*a,**kw)
   finally:prof.disable()
  E.propose_color=first_profile
 rc=runner.main()
finally:
 if prof:prof.disable();prof.dump_stats(str(w/'profile.pstats'))
 if n%4096:chunks.append({'end':n,'sha256':h.hexdigest()})
 info=[]
 for e in engines:
  e.memo.reset();info.append({'stats':dict(e.memo.stats),'epochs':e.memo.epochs})
 (w/'observations.json').write_text(json.dumps({'arm':arm,'mode':mode,'count':n,'counts':counts,'chunks':chunks,'examples':examples,'reuse':info,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'wall_s':time.monotonic()-started},indent=2))
 if prof:
  st=pstats.Stats(prof);rows=[{'file':k[0],'line':k[1],'function':k[2],'primitive_calls':v[0],'calls':v[1],'self_s':v[2],'cumulative_s':v[3]} for k,v in st.stats.items()];(w/'profile.json').write_text(json.dumps(rows,indent=2))
sys.exit(rc)
