"""Full original XML topology/metadata and independent scalar cost audit."""
import pathlib,json,time,array,shutil,argparse,xml.etree.ElementTree as ET
from decimal import Decimal,ROUND_HALF_UP
from prepared_csr import read,TYPES,DIRECTIONS,SIDES,U64
from pre_route_endpoints import sha
ROOT=pathlib.Path(__file__).resolve().parents[1]
def main():
 parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();parent=ROOT/'experiments/multiplier_family_length_switch_csr_2026-10-06'/args.design;p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());assert sha(parent/'protocol.json')==r['protocol_sha256'] and sha(parent/'csr/manifest.json')==r['manifest_sha256']
 graph=p['graph'];assert sha(graph['path'])==graph['sha256'];out=ROOT/'experiments/multiplier_family_length_switch_csr_audit_2026-10-06'/args.design;out.mkdir(parents=True);(out/'source').mkdir();names=['audit_multiplier_length_switch_csr.py','prepared_csr.py','pre_route_endpoints.py']
 sources={n:sha(ROOT/'tools'/n) for n in names}
 for n in names:shutil.copyfile(ROOT/'tools'/n,out/'source'/n)
 protocol={'parent_receipt_sha256':sha(parent/'receipt.json'),'graph':graph,'source_sha256':sources,'scope':'full physical topology, metadata and scalar length-switch transport only; no prediction/legal route/QoR claim'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();m,f=read(parent/'csr',graph['sha256']);assert all(i==v for i,v in enumerate(f['node_ids']));cursor=array.array('Q',f['row_offsets'][:-1]);nodes=edges=0;delays={};stack=[]
 for event,e in ET.iterparse(graph['path'],events=('start','end')):
  if event=='start':stack.append(e);continue
  tag=stack[-2].tag if len(stack)>1 else None
  if e.tag=='switch' and tag=='switches':
   assert e.get('type') not in ['short','buffer'];t=e.find('timing');delay=Decimal(t.get('Tdel','0')) if t is not None else Decimal(0);assert delay.is_finite() and delay>=0;delays[int(e.get('id'))]=int((delay*Decimal(10**12)).to_integral_value(rounding=ROUND_HALF_UP))
  elif e.tag=='node' and tag=='rr_nodes':
   n=int(e.get('id'));assert n==nodes;nodes+=1;loc=e.find('loc');seg=e.find('segment');expected={'types':TYPES[e.get('type')],'directions':DIRECTIONS[e.get('direction','NONE')],'sides':SIDES[loc.get('side','NONE')],'capacities':int(e.get('capacity')),'segments':U64 if seg is None else int(seg.get('segment_id'))};expected.update({k:int(loc.get(k,'0')) for k in ['xlow','xhigh','ylow','yhigh','layer','ptc']})
   for k,v in expected.items():assert f[k][n]==v,(n,k)
  elif e.tag=='edge' and tag=='rr_edges':
   a=int(e.get('src_node'));b=int(e.get('sink_node'));sid=int(e.get('switch_id'));slot=cursor[a];assert slot<f['row_offsets'][a+1];cursor[a]+=1
   assert f['edge_ids'][slot]==edges and f['dest_ranks'][slot]==b and f['switch_ids'][slot]==sid
   span=max(f['xhigh'][b]-f['xlow'][b],f['yhigh'][b]-f['ylow'][b])+1 if f['types'][b] in (4,5) else 0;expected=U64 if f['capacities'][b]==0 else 1+256*span+delays[sid];assert f['costs'][slot]==expected;edges+=1
  if tag in ('rr_nodes','rr_edges','switches','segments','block_types','grid','channels'):stack[-2].remove(e);e.clear()
  stack.pop()
 assert nodes==m['nodes']==r['nodes'] and edges==m['edges']==r['edges'];assert all(cursor[i]==f['row_offsets'][i+1] for i in range(nodes));assert sha(graph['path'])==graph['sha256'];assert all(sha(ROOT/'tools'/n)==h for n,h in sources.items())
 receipt={'protocol_sha256':sha(out/'protocol.json'),'parent_receipt_sha256':protocol['parent_receipt_sha256'],'all_node_metadata_and_edge_costs_match_original_xml':True,'nodes':nodes,'edges':edges,'wall_s':time.monotonic()-start,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
