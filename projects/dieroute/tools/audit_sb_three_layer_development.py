"""Review the two declared development native baselines on the exact three-layer graph."""
import collections,hashlib,json,re,xml.etree.ElementTree as ET
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];P=ROOT/'work/native_sb_three_layer_development_20261015';cache={}
def sha(q):
 q=str(Path(q).resolve())
 if q not in cache:
  h=hashlib.sha256()
  with Path(q).open('rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  cache[q]=h.hexdigest()
 return cache[q]
def main():
 protocol=json.loads((P/'protocol.json').read_text());launch=json.loads((P/'launch_protocol.json').read_text())
 for x in [protocol,launch]:
  for q,h in x['inputs'].items():assert sha(q)==h,q
 result=json.loads((P/'result.json').read_text());assert result['status']=='two_native_development_attempts_terminal'
 assert [x['case'] for x in result['cases']]==['diffeq','alu4']
 original=ROOT/'work/native_sb_layer_capacity_scaling_20261015/layers3_cw80';graph_sha=sha(original/'rr_graph.xml')
 audit_path=ROOT/'work/native_sb_layer_capacity_scaling_20261015/independent_audit.json';audit=json.loads(audit_path.read_text());reference=next(r for r in audit['baselines'] if r['label']=='layers3_cw80');assert graph_sha==reference['graph_sha256']
 rows=[]
 for entry in result['cases']:
  d=P/entry['case'];run=json.loads((d/'run.json').read_text());assert entry['returncode']==run['returncode']==0 and run['status']=='passed' and run==entry['run']
  for key,obj in run['sources'].items():assert sha(obj['path'])==obj['sha256']
  for name,obj in run['artifacts'].items():assert (d/name).stat().st_size==obj['bytes'] and sha(d/name)==obj['sha256'],name
  text=(d/'vpr_stdout.log').read_text()
  for marker in ['Completed routing consistency check successfully.','Circuit successfully routed with a channel width factor of 80.','VPR succeeded']:assert marker in text
  for flag,value in [('--device','DieRouteSBScale3'),('--route_chan_width','80'),('--seed','1'),('--num_workers','1')]:assert run['command'][run['command'].index(flag)+1]==value
  assert sha(d/'rr_graph.xml')==graph_sha and sha(d/'architecture.xml')==sha(original/'architecture.xml')
  wl=int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1])
  blocks=collections.Counter(b.attrib['instance'].split('[')[0] for b in ET.parse(d/'circuit.net').getroot().findall('block'))
  rows.append(dict(case=entry['case'],wirelength=wl,cpd_ns=cpd,cluster_type_counts=dict(blocks),rr_nodes=reference['rr_nodes'],rr_edges=reference['rr_edges'],isolated_nodes=reference['isolated_nodes'],rr_missing_fanin_messages=len(re.findall(r'in check_rr_graph:.*has no fanin',text)),graph_sha256=graph_sha,native_legal=True))
 for q in [P/'result.json',P/'manifest.json',P/'protocol.json',P/'launch_protocol.json',audit_path,Path(__file__).resolve()]:sha(q)
 report=dict(status='two_remaining_declared_development_baselines_native_legal_exact_same_three_layer_RR_verified',cases=rows,ex5p_reference=dict(wirelength=reference['native_wirelength'],cpd_ns=reference['native_cpd_ns'],graph_sha256=graph_sha),source_sha256=cache,scope='Freshpack/place/routeforpredeclareddevelopmentcasesatfixedSB3layer13x10/cw80/seed1;currentinput/source/artifacthashesandactualnativeconsistency/metricsverified. RRgraphbyteidenticaltoindependentlyprofiledex5pgraphincludingisolatedrecords;notallarchitecturepinscertified. NotDieRouteQoR,representativeheterogeneouscohort,heldout,repeatorboardproof.',board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps(dict(status=report['status'],cases=rows)))
if __name__=='__main__':main()
