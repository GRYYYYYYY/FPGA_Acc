"""Review full-graph packing and unchanged-route validation for all twelve posterior width cases."""
import hashlib,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];p=root/'work/width_coverage_roundtrip_20261017';cache={}
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
 r=json.loads((p/'result.json').read_text());assert r['status']=='twelve_width_coverage_full_graph_and_exact_native_tree_roundtrips_complete';refs(r)
 protocol=json.loads((p/'protocol.json').read_text());launch=json.loads((p/'launch_protocol.json').read_text())
 for x in [protocol,launch]:
  for f,h in x['inputs'].items():assert sha(f)==h,f
 expected={v['label']:v for v in protocol['cases']};assert len(r['cases'])==len(expected)==12
 width_audit=json.loads((root/'work/native_fixed_placement_width_coverage_20261017/independent_audit.json').read_text())
 declared_labels=[f"{v['case']}_{v['width']}x{v['height']}_cw{v['channel_width']}_seed{v['seed']}" for v in width_audit['outcomes']]
 assert list(expected)==declared_labels==[v['label'] for v in r['cases']]
 sys.path.insert(0,str(p/'tools'))
 from export_native_vpr_tree import extract
 rows=[]
 for result in r['cases']:
  refs(result);label=result['label'];original=expected[label];case=Path(original['case']);out=p/label
  packed=json.loads((out/'packed_graph_audit.json').read_text());refs(packed)
  assert packed['status']=='all_native_rr_nodes_edges_layers_capacities_and_local_delay_fields_match_packed_graph'
  assert packed['nodes'] > 0 and packed['edges'] > 0
  q=json.loads((out/'native_validation/validation.json').read_text());assert q['legal'] and q['vpr_exit_status']==0
  stdout=(out/'native_validation/vpr_analysis.stdout').read_text();stderr=out/'native_validation/vpr_analysis.stderr'
  assert sha(out/'native_validation/vpr_analysis.stdout')==q['stdout_sha256'] and sha(stderr)==q['stderr_sha256']
  for text in ['Finished loading route file','Completed routing consistency check successfully.','Circuit successfully routed','VPR succeeded']:assert text in stdout
  assert int(re.findall(r'Total wirelength:\s+(\d+)',stdout)[-1])==q['total_wirelength']==original['wirelength']
  assert float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',stdout)[-1])==q['critical_path_delay_ns']==original['cpd_ns']
  native=json.loads((case/'run.json').read_text());device=native['command'][native['command'].index('--device')+1];assert q['command'][q['command'].index('--device')+1]==device
  mapping={'arch_sha256':case/'architecture.xml','circuit_sha256':case/'circuit.blif','net_sha256':case/'circuit.net','place_sha256':case/'circuit.place','route_sha256':out/'noop.route','rr_graph_sha256':case/'rr_graph.xml','vpr_sha256':Path(native['sources']['vpr']['path'])}
  for key,f in mapping.items():assert sha(f)==q['inputs'][key],key
  before,after=extract(case/'circuit.route'),extract(out/'noop.route')
  assert before.keys()==after.keys()
  for net,tree in before.items():
   other=after[net]
   assert tree['source']==other['source'] and tree['sinks']==other['sinks'] and sorted(tree['edges'])==sorted(other['edges']),(label,net)
  assert q['command'][q['command'].index('--route_chan_width')+1]==str(original['width'])
  assert result['exact_node_parent_child_switch_and_sink_pin_identity']
  rows.append(dict(label=label,layers=original['layers'],width=original['width'],nodes=packed['nodes'],edges=packed['edges'],nets=result['nets'],sinks=result['sinks'],tree_edges=result['tree_edges'],wirelength=q['total_wirelength'],cpd_ns=q['critical_path_delay_ns']))
 files=[p/'result.json',p/'protocol.json',p/'launch_protocol.json',root/'work/native_fixed_placement_width_coverage_20261017/independent_audit.json',Path(__file__).resolve()]
 report=dict(status='twelve_width_coverage_full_graph_and_native_noop_roundtrips_independently_reviewed',cases=rows,total_nodes=sum(r['nodes'] for r in rows),total_edges=sum(r['edges'] for r in rows),verified_current_unique_files=len(cache),source_sha256={str(f):sha(f) for f in files},scope='Current source/input/report integrity,all packed nodes/edges audited by frozen full-graph checker,and nativeVPR output/inputs/device/metrics rechecked. Exact tree/switch/pin identity independently re-extracted from original and generated routes; all12 labels checked against width audit. IncludesisolatedRRrecords;temporaryconstantbase64,notnativeindexedcosts. NoalgorithmQoRimprovement,physicalclaimorresearchcompletion.',board_result=False,research_complete=False)
 with (p/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],total_nodes=report['total_nodes'],total_edges=report['total_edges'],cases=len(rows))))
if __name__=='__main__':main()
