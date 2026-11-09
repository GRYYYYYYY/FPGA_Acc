"""Independently check printed native indexed costs and every rebased edge field."""
from decimal import Decimal,ROUND_HALF_EVEN
import hashlib,json,struct,xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'work/sb_native_indexed_costs_20261015';cache={}
def sha(f):
 f=Path(f).resolve();key=str(f)
 if key not in cache:
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  cache[key]=h.hexdigest()
 return cache[key]
def refs(x):
 for f,h in x.get('source_sha256',{}).items():assert sha(f)==h,f

def main():
 result=json.loads((p/'result.json').read_text());assert result['status']=='six_native_indexed_cost_exports_and_exact_edge_rebases_complete';refs(result)
 protocol=json.loads((p/'protocol.json').read_text());launch=json.loads((p/'launch_protocol.json').read_text())
 for obj in [protocol,launch]:
  for f,h in obj['inputs'].items():assert sha(f)==h,f
 rows=[];proofs=[]
 for config in protocol['cases']:
  out=p/config['label'];case=Path(config['native_case']);cost=out/'costs';audit=json.loads((out/'rebase_audit.json').read_text());refs(audit)
  native=json.loads((case/'run.json').read_text());record=json.loads((cost/'costs.json').read_text());assert record['status']=='passed' and record['exit_code']==0
  for name,h in record['case_sha256'].items():assert sha(case/name)==h,name
  for name,h in record['artifacts'].items():assert sha(cost/name)==h,name
  assert sha(Path(native['sources']['vpr']['path']))==record['vpr_sha256']==native['sources']['vpr']['sha256']
  device=native['command'][native['command'].index('--device')+1];assert record['command'][record['command'].index('--device')+1]==device
  table={}
  for line in (cost/'rr_indexed_data.echo').read_text().splitlines()[2:]:
   f=line.split()
   if not f:continue
   kind=f[1];assert kind in ['SOURCE','SINK','OPIN','IPIN','CHANX','CHANY'];offset=3 if kind in ['CHANX','CHANY'] else 2;assert len(f)==offset+7
   key=(kind,int(f[offset+2]));assert key not in table
   value=Decimal(f[offset])*Decimal(10**12);assert value.is_finite() and 0<=value<=65535
   table[key]=int(value.to_integral_value(rounding=ROUND_HALF_EVEN))
  values=(cost/'node_base_cost').read_bytes();assert len(values)==2*config['nodes'];node_count=0
  for _,e in ET.iterparse(case/'rr_graph.xml',events=['end']):
   if e.tag=='node':
    i=int(e.attrib['id']);assert i==node_count;kind=e.attrib['type'];seg=e.find('segment');key=(kind,int(seg.attrib['segment_id']) if seg is not None else -1)
    assert key in table and struct.unpack_from('<H',values,2*i)[0]==table[key];node_count+=1;e.clear()
   elif e.tag=='edge':e.clear()
  assert node_count==config['nodes']
  source=Path(config['original_input']);target=out/'input'
  for ext in ['nodes','resources','tasks']:assert sha(Path(str(source)+'.'+ext))==sha(Path(str(target)+'.'+ext))
  before=Path(str(source)+'.edges').read_bytes();after=Path(str(target)+'.edges').read_bytes();assert len(before)==len(after)==8*config['edges']
  count=0
  for a,b in zip(struct.iter_unpack('<IHH',before),struct.iter_unpack('<IHH',after)):
   assert a[0]==b[0] and a[2]==b[2] and b[1]==struct.unpack_from('<H',values,2*a[0])[0];count+=1
  assert count==config['edges']
  rows.append(dict(label=config['label'],nodes=node_count,edges_checked=count,indexed_classes=len(table),minimum_base_q=min(table.values()),maximum_base_q=max(table.values())))
  proofs.extend([out/'rebase_audit.json',cost/'costs.json',cost/'rr_indexed_data.echo',cost/'node_base_cost'])
 proofs.extend([p/'result.json',p/'protocol.json',p/'launch_protocol.json',Path(__file__).resolve()])
 report=dict(status='six_native_indexed_cost_maps_and_all_edge_rebases_independently_verified',cases=rows,total_node_costs_checked=sum(r['nodes'] for r in rows),total_edges_checked=sum(r['edges_checked'] for r in rows),source_sha256={str(f):sha(f) for f in proofs},scope='IndependentDecimalHALFEVEN mappingofprintednativekind/segmenttabletoeveryfullRRnode;allrebasededgebasefieldschecked,allotheredge/node/resource/taskbytespreserved. Zero-length/nativevirtualrecordsretained. Explicitfixeddevicenativeanalysis;printedprecision/psroundingremain,notcompleteVPRfloat/RCequivalence,algorithmQoRorphysicalevidence.',board_result=False,research_complete=False)
 with (p/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],total_node_costs_checked=report['total_node_costs_checked'],total_edges_checked=report['total_edges_checked'])))
if __name__=='__main__':main()
