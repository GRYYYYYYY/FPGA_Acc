"""Single-run serial prepared-input acceptance experiment, with explicit stage clocks."""
import json,time,runpy,contextlib,sys
from native_qor_admission import admit
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_screened_acceptance_workflow_2026-10-07';out.mkdir()
# Use new artifacts throughout; never combine elapsed times from old receipts.
tags=['bitonic_resident_live_staging','bitonic_resident_staging_native_import','bitonic_resident_staging_n4_canonical','bitonic_resident_staging_n8_canonical','bitonic_resident_staging_n16_canonical','bitonic_swapped_cold_n4_canonical','bitonic_swapped_cold_n8_canonical','bitonic_swapped_cold','bitonic_selected_state']
replacements=[(t,t.replace('bitonic_','bitonic_workflow_screened_',1)) for t in sorted(tags,key=len,reverse=True)]
files=['trial_bitonic_resident_live_staging.py','verify_bitonic_resident_live_staging.py','capture_bitonic_swapped_cold.py','trial_bitonic_resident_staging_native_import.py',*[f'trial_bitonic_resident_staging_n{n}_canonical.py' for n in [4,8,16]],'verify_bitonic_resident_staging_canonical.py','verify_bitonic_swapped_cold.py',*[f'trial_bitonic_swapped_cold_n{n}_canonical.py' for n in [4,8]],'verify_bitonic_swapped_cold_canonical.py','trial_bitonic_selected_state.py','verify_bitonic_selected_state.py']
paths={}
for name in files:
 text=(ROOT/'tools'/name).read_text()
 for a,b in replacements:text=text.replace(a,b)
 text=text.replace('owner_union_wire_rc_context_cached','owner_union_wire_rc_context_cached_tree')
 text=text.replace('bitonic_resident_staging_n{n}', 'bitonic_workflow_screened_resident_staging_n{n}').replace('bitonic_swapped_cold_n{n}', 'bitonic_workflow_screened_swapped_cold_n{n}')
 if name=='trial_bitonic_resident_live_staging.py':
  text=text.replace("order=['baseline','resident','resident','baseline']","order=['resident']").replace('ABBA within samecontext/seedledger','one resident staging attempt per case').replace('four ABBA','one resident')
 if name=='trial_bitonic_resident_staging_native_import.py':text=text.replace('run1_resident.json','run0_resident.json').replace("row['runs'][1]","row['runs'][0]")
 if name=='verify_bitonic_resident_live_staging.py':text=text.replace('all4_update_bytes_equal','single_update_verified').replace('all4_live_rollbacks_verified','live_rollback_verified').replace('four ABBA runs each','one resident run each')

 if name=='verify_bitonic_resident_staging_canonical.py':
  text=text.replace('for n,connections in [(4,371),(8,1514),(16,5070)]:', "admissions=json.loads((ROOT/'experiments/bitonic_workflow_screened_swapped_cold_2026-10-07/admission.json').read_text())['rows']\nfor n,connections in [(4,371),(8,1514),(16,5070)]:\n if not next(x['admitted'] for x in admissions['rows'] if x['count']==n):continue")
 if name=='verify_bitonic_swapped_cold.py':
  start=text.index(' canonical=ROOT/');end=text.index(' good=Fraction',start)
  replacement=" rawbase=ROOT/'experiments/bitonic_workflow_screened_resident_staging_native_import_2026-10-07';rawreceipt=json.loads((rawbase/'receipt.json').read_text());rawrow=next(x for x in rawreceipt['rows'] if x['count']==n);gate=admit(row,rawrow);cpd=gate['candidate_cpd_ns'];wire=gate['candidate_wirelength']\n if gate['admitted']:\n  canonical=ROOT/f'experiments/bitonic_workflow_screened_resident_staging_n{n}_canonical_2026-10-07';v=json.loads((canonical/'verification.json').read_text());cr=json.loads((canonical/'receipt.json').read_text());assert v['receipt_sha256']==sha(canonical/'receipt.json');x=cr['results'][0];assert all(sha(f)==d for f,d in x['sha256'].items());cw=Path(x['cwd'])/'reload';log=(cw/'reload.log').read_text();assert Fraction(cpd)==Fraction(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);assert wire==int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1])\n"
  text=text[:start]+replacement+text[end:];text=text.replace('from stream_native_route_audit import audit','from stream_native_route_audit import audit\nfrom native_qor_admission import admit');text=text.replace("good=Fraction(cpd)<=Fraction(row['cpd_ns']) and wire<=row['wirelength']","good=gate['admitted']")
 if name=='trial_bitonic_selected_state.py':
  start=text.index(';can=ROOT/');end=text.index('\n accept=F',start);block=text[start+1:end]
  text=text[:start]+";accept=ref['joint_nonregression'];candidate=None\n if accept:\n  "+block+text[end:];start=text.index('\n accept=F');end=text.index(';chosen=',start);text=text[:start]+'\n '+text[end+1:]
 target=ROOT/'tools'/name.replace('bitonic_', 'bitonic_workflow_screened_',1);assert not target.exists();compile(text,str(target),'exec');target.write_text(text);paths[name]=target
