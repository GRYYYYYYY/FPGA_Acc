"""All-ID prior/prediction/truth support decomposition, no resource selection."""
import json,sys,math
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_score_label_tie_diagnosis_v1_2026-10-19';O=E/'prospective_external_family_resource_support_transitions_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def confusion(c):
 tp=sum(v for (prior,pred,true),v in c.items() if pred and true);fp=sum(v for (prior,pred,true),v in c.items() if pred and not true);fn=sum(v for (prior,pred,true),v in c.items() if not pred and true);tn=sum(v for (prior,pred,true),v in c.items() if not pred and not true);den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn);return dict(TP=tp,FP=fp,FN=fn,TN=tn,binary_support_phi=(tp*tn-fp*fn)/math.sqrt(den) if den else None)
def main():
 O.mkdir(exist_ok=False);source=I/'protocol.json';proof=I/'independent_verification_v1.json';assert read(proof)['checks']==36;assert all(sha(p)==h for p,h in read(proof)['bindings'].items());bindings=closure([Path(__file__)]);bindings[str(source)]=sha(source);bindings[str(proof)]=sha(proof);cases=read(source)['cases']
 for spec in cases:
  for arm in spec['arms']:
   audit=read(arm['proof']);assert all(sha(p)==h for p,h in audit['bindings'].items());assert audit['bindings'][arm['frame']]==sha(arm['frame'])
   for p in [Path(arm['frame']),Path(arm['proof'])]:bindings[str(p)]=sha(p)
  for p in [Path(spec['domain_proof']),Path(spec['label_proof']),Path(spec['label_physical_audit'])]:bindings[str(p)]=sha(p)
 pp=O/'protocol.json';pp.write_text(json.dumps(dict(cases=cases,bindings=bindings,policy='All45584 fixed positive CHANNEL IDs for every one of3 exposed development cases, six frozen predictors. Support means occupancy>0 exactly, no fitted threshold. Partition by prior/predicted/target positive bits; report additions/removals correctness, full confusion and binary-support phi. This is error attribution, not a new classifier or gate. Unit-capacity bounded endpoint-local head has the SAME support; its resource Spearman equals binary phi, not its whole four-metric acceptance. Labels/gates/paths/ledgers unchanged, no per-NET/resource selection.'),indent=2)+'\n');bindings[str(pp)]=sha(pp);rows=[]
 for spec in cases:
  dp=Path(spec['domain_proof']);meta=read(dp);resources=[json.loads(s) for s in (dp.parent/'resources.jsonl').read_text().splitlines()];ids=[r['id'] for r in resources];assert len(ids)==len(set(ids))==45584 and all(r['capacity']==1 for r in resources);label=read(spec['label_physical_audit']);truth={int(n):v for n,v in label['node_occupancy'].items()};assert all(truth.get(n,0) in (0,1) for n in ids);ledgers={arm['name']:{int(n):v for n,v in read(arm['frame'])['ledger'].items()} for arm in spec['arms']};prior=ledgers['previous_native'];assert all(prior.get(n,0) in (0,1) for n in ids);counts={name:Counter() for name in ledgers};out=O/spec['case'];out.mkdir(parents=True);table=out/'all_resource_transitions.jsonl'
  with table.open('x') as f:
   for n in ids:
    a,b=int(prior.get(n,0)>0),truth.get(n,0);pred={name:int(ledger.get(n,0)>0) for name,ledger in ledgers.items()}
    for name,value in pred.items():counts[name][a,value,b]+=1
    f.write(json.dumps(dict(id=n,prior=a,truth=b,prediction_support=pred),separators=(',',':'))+'\n')
  for name,c in counts.items():
   get=lambda p,q,t:c[p,q,t];added_tp,added_fp=get(0,1,1),get(0,1,0);removed_tp,removed_fp=get(1,0,1),get(1,0,0);row=dict(case=spec['case'],method=name,resources=len(ids),transition_counts={''.join(map(str,k)):c[k] for k in [(p,q,t) for p in (0,1) for q in (0,1) for t in (0,1)]},confusion=confusion(c),added_true_used=added_tp,added_true_unused=added_fp,removed_true_used=removed_tp,removed_true_unused=removed_fp,delta_TP=added_tp-removed_tp,delta_FP=added_fp-removed_fp,delta_correct=added_tp+removed_fp-added_fp-removed_tp);rows.append(row);assert sum(c.values())==len(ids);print('ALL_ID_SUPPORT_TRANSITION',json.dumps({k:v for k,v in row.items() if k!='transition_counts'}),flush=True)
  bindings[str(table)]=sha(table)
 assert all(sha(p)==h for p,h in bindings.items());(O/'verification.json').write_text(json.dumps(dict(status='ALL18_ALL_ID_RESOURCE_SUPPORT_TRANSITIONS_PREPARED',rows=rows,bindings=bindings,scope='Already exposed development error decomposition only; support is not ownership multiplicity, legal route or a replacement metric/acceptance gate.'),indent=2)+'\n')
if __name__=='__main__':main()
