"""Close complete XTEA raw-floor candidate without initial-state parity claims."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_raw_floor_proxy_budget_fixture_v1_2026-10-17';M=D/'model';OLD=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model'
cache={}
def sha(p):
 p=Path(p);st=p.stat();k=(str(p),st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns,st.st_ctime_ns)
 if k not in cache:
  h=hashlib.sha256()
  with p.open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  a=p.stat();assert (a.st_dev,a.st_ino,a.st_size,a.st_mtime_ns,a.st_ctime_ns)==k[1:];cache[k]=h.hexdigest()
 return cache[k]
bindings={str(Path(__file__).resolve()):sha(__file__)}
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
terminal=load(D/'pipeline_terminal.json');assert terminal['all_stages_completed'] and terminal['exit_status']==0
for stage in ['model','initial_audit','sketch_audit','event_audit']:
 t=load(D/(stage+'_terminal.json'));assert t['exit_status']==0 and t['address_space_limit_bytes']==2*2**30
 m=load(D/(stage+'_process.json'));p=Path('/proc')/str(m['pid'])/'stat'
 if p.exists():assert p.read_text().rsplit(')',1)[1].split()[19]!=m['start_stat'].rsplit(')',1)[1].split()[19]
for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
 v=load(M/name);assert v['completed']==2450 and v['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
 for k,h in v['bindings'].items():assert sha(k)==h;assert k not in bindings or bindings[k]==h;bindings[k]=h
v=load(M/'verification.json');assert v['events']==2896 and v['complete_primary_search_after_rejection_and_isolated_witnesses_pass']
assert sha(M/'floors.json')==sha(OLD/'floors.json');bindings[str(OLD/'floors.json')]=sha(OLD/'floors.json')
a=load(M/'initial.json');b=load(OLD/'initial.json')
aa={r['connection_id']:r for r in a['records']};bb={r['connection_id']:r for r in b['records']};assert set(aa)==set(bb) and len(aa)==2450
changed=0
for cid in aa:
 x=json.loads(json.dumps(aa[cid]));y=json.loads(json.dumps(bb[cid]));px=x['answer'].pop('physical_edge_ids');py=y['answer'].pop('physical_edge_ids');assert x==y;changed+=px!=py
assert changed==terminal['changed_initial_paths']==383
protocol=load(M/'protocol.json');assert protocol['budget_policy']=='original_budget_plus_ceil_one_minus_criticality_times_floor_v1' and 'raw-only' in protocol['initial_floor_policy']
out=dict(bindings=bindings,all_pass=True,all2450_connections_and2896events_all3_independent_audits_pass=True,all_initial_nonpath_record_fields_equal_including_floors_budgets_and_delays=True,floors_byte_identical=True,changed_equal_cost_initial_paths=changed,initial_ledger_parity_claimed=False,final_overflow=v['overflow_units'],scope='Complete exposed XTEA producer/auditor correctness. Changed equal-cost initial paths intentionally permit different demand and feedback trajectory. Not unchanged final paths, metrics, native utility, paired timing or end-to-end gain.',promoted=False)
with (D/'closed_admission_v1.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
