"""Fixed largest final-regression CID percase, descriptive divergence/growth only."""
import json,csv,hashlib
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];D=R/'experiments/prospective_external_family_native_target_iteration_observer_v1_2026-10-19';T=R/'experiments/prospective_external_family_worst_path_first_iteration_v1_2026-10-19';C=R/'experiments/prospective_external_family_seed_retention_delay_diagnosis_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def path(q):return [(int(x.split(':')[0]),int(x.split(':')[1])) for x in q['path_sink_to_source_node_switch_occ_hist_pres'].strip(',').split(',') if x]
GRAPH=None
def pressure(q):
 ns=[x.split(':') for x in q['path_sink_to_source_node_switch_occ_hist_pres'].strip(',').split(',') if x]
 return dict(max_occ=max([int(n[2]) for n in ns],default=0),overused_nodes=sum(int(n[2])>GRAPH['caps'][int(n[0])] for n in ns),overflow_units=sum(max(0,int(n[2])-GRAPH['caps'][int(n[0])]) for n in ns),overused_resources=[dict(node=int(n[0]),type=GRAPH['types'][int(n[0])],occ=int(n[2]),capacity=GRAPH['caps'][int(n[0])],history=float(n[3]),present=float(n[4])) for n in ns if int(n[2])>GRAPH['caps'][int(n[0])]],max_history=max([float(n[3]) for n in ns],default=0),max_present=max([float(n[4]) for n in ns],default=0))
def concise(q):return dict(iteration=int(q['iteration']),delay_ns=float(q['delay_s'])*1e9,criticality=float(q['criticality']),pres_fac=float(q['pres_fac']),path_nodes=len(path(q)),**pressure(q))
def main():
 global GRAPH
 graphpath=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml';GRAPH=load_graph(graphpath)
 v=read(D/'trace_verification_v1.json');assert all(sha(p)==h for p,h in v['bindings'].items());bindings={str(graphpath):sha(graphpath),str(D/'trace_verification_v1.json'):sha(D/'trace_verification_v1.json'),str(T/'diagnosis.json'):sha(T/'diagnosis.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for case in read(T/'diagnosis.json')['rows']:
  name=case['case'];top=max(case['rows'],key=lambda q:q['final_delta_as']);assert len(top['CID_candidates'])==1;cid=top['CID_candidates'][0];p=C/name/'connections.json';q=next(q for q in read(p) if q['connection_id']==cid);bindings[str(p)]=sha(p);key=(q['native_net_id'],q['local_pin']);phases={}
  for arm in ('cold','seed'):
   p=D/name/arm/'native/target_iterations.tsv';bindings[str(p)]=sha(p);phases[arm]={}
   for r in csv.DictReader(p.open(),delimiter='\t'):
    if (int(r['net']),int(r['pin']))==key:assert r['name']==q['net_name'];phases[arm][(r['phase'],int(r['iteration']))]=r
  cold,seed=phases['cold'],phases['seed'];h=min(max(it for ph,it in cold),max(it for ph,it in seed));delaydiff=next((it for it in range(1,h+1) if cold['AFTER',it]['delay_s']!=seed['AFTER',it]['delay_s']),None);pathdiff=next((it for it in range(1,h+1) if path(cold['AFTER',it])!=path(seed['AFTER',it])),None)
  after=[seed['AFTER',it] for it in range(1,max(it for ph,it in seed)+1)];jumps=[(float(b['delay_s'])-float(a['delay_s']),a,b) for a,b in zip(after,after[1:])];jump=max(jumps,key=lambda t:t[0]);row=dict(case=name,CID=cid,net=q['net_name'],common_horizon=h,first_POST_delay_difference=delaydiff,first_POST_exact_path_difference=pathdiff,largest_seed_delay_increase_ns=jump[0]*1e9,before_largest_increase=concise(jump[1]),after_largest_increase=concise(jump[2]),PRE_snapshot_for_increase=concise(seed['BEFORE',int(jump[2]['iteration'])]),seed_last=concise(after[-1]),seed_last_delay_matches_selected_final=abs(float(after[-1]['delay_s'])-top['seed_final_as']/1e18)<1e-14)
  if delaydiff:row['first_delay_difference_pair']={a:concise(phases[a]['AFTER',delaydiff]) for a in ('cold','seed')}
  rows.append(row);print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'growth_diagnosis_v2.json').write_text(json.dumps(dict(status='ALL3_FIXED_MAX_REGRESSION_CONNECTION_ITERATION_GROWTH_LOCATED',rows=rows,bindings=bindings,scope='Iteration-boundary snapshots only. Overuse uses actual original XML capacities; max_occ alone is not congestion. Max path pressure need not be resource causing reroute. No perNET invocation frontier or causal owner identity. Posthoc target identities cannot become label-free policy.'),indent=2)+'\n')
if __name__=='__main__':main()
