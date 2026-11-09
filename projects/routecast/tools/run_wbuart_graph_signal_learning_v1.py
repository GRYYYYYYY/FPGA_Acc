"""Freeze all fold training commands and await all terminal models/predictions."""
import json,sys,subprocess,concurrent.futures
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_graph_signal_learning_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_graph_signal_learning_design_v1_2026-10-20/protocol.json';features=E/'wbuart_graph_learning_features_v1_2026-10-20/verification.json';contract=E/'logistic_batch_contract_v1_2026-10-20/verification.json'
 for p in [design,features,contract]:assert all(sha(name)==h for name,h in read(p)['bindings'].items())
 files=[Path(__file__),R/'tools/train_wbuart_graph_signal_fold_v1.py',R/'tools/forecast_split_provenance_v1.py',R/'tools/compiled_logistic_batch_v1.py',R/'build/logistic_batch_v1_2026-10-20/logistic.so',design,features,contract];m={'output':str(D),'design':str(design),'features':str(features),'inventory':str(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json'),'workers':3,'bindings':{str(p):sha(p) for p in files},'scope':'Retrospective within-exposed-family fold development. No hyperparameter scan, evaluation label input or new family claim.'};mp=D/'manifest.json';mp.write_text(json.dumps(m,indent=2)+'\n')
 def run(episode):
  p=D/(episode+'.log')
  with p.open('x') as f:result=subprocess.run([sys.executable,str(R/'tools/train_wbuart_graph_signal_fold_v1.py'),str(mp),episode],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  row={'episode':episode,'exit_status':result.returncode,'log':str(p)};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:terminal=list(pool.map(run,['episode_01','episode_02','episode_03']))
 (D/'terminal.json').write_text(json.dumps({'rows':terminal,'all_pass':all(x['exit_status']==0 for x in terminal)},indent=2)+'\n');assert all(x['exit_status']==0 for x in terminal),'preserve all failed artifacts'
 rows=[r for ep in ['episode_01','episode_02','episode_03'] for r in read(D/ep/'verification.json')['rows']];assert len(rows)==18;(D/'predictions_frozen.json').write_text(json.dumps({'status':'ALL6_MODELS_AND18_OUT_OF_EPISODE_PREDICTIONS_FROZEN','rows':rows,'bindings':{str(mp):sha(mp),**{str(D/ep/'verification.json'):sha(D/ep/'verification.json') for ep in ['episode_01','episode_02','episode_03']}},'quality_evaluation_pending':True},indent=2)+'\n');print('ALL_GRAPH_LEARNING_PREDICTIONS_FROZEN',flush=True)
if __name__=='__main__':main()
