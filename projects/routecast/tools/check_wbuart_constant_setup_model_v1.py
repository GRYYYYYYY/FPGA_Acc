"""All-node native tag parity + all data atom/connection bits, every fixed vector."""
import csv,hashlib,json,struct,math
from pathlib import Path
from collections import defaultdict
from native_setup_reference_constants_v3 import SetupReference
from nominal_component_timing_bridge_constants_v3 import NominalComponentTimingBridge
R=Path(__file__).resolve().parents[1];B=R/'experiments/wbuart_nominal_contexts_v1_2026-10-20';C=R/'experiments/wbuart_delay_components_v1_2026-10-20';N=R/'experiments/wbuart_setup_tags_v1_2026-10-20';O=R/'experiments/wbuart_constant_setup_model_contract_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def table(p):return list(csv.DictReader(p.open(),delimiter='\t'))
def bits(v):return struct.pack('>f',float(v)).hex()
def native_tags(path):
 result={}
 for r in table(path):
  key=int(r['node']),r['kind'],int(r['launch']),int(r['capture']);assert key not in result and r['valid']=='1';v=struct.unpack('>f',bytes.fromhex(r['bits']))[0];assert not math.isnan(v) and bits(r['seconds'])==r['bits'];result[key]=(r['bits'],r['constant']=='1')
 return result
def model_tags(a):
 result={}
 for kind,field in [('A','arrivals'),('R','required'),('S','slacks'),('CL','clock_launch'),('CC','clock_capture')]:
  for node,values in a[field].items():
   for key,v in values.items():
    launch,capture=key if isinstance(key,tuple) else (key,-1);launch=-1 if launch is None else launch;result[node,kind,launch,capture]=(bits(v),kind=='A' and launch==-1 and capture==-1 and v==-math.inf)
 return result
