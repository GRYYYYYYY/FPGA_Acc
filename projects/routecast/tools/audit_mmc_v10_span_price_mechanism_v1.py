"""Independent original node metadata and complete feedback price-state audit."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from array import array
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from path_rc import number
D=R/'experiments/ultraembedded_mmc_continuous_workflow_v10_2026-10-09'
O=R/'experiments/mmc_v10_feedback_hotspots_v2_2026-10-09/mmc'
vp=D/'verification.json';proof=json.loads(vp.read_text());assert proof['all_cases_both_complete_arms_authenticated'];assert all(sha(p)==h for p,h in proof['bindings'].items())
bindings={**closure([Path(__file__)]),str(vp):sha(vp)}
model=D/'seed/model/mmc'
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
ep=load(D/'seed/demand/mmc/endpoints.json');graph=Path(ep['inputs']['graph']['path']);assert sha(graph)==ep['graph_sha256'];bindings[str(graph)]=sha(graph)
initial=load(model/'initial.json');round0=load(model/'round0.json');round1=load(model/'round1.json');protocol=load(model/'protocol.json');assert protocol['static_channel_span_price_ns']=='1/20 per destination CHAN span, applied in feedback only; initial remains exact zero-price RC floor'
caps=array('Q');spans=array('Q');group=[];electrical=defaultdict(Counter);segments={};stack=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='segments':segments={int(x.get('id')):dict(x.attrib) for x in e.findall('segment')}
 if e.tag=='node' and parent=='rr_nodes':
  n=int(e.get('id'));assert n==len(caps);cap=int(e.get('capacity'));loc=e.find('loc');span=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1
  kind=e.get('type');seg=e.find('segment');key=(kind,int(seg.get('segment_id'))) if kind in {'CHANX','CHANY'} else None
  caps.append(cap);spans.append(span if key else 0);group.append(key)
  if key:timing=e.find('timing');electrical[key][(timing.get('R'),timing.get('C'))]+=1
  stack[-2].remove(e);e.clear()
 if e.tag=='rr_nodes':break
 stack.pop()
assert caps and segments and sha(graph)==ep['graph_sha256']
stats=defaultdict(lambda:Counter());channels=0
for n,(cap,span,key) in enumerate(zip(caps,spans,group)):
 old=max(0,initial['ledger'].get(str(n),0)-cap);mid=max(0,round0['ledger'].get(str(n),0)-cap)
 assert round0['prices'].get(str(n),0)==span+old
 assert round1['prices'].get(str(n),0)==span+old+mid
 if not key or not cap:continue
 channels+=1;s=stats[key];s['nodes']+=1;s['capacity']+=cap;s['span']+=span;s['initial_occupancy']+=initial['ledger'].get(str(n),0);s['final_occupancy']+=round1['ledger'].get(str(n),0);s['initial_overflow']+=old;s['round0_overflow']+=mid;s['round0_price']+=span+old;s['round1_price']+=span+old+mid
rows=[]
for key,s in sorted(stats.items()):
 timing=electrical[key];rows.append(dict(type=key[0],segment=segments[key[1]],counts=dict(s),mean_span=s['span']/s['nodes'],mean_initial_feedback_price=s['round0_price']/s['nodes'],mean_final_feedback_price=s['round1_price']/s['nodes'],node_timing_classes=[dict(R=a,C=b,count=count) for (a,b),count in timing.items()],all_node_R_C_zero=all(number(a)==number(b)==0 for a,b in timing)))
assert channels==258720
budgets=Counter((x['floor_integer'],x['budget_integer']) for x in initial['records'])
result=dict(bindings=bindings,all_original_node_price_states_equal=True,nodes=len(caps),positive_channels=channels,rows=rows,budget_range=dict(min_floor=min(a for a,b in budgets),max_floor=max(a for a,b in budgets),min_budget=min(b for a,b in budgets),max_budget=max(b for a,b in budgets),price_unit_integer=protocol['price_unit_integer']),scope='Complete original node metadata and both recorded price states, including nonchannel overflow. Initial zero-price policy source/protocol authenticated; no independent shortest-path/weighted optimality or causal diagnosis. No parameter fitting or candidate change; hypothetical correction requires new full audits and quality/cost trials.')
assert all(sha(p)==h for p,h in bindings.items())
(O/'span_price_mechanism_audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2),flush=True)
