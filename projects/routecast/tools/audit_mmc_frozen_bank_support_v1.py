"""Rebuild every frozen A/B NET support from original XML physical paths."""
import json,time,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
D=R/'experiments/mmc_frozen_bank_support_v1_2026-10-21';D.mkdir(exist_ok=True)
P=R/'experiments/mmc_bank_mandatory_capacity_v1_2026-10-21/verification.json'
F=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json'
plan=json.loads(P.read_text());frozen=json.loads(F.read_text());bindings={str(p):sha(p) for p in [P,F,Path(__file__)]}
cases=[];wanted=set();graph=None;start=time.perf_counter()
for row in plan['rows']:
 bankfile=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/row['case']/'banks.jsonl'
 assert sha(bankfile)==frozen['bindings'][str(bankfile)];bindings[str(bankfile)]=sha(bankfile)
 bankrows=[json.loads(x) for x in bankfile.open()];banks={x['net_id']:x for x in bankrows};assert len(banks)==len(bankrows)
 epfile=Path(row['endpoint']);ep=json.loads(epfile.read_text());bindings[str(epfile)]=sha(epfile)
 g=Path(ep['inputs']['graph']['path']);assert graph is None or graph==g;graph=g;assert sha(g)==ep['graph_sha256'];bindings[str(g)]=sha(g)
 endpoints={q['connection_id']:q for q in ep['connections']};assert len(endpoints)==len(ep['connections'])
 arms={}
 for arm,path in row['frames'].items():
  assert sha(path)==plan['bindings'][path];bindings[path]=sha(path)
  records=json.loads(Path(path).read_text())['records'];assert len(records)==len(endpoints) and {q['connection_id'] for q in records}==set(endpoints)
  for q in records:
   assert all(q[k]==endpoints[q['connection_id']][k] for k in ['net_id','source','sink']);wanted.update(q['answer']['physical_edge_ids'])
  arms[arm]=records
 cases.append((row['case'],banks,arms))
arcs={};kinds=[];capacities=[];stack=[];edge_index=0

def begin(name,a):
 global edge_index
 parent=stack[-1] if stack else None;stack.append(name)
 if name=='node' and parent=='rr_nodes':
  assert int(a['id'])==len(kinds);kinds.append(a['type']);capacities.append(int(a['capacity']))
 elif name=='edge' and parent=='rr_edges':
  if edge_index in wanted:arcs[edge_index]=(int(a['src_node']),int(a['sink_node']))
  edge_index+=1

def end(name):assert stack.pop()==name
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
with graph.open('rb') as f:
 while block:=f.read(8*1024*1024):parser.Parse(block,False)
parser.Parse(b'',True);assert set(arcs)==wanted
rows=[]
for case,banks,arms in cases:
 for arm,records in arms.items():
  unions=defaultdict(set);parents=defaultdict(dict)
  for q in records:
   net=q['net_id'];node=q['source'];assert kinds[node]=='SOURCE';seen={node};unions[net].add(node)
   for eid in q['answer']['physical_edge_ids']:
    src,dst=arcs[eid];assert src==node and dst not in seen and capacities[dst]>0
    if dst in parents[net]:assert parents[net][dst]==src
    parents[net][dst]=src;seen.add(dst);unions[net].add(dst);node=dst
   assert node==q['sink'] and kinds[node]=='SINK'
  assert set(unions)==set(banks)
  for net,owned in unions.items():assert owned==set(banks[net][arm]) and len(banks[net][arm])==len(owned)
  rows.append({'case':case,'arm':arm,'NETs':len(unions),'connections':len(records),'all_original_path_supports_equal_frozen_banks':True})
  print('BANK SUPPORT VERIFIED',case,arm,len(unions),len(records),flush=True)
assert all(sha(p)==h for p,h in bindings.items())
result={'status':'ALL3_FULL_A_B_BANK_SUPPORTS_REBUILT_FROM_ORIGINAL_XML_PATHS','rows':rows,'bindings':bindings,'seconds':time.perf_counter()-start,'scope':'All endpoint-bound complete source-to-sink paths, positive node capacities, acyclic paths and shared node parents; exact full support equality to frozen banks. No delay, budget, native legality, joint capacity or gain claim.'}
p=D/'independent_verification_v1.json';tmp=p.with_suffix('.tmp');tmp.write_text(json.dumps(result,indent=2)+'\n');tmp.replace(p)
