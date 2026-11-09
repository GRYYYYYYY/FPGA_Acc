"""Graph-bound snapshot-to-exact search context, no XML parse; model-required node view only."""
import json
from pathlib import Path
from array import array
from fractions import Fraction
import xml.etree.ElementTree as E
from pre_route_endpoints import sha
from csr_exact_buffered_rc import ExactBufferedRC
from class_cached_integer_rc_v1 import IntegerRC
R=Path(__file__).resolve().parents[1]
def load_endpoints(endpoint_path):
 ep=json.loads(Path(endpoint_path).read_text());assert all(sha(v['path'])==v['sha256'] for v in ep['inputs'].values());graph=Path(ep['inputs']['graph']['path']);digest=sha(graph);assert digest==ep['graph_sha256']
 S=R/'experiments/sha_native_resident_snapshot_v3_2026-10-10';proofpath=R/'experiments/native_resident_csr_order_v1_2026-10-10/verification.json';proof=json.loads(proofpath.read_text());assert proof['all_native_ordered_arcs_equal_original_CSR'] and proof['all_native_CSR_slots_equal_original_physical_edge_ID'] and all(sha(p)==h for p,h in proof['bindings'].items());assert proof['bindings'][str(graph)]==digest if str(graph) in proof['bindings'] else digest==json.loads((S/'independent_verification.json').read_text())['bindings'].get(str(graph))
 M=R/'experiments/native_switch_exact_rc_boundary_v1_2026-10-10';metadata=json.loads((M/'exact_switch_metadata.json').read_text());electrical=json.loads((M/'verification.json').read_text());assert metadata['graph_sha256']==digest and metadata['source_verification_sha256']==sha(M/'verification.json') and electrical['node_RC_zero_for_all91088'] and all(sha(p)==h for p,h in electrical['bindings'].items());assert [(x['switch_id'],x['exact_R'],x['exact_Tdel']) for x in metadata['switches']]==[(x['switch_id'],x['exact_R'],x['exact_Tdel']) for x in electrical['switch_entries']]
 types={0:'SOURCE',1:'SINK',2:'IPIN',3:'OPIN',4:'CHANX',5:'CHANY'};nodes=[];degrees=array('Q');f={k:array('Q') for k in ['node_ids','row_offsets','dest_ranks','edge_ids','switch_ids','costs','capacities']};previous=-1
 for line in (S/'on/resident.tsv').read_text().splitlines():
  x=line.split('\t')
  if x[0]=='N':
   n,kind,cap,xlo,xhi,ylo,yhi,layer=map(int,x[1:9]);assert n==len(nodes) and float.fromhex(x[9])==float.fromhex(x[10])==0;node=E.Element('node',id=str(n),type=types[kind],capacity=str(cap));E.SubElement(node,'loc',xlow=str(xlo),xhigh=str(xhi),ylow=str(ylo),yhigh=str(yhi),layer=str(layer));nodes.append(node);degrees.append(0);f['node_ids'].append(n);f['capacities'].append(cap)
  elif x[0]=='E':
   u,v,sid=map(int,x[1:]);assert u>=previous;previous=u;degrees[u]+=1;f['edge_ids'].append(len(f['dest_ranks']));f['dest_ranks'].append(v);f['switch_ids'].append(sid);f['costs'].append(1)
 f['row_offsets'].append(0)
 for degree in degrees:f['row_offsets'].append(f['row_offsets'][-1]+degree)
 assert len(nodes)==91088 and len(f['edge_ids'])==801735
 switches={x['switch_id']:(Fraction(x['exact_R']),Fraction(x['exact_Tdel'])) for x in metadata['switches']};rc=IntegerRC(ExactBufferedRC(f,array('Q',[0])*len(nodes),[(Fraction(),Fraction())],switches));assert rc.scale==metadata['integer_scale'];assert sha(graph)==digest
 return graph,digest,nodes,f,rc,ep['connections']
