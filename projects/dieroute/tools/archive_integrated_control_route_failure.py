"""Snapshot an illegal routing check without changing the still-running link."""
import hashlib,json,re
from pathlib import Path

D=Path('work/native_integrated_control_stages_hw_20261015')
log=D/'link_temp/link/vivado/vpl/prj/prj.runs/impl_1/level0_wrapper.vdi'
raw=log.read_bytes();text=raw.decode(errors='replace')
signals=re.findall(r'\[Route 35-162\] (\d+) signals failed to route',text)
overlaps=re.findall(r'\[Route 35-2\] Design is not legally routed\. There are (\d+) node overlaps',text)
assert signals and overlaps and 'Verification failed' in text
O=Path('work/integrated_control_route_failure_interim_20261016');O.mkdir(exist_ok=False)
(O/'route_log_snapshot.vdi').write_bytes(raw)
manifest=D/'manifest.json';mraw=manifest.read_bytes();(O/'producer_manifest_snapshot.json').write_bytes(mraw);state=json.loads(mraw)
processes={}
for pid in [2063514,2851472,state['pid']]:
 p=Path('/proc')/str(pid)/'stat'
 if p.exists():processes[str(pid)]=p.read_text()
(O/'process_stat_snapshot.json').write_text(json.dumps(processes,indent=2)+'\n')
report=dict(status='route_verification_illegal_snapshot_link_not_yet_terminal',failed_signals=int(signals[-1]),node_overlaps=int(overlaps[-1]),producer_status=state['status'],link_returncode=state.get('link_returncode'),processes_observed=list(processes),route_phase10_seen='Phase 10 Depositing Routes' in text,source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [O/'route_log_snapshot.vdi',O/'producer_manifest_snapshot.json',O/'process_stat_snapshot.json',Path(__file__)]},scope='Log phase9 reports routing congestion and illegal node overlaps; current v++ completion and named-checkpoint reports not yet established. Top contending-node examples involve commit traffic FIFO and both phase helper hierarchies; no single-cause or timing signoff claim.',adopted=False,board_result=False,research_complete=False)
(O/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='source_sha256'}))
