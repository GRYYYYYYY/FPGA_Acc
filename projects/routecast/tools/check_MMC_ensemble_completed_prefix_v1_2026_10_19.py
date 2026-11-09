"""Early independent probability/identity check; never a full prediction admission."""
import pathlib,json,hashlib
from collections import defaultdict,Counter
from audit_MMC_full_NET_tree_ensemble_v1_2026_10_19 import audit_probabilities
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';P=M/'protocol.json';spec=json.loads(P.read_text());O=R/'experiments/mmc_ensemble_completed_prefix_check_v1_2026-10-19';O.mkdir();ep=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';meta=json.loads(ep.read_text());groups=defaultdict(list)
 for q in meta['connections']:groups[q['net_id']].append(q)
 selected=sorted(groups)[:1000];snapshot=O/'first1000_complete_records.jsonl'
 with (M/'NET_contributions.jsonl').open() as source,snapshot.open('x') as out:
  for i in range(1000):
   line=source.readline();row=json.loads(line);assert row['index']==i;out.write(line)
 modes=Counter();total_nodes=total_edges=0
 with snapshot.open() as stream:
  for i,line in enumerate(stream):
   row=json.loads(line);net=selected[i];qs=groups[net];assert row['net_id']==net and row['first_case']=='episode_01';assert {row['source']}=={q['source'] for q in qs} and row['sinks']==sorted({q['sink'] for q in qs});choices,labels,prob=audit_probabilities(row);modes[row['mode']]+=1;total_nodes+=len(labels);total_edges+=sum(map(len,choices.values()))
   if (i+1)%100==0:print('PREFIX PROBABILITY PASS',i+1,flush=True)
 assert sum(modes.values())==1000;files=[P,ep,snapshot,pathlib.Path(__file__).resolve(),R/'tools/audit_MMC_full_NET_tree_ensemble_v1_2026_10_19.py'];proof=dict(status='FIRST1000_COMPLETE_NET_RECORD_IDENTITIES_AND_INDEPENDENT_PROBABILITIES_PASS',bindings={str(p):sha(p) for p in files},NETs=1000,modes=dict(modes),support_nodes=total_nodes,support_edges=total_edges,full_prediction_admitted=False,physical_XML_reaudit_still_pending=True,scope='Early prefix diagnostic only. Mathematical probability and input identity checks on exact immutable1000record snapshot. Not allNETs/all3layouts, original XML physical edges/global minimum certification, forecast quality or timing gain; main full audit remains mandatory.')
 with (O/'verification.json').open('x') as f:json.dump(proof,f,indent=2);f.write('\n')
 print(proof['status'],flush=True)
if __name__=='__main__':main()
