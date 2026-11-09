"""Fixed CART baseline, no depth or threshold selection."""
import json,subprocess,concurrent.futures,sys
from pathlib import Path
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_paired_bbox_cart_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);design=E/'wbuart_paired_bbox_CART_design_v1_2026-10-20/protocol.json';features=E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json';contract=E/'fixed_cart_contract_v1_2026-10-20/verification.json';original=E/'wbuart_owner_delta_cart_v1_2026-10-20'
 for p in [design,features,contract,original/'independent_verification_v1.json']:assert all(sha(name)==h for name,h in read(p)['bindings'].items())
 files=[E/'wbuart_paired_bbox_features_v1_2026-10-20/independent_verification_v1.json',original/'predictions_frozen.json',Path(__file__),R/'tools/train_wbuart_paired_bbox_cart_fold_v1.py',R/'tools/compiled_fixed_cart_v1.py',R/'build/fixed_cart_v1_2026-10-20/cart.so',design,features,contract,original/'independent_verification_v1.json'];m={'output':str(D),'design':str(design),'features':str(features),'original':str(original),'inventory':str(E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json'),'workers':3,'bindings':{str(p):sha(p) for p in files},'scope':'Fixed nonlinear classical baseline on same raw features/folds. Exposed WBUART development only; no hyperparameter search or original study replacement.'};mp=D/'manifest.json';mp.write_text(json.dumps(m,indent=2)+'\n')
 def run(ep):
  with (D/(ep+'.log')).open('x') as f:p=subprocess.run([sys.executable,str(R/'tools/train_wbuart_paired_bbox_cart_fold_v1.py'),str(mp),ep],cwd=R,stdout=f,stderr=subprocess.STDOUT)
  row={'episode':ep,'exit_status':p.returncode};print(json.dumps(row),flush=True);return row
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:terminal=list(pool.map(run,['episode_01','episode_02','episode_03']))
 (D/'terminal.json').write_text(json.dumps({'rows':terminal,'all_pass':all(r['exit_status']==0 for r in terminal)},indent=2)+'\n');assert all(r['exit_status']==0 for r in terminal),'preserve failures'
 paths=[D/ep/'verification.json' for ep in ['episode_01','episode_02','episode_03']];rows=[r for p in paths for r in read(p)['rows']];assert len(rows)==9;control=read(original/'predictions_frozen.json');rows.extend(dict(r,mode='control38',reused=True) for r in control['rows'] if r['mode']=='main');assert len(rows)==18;(D/'predictions_frozen.json').write_text(json.dumps({'status':'ALL3_PAIRED_BBOX_MODELS_AND3_REUSED_CONTROLS_FROZEN','rows':rows,'bindings':{str(p):sha(p) for p in [mp,*paths]}},indent=2)+'\n');print('ALL3_PAIRED_BBOX_AND3_REUSED_CONTROL_MODELS_FROZEN',flush=True)
if __name__=='__main__':main()
