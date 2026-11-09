"""Read-only cross-implementation comparison of terminal audited arms only."""
import json,hashlib,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';S=E/'wbuart_map_priority_trial_v1_2026-10-20';P=E/'wbuart_prepared_map_replication_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def location(root,case,init,timing,mode):
 if case=='w096/episode_01' and init=='native_retained' and timing=='warm_timing_round_updated':
  if root==P:return E/'wbuart_prepared_map_preflight_v1_2026-10-20'/mode
  return E/('wbuart_map_priority_control_v1_2026-10-20' if mode=='H0' else 'wbuart_map_priority_nonzero_v1_2026-10-20')/mode
 return root/case/init/timing/mode

def main():
 output=Path(sys.argv[1]);assert not output.exists();manifest=P/'manifest.json';rows=[];pending=[];bindings={str(Path(__file__)):sha(__file__),str(manifest):sha(manifest)}
 for c in read(manifest)['cases']:
  for init in ['raw_min','native_retained']:
   for timing in ['warm_timing_frozen','warm_timing_round_updated']:
    for mode in ['H0','MAP']:
     key={'case':c['case'],'initializer':init,'timing_policy':timing,'priority':mode};a,b=[location(root,c['case'],init,timing,mode) for root in [S,P]]
     if not all((p/'complete_event_audit.json').exists() and (p/'receipt.json').exists() for p in [a,b]):pending.append(key);continue
     for n in ['initial.json','round0.json','round1.json','sketch.json','primary_budget_repairs.json']:assert read(a/n)==read(b/n),(key,n)
     ar,br=read(a/'receipt.json'),read(b/'receipt.json');assert [r['events'] for r in ar['rounds']]==[r['events'] for r in br['rounds']],key;assert ar['heuristic_calls']==br['heuristic_calls']
     for i in [0,1]:assert read(a/f'timing_round{i}.json')['criticalities']==read(b/f'timing_round{i}.json')['criticalities'],key
     for p in [a,b]:
      audit=p/'complete_event_audit.json';v=read(audit);assert v['events']==2148
      # Bind completed audits and receipts; their own full dependency hashes are verified by study reviewers.
      bindings[str(audit)]=sha(audit);bindings[str(p/'receipt.json')]=sha(p/'receipt.json')
     rows.append(key)
 assert len(rows)+len(pending)==72
 output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps({'status':'ALL72_FULL_TRAJECTORIES_MATCH' if not pending else 'PARTIAL_COMPLETED_ARMS_EXACT_MATCH_OTHERS_STILL_PENDING','matched_arms':len(rows),'matched_MAP_arms':sum(x['priority']=='MAP' for x in rows),'rows':rows,'pending':pending,'bindings':bindings,'scope':'Completed audited scalar/prepared states/events/repair/timing equality only. Partial report cannot establish full36 MAP equivalence or full paid speedup.'},indent=2)+'\n');print('EXACT_CROSSCHECK',len(rows),'MAP',sum(x['priority']=='MAP' for x in rows),'pending',len(pending))
if __name__=='__main__':main()
