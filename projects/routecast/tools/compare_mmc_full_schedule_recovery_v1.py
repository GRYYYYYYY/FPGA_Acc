"""Compare audited full and affected schedules; historical times are descriptive."""
import collections, datetime, hashlib, json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
F=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12'
A=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/model'
bindings={}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def read(p):
 bindings[str(p)]=sha(p)
 return json.loads(p.read_text())
def authenticate(p):
 d=read(p)
 for name,digest in d['bindings'].items():
  q=Path(name);assert sha(q)==digest,name;bindings[name]=digest
 return d
read(Path(__file__).resolve()) if False else bindings.update({str(Path(__file__).resolve()):sha(Path(__file__).resolve())})
protocol=authenticate(F/'comparison_analysis_protocol_v1.json')
for name in ['model','initial_audit','sketch_audit','event_audit','pipeline']:
 assert read(F/(name+'_terminal.json'))['exit_status']==0
for root in [F/'model',A]:
 for name in ['initial_physical_verification.json','sketch_physical_verification.json','verification.json']:
  d=authenticate(root/name)
  assert d['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
  if name=='verification.json':assert d['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
for name in ['initial.json','round0.json']:
 assert read(F/'model'/name)==read(A/name)
a=read(A/'round1.json');f=read(F/'model/round1.json')
ar=read(A/'receipt.json');fr=read(F/'model/receipt.json')
affected=set(ar['rounds'][1]['affected_nets']);allnets=set(fr['rounds'][1]['affected_nets'])
assert len(affected)==19360 and len(allnets)==55300 and affected<=allnets
maps=[]
for frame in [a,f]:
 m={x['connection_id']:x for x in frame['records']}
 assert len(m)==len(frame['records'])==115572;maps.append(m)
assert maps[0].keys()==maps[1].keys()
stats={key:collections.Counter() for key in ['affected','skipped']}
for cid,x in maps[0].items():
 y=maps[1][cid]
 assert all(x[k]==y[k] for k in ['net_id','source','sink','budget_integer','floor_integer'])
 s=stats['affected' if x['net_id'] in affected else 'skipped'];s['connections']+=1
 s['different_paths']+=x['answer']['physical_edge_ids']!=y['answer']['physical_edge_ids']
 delta=y['answer']['delay']-x['answer']['delay'];s['full_delay_lower' if delta<0 else 'full_delay_higher' if delta>0 else 'equal_delay']+=1
 s['full_minus_affected_delay_integer_sum']+=delta
state={}
for key in ['ledger','epochs','prices']:
 x=a[key];y=f[key];keys=x.keys()|y.keys()
 state[key]={'different_entries':sum(x.get(k,0)!=y.get(k,0) for k in keys),'affected_entries':len(x),'full_entries':len(y),'full_minus_affected_sum':sum(y.values())-sum(x.values())}
rows={}
for label,receipt in [('affected',ar),('full',fr)]:
 rows[label]={'timers':{k:v for k,v in receipt.items() if k.endswith('_seconds')},'rounds':[{'round_index':x['round_index'],'nets':len(x['affected_nets']),'statuses':dict(collections.Counter(e['status'] for e in x['events'])),'seconds':x['seconds'],'overflow_before':x['overflow_before'],'overflow_after':x['overflow_after']} for x in receipt['rounds']]}
assert all(sha(Path(p))==digest for p,digest in bindings.items())
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':bindings,'initial_and_round0_complete_frames_equal':True,'connection_groups':{k:dict(v) for k,v in stats.items()},'state_differences':state,'schedules':rows,'scope':'Audited mmc development scheduling comparison. Historical timers are unpaired and nested; no causal speed, hotspot quality, native QoR, heldout or end-to-end gain claim.'}
p=F/'schedule_comparison_v1.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
