"""Independent Expat XML owner audit and fixed stable-support sensitivity diagnostic."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from xml.parsers import expat
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from external_forecast_metrics_v1 import metrics,gate
R=Path(__file__).resolve().parents[1];T=R/'experiments/prospective_external_family_temporal_prior_utilization_v1_2026-10-19';P=R/'experiments/prospective_external_family_temporal_prior_errors_v1_2026-10-19';D=R/'experiments/prospective_external_family_temporal_owner_turnover_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);protocol=read(T/'protocol.json');bindings={str(Path(__file__).resolve()):sha(__file__)}
 for receipt in [T/'independent_verification_v1.json',P/'summary.json',P/'independent_partition_verification_v1.json']:
  a=read(receipt);assert all(sha(p)==h for p,h in a['bindings'].items());bindings[str(receipt)]=sha(receipt)
 (D/'protocol.json').write_text(json.dumps(dict(cases=protocol['cases'],policy='Independent Expat edge reconstruction, all resource edit masks and NET support-count audit. Before outcomes: one diagnostic ablation sets every globally old-and-current occupied resource score to1, regardless of label or owner. Others unchanged. Same full-domain metrics/controls/gates; not a calibrated or capacity/physical forecast acceptance. No coefficients or case selection.'),indent=2)+'\n');bindings[str(D/'protocol.json')]=sha(D/'protocol.json')
 s=read(protocol['cases'][0]['original_comparison_spec']);ep=read(s['endpoint']);graph=ep['inputs']['graph']['path'];assert sha(graph)==ep['graph_sha256'];bindings[graph]=sha(graph);dest=[];parser=expat.ParserCreate();stack=[]
 def start(name,attrs):
  if name=='edge' and stack and stack[-1]=='rr_edges':dest.append(int(attrs['sink_node']))
  stack.append(name)
 def end(name):assert stack.pop()==name
 parser.StartElementHandler=start;parser.EndElementHandler=end
 with open(graph,'rb') as f:parser.ParseFile(f)
 rows=[]
 for c in protocol['cases']:
  s=read(c['original_comparison_spec']);folder=Path(s['domain_proof']).parent;resources=[json.loads(x) for x in (folder/'resources.jsonl').read_text().splitlines()];bins=read(folder/'spatial_bins.json');domain=read(s['domain_proof']);ids={r['id'] for r in resources};owners=[defaultdict(set),defaultdict(set)];nets=[defaultdict(dict),defaultdict(dict)]
  for i,path in enumerate([c['source_frame'],c['current_frame']]):
   for q in read(path)['records']:
    net=q['net_id'];nets[i][net][q['connection_id']]=q
    nodes={q['source']}|{dest[e] for e in q['answer']['physical_edge_ids']}
    for n in nodes&ids:owners[i][n].add(net)
  classes={};supports=[defaultdict(set),defaultdict(set)]
  for i in (0,1):
   for n,ns in owners[i].items():
    for net in ns:supports[i][net].add(n)
  for net,a in nets[0].items():
   b=nets[1][net];assert a.keys()==b.keys();source=any(q['source']!=b[k]['source'] for k,q in a.items());sinks=sum(q['sink']!=b[k]['sink'] for k,q in a.items());classes[net]=4 if source and sinks else 1 if source else 2 if sinks else 0
  expected_mask=Counter()
  for n in ids:
   for net in owners[0][n]^owners[1][n]:expected_mask[n]|=classes[net]
  observed={r['net_id']:r for r in read(P/c['case']/'NETs.json')}
  for net in nets[0]:
   a,b=supports[0][net],supports[1][net];assert (observed[net]['old_only'],observed[net]['new_only'],observed[net]['shared'])==(len(a-b),len(b-a),len(a&b))
  comparison=read(T/c['case']/'comparison.json');scores={n:F(*v) for n,v in comparison['score_vectors']['resource']};physical=read(s['label_physical_audit']);truth={int(n):v for n,v in physical['node_occupancy'].items()};turnover=[];seen=set()
  out=D/c['case'];out.mkdir(parents=True)
  with (out/'owner_masks.jsonl').open('x') as f:
   for line in (P/c['case']/'resources.jsonl').read_text().splitlines():
    r=json.loads(line);n=r['id'];assert n not in seen;seen.add(n);assert r['edit_mask']==expected_mask[n]
    f.write(json.dumps(dict(id=n,old_owners=sorted(owners[0][n]),current_owners=sorted(owners[1][n]),edit_mask=expected_mask[n]))+'\n')
    if owners[0][n] and owners[1][n] and scores[n]<1:turnover.append(dict(id=n,old_owners=sorted(owners[0][n]),current_owners=sorted(owners[1][n]),shared_owners=sorted(owners[0][n]&owners[1][n]),score=[scores[n].numerator,scores[n].denominator],truth=int(truth.get(n,0)>0)))
  assert seen==ids
  def vector(values):
   spatial=Counter()
   for r in resources:
    for k in r['bins']:spatial[tuple(k)]+=values.get(r['id'],0)
   return dict(resource={n:F(values.get(n,0)) for n in ids},spatial={tuple(b['key']):F(spatial[tuple(b['key'])],b['capacity']) for b in bins})
  ablation={n:F(1) if owners[0][n] and owners[1][n] else scores[n] for n in ids};m=metrics(vector(ablation),vector(truth),domain['resource_k'],domain['spatial_k']);checks={name:gate(m,comparison['metrics'][name]) for name in ['previous_native','raw_min_on']};row=dict(case=c['case'],resources=len(ids),stable_downweighted=turnover,ablation_metrics={scope:{k:v[k] for k in ['spearman','top_k_hits','k','universe_size']} for scope,v in m.items()},ablation_checks=checks,ablation_case_gate=all(v['pass_primary_gate'] for v in checks.values()));rows.append(row)
  for p in [out/'owner_masks.jsonl',P/c['case']/'resources.jsonl',P/c['case']/'NETs.json',T/c['case']/'comparison.json']:bindings[str(p)]=sha(p)
  print(c['case'],'stable',len(turnover),'ablation gate',row['ablation_case_gate'],row['ablation_metrics'],flush=True)
 assert all(sha(p)==h for p,h in bindings.items())
 (D/'verification.json').write_text(json.dumps(dict(status='ALL136752_EDIT_MASKS_AND_ALL_NET_SUPPORT_COUNTS_EXPAT_RECONSTRUCTED',rows=rows,bindings=bindings,scope='Owner/mask independent reconstruction complete. Stable-support ablation is a fixed diagnostic evaluated with production metrics, not yet independently metric-verified. No model acceptance.'),indent=2)+'\n')
if __name__=='__main__':main()
