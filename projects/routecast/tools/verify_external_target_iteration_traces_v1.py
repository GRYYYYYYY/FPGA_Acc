"""Independent original XML edge/delay checks and exact all6 observer final equivalence."""
import json,csv,sys,math,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from zero_rc_budget_certificate_graph_v1 import load_graph
from verify_external_native_seed_feasibility_v1 import route_nodes
D=R/'experiments/prospective_external_family_native_target_iteration_observer_v1_2026-10-19';BASE=R/'experiments/prospective_external_family_native_seed_delay_handoff_v1_2026-10-19';G=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/w160/source/rr_graph.xml'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def main():
 v=read(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());g=load_graph(G);arcs=set(zip(g['us'],g['vs'],g['switches']));bindings={str(D/'verification.json'):sha(D/'verification.json'),str(G):sha(G),str(Path(__file__).resolve()):sha(__file__)};results=[]
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';out=D/case/'native';old=BASE/case/'native';a,b=read(out/'verification.json'),read(old/'verification.json');assert a['status']==b['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(a[k]==b[k] for k in ('wirelength','diagnostic_cpd_ns','iterations'));assert route_nodes(out/'output.route')==route_nodes(old/'output.route')
   for name in ('initial_connections.tsv','first_iteration.route'):assert sha(out/name)==sha(old/name)
   path=out/'target_iterations.tsv';groups={};count=arccount=0
   for q in csv.DictReader(path.open(),delimiter='\t'):
    it=int(q['iteration']);phase=q['phase'];key=(int(q['net']),int(q['pin']));id=(phase,it,key);assert id not in groups;crit=float(q['criticality']);delay=float(q['delay_s']);assert math.isfinite(crit) and 0<=crit<=1 and math.isfinite(delay) and delay>=0
    nodes=[x.split(':') for x in q['path_sink_to_source_node_switch_occ_hist_pres'].strip(',').split(',') if x];ids=[int(x[0]) for x in nodes];assert len(ids)==len(set(ids));raw=0
    for n in nodes:assert int(n[2])>=0 and math.isfinite(float(n[3])) and float(n[3])>=1 and math.isfinite(float(n[4])) and float(n[4])>=1
    for child,parent in zip(nodes,nodes[1:]):
     u,w,sw=int(parent[0]),int(child[0]),int(child[1]);assert (u,w,sw) in arcs;raw+=g['weights'][sw];arccount+=1
    if phase=='AFTER':assert nodes and g['types'][ids[0]]=='SINK' and g['types'][ids[-1]]=='SOURCE';assert math.isclose(delay,raw/1e18,rel_tol=2e-6,abs_tol=1e-15),(case,it,key,delay,raw)
    groups[id]=q;count+=1
   first={key for phase,it,key in groups if phase=='BEFORE' and it==1};assert first
   assert len(groups)==len(first)*2*a['iterations']
   for it in range(1,a['iterations']+1):
    for key in first:
     assert ('BEFORE',it,key) in groups and ('AFTER',it,key) in groups
     if it>1:assert groups['BEFORE',it,key]['delay_s']==groups['AFTER',it-1,key]['delay_s'];assert groups['BEFORE',it,key]['criticality']==groups['AFTER',it-1,key]['criticality']
   for p in [path,out/'verification.json',old/'verification.json',out/'output.route',old/'output.route']:bindings[str(p)]=sha(p)
   results.append(dict(case=case,iterations=a['iterations'],targets=len(first),rows=count,original_XML_path_arcs_checked=arccount,exact_final_native_metrics_and_node_unions=True,exact_initial_and_first_route_bytes=True));print(json.dumps(results[-1]),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'trace_verification_v1.json').write_text(json.dumps(dict(status='ALL6_OBSERVER_EQUIVALENCE_AND_ORIGINAL_XML_TRACE_PATHS_CHECKED',rows=results,bindings=bindings,scope='PRE snapshot is before whole iteration, not exact perNET invocation frontier. POST pressure after cost update; no causal attribution or paid timing.'),indent=2)+'\n')
if __name__=='__main__':main()
