"""Independent greedy replay and token seed-branch/current pin-index verification."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from zero_rc_budget_certificate_graph_v1 import load_graph
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_native_utility_seed_inputs_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 proof=read(D/'verification.json');assert all(sha(p)==h for p,h in proof['bindings'].items());protocol=read(D/'protocol.json');g=load_graph(protocol['cases'][0]['graph']);rows=[]
 for c,published in zip(protocol['cases'],proof['rows']):
  case=c['case'];out=D/case;ep=read(c['endpoint']);original=read(c['frame']);groups=defaultdict(list)
  for q in original['records']:groups[q['net_id']].append(q)
  support={}
  for net,recs in groups.items():
   nodes=set()
   for q in recs:
    u=q['source'];nodes.add(u)
    for e in q['answer']['physical_edge_ids']:assert g['us'][e]==u;u=g['vs'][e];nodes.add(u)
    assert u==q['sink']
   support[net]=nodes
  decisions=read(out/'decisions.json');order=sorted(groups,key=lambda n:(-len(groups[n]),len(support[n]),n));assert [x['net_id'] for x in decisions]==order;ledger=Counter();kept=[];rejected=[]
  for n,d in zip(order,decisions):
   blockers=sorted(x for x in support[n] if ledger[x]>=g['caps'][x]);assert blockers==d['blocking_nodes'] and d['admitted']==(not blockers)
   if blockers:rejected.append(n)
   else:ledger.update(support[n]);kept.append(n)
  subset=read(out/'subset.json');assert sorted(kept)==subset['retained_nets'] and sorted(rejected)==subset['required_reroute_nets'];assert {int(n):v for n,v in subset['ledger'].items()}==dict(ledger);expected={q['connection_id']:q for n in kept for q in groups[n]};assert {q['connection_id']:q for q in subset['records']}==expected;allids={q['connection_id'] for q in ep['connections']};assert set(subset['required_reroute_connection_ids'])==allids-expected.keys() and subset['required_connections']==len(allids)==15616
  pins=read(out/'pin_bindings.json');payload={r['connection_id']:r for r in read(c['pin_payload'])};manifest=Path(c['pin_payload']).parent/'work/pin_manifest.tsv';rawpins={}
  for line in manifest.open():
   x=line.rstrip('\n').split('\t')
   if x[0]=='P':rawpins[int(x[2]),int(x[4])]=(x[11],int(x[9]),int(x[10]))
  lookup={}
  for cid,q in expected.items():
   binding=pins[str(cid)];r=payload[cid];assert (binding['net'],binding['pin'],binding['name'])==(r['native_net_id'],r['local_sink_pin'],r['net_name']);assert rawpins[binding['net'],binding['pin']]==(binding['name'],q['source'],q['sink']);lookup[binding['net'],binding['pin']]=cid
  net=None;paths={};previous=None;last_switch=None;root=None;observed={}
  for line in (out/'seed.route').open():
   x=line.split()
   if x and x[0]=='Net':net=int(x[1]);paths={};previous=None;root=None
   elif x and x[0]=='Node:':
    n=int(x[1]);kind=x[2];switch=int(x[x.index('Switch:')+1])
    if kind=='SOURCE':root=n;paths[n]=()
    elif kind=='SINK':
     pin=int(x[x.index('Net_pin_index:')+1]);cid=lookup[net,pin];assert cid not in observed;observed[cid]=paths[previous]+((previous,n,last_switch),);q=expected[cid];assert root==q['source'] and n==q['sink']
    elif n not in paths:paths[n]=paths[previous]+((previous,n,last_switch),)
    previous=n;last_switch=switch
  assert observed.keys()==expected.keys()
  for cid,q in expected.items():assert observed[cid]==tuple((g['us'][e],g['vs'][e],g['switches'][e]) for e in q['answer']['physical_edge_ids'])
  assert len(expected)==published['retained_connections'];rows.append(dict(case=case,retained_NETs=len(kept),omitted_NETs_still_required=len(rejected),retained_connections=len(expected),omitted_connections_still_required=len(allids)-len(expected),required_total_connections=len(allids)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_GREEDY_CAPACITY_SELECTION_FULL_DEMAND_PARTITIONS_AND_NATIVE_PIN_SERIALIZATION_VERIFIED',rows=rows,bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)},scope='Original XML arc triples/current native pre-search pin manifest checked. No actual native read_route/packed pin-equivalence/nonconfigurable/canonical/STA acceptance yet; all omissions remain required work.'),f,indent=2)
 print(json.dumps(rows))
if __name__=='__main__':main()
