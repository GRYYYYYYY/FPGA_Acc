"""Independent XML/NET-owner reconstruction of bounded real primitive evidence."""
import json,hashlib,struct,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction as F
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_map_weighted_real_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def f32(x):return struct.unpack('f',struct.pack('f',x))[0]
def num(bits):return struct.unpack('>f',bytes.fromhex(bits))[0]
def main():
 source=D/'verification.json';v=read(source)
 for p,h in v['bindings'].items():assert sha(p)==h
 manifest=read(E/'wbuart_map_probe_targets_v1_2026-10-20/manifest.json');forecast=read(E/'wbuart_forecasts_v1_2026-10-20/verification.json');rows=[];bindings={str(source):sha(source),str(Path(__file__)):sha(__file__)}
 for row in v['rows']:
  case=next(x for x in manifest['cases'] if x['target_case']==row['case']);ep=read(case['endpoint']);graph=Path(ep['inputs']['graph']['path']);root=ET.parse(graph).getroot();nodes=list(root.find('rr_nodes'));edges=list(root.find('rr_edges'));outgoing=defaultdict(list)
  for eid,e in enumerate(edges):outgoing[int(e.get('src_node'))].append((eid,int(e.get('sink_node')),int(e.get('switch_id'))))
  csr=[x for u in range(len(nodes)) for x in outgoing[u]];switch={int(x.get('id')):F(x.find('timing').get('Tdel','0')) for x in root.find('switches')};assert all(F(x.find('timing').get('R','0'))==0 for x in root.find('switches'));assert all(F(n.find('timing').get('R'))==F(n.find('timing').get('C'))==0 for n in nodes)
  arm=Path(next(a['output'] for r in forecast['rows'] if r['case']==row['case'] for a in r['arms'] if a['initializer']=='native_retained' and a['timing_policy']=='warm_timing_round_updated'));warm=read(arm/'initial.json');owners=defaultdict(set)
  for rec in warm['records']:
   u=rec['source'];owners[u].add(rec['net_id'])
   for eid in rec['answer']['physical_edge_ids']:
    edge=edges[eid];assert int(edge.get('src_node'))==u;u=int(edge.get('sink_node'));owners[u].add(rec['net_id'])
   assert u==rec['sink']
  assert {n:len(s) for n,s in owners.items()}=={int(n):count for n,count in warm['ledger'].items() if count}
  proof=E/'wbuart_node_bases_v1_2026-10-20'/row['case'].split('/')[0]/'verification.json';pv=read(proof);scale=pv['scale'];table=next(Path(p) for p in pv['bindings'] if p.endswith('/indexed.tsv'));lines=[x.split() for x in table.read_text().splitlines()];idx={int(x[1]):x for x in lines if x[0]=='I'};mapping={};types=['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY']
  for x in lines:
   if x[0]=='N':
    r=idx[int(x[2])];f=F.from_float(f32(float(r[3])))*scale;mapping[types[int(x[1])],int(r[2])]=-(-f.numerator//f.denominator)
  costs=[]
  for n,node in enumerate(nodes):
   seg=node.find('segment');base=mapping[node.get('type'),int(seg.get('segment_id')) if seg is not None else -1];loc=node.find('loc');span=max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))+1 if node.get('type') in ['CHANX','CHANY'] else 0;other=len(owners[n]-{0});costs.append(base*(1+max(0,other-int(node.get('capacity'))+1))+scale//20000000000*span)
  records={r['connection_id']:r for r in warm['records']};timing={r['connection_id']:r for r in read(arm/'timing_round0.json')['criticalities']};checked=0
  for mode in ['H0','MAP']:
   arrival={};parents={}
   for q in row['queries']:
    rec=records[q['CID']];answer=q[mode];c=F(q['criticality']);assert c==F.from_float(num(timing[q['CID']]['criticality_bits']));assert q['budget']==rec['budget_integer'];source_rr=rec['source'];arrival.setdefault(source_rr,0);seeds=set(arrival);u=source_rr;raw=0;seen={u};tail=False;tailcost=0;tailnodes=[]
    for slot in answer['path_slots']:
     eid,dest,sid=csr[slot];assert int(edges[eid].get('src_node'))==u;assert dest not in seen;seen.add(dest);delta=switch[sid]*scale;assert delta.denominator==1;raw+=int(delta)
     if u==answer['attach']:tail=True
     if tail:assert dest not in seeds;tailcost+=costs[dest];tailnodes.append((u,dest,slot,raw))
     else:assert parents[dest]==(u,slot)
     u=dest
    assert u==rec['sink'] and raw==answer['raw'];g=c*raw+(1-c)*tailcost;assert g*answer['objective_denominator']==answer['objective_numerator'];assert (raw<=q['budget'])==answer['committed'];assert answer['attach'] in seeds
    if answer['committed']:
     for parent,dest,slot,r in tailnodes:parents[dest]=(parent,slot);arrival[dest]=r
    checked+=1
  rows.append({'case':row['case'],'all_warm_NET_owners_rebuilt':True,'path_objective_checks':checked});print(row['case'],'INDEPENDENT_PASS',flush=True)
  for p in [graph,proof,table,arm/'initial.json',arm/'timing_round0.json']:bindings[str(p)]=sha(p)
 assert len(rows)==9
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_XML_OWNER_LEDGER_PRICES_SHARED_TREE_PHYSICAL_PATH_RAW_AND_OBJECTIVE_PASS','rows':rows,'bindings':bindings,'scope':'Independent full warm owner reconstruction and indexed base/price/path/retained objective accounting. Heap search behavior remains separately covered by producer reference; no allNET quality/native equivalence claim.'},indent=2)+'\n')
if __name__=='__main__':main()
