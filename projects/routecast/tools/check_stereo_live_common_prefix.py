"""Snapshot complete common journal lines without altering active experiments."""
import json,pathlib,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
BASE=ROOT/'experiments/stereo_prospective_validation_2026-10-05'
NAMES=['ordinary_additive_class_cache_prediction_undriven_v2','ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 protocols=[json.loads((BASE/n/'protocol.json').read_text()) for n in NAMES]
 keys=['endpoints_version','frontend_protocol_sha256','frontend_revision_scope','prepared_artifact','conversion_receipt_sha256','inputs','csr_manifest_sha256','physical_cost_audit_sha256','policy_sha256','method','order']
 for k in keys:assert protocols[0][k]==protocols[1][k],k
 hashes=[hashlib.sha256(),hashlib.sha256()];count=0;last=None;seen=set()
 with (BASE/NAMES[0]/'net_results.jsonl').open('rb') as a,(BASE/NAMES[1]/'net_results.jsonl').open('rb') as b:
  while True:
   lines=[a.readline(),b.readline()]
   if not all(v.endswith(b'\n') for v in lines):break
   rows=[json.loads(v) for v in lines]
   assert rows[0]==rows[1],f'journal mismatch at {count}'
   last=rows[0]['net_id'];assert last not in seen;seen.add(last)
   for h,line in zip(hashes,lines):h.update(line)
   count+=1
 assert count>0
 out=BASE/'live_host_prefix_comparison';out.mkdir(exist_ok=True)
 target=out/f'common_{count}_authenticated_results.json'
 assert not target.exists()
 report={'completed_common_networks':count,'last_net_id':last,'all_journal_objects_exact':True,'prefix_sha256':[h.hexdigest() for h in hashes],'protocol_sha256':[sha(BASE/n/'protocol.json') for n in NAMES],'verified_protocol_keys':keys,'source_sha256':sha(pathlib.Path(__file__)),'scope':'live completed common prefix only; full61314net parity not proven; no runtime speedup'}
 target.write_text(json.dumps(report,indent=2)+'\n')
 source=out/'source';source.mkdir(exist_ok=True);(source/f'common_{count}_{pathlib.Path(__file__).name}').write_bytes(pathlib.Path(__file__).read_bytes())
 print(json.dumps(report))
if __name__=='__main__':run()
