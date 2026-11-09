"""Review a bounded interface probe without claiming full search/commit completion."""
import hashlib,json,re,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'work/native_sharded_quotient_budget1_diagnostic_20261015'
def sha(q):
 h=hashlib.sha256()
 with Path(q).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='diagnostic_exited_requires_review' and m['returncode']==0
 for obj in [p,json.loads((P/'launch_protocol.json').read_text())]:
  for q,h in obj['source_sha256'].items():assert sha(q)==h,q
 assert p['label_capacity']==2097152 and p['maximum_expansions']==1 and not p['optional_quotient_heuristic_omitted']
 log=(P/'run.log').read_text();markers=['native initialization verified_bytes=','DIAG seed_begin index=0','DIAG seed_wait_complete index=0','DIAG snapshot_begin limit=1','DIAG snapshot_wait_complete'];positions=[log.index(s) for s in markers];assert positions==sorted(positions)
 stdout=(P/'stdout.log').read_text();assert 'scheduler config ert(1), dataflow(1)' in stdout
 result=struct.unpack('<8Q',(P/'artifacts/result.raw').read_bytes());meta=struct.unpack('<8Q',(P/'artifacts/metadata.raw').read_bytes());goal=struct.unpack('<8Q',(P/'artifacts/goal.raw').read_bytes())
 assert result[0]==2 and result[1]==1 and result[2]==1 and meta[0]==1 and meta[1]==1 and meta[2]==2 and not any(goal)
 assert (P/'artifacts/observations.raw').stat().st_size==64
 source=(P/'source/tb/host.cpp').read_text();assert source.index('auto preserved=')<source.index('fs::create_directories(out)')<source.index('closed loop requires found nonempty path')
 imported=int(re.search(r'native initialization verified_bytes=(\d+)',log)[1]);assert imported==4482650920
 groups={int(a):dict(group=int(g),bytes=int(n),address=int(addr)) for a,g,n,addr in re.findall(r'DIAG BO index=(\d+) group=(\d+) bytes=(\d+) address=(\d+)',log)};assert groups[8]['bytes']==2097152*64 and groups[9]['bytes']==8388608*64 and groups[10]['bytes']==33554432*64
 assert 'potential consistency edges=212892069' in log
 assert len(groups)==15 and [groups[i]['group'] for i in [3,4,5]]==[13,14,15]
 assert all(m['original_processes_still_present'].values())
 files=[P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'source/tb/host.cpp',P/'run.log',P/'stdout.log',*P.joinpath('artifacts').glob('*.raw'),Path(__file__).resolve()]
 report=dict(status='seed_and_snapshot_CUs_returned_at_one_expansion_bound_full_closed_loop_not_run',host_returncode=0,expected_host_exit_reason='Instrumentedhostacceptsexpectedbudgetstatus2afteroneexpansion.',search_status=2,expanded=1,edge_visits=1,seed_calls=1,snapshot_calls=1,observations=1,labels=2,verified_upload_bytes=imported,authority_preservation_assertions_passed_before_artifact_export=True,buffer_groups=groups,observed_elapsed_wall_seconds=m['elapsed_wall_seconds'],original_processes_still_present=m['original_processes_still_present'],source_sha256={str(q):sha(q) for q in files},scope='ActualXRThw_emufullCSR/authorityinterfaceprobe,scratch2097152labels/limit1/withquotient. Seedandsnapshotreturn;budgetandreadonlyauthoritychecksobserved. Doesnotexercisecompletecrossdiepath/commit,proveoriginal2Mlabel/2Mexpansionjobprogressordeadlock,orprovidephysicalboard/performanceevidence. Walltimeincludessetup/transfersandmustnotbeextrapolatedperexpansion. Matchedquotientenabledcontrasttolargeworkspaceprobe;priorfailedsetupsremainarchivedseparately.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','buffer_groups']}))
if __name__=='__main__':main()
