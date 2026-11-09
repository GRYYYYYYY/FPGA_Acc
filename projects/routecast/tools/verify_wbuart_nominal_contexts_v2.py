"""Independent typed graph/DAG, atom float aggregation and all clock getter joins."""
import csv,hashlib,json,math,struct
from collections import Counter,defaultdict,deque
from pathlib import Path
from load_native_clock_constraints_v1 import load,resolve,value,serializable
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_nominal_contexts_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bits(v):return struct.pack('>f',float(v)).hex()
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def main():
 terminal=json.loads((D/'terminal.json').read_text());proto=json.loads((D/'protocol.json').read_text());assert len(terminal['rows'])==12 and all(r['passed'] for r in terminal['rows'])
 for n,h in proto['bindings'].items():assert sha(Path(n))==h
 bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/load_native_clock_constraints_v1.py',D/'terminal.json',D/'protocol.json']};rows=[]
 for job in proto['jobs']:
  d=D/job['case'];receipt=json.loads((d/'receipt.json').read_text());assert receipt['capture_passed'] and receipt['exit_status']==0
  for n,h in receipt['bindings'].items():assert sha(Path(n))==h
  nodes={};edges=table(d/'timing_edges.tsv')
  for r in table(d/'timing_nodes.tsv'):nid=int(r['node']);assert nid not in nodes;nodes[nid]=int(r['type'])
  assert len({int(e['edge']) for e in edges})==len(edges);inc=Counter();following=defaultdict(list)
  for e in edges:
   u,v=int(e['source']),int(e['sink']);assert u in nodes and v in nodes and int(e['disabled']) in (0,1);assert all(math.isfinite(float(e[k])) for k in ['value_max_or_setup_s','value_min_or_hold_s'])
   if not int(e['disabled']):following[u].append(v);inc[v]+=1
  queue=deque(n for n in nodes if inc[n]==0);seen=0
  while queue:
   n=queue.popleft();seen+=1
   for v in following[n]:
    inc[v]-=1
    if inc[v]==0:queue.append(v)
  assert seen==len(nodes)
  atoms=table(d/'timing_atoms.tsv');assert len({int(a['atom_pin']) for a in atoms})==len(atoms);groups=defaultdict(list);nodegroups=defaultdict(set)
  for a in atoms:
   for key in ['external_node','internal_node']:
    if a[key]:assert int(a[key]) in nodes
   if a['raw_criticality']:
    key=int(a['native_net']),int(a['local_pin']);assert key[1]>0;groups[key].append(a);nodegroups[int(a['external_node'])].add(key)
  previous=Path(job['previous_timing_directory']);payload=previous/'initial_connection_criticalities.json';original=json.loads(payload.read_text());assert len(groups)==len(original)==2493 and sum(map(len,groups.values()))==3892
  assert sum(r['atom_count'] for r in original)==3892
  priorproof=json.loads((previous/'verification.json').read_text());assert priorproof['atom_rows']==4493 and priorproof['ignored_clock_pins']==71 and priorproof['ignored_nonclock_pins']==2
  for r in original:
   gs=groups[r['native_net_id'],r['local_sink_pin']];assert len(gs)==r['atom_count'];assert bits(max(float(a['raw_criticality']) for a in gs))==r['raw_criticality_bits'] and bits(min(float(a['setup_slack_s']) for a in gs))==r['slack_bits']
  initial={(int(r['net']),int(r['pin'])):r for r in table(d/'initial_connections.tsv')};assert len(initial)==2493 and set(initial)==set(groups)
  for r in original:assert (int(initial[r['native_net_id'],r['local_sink_pin']]['source_rr']),int(initial[r['native_net_id'],r['local_sink_pin']]['sink_rr']))==(r['source_rr'],r['target_rr'])
  constraints=load(d/'clock_constraints.tsv');domains=set(constraints['domains']);sinks={n for n,t in nodes.items() if t==1};assert domains and all(a['source']==-1 or a['source'] in nodes for a in constraints['domains'].values());assert all(n in nodes for n in constraints['constants'])
  for (kind,s,t,c),v in constraints['clock_constraints'].items():assert s in domains and t in domains and (c==-1 or c in sinks)
  for (kind,delay,n,domain),v in constraints['io_constraints'].items():assert n in nodes and domain in domains
  queried=set()
  for q in constraints['native_queries']:
   key=q['source'],q['sink'],q['capture'];assert key not in queried;queried.add(key);assert resolve(constraints,*key)=={k:q[k] for k in ['setup','hold','analyze']}
  assert queried=={(s,t,n) for s in domains for t in domains for n in sinks|{-1}}
  for q in constraints['native_latency_queries']:assert q['value']==constraints['latencies'].get((q['kind'],q['domain']),value('0'))
  for q in constraints['native_uncertainty_queries']:
   for mode in ['SETUP','HOLD']:assert q[mode.lower()]==constraints['uncertainties'].get((mode,q['source'],q['sink']),value('0'))
  machine=d/'clock_constraints.json';machine.write_text(json.dumps(serializable(constraints),indent=2)+'\n');candidates=[];covered=set()
  for e in edges:
   if int(e['type'])!=3 or int(e['disabled']):continue
   keys=nodegroups.get(int(e['sink']),set())
   for key in keys:
    covered.add(key);candidates.append({'edge':int(e['edge']),'native_net':key[0],'local_pin':key[1],'nominal_local_offset_s':float(e['value_max_or_setup_s'])-float(initial[key]['delay_s'])})
  assert covered==set(groups);candidatefile=d/'external_edge_candidates.json';candidatefile.write_text(json.dumps(candidates)+'\n');vp=d/'verification.json';paths=[d/'receipt.json',d/'protocol.json',d/'native.log',*[d/n for n in ['timing_nodes.tsv','timing_edges.tsv','timing_atoms.tsv','initial_connections.tsv','clock_constraints.tsv']],machine,candidatefile,payload];record={'status':'CURRENT_TIMING_GRAPH_ATOM_FLOATS_AND_ALL_NATIVE_CLOCK_QUERIES_VERIFIED','case':job['case'],'timing_nodes':len(nodes),'timing_edges':len(edges),'atom_pins':len(atoms),'routing_connections':2493,'data_atom_rows':3892,'all_snapshot_atom_rows':4493,'ignored_snapshot_atom_rows':601,'enabled_DAG_verified':True,'clock_domains':len(domains),'domain_names':[r['name'] for r in constraints['domains'].values()],'resolved_clock_capture_queries':len(queried),'external_edge_candidates':len(candidates),'CID_source_pin_binding_and_offset_invariance_proven':False,'new_target_route_labels':False,'bindings':{str(p):sha(p) for p in paths}};vp.write_text(json.dumps(record,indent=2)+'\n');rows.append({'case':job['case'],'verification':str(vp),'sha256':sha(vp),'nodes':len(nodes),'edges':len(edges),'clock_queries':len(queried)});print('WBUART_NOMINAL_CONTEXT_VERIFIED',job['case'],len(nodes),len(edges),len(queried),flush=True)
 for n,h in bindings.items():assert sha(Path(n))==h
 (D/'verification.json').write_text(json.dumps({'status':'ALL12_CURRENT_NATIVE_TIMING_DAGS_ATOM_AGGREGATES_AND_CLOCK_GETTERS_VERIFIED','rows':rows,'bindings':{**bindings,**{r['verification']:r['sha256'] for r in rows}},'dynamic_fixed_nominal_feedback_qualified':False,'new_target_route_labels':False,'strict_unseen_admitted':False,'scope':'Fresh nominal graph/clock metadata and initial atom aggregate parity only; external candidates not yet exact source-pin/CID/component certificates. Not post-edit native STA or complete predictor inputs.'},indent=2)+'\n')
if __name__=='__main__':main()
