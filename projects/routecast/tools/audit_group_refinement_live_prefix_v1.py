"""Read-only first256 checkpoint prefix audit; full running trial is untouched."""
import json,sys,hashlib,subprocess,time
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from zero_rc_budget_certificate_graph_v1 import load_graph
E=R/'experiments';I=E/'prospective_external_family_sequential_group_refinement_v1_2026-10-20';D=E/'sequential_group_refinement_live_prefix_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 cases=read(I/'protocol.json')['cases'];D.mkdir(exist_ok=False);graph=Path(read(Path(cases[0]['endpoint']))['inputs']['graph']['path']);g=load_graph(graph);results=[];bindings={str(I/'protocol.json'):sha(I/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}
 for c in cases:
  case=c['case'];src=I/case/'on/events.jsonl';off=I/case/'off';p=read(off/'protocol.json');source=read(off/'initial_round.json');data=[]
  with src.open('rb') as f:
   for i in range(256):
    line=f.readline();assert line.endswith(b'\n'),'prefix not complete';data.append(line)
  events=[json.loads(line) for line in data];assert events[-1]['index']==255 and 'state_digest_after' in events[-1];out=D/case;out.mkdir(parents=True);initial=source;records={q['connection_id']:q for q in source['records']};ledger=dict(source['ledger']);epochs=dict(source['epochs'])
  for event in events:
   if event['status']=='GROUP_DRAFT_MATERIALIZED':
    for recs in event['candidate'].values():records.update({q['connection_id']:q for q in recs})
    for node,value in event['plan']['updates'].items():
     if value:ledger[node]=value
     else:ledger.pop(node,None)
    epochs.update(event['result_epochs'])
  final=dict(records=[records[q['connection_id']] for q in source['records']],ledger=ledger,epochs=epochs,prices=source['prices']);assert digest(final)==events[-1]['state_digest_after'];(out/'events.jsonl').write_bytes(b''.join(data));(out/'initial_round.json').write_text(json.dumps(initial)+'\n');(out/'final_round.json').write_text(json.dumps(final)+'\n');schedule=read(p['schedule'])[:256];sp=out/'schedule_prefix.json';sp.write_text(json.dumps(schedule)+'\n');provenance=dict(mode='READ_ONLY_LIVE_PREFIX_AUDIT_NOT_FULL_RUN_RESULT',source_live_file=str(src),source_prefix_bytes=sum(map(len,data)),source_prefix_sha256=hashlib.sha256(b''.join(data)).hexdigest(),runtime_checkpoint_digest=events[-1]['state_digest_after'],source_full_schedule=p['schedule'],full_trial_continues=True);prov=out/'prefix_provenance.json';prov.write_text(json.dumps(provenance,indent=2)+'\n');base=read(Path(p['baseline'])/'sketch.json');ind=Counter()
  for q in final['records']:ind.update({q['source']}|{g['vs'][e] for e in q['answer']['physical_edge_ids']})
  base.update(records=final['records'],epochs=epochs,ledger=ledger,independent_connection_ledger=dict(ind),overflow_units=sum(max(0,v-g['caps'][int(n)]) for n,v in ledger.items()),overflow_nodes=sum(v>g['caps'][int(n)] for n,v in ledger.items()));(out/'sketch.json').write_text(json.dumps(base)+'\n');(out/'component_summary.json').write_text(json.dumps(dict(counts=dict(Counter(e['status'] for e in events)),groups=256,initial_digest=digest(initial),final_digest=digest(final),scope='Prefix only; no timing/quality claim'))+'\n');p.update(enabled=True,schedule=str(sp),scope='256 group live prefix only, full source trial still running');p['bindings']=dict(p['bindings']);p['bindings'].update({str(sp):sha(sp),str(prov):sha(prov)});(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps(dict(bindings=p['bindings'],files={str(q):sha(q) for q in out.iterdir() if q.is_file()}),indent=2)+'\n');subprocess.run([sys.executable,str(R/'tools/verify_sequential_group_refinement_v1.py'),str(out),str(out/'complete_prefix_audit.json')],cwd=R,check=True);audit=read(out/'complete_prefix_audit.json');assert audit['groups']==256 and audit['checkpoints']==1;row=dict(case=case,groups=256,counts=audit['counts'],overflow=audit['overflow_units'],runtime_checkpoint_and_independent_prefix_replay_equal=True);results.append(row);print(json.dumps(row),flush=True)
  for q in [out/'complete_prefix_audit.json',prov]:bindings[str(q)]=sha(q)
 (D/'verification.json').write_text(json.dumps(dict(status='ALL3_FIRST256_LIVE_GROUP_EVENT_PREFIXES_INDEPENDENTLY_AUDITED',rows=results,bindings=bindings,scope='Prefix verification only, not full scheduled completion or quality. No live file was rewritten or restarted.'),indent=2)+'\n')
if __name__=='__main__':main()
