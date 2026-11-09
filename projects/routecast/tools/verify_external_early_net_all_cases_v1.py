"""Audit all observation outputs and split source/target first-iteration response."""
import json,csv,re,math,sys
from pathlib import Path
from collections import Counter,defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from stream_native_route_audit_expat_v3 import audit
from verify_external_initial_response_observer_source_v1 import trees
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_early_net_observer_v1_2026-10-19';P=E/'prospective_external_family_temporal_prior_errors_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def observe(folder,endpoint,out):
 proof=read(folder/'verification.json');assert proof['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(sha(p)==h for p,h in proof['bindings'].items());ep=read(endpoint);rows=list(csv.DictReader((folder/'initial_connections.tsv').open(),delimiter='\t'));assert len(rows)==15616;by={(int(r['net']),int(r['pin'])):r for r in rows};assert len(by)==len(rows)
 assert Counter((int(r['net']),int(r['source_rr']),int(r['sink_rr'])) for r in rows)==Counter((q['net_id'],q['source'],q['sink']) for q in ep['connections'])
 for r in rows:assert math.isfinite(float(r['delay_s'])) and float(r['delay_s'])>=0 and 0<=float(r['criticality'])<=1
 pairs=[tuple(map(int,m)) for m in re.findall(r'^RC_FIRST_NET_ORDER (\d+) (\d+)$',(folder/'native.log').read_text(),re.M)];assert [i for i,n in pairs]==list(range(len(pairs))) and len({n for i,n in pairs})==len(pairs)
 physical=audit(ep['inputs']['graph']['path'],folder/'first_iteration.route');assert Counter((q['net_id'],q['source'],q['sink']) for q in physical['connections'])==Counter((q['net_id'],q['source'],q['sink']) for q in ep['connections']);out.write_text(json.dumps(physical)+'\n')
 supports={n:{int(x.split()[1]) for x in lines if x.split()[2] in ['CHANX','CHANY']} for n,lines in trees(folder/'first_iteration.route').items()};return by,[n for i,n in pairs],supports

def main():
 terminal=read(D/'targets_terminal.json');assert terminal['status']=='ALL3_OBSERVER_NATIVE_CASES_PHYSICAL_CANONICAL_PASS';out=D/'all_case_audit_v1';out.mkdir(exist_ok=False);manifest=read(D/'target_manifest.json');source=read(D/'manifest.json')['cases'][0];oldrows,oldorder,oldsupport=observe(D/'source',source['endpoint'],out/'source_first_physical.json');bindings={str(Path(__file__).resolve()):sha(__file__),str(D/'targets_terminal.json'):sha(D/'targets_terminal.json')};summary=[]
 for c in manifest['cases']:
  case=c['case'];folder=Path(c['output']);original=E/'prospective_external_family_supplementary_development_v1_2026-10-19/native'/case;assert trees(folder/'output.route')==trees(original/'output.route');assert read(folder/'physical_audit.json')['node_occupancy']==read(original/'physical_audit.json')['node_occupancy'];p=out/(case.replace('/','_')+'_first_physical.json');rows,order,support=observe(folder,c['endpoint'],p);assert rows.keys()==oldrows.keys();kinds={r['net_id']:'edited' if r['edit_mask'] else 'clean' for r in read(P/case/'NETs.json')};counts=defaultdict(Counter);changed=[]
  for k,a in oldrows.items():
   b=rows[k];endpoint_changed=(a['source_rr'],a['sink_rr'])!=(b['source_rr'],b['sink_rr']);delay_changed=float(a['delay_s'])!=float(b['delay_s']);crit_changed=float(a['criticality'])!=float(b['criticality']);group='edited_endpoint' if endpoint_changed else 'unchanged_endpoint';counts[group].update(connections=1,delay_changed=int(delay_changed),criticality_changed=int(crit_changed));
   if delay_changed or crit_changed:changed.append(dict(net=k[0],pin=k[1],NET_class=kinds[k[0]],endpoint_changed=endpoint_changed,delay_changed=delay_changed,criticality_changed=crit_changed,old_delay=a['delay_s'],new_delay=b['delay_s'],old_criticality=a['criticality'],new_criticality=b['criticality']))
  supportstats=defaultdict(Counter)
  for net in kinds:
   a,b=oldsupport[net],support[net];supportstats[kinds[net]].update(NETs=1,changed_NETs=int(a!=b),removed=len(a-b),added=len(b-a))
  row=dict(case=case,final_route_identical=True,actual_first_NET_order_identical=order==oldorder,initial_connection_changes={k:dict(v) for k,v in counts.items()},first_iteration_support_changes={k:dict(v) for k,v in supportstats.items()});summary.append(row);print(json.dumps(row),flush=True);detail=out/(case.replace('/','_')+'_initial_changes.json');detail.write_text(json.dumps(changed,indent=2)+'\n')
  for f in [p,detail,folder/'verification.json',folder/'initial_connections.tsv',folder/'first_iteration.route',folder/'native.log',original/'output.route']:bindings[str(f)]=sha(f)
 for f in [D/'source/verification.json',D/'source/initial_connections.tsv',D/'source/first_iteration.route',D/'source/native.log',out/'source_first_physical.json']:bindings[str(f)]=sha(f)
 assert all(sha(p)==h for p,h in bindings.items());(D/'all_case_verification_v1.json').write_text(json.dumps(dict(status='ALL4_FIRST_ITERATION_XML_PATHS_AND_ALL3_FINAL_ROUTE_EQUIVALENCE_VERIFIED',rows=summary,bindings=bindings,scope='Initial printed decimal values compared as float roundtrip; no independent STA recomputation or hold export. First iteration physical trees may overflow, no legal route/QoR claim. CIDs use native NET/pin identity; actual NET call sequence compared, not individual sink scheduling. Original labels and gates unchanged.'),indent=2)+'\n')
if __name__=='__main__':main()