def main():
 O.mkdir(exist_ok=False);t=read(N/'terminal.json');assert t['all_pass'] and len(t['rows'])==36;cp=read(C/'verification.json');assert cp['checks']==560448
 for d in [cp,read(N/'protocol.json')]:
  for n,h in d['bindings'].items():assert sha(Path(n))==h
 proto=read(N/'protocol.json');paths=[Path(__file__),R/'tools/native_setup_reference_constants_v3.py',R/'tools/nominal_component_timing_bridge_constants_v3.py',R/'tools/load_native_clock_constraints_v1.py',N/'terminal.json',N/'protocol.json',C/'verification.json',B/'edge_CID_verification_v1.json'];bindings={str(p):sha(p) for p in paths};(O/'protocol.json').write_text(json.dumps({'bindings':bindings,'acceptance':'All36 baseline+changed vectors: every native A/R/S/CL/CC domain/tag presence/float32 bit pattern/constant flag must match; every3892 routed atom slack/raw criticality and every2493 cluster aggregate must match. Zero tolerance, no filtered cases or ignored constant nodes in tag comparison. Model receives only baseline graph/constraints/components and changed RR vector. Partial or negative RR vectors rejected.','scope':'Fixed current packing, declared constant profile, setup only. Not generic hold/STA, IPIN remapping invariance, source HDL/four-state, predictor quality or paid-time gain.'},indent=2)+'\n');results=[];tags=0;atoms_count=0;connections_count=0
 for job in proto['jobs']:
  base=B/job['base_case'];out=C/job['case'];native=N/job['case'];rec=read(native/'receipt.json');assert rec['passed']
  for n,h in rec['bindings'].items():assert sha(Path(n))==h
  mapping=read(base/'external_edge_CID_bindings_v1.json');bridge=NominalComponentTimingBridge(base,C/job['base_case']/'scaled/components_before.tsv',mapping);rr0={(int(q['net']),int(q['pin'])):float(q['delay_s']) for q in table(base/'initial_connections.tsv')};rr1={(int(q['net']),int(q['pin'])):float(q['delay_s']) for q in table(out/'updated_connections.tsv')};assert len(rr0)==len(rr1)==2493
  mismatch=[];case_tags=0
  for label,rr,file in [('before',rr0,'setup_tags_before.tsv'),('after',rr1,'setup_tags_after.tsv')]:
   a=bridge.analyze(rr);nt=native_tags(native/file);mt=model_tags(a);missing=sorted(nt.keys()-mt.keys());extra=sorted(mt.keys()-nt.keys());bad=[{'key':k,'model':mt[k],'native':nt[k]} for k in sorted(nt.keys()&mt.keys()) if nt[k]!=mt[k]]
   if missing or extra or bad:mismatch.append({'phase':label,'missing':missing,'extra':extra,'bad':bad})
   case_tags+=len(nt)
  # a is after-vector analysis, generated solely from baseline + new RR.
  groups=defaultdict(list);bad_atoms=[]
  for row in table(out/'timing_atoms.tsv'):
   if not row['raw_criticality']:continue
   node=int(row['external_node']);slacks=a['slacks'][node]
   if not slacks:bad_atoms.append({'atom_pin':int(row['atom_pin']),'reason':'missing_model_slack'});continue
   slack=min(slacks.values());crit=a['criticality'][node];groups[int(row['native_net']),int(row['local_pin'])].append((slack,crit));atoms_count+=1
   if bits(slack)!=bits(row['setup_slack_s']) or bits(crit)!=bits(row['raw_criticality']):bad_atoms.append({'atom_pin':int(row['atom_pin']),'model_slack':bits(slack),'native_slack':bits(row['setup_slack_s']),'model_crit':bits(crit),'native_crit':bits(row['raw_criticality'])})
  bad_connections=[];updated=table(out/'updated_connections.tsv');assert len(updated)==2493
  for row in updated:
   key=int(row['net']),int(row['pin']);vals=groups[key];connections_count+=1
   if not vals or bits(min(s for s,c in vals))!=bits(row['slack_s']) or bits(max(c for s,c in vals))!=bits(row['criticality']):bad_connections.append(key)
  for invalid in [dict(list(rr1.items())[1:]),dict(rr1,**{})]:
   if len(invalid)==len(rr1):invalid[next(iter(invalid))]=-1.
   try:bridge.edge_weights(invalid)
   except ValueError:pass
   else:raise AssertionError('invalid RR accepted')
  d=O/job['case'];d.mkdir(parents=True);mfile=d/'mismatches.json';mfile.write_text(json.dumps({'tags':mismatch,'atoms':bad_atoms,'connections':bad_connections})+'\n');result={'case':job['case'],'tag_rows_checked':case_tags,'tag_mismatch_phases':len(mismatch),'atom_records':sum(map(len,groups.values())),'atom_mismatches':len(bad_atoms),'connection_aggregates':len(updated),'connection_mismatches':len(bad_connections),'invalid_vectors_rejected':True};results.append(result);tags+=case_tags
  for p in [native/'receipt.json',native/'setup_tags_before.tsv',native/'setup_tags_after.tsv',out/'updated_connections.tsv',out/'timing_atoms.tsv',mfile]:bindings[str(p)]=sha(p)
  print('CONSTANT_SETUP_COMPARE',job['case'],len(mismatch),len(bad_atoms),len(bad_connections),flush=True)
 assert len(results)==36 and atoms_count==140112 and connections_count==89748
 passed=all(r['tag_mismatch_phases']==r['atom_mismatches']==r['connection_mismatches']==0 for r in results)
 for n,h in bindings.items():assert sha(Path(n))==h
 result={'status':'ALL36_ALL_NODE_CONSTANT_TAGS_AND_DATA_FLOAT32_EXACT_PASS' if passed else 'CONSTANT_SETUP_NATIVE_ORACLE_MISMATCH','passed':passed,'rows':results,'tag_rows_checked':tags,'routed_atom_records':atoms_count,'connection_aggregates':connections_count,'old_reference_guard_unchanged':True,'new_target_route_labels':False,'strict_unseen_admitted':False,'full_generic_STA_qualified':False,'bindings':{str(O/'protocol.json'):sha(O/'protocol.json'),**bindings}};(O/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print('CONSTANT_SETUP_TERMINAL',passed,tags,flush=True)
if __name__=='__main__':main()
