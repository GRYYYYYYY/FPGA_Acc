"""Independent scope audit of single-factor ablation before terminal results."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/rr_remaining_tail_zero_seed_ablation_20261015';A=R/'work/rr_remaining_tail_precision_development_v2_20261015'
def main():
 refs={};rows=[]
 def bind(p):
  refs[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
 protocol=json.loads((P/'protocol.json').read_text())
 assert [c['label'] for c in protocol['cases']]==['ex5p','diffeq','alu4']
 assert protocol['arms']==[dict(label='weight0_scale256',mode='downstream_bounded',remaining_tail=1,timing_weight=0,cost_scale=256)]
 for c in protocol['cases']:
  paths=[P/'recipes'/c['label']/'weight0_scale256/pair.json',A/'recipes'/c['label']/'scale256/pair.json']
  steps=[json.loads(f.read_text())['steps'][0] for f in paths]
  new,old=[dict(s['routing_environment']) for s in steps]
  assert new.pop('DIEROUTE_TREE_TIMING_WEIGHT_Q')=='0' and old.pop('DIEROUTE_TREE_TIMING_WEIGHT_Q')=='128';assert new==old
  for k,v in [('DIEROUTE_MAX_ITERATIONS','30'),('DIEROUTE_MIN_TIMING_ITERATIONS','3'),('DIEROUTE_REMAINING_LAYER_TAIL','1'),('DIEROUTE_COST_SCALE','256')]:assert new[k]==v
  assert steps[0]['command'][:3]==steps[1]['command'][:3] and steps[0]['command'][4:]==steps[1]['command'][4:]
  for name in ['input.tasks','source']:
   first=paths[0].parent/name;second=paths[1].parent/name;assert first.resolve()==second.resolve()
  for f in paths:bind(f)
  assert refs[str(paths[0])]==protocol['source_sha256'][str(paths[0])]
  rows.append(dict(case=c['label'],only_routing_environment_change='DIEROUTE_TREE_TIMING_WEIGHT_Q:128->0',same_input_tasks_and_source_target=True))
 source=R/'work/rr_remaining_layer_tail_variant_20261015/source/dieroute/src/wide_controller.cpp';s=source.read_text();start=s.index('std::vector<SearchSeed> tree_seeds(');end=s.index('\nvoid ripup(',start);body=s[start:end]
 assert 'cost_scale*timing_weight_q/(65535U*256U)' in body and 'tree.depth.at(item.first)' in body
 for p in [source,P/'protocol.json',P/'launch_protocol.json',A/'independent_audit.json',Path(__file__).resolve()]:bind(p)
 report=dict(status='three_zero_seed_configurations_single_factor_verified',cases=rows,tree_seed_source_excerpt=body,source_sha256=refs,scope='Recipe control audit. Zero weight removes accumulated-tree-delay initial seed cost; tree seed vertices and depth metadata remain. Edge timing costs and native STA remain enabled. Source excerpt bound by this supplemental audit after launch; no new prelaunch source identity claim, run/QoR/adoption/physical result.',adopted=False,board_result=False,research_complete=False)
 with (P/'configuration_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(report['status'])
if __name__=='__main__':main()
