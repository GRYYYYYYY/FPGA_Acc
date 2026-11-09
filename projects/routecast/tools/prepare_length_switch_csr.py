"""Reweight authenticated full physical CSR with the original rr_length_switch.
No node/arc pruning, no labels; writes a fresh independent transport directory.
"""
import argparse,json,hashlib,shutil,sys
from pathlib import Path
from array import array
from decimal import Decimal,ROUND_HALF_UP
import xml.etree.ElementTree as ET
from prepared_csr import read,sha,U64

def switches(graph):
 stack=[];result={}
 for event,node in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(node);continue
  if node.tag=='switch' and len(stack)>1 and stack[-2].tag=='switches':
   if node.attrib.get('type') in {'short','buffer'}:raise ValueError('nonconfigurable closure unsupported, as original Sketch')
   timing=node.find('timing');delay=Decimal(timing.attrib.get('Tdel','0')) if timing is not None else Decimal(0)
   if not delay.is_finite() or delay<0:raise ValueError('invalid delay')
   result[int(node.attrib['id'])]=int((delay*Decimal(10**12)).to_integral_value(rounding=ROUND_HALF_UP))
  if node.tag=='switches':return result
  stack.pop()
 raise ValueError('missing switches')

def cost(kind,xlow,xhigh,ylow,yhigh,capacity,delay):
 if capacity==0:return U64
 length=max(xhigh-xlow,yhigh-ylow)+1 if kind in (4,5) else 0
 value=1+256*length+delay
 if not 0<=value<U64:raise ValueError('cost outside CSR uint64 range')
 return value

def main():
 p=argparse.ArgumentParser();p.add_argument('--prepared',type=Path,required=True);p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise ValueError('fresh output required')
 digest=sha(a.graph);m,f=read(a.prepared,digest);delays=switches(a.graph)
 values=array('Q');n=0
 for dst,sid in zip(f['dest_ranks'],f['switch_ids']):
  values.append(cost(f['types'][dst],f['xlow'][dst],f['xhigh'][dst],f['ylow'][dst],f['yhigh'][dst],f['capacities'][dst],delays[sid]));n+=1
 assert n==m['edges']
 a.output.mkdir(parents=True)
 for name,entry in m['files'].items():
  if name!='costs':shutil.copy2(a.prepared/entry['file'],a.output/entry['file'])
 if sys.byteorder!='little':values.byteswap()
 path=a.output/m['files']['costs']['file'];path.write_bytes(values.tobytes());m['files']['costs']['sha256']=sha(path)
 m['context']={'graph_sha256':digest,'cost_identity':{'definition':'semantic_sketch rr_length_switch: 1+256*destination channel span+switch delay ps round half up','implementation_sha256':sha(Path(__file__).with_name('semantic_sketch.py')),'preparer_sha256':sha(__file__)},'scale':1,'normalization':'none','mode':'rr_length_switch','cost_payload_sha256':sha(path),'edge_mapping_sha256':m['files']['edge_ids']['sha256']}
 m['context_sha256']=hashlib.sha256(json.dumps(m['context'],sort_keys=True).encode()).hexdigest();(a.output/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
 assert sha(a.graph)==digest
 (a.output/'preparation_receipt.json').write_text(json.dumps({'all_physical_edges':n,'topology_payloads_unchanged':True,'graph_sha256':digest,'source_manifest_sha256':sha(a.prepared/'manifest.json'),'context_sha256':m['context_sha256'],'manifest_sha256':sha(a.output/'manifest.json'),'scope':'cost preparation only; full replay/audit still required'},indent=2)+'\n')
 print(json.dumps({'stage':'prepared','edges':n,'context_sha256':m['context_sha256']}),flush=True)

if __name__=='__main__':main()
