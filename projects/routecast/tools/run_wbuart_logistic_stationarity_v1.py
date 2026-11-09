"""All six same-objective Newton diagnostics frozen before score evaluation."""
import json,subprocess,concurrent.futures,sys
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_logistic_stationarity_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_logistic_stationarity_design_v1_2026-10-20/protocol.json';features=E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json';contract=E/'logistic_newton_contract_v1_2026-10-20/verification.json';original=E/'wbuart_graph_signal_learning_v1_2026-10-20'
 for p in [design,features,contract,original/'independent_verification_v1.json']:assert all(sha(name)==h for name,h in read(p)['bindings'].items())
 files=[Path(__file__),R/'tools/train_wbuart_stationarity_fold_v1.py',R/'tools/compiled_logistic_newton_v1.py',R/'build/logistic_newton_v1_2026-10-20/newton.so',design,features,contract,original/'independent_verification_v1.json'];m={'output':str(D),'design':str(design),'features':str(features),'original':str(original),'inventory':str(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json'),'workers':3,'bindings':{str(p):sha(p) for p in files},'scope':'Train-only solver adequacy diagnostic, not a replacement of original fixed1000-step study; no exact optimum certificate.'};mp=D/'manifest.json';mp.write_text(json.dumps(m,indent=2)+'\n')
 def run(ep):
  with (D/(ep+'.log')).open('x') as f:p=subprocess.run([sys.executable,str(R/'tools/train_wbuart_stationarity_fold_v1.py'),str(mp),ep],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  row={'episode':ep,'exit_status':p.returncode};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:terminal=list(pool.map(run,['episode_01','episode_02','episode_03']))
 (D/'terminal.json').write_text(json.dumps({'rows':terminal,'all_pass':all(r['exit_status']==0 for r in terminal)},indent=2)+'\n');assert all(r['exit_status']==0 for r in terminal),'preserve failures'
 paths=[D/ep/'verification.json' for ep in ['episode_01','episode_02','episode_03']];rows=[r for p in paths for r in read(p)['rows']];assert len(rows)==18;(D/'predictions_frozen.json').write_text(json.dumps({'status':'ALL6_SAME_OBJECTIVE_MODELS_AND18_PREDICTIONS_FROZEN','rows':rows,'all_numeric_stationary':all(r['numeric_stationarity'] for r in rows),'bindings':{str(p):sha(p) for p in [mp,*paths]}},indent=2)+'\n');print('ALL_STATIONARITY_MODELS_FROZEN',all(r['numeric_stationarity'] for r in rows),flush=True)
if __name__=='__main__':main()
