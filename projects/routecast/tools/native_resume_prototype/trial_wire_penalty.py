"""Candidate-own worst-path NETs; freeze other NET ownership and query all released sinks."""
import json,re,struct,subprocess,sys,time
import xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:3]);penalty_ns=Fraction(sys.argv[3]);base=ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07';out=ROOT/f'experiments/native_resume_wire_penalty_{sys.argv[3]}_w{w}_m{i}_2026-10-07';out.mkdir(exist_ok=False);start=time.perf_counter()
verified=ROOT/'experiments/native_resume_singlepass_floor_controls_2026-10-07/verification.json';proof=json.loads(verified.read_text());assert all(sha(f)==h for f,h in proof['bindings'].items());route=base/'canonical/design.route';report=base/'canonical/report_timing.setup.rpt';body=report.read_text().split('#Path 2')[0];paths=physical_paths(route);selected=[]
for atom,port in re.findall(r'^(\S+)\.(inpad|out)\[\d+\]\s+\(',body,re.M):
 if atom in paths and paths[atom] and atom not in selected:selected.append(atom)
assert selected
endpoint=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(endpoint.read_text());graph,digest,nodes,f,rc,queries=load_endpoints(endpoint);names=meta['net_names'];owners={name:{n for p in ps for n,sw in p} for name,ps in paths.items() if ps};occupancy=Counter(n for union in owners.values() for n in union);assert all(v<=f['capacities'][n] for n,v in occupancy.items());prepared=time.perf_counter()
binary=ROOT/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor';prior=base/'floor_context/epoch_1/receipt.json';unconditional={x['query']['connection_id']:x['minimum_integer'] for x in json.loads(prior.read_text())['answers']};slot_by_arc={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};initial=[rc.initial(n) for n in range(len(nodes))]
span={}
for event,n in ET.iterparse(graph,events=('end',)):
 if n.tag=='node':
  if n.get('type') in ('CHANX','CHANY'):
   loc=n.find('loc');span[int(n.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
  n.clear()
penalty=penalty_ns*rc.scale/10**9;assert penalty.denominator==1;penalty=int(penalty)
weights=[d+penalty*span.get(f['dest_ranks'][slot],0) for slot,d in enumerate(rc.increments)];assert max(initial)+len(nodes)*max(weights)<2**64
protocol=dict(penalty_ns=str(penalty_ns),inputs={str(p):sha(p) for p in (verified,route,report,endpoint,graph,binary,prior,Path(__file__))},selected_net_names=selected,policy='All external NET drivers appearing on own final worst setup path; all sinks per selected NET. Freeze all other NET node-union ownership; release whole selected NET. Graph-model additive RC only, no cold labels; final candidate acquisition/proof cost excluded.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for index,name in enumerate(selected):
 qs=[q for q in queries if names[str(q['net_id'])]==name];assert qs
 other={n:count-int(n in owners[name]) for n,count in occupancy.items()};capacity=[max(0,f['capacities'][n]-other.get(n,0)) for n in range(len(nodes))];assert all(capacity[q['source']]>0 and capacity[q['sink']]>0 for q in qs)
 payload=out/f'net_{index}.bin'
 with payload.open('wb') as stream:
  for values in ([0x5243464c4f4f5231,len(nodes),len(f['edge_ids']),len(qs)],f['row_offsets'],f['dest_ranks'],weights,capacity,initial,[v for q in qs for v in (q['connection_id'],q['source'],q['sink'])]):
   for v in values:stream.write(struct.pack('<Q',v))
 file=out/f'net_{index}.jsonl'
 with file.open('w') as log:subprocess.run([str(binary),str(payload)],stdout=log,stderr=subprocess.PIPE,check=True,timeout=120)
 answers={a['connection_id']:a for a in map(json.loads,file.read_text().splitlines())};records=[];newunion=set();parents={};conflicts=[]
 for q in qs:
  a=answers[q['connection_id']];assert a['minimum_integer'] is not None
  edges=[f['edge_ids'][s] for s in a['slots']];delay=rc.path(q['source'],q['sink'],edges);assert delay>=unconditional[q['connection_id']];assert rc.initial(q['source'])+sum(weights[s] for s in a['slots'])==a['minimum_integer']
  node=q['source'];newunion.add(node)
  for s in a['slots']:
   dest=f['dest_ranks'][s];parent=(node,f['switch_ids'][s]);assert capacity[dest]>0
   if dest in parents and parents[dest]!=parent:conflicts.append(dest)
   parents[dest]=parent;node=dest;newunion.add(node)
  current=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(current)==1;cp=current[0];slots=[slot_by_arc[u,v,switch] for (u,_),(v,switch) in zip(cp,cp[1:])];current_delay=rc.path(q['source'],q['sink'],[f['edge_ids'][s] for s in slots])
  records.append(dict(query=q,unconditional_integer=unconditional[q['connection_id']],conditional_integer=delay,weighted_integer=a['minimum_integer'],current_path_additive_integer=current_delay,physical_edge_ids=edges,changed_path=edges!=[f['edge_ids'][s] for s in slots]))
 assert not conflicts and all(other.get(n,0)+1<=f['capacities'][n] for n in newunion)
 old_wire=sum(span.get(n,0) for n in owners[name]);new_wire=sum(span.get(n,0) for n in newunion)
 rows.append(dict(old_wire=old_wire,new_wire=new_wire,wire_budget_pass=new_wire<=old_wire,all_path_delays_no_worse=all(r['conditional_integer']<=r['current_path_additive_integer'] for r in records),net=name,records=records,other_occupancy={str(n):v for n,v in other.items() if v},new_union=sorted(newunion),consistent_parent_tree=True,other_net_capacity_feasible_union=True,payload_sha256=sha(payload),output_sha256=sha(file),conditional_floor_raised_connections=sum(x['conditional_integer']>x['unconditional_integer'] for x in records),positive_current_gap_connections=sum(x['current_path_additive_integer']>x['conditional_integer'] for x in records)));print(w,name,len(records),'raised',rows[-1]['conditional_floor_raised_connections'],'positive gaps',rows[-1]['positive_current_gap_connections'],'wire',old_wire,new_wire,'delay_no_worse',rows[-1]['all_path_delays_no_worse'],flush=True)
assert all(sha(p)==h for p,h in protocol['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),scale=rc.scale,preparation_seconds=prepared-start,query_and_proof_seconds=time.perf_counter()-prepared,total_seconds=time.perf_counter()-start,rows=rows,scope='Fixed weighted additive-RC/channel-span search; wholeNET union budgets evaluated after search. Not an exact union-constrained optimizer. Whole released NET independent shortest paths share a predecessor tree and respect frozen otherNET node capacities. Not native pin/configurability/timing validation, not shared-tree loaded STA or simultaneous replacement of multiple NETs. Selection retrospective own final candidate, no cold oracle.'),indent=2)+'\n')
