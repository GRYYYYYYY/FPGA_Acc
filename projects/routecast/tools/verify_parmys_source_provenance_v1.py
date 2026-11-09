"""Bind source RAM names to exact-parity logged replay macro descendants."""
import json,hashlib,re
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'parmys_source_provenance_replay_v1_2026-10-21';P=E/'preserved_source_ram_mapping_v1_2026-10-21';B=E/'private_parmys_provenance_build_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for root in [B,D]:
  for p,h in json.loads((root/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 result=json.loads((D/'results.json').read_text());assert len(result['rows'])==4 and all(r['exit_code']==0 for r in result['rows']);rows=[]
 for name in ['mcml','mkDelayWorker32B']:
  f=D/name;original=json.loads((f/'original/mapped.json').read_text());instrumented=json.loads((f/'instrumented/mapped.json').read_text());assert original==instrumented
  boundary=json.loads((P/name/'preserved_boundary.json').read_text())['modules'][name];expected={n:c for n,c in boundary['cells'].items() if c['type'].endswith(('single_port_ram','dual_port_ram'))};log=(f/'instrumented/yosys.log').read_text();source2node={};node2root={}
  for line in log.splitlines():
   if line.startswith('RC_RAM_INPUT\t'):
    _,source,node=line.split('\t');source=source.removeprefix('\\');assert source not in source2node;source2node[source]=node
   if line.startswith('RC_RAM_CREATE\t'):
    _,node,root=line.split('\t');assert node not in node2root;node2root[node]=root
  assert set(source2node)==set(expected);assert set(node2root)==set(source2node.values());root2source={node2root[node]:s for s,node in source2node.items()};assert len(root2source)==len(expected)
  m=instrumented['modules'][name];aliases=defaultdict(list)
  for n,v in m['netnames'].items():
   for bit in v['bits']:aliases[bit].append(n)
  groups=defaultdict(list);padding=Counter()
  for cn,c in m['cells'].items():
   if c['type'] not in ['single_port_ram','dual_port_ram']:continue
   z=c['connections'];outs=[bit for k,bs in z.items() if c['port_directions'][k]=='output' for bit in bs];matches={root for bit in outs for alias in aliases[bit] for root in root2source if re.match(re.escape(root)+r'(?=$|[-_^])',alias)};assert len(matches)==1,(cn,matches);root=next(iter(matches));source=root2source[root];groups[source].append(cn)
   ap=['addr1','addr2'] if c['type']=='dual_port_ram' else ['addr'];dp='data1' if c['type']=='dual_port_ram' else 'data';assert len(z[dp])==1
   for p in ap:assert len(z[p])==11;padding[source]+=z[p].count('x')
  assert set(groups)==set(expected);sources=[]
  for source,c in expected.items():
   z=c['connections'];a=len(z.get('addr1',z.get('addr')));w=len(z.get('data1',z.get('data')));count=w*(1<<max(0,a-11));assert len(groups[source])==count
   sources.append({'source_instance':source,'mapper_input_node':source2node[source],'mapper_memory_root':node2root[source2node[source]],'address_bits':a,'data_bits':w,'descendant_count':count,'descendant_cells':groups[source],'physical_address_x_connections':padding[source]})
  rows.append({'source':name,'exact_original_vs_instrumented_JSON_parity':True,'logical_RAM_count':len(expected),'physical_RAM_count':sum(map(len,groups.values())),'groups':sources,'bindings':{str(p.relative_to(R)):sha(p) for p in [f/'original/mapped.json',f/'instrumented/mapped.json',f/'instrumented/yosys.log']}})
 out={'status':'ALL_19_RAM_GROUPS_BOUND_TO_EXACT_PARITY_REPLAY','rows':rows,'scope':'Provenance applies only to newly replayed mapped artifacts. Existing earlier full-source mapped file has different serialized IDs/names and is not given a positional mapping. Logged cell->input node->memory root plus output net aliases bind all descendants uniquely. Shape/count checks supplement identities; they are not semantic equivalence. X-padded physical address connections are recorded, not assumed zero or valid functional simulation.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status']);print([(r['source'],r['logical_RAM_count'],r['physical_RAM_count']) for r in rows])
if __name__=='__main__':main()
