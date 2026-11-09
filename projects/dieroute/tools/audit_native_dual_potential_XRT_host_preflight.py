"""Audit compiled host transformation and intentional missing-capability rejection."""
import hashlib,json,re
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/native_dual_potential_XRT_pipeline_20261015'
def main():
 refs={}
 def sha(f):
  p=Path(f).resolve();key=str(p)
  if key not in refs:
   h=hashlib.sha256()
   with p.open('rb') as stream:
    for b in iter(lambda:stream.read(1048576),b''):h.update(b)
   refs[key]=h.hexdigest()
  return refs[key]
 protocol=json.loads((P/'protocol.json').read_text());compile=json.loads((P/'compile_protocol.json').read_text());guard=json.loads((P/'guard_preflight_protocol.json').read_text());result=json.loads((P/'guard_preflight_result.json').read_text())
 for obj in [protocol,compile,guard,result]:
  for f,h in obj['source_sha256'].items():assert sha(f)==h,f
 assert json.loads((P/'compile_result.json').read_text())['returncode']==0
 assert '-DDIEROUTE_NATIVE_PACKED_POTENTIAL8=1' in compile['command'] and '-DDIEROUTE_NATIVE_HIGHER_G_TIE=1' in compile['command']
 source=(P/'source/tb/host.cpp').read_text();restored=source
 for c in reversed(json.loads((P/'host_format_changes.json').read_text())):
  assert restored.count(c['after'])==1;restored=restored.replace(c['after'],c['before'],1)
 parent=R/'work/native_two_phase_identity_XRT_pipeline_20261015/source/tb/host.cpp';assert restored==parent.read_text()
 assert source.index('potential consistency edges=')<source.index('native_prepare_potential_buffer(potential)')<source.index('bound dual-format image contract required')<source.index('auto& ctx=xrt_host::device_context')
 cpu=R/'work/native_potential_dual_format_Cmodel_20261015'
 for name in ['native_potential_buffer.hpp','native_search_hbm_potential.hpp']:assert sha(P/'source'/name)==sha(cpu/'include'/name)
 assert guard['command'][1:9]==protocol['command'][1:9] and guard['command'][10:]==protocol['command'][10:]
 assert protocol['maximum_probe_wall_seconds']==1800 and protocol['maximum_expansions']==protocol['label_capacity']==2097152
 assert result['status']=='missing_capability_rejected_after_full_native_preprocessing_before_device_context' and result['returncode']==1 and result['output_not_created']
 log=(P/'guard_preflight.stderr').read_text();assert log.rstrip().endswith('bound dual-format image contract required') and 'STAGE name=potential_format_selected a=2 b=91975784' in log
 edges=int(re.search(r'potential consistency edges=(\d+)',log).group(1));original=R/'work/native_policy_identity_hop_bound_20261015/independent_audit.json';assert edges==json.loads(original.read_text())['eligible_edges']==212892069
 assert not Path(guard['command'][9]).exists()
 for f in [P/'protocol.json',P/'compile_protocol.json',P/'compile_result.json',P/'host_format_changes.json',P/'guard_preflight_protocol.json',P/'guard_preflight_result.json',P/'guard_preflight.stderr',P/'guard_preflight.stdout',parent,original,cpu/'independent_audit.json',Path(__file__).resolve()]:sha(f)
 report=dict(status='dual_host_compiled_full_native_preprocessing_format2_and_missing_capability_guard_verified',compiled=True,original_eligible_edges_checked=edges,potential_format=2,potential_payload_bytes=91975784,expected_real_run_verified_upload_bytes=protocol['expected_verified_upload_bytes'],preflight_returncode=1,device_context_not_reached=True,source_sha256=refs,adopted=False,board_result=False,research_complete=False,scope='Actual new compiled host performed full original eligible-edge consistency check and shared lossless packing, then intentionally rejected absent capability before device_context. Changes reverse byte-exact to frozen unpacked control. No device/BO/XRT image execution or throughput proof; planned upload count not observed transfer. Packing/dump costs remain charged to future1800s run.')
 with (P/'host_preflight_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
if __name__=='__main__':main()
