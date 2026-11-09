"""Independent all-edge XML lexicographic potential verification, fixed16NETs."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from array import array
import sys
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 O=R/'experiments/mmc_NET_tree_csr_certified_batch_v2_2026-10-19';rp=O/'receipt.json';v=json.loads(rp.read_text());assert v['status']=='FIXED16_NET_CERTIFIED_CSR_POTENTIALS_AND_256_TREES_PRODUCED'
 for p,h in v['bindings'].items():assert sha(p)==h,p
 old=R/'experiments/mmc_NET_tree_csr_batch_v1_2026-10-19';oldproof=old/'independent_XML_verification_v1.json';op=json.loads(oldproof.read_text());oldreceipt=old/'receipt.json';prior=json.loads(oldreceipt.read_text());assert op['status']=='ALL16_NET_SUPPORT_EDGES_AND_256_TREES_INDEPENDENT_XML_PASS' and op['bindings'][str(oldreceipt)]==sha(oldreceipt)
 graph=next(pathlib.Path(p) for p in v['bindings'] if p.endswith('rr_graph.xml'));assert op['bindings'][str(graph)]==sha(graph);caps=array('I');kinds=array('B');us=array('I');vs=array('I');weights=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append({'SOURCE':0,'SINK':1}.get(e.get('type'),2));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0 and e.get('type') in ['buffer','mux','tristate'];value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1 and value>=0;switches[int(e.get('id'))]=int(value)
  elif e.tag=='edge' and parent=='rr_edges':
   us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert sys.byteorder=='little' and len(us)==8097539 and len(caps)==904438
 eligible=array('B',(int(caps[a]>0 and caps[b]>0 and kinds[a]!=1 and kinds[b]!=0) for a,b in zip(us,vs)));eligible_count=sum(eligible);maxweight=max(weights);rows=[];bindings={str(rp):sha(rp),str(oldproof):sha(oldproof),str(oldreceipt):sha(oldreceipt),str(graph):sha(graph),str(pathlib.Path(__file__).resolve()):sha(__file__)}
 for row in v['rows']:
  net=row['net_id'];p=O/f'net_{net}.json';original=old/f'net_{net}.json';assert prior['bindings'][str(original)]==sha(original);netdata=json.loads(p.read_text());assert netdata==json.loads(original.read_text())
  pcpath=O/f'net_{net}_potential_cost.bin';phpath=O/f'net_{net}_potential_hops.bin';pc=array('Q');pc.frombytes(pcpath.read_bytes());ph=array('I');ph.frombytes(phpath.read_bytes());assert pc.itemsize==8 and ph.itemsize==4 and len(pc)==len(ph)==904438;assert max(pc)+maxweight<2**64 and max(ph)+1<2**32
  for a,b,weight,valid in zip(us,vs,weights,eligible):
   if valid:assert (pc[b],ph[b])<=(pc[a]+weight,ph[a]+1),(net,a,b)
  source=netdata['source'];assert int(pc[source])==int(ph[source])==0
  for sink in netdata['sinks']:assert (int(pc[sink]),int(ph[sink]))==tuple(netdata['distance'][str(sink)])
  rows.append(dict(net_id=net,eligible_edges_checked=eligible_count,sinks_certified=len(netdata['sinks']),minimum_RC_and_minimum_hops_dual_pass=True,all_16_witness_trees_equal_prior_independent_XML_audit=True));bindings.update({str(q):sha(q) for q in [p,original,pcpath,phpath]});print('GLOBAL DUAL PASS',net,len(netdata['sinks']),flush=True)
 with (O/'independent_global_dual_verification_v1.json').open('x') as f:json.dump(dict(status='ALL16_REAL_NETS_GLOBAL_LEXICOGRAPHIC_SHORTEST_PATH_DUALS_PASS',bindings=bindings,rows=rows,checked_edge_inequalities=sum(row['eligible_edges_checked'] for row in rows),scope='Global minima certified for the fixed16NET sink paths only in the exact additive RC/min-hop domain. XML path support admission transferred by exact full input/support/sample JSON equality. Not all55300NETs, full STA, congestion prediction quality or fullworkflow gain.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
