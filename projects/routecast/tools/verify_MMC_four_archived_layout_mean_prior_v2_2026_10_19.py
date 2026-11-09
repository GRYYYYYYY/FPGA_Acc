"""Independent per-node four-way arithmetic and full original-XML capacity admission."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from array import array
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_four_archived_layout_mean_prior_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 pp=O/'protocol.json';rp=O/'production_receipt.json';fp=O/'occupancy_sum.json';p=json.loads(pp.read_text());r=json.loads(rp.read_text());f=json.loads(fp.read_text());assert sha(fp)==r['prior_sha256'] and p['weights']==[1]*4 and p['denominator']==f['denominator']==4
 for doc in [p,r]:
  for x,h in doc['bindings'].items():assert sha(pathlib.Path(x))==h
 ledgers=[];bindings={str(x):sha(x) for x in [pp,rp,fp,pathlib.Path(__file__).resolve()]}
 for x in p['historical_states']:
  sp=pathlib.Path(x['state']);vp=pathlib.Path(x['verification']);v=json.loads(vp.read_text());assert sha(sp)==x['state_sha256']==v['bindings'][str(sp)];s=json.loads(sp.read_text());ledger={int(k):n for k,n in s[x['ledger_key']].items()};ledgers.append(ledger)
  if x['tag']!='source':assert s['inputs_sha256']['graph']==f['graph_sha256']
  bindings[str(sp)]=sha(sp);bindings[str(vp)]=sha(vp)
 union=set().union(*(set(x) for x in ledgers));reported={int(k):v for k,v in f['summed_unique_NET_occupancy'].items()};assert set(reported)==union
 for n in union:assert type(reported[n]) is int and reported[n]==sum(x.get(n,0) for x in ledgers)
 sv=json.loads(pathlib.Path(p['historical_states'][0]['verification']).read_text());graphs=[pathlib.Path(x) for x,h in sv['bindings'].items() if h==f['graph_sha256'] and x.endswith('.xml')];assert graphs and all(sha(x)==f['graph_sha256'] for x in graphs);graph=sorted(graphs)[0];assert sha(graph)==f['graph_sha256'];caps=array('I');channels=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   n=int(e.get('id'));assert n==len(caps);cap=int(e.get('capacity'));caps.append(cap)
   if e.get('type') in ['CHANX','CHANY'] and cap>0:assert cap==1;channels.append(n)
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert len(caps)==904438 and len(channels)==258720
 for n in union:
  assert 0<=n<len(caps) and 0<reported[n]<=4*caps[n]
  for ledger in ledgers:assert 0<=ledger.get(n,0)<=caps[n]
 histogram={str(k):sum(reported.get(n,0)==k for n in channels) for k in range(5)};assert sum(histogram.values())==len(channels);bindings[str(graph)]=sha(graph)
 result=dict(status='EXACT_FOUR_HISTORICAL_LEDGER_MEAN_AND_FULL_XML_CAPACITIES_VERIFIED',bindings=bindings,graph_sha256=f['graph_sha256'],nodes=len(caps),positive_CHANNEL_nodes=len(channels),historical_states=4,denominator=4,CHANNEL_sum_histogram=histogram,all_node_integer_sums_exact=True,all_historical_and_mean_node_occupancies_within_capacities=True,all_zero_CHANNEL_nodes_retained_in_evaluation_domain=True,target_labels_opened=0,scope='Arithmetic occupancy-prior admission only. Mean does not represent a simultaneous physical routing or per-connection RC guarantee, has no target-specific geometry adaptation, and cannot imply original prediction-quality, native utility, prospective history or heldout success.')
 (O/'independent_prediction_verification_v1.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],histogram,flush=True)
if __name__=='__main__':main()
