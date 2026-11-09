"""Independent actual binary32 expiry/readback and native zero/absent parity."""
import pathlib,json,hashlib,struct,re,traceback
from audit_mmc_v16_native_iteration_work_v1 import parse
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_first_iteration_hint_admission_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def words(p):
 h,data=p.read_bytes().split(b'\n',1);assert h==b'RCACCBITS1 904438' and len(data)==904438*4;return [x[0] for x in struct.iter_unpack('<I',data)]
def prefix(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for line in f:
   h.update(line)
   if line==b'CP iteration_begin 2\n':return h.hexdigest()
 raise AssertionError('missing second iteration boundary')
def qor(p):
 t=p.read_text();return (re.findall(r'Total wirelength:\s*(\d+)',t)[-1],re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',t)[-1])
def main():
 pp=O/'protocol.json';rp=O/'results.json';p=json.loads(pp.read_text());r=json.loads(rp.read_text());assert r['status']=='ALL3_SEMANTIC_PILOT_NATIVE_ARMS_TERMINAL' and r['bindings']==p['bindings'];bindings={str(f):sha(f) for f in [pp,rp,pathlib.Path(__file__).resolve(),R/'tools/audit_mmc_v16_native_iteration_work_v1.py']}
 for f,h in p['bindings'].items():assert sha(pathlib.Path(f))==h
 ref=pathlib.Path(p['reference_zero']);positive=pathlib.Path(p['positive_reference']);rows=[];fields=['iteration','present_factor_text','BB_updates','heap_pushes','rerouted_NET_operations','rerouted_connection_operations','overused_RR_nodes'];old=parse((ref/'native.log').read_text())
 for row in r['rows']:
  arm=row['arm'];D=O/arm;assert row['exit_status']==0 and row['FULL_pass'] and row['VPR_success']
  for f,h in row['files'].items():assert sha(pathlib.Path(f))==h
  bindings.update(row['files']);bindings[str(D/'receipt.json')]=sha(D/'receipt.json');log=(D/'native.log').read_text()
  for name in ['design.blif','design.net','design.place']:assert (D/name).read_bytes()==(ref/name).read_bytes()
  if arm in ['absent','zero']:
   for name in ['output.route','design.net.post_routing','owner_trace.tsv']:assert sha(D/name)==sha(ref/name);bindings[str(ref/name)]=sha(ref/name)
   new=parse(log);assert [{k:x[k] for k in fields} for x in new['rows']]==[{k:x[k] for k in fields} for x in old['rows']];assert qor(D/'native.log')==qor(ref/'native.log')
  if arm=='absent':assert 'first iteration hint expired' not in log and not (D/'initial.bin').exists();rows.append(dict(arm=arm,old_zero_route_packed_owner_trace_integer_work_QoR_exact=True));continue
  plan=next(x for x in p['arms'] if x['arm']==arm);risk=pathlib.Path(plan['environment_set']['ROUTECAST_EXCESS_PRELOAD']);entries={}
  for line in risk.read_text().splitlines()[1:]:
   n,bits=map(int,line.split());x=struct.unpack('<f',struct.pack('<I',bits))[0];entries[n]=struct.unpack('<I',struct.pack('<f',1+x))[0]
  initial,before,after=[words(D/name) for name in ['initial.bin','before.bin','after.bin']];changed={n for n,(a,b) in enumerate(zip(before,after)) if a!=b};assert changed=={n for n,bits in entries.items() if bits!=0x3f800000}
  for n in range(904438):
   assert initial[n]==entries.get(n,0x3f800000)
   if n in entries:assert before[n]==initial[n] and after[n]==0x3f800000
   else:assert before[n]==after[n]
  assert re.findall(r'ROUTECAST first iteration hint expired entries=(\d+)',log)==[str(len(entries))]
  if arm=='hint':
   assert initial==words(positive/'preload_state.bin');assert prefix(D/'owner_trace.tsv')==prefix(positive/'owner_trace.tsv');bindings[str(positive/'preload_state.bin')]=sha(positive/'preload_state.bin');bindings[str(positive/'owner_trace.tsv')]=sha(positive/'owner_trace.tsv')
  else:assert not entries and before==after
  rows.append(dict(arm=arm,initial_preload_exact=True,hint_entries=len(entries),expiry_guard_saw_exact_initial_bits=True,expired_hint_entries_exactly_one=True,all_nonhint_bits_preserved=True,first_iteration_owner_trace_matches_persistent_hint=(True if arm=='hint' else None),old_zero_route_packed_owner_trace_integer_work_QoR_exact=(True if arm=='zero' else None)))
  bindings[str(risk)]=sha(risk)
 result=dict(status='ACTUAL_FIRST_ITERATION_HINT_EXPIRY_BITS_AND_ZERO_ABSENT_NATIVE_EQUIVALENCE_PASS',cases=rows,bindings=bindings,all3_utility_trial_semantically_admitted=True,native_utility_proven=False,original_zero_counter_gate_repaired=False,scope='Episode01 semantic admission only. Actual initial/pre/post cost arrays and unchanged non-hint bits, unchanged persistent-hint first-iteration trajectory, zero and absent complete native trajectory parity. No complete all3 utility, canonical pin admission of positive pilot, cold forecast quality, setup closure or end-to-end speedup claim.')
 (O/'independent_semantic_verification_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],rows,flush=True)
if __name__=='__main__':
 try:main()
 except Exception as e:
  (O/'semantic_verification_failure_v1.json').open('x').write(json.dumps(dict(error=repr(e),traceback=traceback.format_exc()),indent=2)+'\n');raise
