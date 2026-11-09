"""Native-orphan branch/source-move fixtures plus independent Python kernel replay."""
import json,copy,random,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from compiled_criticality_tree_v1 import Graph,BINARY
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from native_channel_reuse_initializer_v1 import initialize
from fractions import Fraction
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_channel_reuse_initializer_contract_v2_2026-10-19'
def csr(n,edges):
 offsets=[0];dest=[];inc=[];slots={}
 for u in range(n):
  for (a,b),weight in sorted(edges.items()):
   if a==u:slots[a,b]=len(dest);dest.append(b);inc.append(weight)
  offsets.append(len(dest))
 return dict(row_offsets=offsets,dest_ranks=dest,edge_ids=list(range(len(dest))),capacities=[1]*n),inc,slots
def record(cid,source,sink,path,inc):return dict(connection_id=cid,net_id=0,source=source,sink=sink,answer=dict(status='FOUND',physical_edge_ids=path,delay=sum(inc[e] for e in path)))
def main():
 D.mkdir(exist_ok=False);f,w,s=csr(5,{(0,2):1,(1,2):3,(1,3):1,(2,4):2,(3,4):1});g=Graph(f,w,[0]*5);old=[record(0,0,4,[s[0,2],s[2,4]],w)];q=[dict(connection_id=0,net_id=0,source=1,sink=4)];fb={0:record(0,1,4,[s[1,3],s[3,4]],w)['answer']};snapshot=copy.deepcopy(old)
 a=initialize(g,f,['SOURCE','SOURCE','CHANX','CHANX','SINK'],q,old,{0:6},range(len(w)),lambda:fb);assert not a['whole_NET_fallback'] and a['answers'][0]['physical_edge_ids']==[s[1,2],s[2,4]] and a['answers'][0]['delay']==5
 b=initialize(g,f,['SOURCE','SOURCE','CHANX','CHANX','SINK'],q,old,{0:2},range(len(w)),lambda:fb);assert b['whole_NET_fallback'] and b['answers']==fb and old==snapshot
 try:initialize(g,f,['SOURCE','SOURCE','CHANX','CHANX','SINK'],q,old,{0:1},range(len(w)),lambda:fb)
 except ValueError:pass
 else:raise AssertionError('invalid warm fallback admitted')
 assert old==snapshot;g.close();rng=random.Random(2026101907);cases=0;fallbacks=0
 for _ in range(100):
  n=14;edges={(0,v):rng.randrange(1,20) for v in range(1,10)}
  for u in range(1,10):
   for v in range(u+1,n):
    if v>=10 or rng.random()<.3:edges[u,v]=rng.randrange(1,20)
  f,w,s=csr(n,edges);kinds=['SOURCE']+['CHANX']*9+['SINK']*4;g=Graph(f,w,[0]*n);ref=Reference(f,w,[0]*n)
  for name,value in ref._snapshot.items():setattr(ref,name,value)
  plain=ref.tree(0);base={}
  for cid,sink in [(0,10),(1,12)]:
   result=plain.expand(sink,Fraction(1),{},10000);assert result['committed'];base[cid]=dict(status='FOUND',physical_edge_ids=list(result['path_slots']),delay=result['raw'])
  old=[record(0,0,10,[s[0,2],s[2,10]],w),record(1,0,11,[s[0,3],s[3,11]],w)];queries=[dict(connection_id=0,net_id=0,source=0,sink=10),dict(connection_id=1,net_id=0,source=0,sink=12)];budgets={0:max(old[0]['answer']['delay'],base[0]['delay']),1:base[1]['delay']+rng.choice([0,3,1000])};snapshot=copy.deepcopy(old);a=initialize(g,f,kinds,queries,old,budgets,range(len(w)),lambda:copy.deepcopy(base));b=initialize(ref,f,kinds,queries,old,budgets,range(len(w)),lambda:copy.deepcopy(base));assert a==b and old==snapshot;cases+=1;fallbacks+=a['whole_NET_fallback'];g.close()
 files={**closure([Path(__file__)]),str(BINARY):sha(BINARY)};(D/'verification.json').write_text(json.dumps(dict(status='NATIVE_CHANNEL_REUSE_CPP_PYTHON_EQUIVALENCE_AND_ATOMIC_BUDGET_FALLBACK_VERIFIED',random_graphs=cases,whole_NET_fallbacks=fallbacks,moved_source_reuses_orphan_native_channel_fixture=True,raw_budget_forces_audited_warm_fallback=True,invalid_fallback_rejected=True,source_records_unchanged=True,bindings=files,scope='Greedy per-CID expansion prefers new non-native CHANNEL count then raw delay for frozen tree. Not globally optimal multi-sink budget-constrained edit distance; over-budget weighted optimum falls back instead of proving infeasibility.'),indent=2)+'\n');print('PASS',cases,'fallbacks',fallbacks)
if __name__=='__main__':main()
