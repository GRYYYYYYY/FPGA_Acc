"""Review all four fixed fanout/present native arms without relaxing quality gates."""
import csv,hashlib,json,struct
from pathlib import Path
root=Path(__file__).resolve().parents[1]
p=root/'work/rr_fanout_present_interaction_variant_v2_20261015'

def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as stream:
  for b in iter(lambda:stream.read(1048576),b''):h.update(b)
 return h.hexdigest()

def main():
 result=json.loads((p/'native_result.json').read_text());assert result['status']=='twenty_native_fanout_present_runs_and_independent_audits_complete'
 protocol=json.loads((p/'native_protocol.json').read_text())
 for container in [result,protocol]:
  for f,h in container['source_sha256'].items():assert sha(Path(f))==h,f
 owners=[a[0] for a in struct.iter_unpack('<H',Path(protocol['topology_prefix']+'.node_die').read_bytes())]
 outcomes={};proofs=[];parent_checks=0
 for arm,cfg in protocol['arms'].items():
  previous=None
  for i in range(5):
   d=p/f'native_runs/{arm}_{i}';report=json.loads((d/'route.json').read_text())
   assert report['legal'] and report['net_dispatch_order']==cfg['net_order'] and report['present_schedule_mode']==cfg['present_mode']
   report.pop('wall_ms');hashes={f.name:sha(f) for f in d.glob('route.*') if f.name!='route.json'}
   if previous is not None:assert previous==(report,hashes),(arm,i)
   previous=(report,hashes)
   f=d/'dispatch_resource_replay_audit.json';audit=json.loads(f.read_text());assert audit['cpu_legal'] and audit['final_resources_and_costs_byte_equivalent'];proofs.append(f)
   if cfg['net_order']==0:
    f=d/'legacy_parent_compatibility.json';audit=json.loads(f.read_text());assert audit['status']=='unchanged_legacy_net_dispatch_matches_completed_reference';parent_checks+=len(audit['checks']);proofs.append(f)
  d=p/f'native_runs/{arm}_0';qfile=d/'native_validation/validation.json';q=json.loads(qfile.read_text());assert q['legal'] and q['vpr_exit_status']==0;assert (q['baseline_wirelength'],q['baseline_cpd_ns'])==(9664,9.60037);proofs.append(qfile)
  crossing=set()
  with (d/'route.route_trees.csv').open() as stream:
   for row in csv.DictReader(stream):
    net,a,b=[int(row[k]) for k in ['net_id','parent','child']]
    if owners[a]!=owners[b]:crossing.add((net,a,b))
  expected=result['outcomes'][arm];assert len(crossing)==expected['model_crossings']
  gates=dict(native_legal=q['legal'],wirelength_nondegrade=q['total_wirelength']<=9664,cpd_nondegrade=q['critical_path_delay_ns']<=9.60037,model_crossings_nondegrade=len(crossing)<=protocol['baseline_model_crossings'])
  assert gates==expected['checks']
  outcomes[arm]=dict(repeats=5,wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns'],model_crossings=len(crossing),checks=gates,all_ex5p_model_checks_pass=all(gates.values()))
 proofs.extend([p/'native_result.json',p/'native_protocol.json',Path(__file__).resolve()])
 audit=dict(status='twenty_native_fanout_present_runs_independently_reviewed',outcomes=outcomes,parent_artifact_receipt_checks=parent_checks,source_sha256={str(f):sha(f) for f in proofs},adopted=False,scope='Fourfixedarmsx5ex5pdevelopmentruns,determinism,replay,parentreceiptandfrozeninputhashesverified;nativevalidationoneperarm;modelcrossings independently recounted. Noheldoutopening,physicalSLLclaim,generalqualityadoption orfullresearchcompletion.',board_result=False,research_complete=False)
 with (p/'independent_audit.json').open('x') as out:json.dump(audit,out,indent=2);out.write('\n')
 print(json.dumps(dict(status=audit['status'],outcomes=outcomes,parent_checks=parent_checks)))

if __name__=='__main__':main()
