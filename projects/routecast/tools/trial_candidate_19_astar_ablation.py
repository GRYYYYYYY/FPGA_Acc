"""Retrospective same-cohort A* heuristic-weight diagnostic; no predictor tuning claim."""
import json,os,re,shutil,subprocess
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/candidate_19_astar_ablation_2026-10-06';out.mkdir();work=root/'work/candidate_19_astar_ablation_2026-10-06';work.mkdir();parent=root/'experiments/candidate_19_connection_capture_2026-10-06';prior=json.loads((parent/'receipt.json').read_text());row=next(x for x in prior['results'] if x['variant']=='prerelease');assert all(sha(p)==h for p,h in row['files_sha256'].items());src=Path(row['cwd']);results=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for factor in ('1.2','1.0','0.0'):
 cwd=work/factor;cwd.mkdir()
 for n in ('design.net','design.place','design.blif','seed.route','repair_names.txt'):shutil.copyfile(src/n,cwd/n)
 cmd=row['command']+['--astar_fac',factor];runenv={**env,'ROUTECAST_NATIVE_SEED':str(cwd/'seed.route'),'ROUTECAST_REPAIR_NET_NAMES':str(cwd/'repair_names.txt'),'ROUTECAST_PRERELEASE_NET_NAMES':str(cwd/'repair_names.txt'),'ROUTECAST_CONNECTION_CAPTURE_DIR':str(cwd)}
 with (cwd/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=cwd,env=runenv,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(cwd/'run.log').read_text();assert code==0 and 'VPR succeeded' in log and 'Completed routing consistency check successfully.' in log;cpd=float(re.search(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[1]);graph=cmd[cmd.index('--read_rr_graph')+1];physical=audit(graph,cwd/'output.route');assert len(physical['connections'])==516 and not physical['overflow_units'];counts=re.findall(r'total_nets_routed:\s*(\d+)\s+total_connections_routed:\s*(\d+)\s+total_heap_pushes:\s*(\d+)\s+total_heap_pops:\s*(\d+)',log);results.append({'astar_fac':factor,'cpd_ns':cpd,'search_counts':[list(map(int,c)) for c in counts],'cwd':str(cwd),'command':cmd,'files_sha256':{str(p):sha(p) for p in cwd.iterdir() if p.is_file()}});print(factor,cpd,counts,flush=True)
(out/'receipt.json').write_text(json.dumps({'results':results,'parent_receipt_sha256':sha(parent/'receipt.json'),'binary_sha256':sha(row['command'][0]),'source_sha256':sha(Path(__file__)),'scope':'Candidate-19 same expanded prereleased cohort, A* weight 1.2/1/0. Retrospective heuristic diagnostic; no whole-pipeline performance, universal admissibility or unseen-family claim.'},indent=2)+'\n')