from freeze_priority_family import closure
protocol=dict(sources=closure([Path(__file__),*paths.values()]),scope='One resident attempt on each of three prepared swaps; fresh target frontend, context/seed import, staging, independent demand proof, raw native quality screening and canonical validation ONLY for provisional joint admits, fresh cold oracle, cold canonical fallback, selected reload/endpoint/ledger proof. Serial stages share private same-tree/class-memo read-only RR cache; clocks include logging and proofs. Original mapped netlist/initial placement/seed routes/RR graph and tool compilation excluded. Full baseline and aggregate verification pending; not raw-input end-to-end or stable speedup.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[];tick=time.perf_counter()
def stage(name):
 p=paths[name];start=time.perf_counter()
 with (out/(name+'.log')).open('w') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):runpy.run_path(str(p),run_name='__main__')
 rows.append(dict(stage=name,seconds=time.perf_counter()-start,log_sha256=sha(out/(name+'.log'))));(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),stages=rows,complete=False,elapsed=time.perf_counter()-tick),indent=2)+'\n');print(name,rows[-1]['seconds'],flush=True)
from cached_rr_endpoint_context_tree import clear_cache
clear_cache()
for name in files:
 # canonical import needs authenticated raw import receipt, produced immediately after import.
 if name=='trial_bitonic_resident_staging_n4_canonical.py':
  p=ROOT/'experiments/bitonic_workflow_screened_resident_staging_native_import_2026-10-07';r=json.loads((p/'receipt.json').read_text());assert r['complete']
  for x in r['rows']:assert x['status']=='RAW_NATIVE_FULL_STA_SUCCESS' and all(sha(f)==h for f,h in x['files'].items())
  (p/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(p/'receipt.json'),scope='Raw import bound; canonical independent proof follows.'),indent=2)+'\n')
  cold=ROOT/'experiments/bitonic_workflow_screened_swapped_cold_2026-10-07';cr=json.loads((cold/'receipt.json').read_text());admissions=[admit(c,x) for c,x in zip(cr['rows'],r['rows'])];(cold/'admission.json').write_text(json.dumps(dict(rows=admissions,cold_receipt_sha256=sha(cold/'receipt.json'),raw_receipt_sha256=sha(p/'receipt.json')),indent=2)+'\n')
 if name.startswith('trial_bitonic_resident_staging_n'):
  n=int(name.split('_n')[1].split('_')[0]);gate=next(x for x in admissions if x['count']==n)
  if not gate['admitted']:
   log=out/(name+'.log');log.write_text(json.dumps(dict(skipped=True,reason=gate['reasons']))+'\n');rows.append(dict(stage=name,seconds=0.0,status='SKIPPED_QOR_REJECTED',log_sha256=sha(log)));continue

 stage(name)
assert all(sha(f)==h for f,h in protocol['sources'].items())
(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),stages=rows,complete=True,workflow_seconds=time.perf_counter()-tick),indent=2)+'\n')
