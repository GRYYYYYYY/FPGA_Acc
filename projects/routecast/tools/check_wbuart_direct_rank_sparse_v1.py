"""Real-case random transaction/full-rebuild equivalence, no training."""
import json,random
from pathlib import Path
from direct_rank_domain_v1 import load_training_domains
from direct_rank_sparse_state_v1 import State
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments'
def read(p):return json.loads(Path(p).read_text())
def main():
 rng=random.Random(20261020);features={r['case']:r for r in read(E/'wbuart_paired_bbox_features_v1_2026-10-20/verification.json')['rows']};specs={r['case']:r['specification'] for r in read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json')['comparisons']};model=read(E/'wbuart_paired_bbox_cart_v1_2026-10-20/episode_01/main/model.json');domains,_=load_training_domains(R,model,features,specs);transactions=rejections=0
 for case,d in domains:
  for initial in [[0]*len(d.ids),[1]*len(d.ids),[int(i%3==0) for i in range(len(d.ids))]]:
   state=State(d,initial);assert state.score()==d.score(initial)
   for step in range(20):
    chosen=rng.sample(range(len(initial)),rng.randint(0,32));changes=[(i,rng.randrange(2)) for i in chosen];state.update(changes)
    for i,p in changes:initial[i]=p
    assert state.points==initial and state.score()==d.score(initial);transactions+=1
   before=state.points.copy();score=state.score()
   for changes in [[(-1,0)],[(len(initial),1)],[(0,2)],[(0,0),(0,1)]]:
    try:state.update(changes)
    except ValueError:pass
    else:raise AssertionError('invalid update accepted')
    assert state.points==before and state.score()==score;rejections+=1
  print('SPARSE_STATE_REAL_CASE_PASS',case,flush=True)
 D=E/'wbuart_direct_rank_sparse_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/direct_rank_sparse_state_v1.py',R/'tools/direct_rank_domain_v1.py',E/'wbuart_direct_rank_domain_contract_v1_2026-10-20/verification.json'];v={'status':'PASS_REAL_SPARSE_BINARY_STATE_FULL_REBUILD_EQUIVALENCE','cases':6,'transactions':transactions,'atomic_invalid_rejections':rejections,'bindings':{str(p):sha(p) for p in files},'scope':'Resource sufficient statistics/TopK indexed; spatial ranks still rebuilt. Not complete split trainer or performance claim; no model fit.'};(D/'verification.json').write_text(json.dumps(v,indent=2)+'\n');print(v['status'],transactions,rejections)
if __name__=='__main__':main()
