"""Independent full-XML RC-only dual/cut capacity contradiction verification."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET,sys
from fractions import Fraction
from array import array
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_frozen_budget_RC_tight_separator_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(pathlib.Path(p))==h
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');kinds=[];us=array('I');vs=array('I');weights=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0;w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;switches[int(e.get('id'))]=int(w)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(us)==8097539 and len(caps)==904438 and sys.byteorder=='little';node=protocol['node'];assert caps[node]==1 and kinds[node] in ['CHANX','CHANY'];assert len({r['net_id'] for r in protocol['selected_NETs']})>caps[node];rows=[]
 bindings={str(p):sha(p) for p in [O/'protocol.json',O/'results.json',graph,pathlib.Path(__file__).resolve()]}
 for spec in protocol['selected_NETs']:
  net=spec['net_id'];pcp=pathlib.Path(spec['potential_file']);pc=array('Q');pc.frombytes(pcp.read_bytes());cutp=O/f'net_{net}_cost_tight_cut.bin';cut=cutp.read_bytes();assert len(pc)==len(cut)==len(caps) and set(cut)<={0,1};source=spec['source'];sink=spec['sink'];assert pc[source]==0 and pc[sink]==spec['floor']==spec['budget'];assert cut[source]==1 and cut[node]==0
  checked=0;tight=0;closure=0
  for a,b,w in zip(us,vs,weights):
   if caps[a]<=0 or caps[b]<=0 or kinds[a]=='SINK' or kinds[b]=='SOURCE':continue
   assert pc[b]<=pc[a]+w;checked+=1
   if pc[b]==pc[a]+w:
    tight+=1
    if a!=node and b!=node and cut[a]:assert cut[b];closure+=1
  tp=R/f'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19/net_{net}_original.json';tree=json.loads(tp.read_text());assert tree['source']==source and tree['sink_floors'][str(sink)]==tree['sink_budgets'][str(sink)]==spec['budget'];current=source;value=0;seen={source}
  for eid in tree['paths'][str(sink)]:
   assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==current and b not in seen and caps[b]>0 and kinds[a]!='SINK' and kinds[b]!='SOURCE';current=b;seen.add(b);value+=w
  assert current==sink and value==pc[sink]
  original=next(row for row in result['rows'] if row['net_id']==net);assert original['sink_unreachable_without_node']==(cut[sink]==0)
  row=dict(net_id=net,source=source,sink=sink,capacity1_node=node,original_budget_units_1e18=spec['budget'],all_original_edges_RC_dual_checked=checked,all_RC_tight_edges=tight,outgoing_cut_closure_edges_checked=closure,all_budget_feasible_paths_require_node=(cut[sink]==0));rows.append(row)
  for p in [pcp,cutp,tp]:bindings[str(p)]=sha(p)
  print(row,flush=True)
 proven=all(row['all_budget_feasible_paths_require_node'] for row in rows);assert result['proposed_capacity_budget_infeasibility']==proven
 status='FROZEN_DIAGNOSTIC_BUDGETS_GLOBALLY_CAPACITY_INFEASIBLE_BY_RC_ONLY_CUTS' if proven else 'RC_ONLY_CUTS_VALID_BUT_SELECTED_NODE_NOT_PROVEN_REQUIRED'
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status=status,rows=rows,bindings=bindings,argument='For zero-slack sink, all budget-feasible paths must be cost-tight in feasible full-RR potentials. The cut contains source, excludes the node, and is closed under every eligible RC-tight edge avoiding the node. If sink lies outside, every budget path uses node. Distinct NETs exceeding original XML node capacity contradict simultaneous feasibility.',scope='Full graph and arbitrary path hop counts for the fixed two source/sink zero-slack budgets only. Not global native infeasibility, original RouteCast quality impossibility, arbitrary new budgets or complete research.'),f,indent=2)
 print(status,flush=True)
if __name__=='__main__':main()
