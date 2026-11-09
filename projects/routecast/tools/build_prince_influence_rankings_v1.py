"""Fixed continuous source/initializer spatial influence scores; no target labels."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as Q
from array import array
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_influence_rankings_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);protocol=dict(budgets_percent=[10,25,50],selection='All dirty NETs mandatory plus floor(clean_NET_count*percent/100) clean NETs. Descending exact score, ascending NET ID ties.',scores={'delta_mean':'Source clean CHANNEL inclusive-bin visit weighted mean of abs(sum dirty warm bin visits - sum dirty source bin visits)/bin capacity','exposure_mean':'Same weighted mean of dirty warm bin visits/bin capacity','overlap_fraction':'Fraction of clean source inclusive-bin visits touching any dirty warm bin','source_length':'Source unique CHANNEL node count','fanout':'Source data CID count'},scope='Development input-only score freeze; no target native route/occupancy read. Historical development labels already exposed, no blind/unseen claim. All five methods and budgets retained; no best-method promotion from this screen.',bindings={str(Path(__file__)):sha(__file__)})
 (D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
 for w in [128,160]:
  base=E/'prince_native_cohort_v1_2026-10-20'/f'w{w}';graph=base/'source/rr_graph.xml';dest=array('I')
  for event,x in ET.iterparse(graph):
   if x.tag=='edge':dest.append(int(x.get('sink_node')))
   x.clear()
  source=E/'prince_native_source_checkpoints_v1_2026-10-20'/f'w{w}'/'initial.json';old=json.loads(source.read_text());oldrows={x['connection_id']:x for x in old['records']};rp=E/'prince_quality_domains_v1_2026-10-20'/f'w{w}'/'resources.jsonl';bp=rp.parent/'spatial_bins.json';resourcebins={x['id']:[tuple(k) for k in x['bins']] for x in map(json.loads,rp.open())};capacity={tuple(x['key']):x['capacity'] for x in json.loads(bp.read_text())}
  def nodes(frame):
   result=defaultdict(set)
   for x in frame['records']:result[x['net_id']].update(dest[eid] for eid in x['answer']['physical_edge_ids'] if dest[eid] in resourcebins)
   return result
  def bins(ns):return Counter(key for n in ns for key in resourcebins[n])
  sn=nodes(old);fanout=Counter(x['net_id'] for x in old['records'])
  for i in [1,2,3]:
   case=f'w{w}/episode_{i:02d}';ep=base/f'episode_{i:02d}'/'pre_route_endpoints.json';meta=json.loads(ep.read_text());warm=E/'prince_warm_initializers_v1_2026-10-20'/case/'native_retained';seedpath=warm/'initial.json';seed=json.loads(seedpath.read_text());assert seed['graph_sha256']==old['graph_sha256']==meta['graph_sha256']==sha(graph);dirty={x['net_id'] for x in meta['connections'] if (x['source'],x['sink'])!=(oldrows[x['connection_id']]['source'],oldrows[x['connection_id']]['sink'])};clean=set(fanout)-dirty;wn=nodes(seed);before=Counter();after=Counter()
   for net in dirty:before.update(bins(sn[net]));after.update(bins(wn[net]))
   delta={key:Q(abs(after[key]-before[key]),capacity[key]) for key in capacity};exposure={key:Q(after[key],capacity[key]) for key in capacity};cb={net:bins(sn[net]) for net in clean};scores={};inverted=defaultdict(list)
   for net,visits in cb.items():
    total=sum(visits.values());den=max(1,total);scores[net]=dict(delta_mean=sum((count*delta[key] for key,count in visits.items()),Q())/den,exposure_mean=sum((count*exposure[key] for key,count in visits.items()),Q())/den,overlap_fraction=Q(sum(count for key,count in visits.items() if after[key]),den),source_length=Q(len(sn[net])),fanout=Q(fanout[net]))
    for key,count in visits.items():inverted[key].append((net,count))
   # Independent transposed bin-to-NET accumulation of all three spatial numerators.
   audit={net:[Q(),Q(),0] for net in clean}
   for key,owners in inverted.items():
    for net,count in owners:audit[net][0]+=count*delta[key];audit[net][1]+=count*exposure[key];audit[net][2]+=count*bool(after[key])
   for net in clean:
    den=max(1,sum(cb[net].values()));assert [scores[net][m] for m in ['delta_mean','exposure_mean','overlap_fraction']]==[x/den if isinstance(x,Q) else Q(x,den) for x in audit[net]]
   rankings={m:sorted(clean,key=lambda net:(-scores[net][m],net)) for m in protocol['scores']};selection={m:{str(b):sorted(dirty|set(order[:len(clean)*b//100])) for b in protocol['budgets_percent']} for m,order in rankings.items()};paths=[source,graph,rp,bp,ep,seedpath,warm/'verification.json',D/'protocol.json'];bindings={str(p):sha(p) for p in paths};out=D/case;out.mkdir(parents=True);p=out/'rankings.json';p.write_text(json.dumps(dict(case=case,dirty_NETs=sorted(dirty),clean_NETs=sorted(clean),scores={str(n):{m:[x.numerator,x.denominator] for m,x in s.items()} for n,s in scores.items()},rankings=rankings,selections=selection,bindings=bindings,no_target_label_inputs=True),indent=2)+'\n');rows.append(dict(case=case,rankings=str(p),sha256=sha(p)));print('INFLUENCE_RANKINGS',case,len(clean),flush=True)
 (D/'verification.json').write_text(json.dumps(dict(rows=rows,bindings={str(D/'protocol.json'):sha(D/'protocol.json'),**{x['rankings']:x['sha256'] for x in rows}},transposed_score_reconstruction_pass=True),indent=2)+'\n')
if __name__=='__main__':main()
