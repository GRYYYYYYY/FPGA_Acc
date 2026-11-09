"""Audit the completed switchblock baseline matrix, including isolated RR records."""
from array import array
from collections import Counter
import hashlib,json,math,re
from pathlib import Path
import xml.etree.ElementTree as ET
root=Path(__file__).resolve().parents[1];p=root/'work/native_sb_layer_capacity_scaling_20261015'
cache={}
def sha(f):
 f=Path(f).resolve()
 if str(f) not in cache:
  h=hashlib.sha256()
  with f.open('rb') as stream:
   for b in iter(lambda:stream.read(1048576),b''):h.update(b)
  cache[str(f)]=h.hexdigest()
 return cache[str(f)]
class HashReader:
 def __init__(self,path):self.stream=path.open('rb');self.h=hashlib.sha256()
 def read(self,size=-1):
  b=self.stream.read(size);self.h.update(b);return b
 def close(self):self.stream.close()

def main():
 state=json.loads((p/'manifest.json').read_text());assert state['status']=='six_native_baselines_routed_and_true_layers_verified'
 protocol=json.loads((p/'protocol.json').read_text());binding=json.loads((p/'runtime_binding.json').read_text())
 for x in [protocol,binding]:
  for f,h in x['inputs'].items():assert sha(f)==h,f
 assert {(x['layers'],x['width']) for x in protocol['commands']}=={(l,w) for l in [2,3,4] for w in [80,96]}
 rows=[];sources={};kind_ids={k:i for i,k in enumerate(['SOURCE','SINK','IPIN','OPIN','CHANX','CHANY'])}
 for recipe in protocol['commands']:
  d=p/recipe['label'];record=json.loads((d/'run.json').read_text());assert record['status']=='passed' and record['returncode']==0
  text=(d/'vpr.log').read_text();assert 'VPR succeeded' in text and 'RouterOpts.check_route: FULL' in text
  assert f"Circuit successfully routed with a channel width factor of {recipe['width']}." in text
  wl=int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]);assert wl>0 and math.isfinite(cpd) and cpd>0
  layers=array('B');kinds=array('B');out=array('I');fanin=array('I');none=array('B');cross=Counter();grid=Counter();widths=[];edge_count=0
  graph=d/'rr_graph.xml';reader=HashReader(graph)
  try:
   for _,e in ET.iterparse(reader,events=['end']):
    if e.tag=='node':
     assert int(e.attrib['id'])==len(layers);assert e.attrib['type'] in kind_ids
     loc=e.find('loc');assert loc is not None and 'layer' in loc.attrib
     layers.append(int(loc.attrib['layer']));kinds.append(kind_ids[e.attrib['type']]);out.append(0);fanin.append(0);none.append(e.attrib['type'] in ['CHANX','CHANY'] and e.attrib.get('direction')=='NONE');e.clear()
    elif e.tag=='edge':
     u,v=(int(e.attrib[k]) for k in ['src_node','sink_node']);assert max(u,v)<len(layers)
     out[u]+=1;fanin[v]+=1;edge_count+=1
     if layers[u]!=layers[v]:cross[(layers[u],layers[v])]+=1
     e.clear()
    elif e.tag=='grid_loc':grid[(int(e.attrib['layer']),int(e.attrib['x']),int(e.attrib['y']))]+=1;e.clear()
    elif e.tag=='channel' and 'chan_width_max' in e.attrib:widths.append(int(e.attrib['chan_width_max']))
  finally:reader.close()
  cache[str(graph.resolve())]=reader.h.hexdigest();assert sha(graph)==record['artifacts']['rr_graph.xml']['sha256']
  assert set(layers)==set(range(recipe['layers'])) and widths==[recipe['width']]
  assert len(grid)==13*10*recipe['layers'] and all(v==1 for v in grid.values()) and max(x[1] for x in grid)==12 and max(x[2] for x in grid)==9
  assert set(cross)=={(i,i+1) for i in range(recipe['layers']-1)}|{(i+1,i) for i in range(recipe['layers']-1)}
  producer=json.loads((d/'layer_capacity_audit.json').read_text());assert producer['rr_nodes']==len(layers) and producer['cross_layer_directed_edges']=={str(k):v for k,v in cross.items()}
  for name,meta in record['artifacts'].items():assert sha(d/name)==meta['sha256'],name
  isolated=sum(a==b==0 for a,b in zip(out,fanin))
  row=dict(label=recipe['label'],layers=recipe['layers'],channel_width=recipe['width'],native_wirelength=wl,native_cpd_ns=cpd,rr_nodes=len(layers),rr_edges=edge_count,isolated_nodes=isolated,nonisolated_nodes=len(layers)-isolated,direction_none_channel_nodes=sum(none),cross_layer_directed_edges=sum(cross.values()),cross_layer_pairs={str(k):v for k,v in cross.items()},rr_check_missing_fanin_messages=len(re.findall(r'in check_rr_graph:.*has no fanin',text)),graph_sha256=sha(graph))
  rows.append(row)
  for f in [d/'run.json',d/'vpr.log',d/'architecture.xml',graph,d/'layer_capacity_audit.json']:sources[str(f)]=sha(f)
 # The three-layer feasibility probe is reproduced without changing its architecture or seed.
 reference=root/'work/native_sb_three_layer_feasibility_20261015/layers3_cw80';actual=p/'layers3_cw80';checks=[]
 for name in ['circuit.net','circuit.net.post_routing','circuit.place','circuit.route','rr_graph.xml']:
  assert sha(reference/name)==sha(actual/name),name;checks.append(name)
  sources[str(reference/name)]=sha(reference/name)
 for f in [p/'manifest.json',p/'protocol.json',p/'runtime_binding.json',Path(__file__).resolve()]:sources[str(f)]=sha(f)
 report=dict(status='six_native_switchblock_layer_capacity_baselines_independently_audited',baselines=rows,three_layer_probe_exact_artifacts=checks,source_sha256=sources,scope='One auditedVPRbinary,ex5pdevelopment,seed1,fixed13x10perlayer,totalareagrowswithlayers. Full native circuit route checks,actualRR metadata,all producer-artifacthashes andgraphdegreecounts verified. Isolated/exportedvirtualrecords are not usable-wire or physical-area counts. Missing-fanin diagnostics preserved,so this doesnot certifyeveryarchitecturepin orheterogeneousworkload. Freshplacementpercell;noDieRouteQoR/scaling,oldbaseline replacement,heldoutorboardclaim.',board_result=False,research_complete=False)
 with (p/'independent_audit.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(json.dumps(dict(status=report['status'],baselines=rows)))

if __name__=='__main__':main()
