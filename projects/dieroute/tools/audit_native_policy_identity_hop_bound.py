"""Bind full original inputs to policy-identity reverse adjacency verification."""
from pathlib import Path
import hashlib,json,struct
R=Path(__file__).resolve().parents[1];P=R/'work/native_policy_identity_hop_bound_20261015'
def sha(f):
 h=hashlib.sha256()
 with Path(f).open('rb') as v:
  for b in iter(lambda:v.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=json.loads((P/'protocol.json').read_text());m=json.loads((P/'manifest.json').read_text());assert m['status']=='full_identity_reverse_and_consistency_complete_requires_review' and len(m['steps'])==2
 for obj in [p,json.loads((P/'launch_protocol.json').read_text())]:
  for field in ['source_sha256','input_source_sha256']:
   for f,h in obj.get(field,{}).items():assert sha(f)==h,f
 for expected,actual in zip(p['steps'],m['steps']):assert actual['returncode']==0 and actual['status']=='passed' and actual['command']==expected['command']
 v=json.loads((P/'verify.stdout').read_text());a=json.loads((P/'identity_quotient/audit.json').read_text());assert v['status']=='passed' and v['nodes']==a['nodes']==91975782 and a['original_arcs']==253648514
 assert v['eligible_edges_bijectively_verified']==v['consistent_edges']==a['eligible_arcs']==p['expected_eligible_edges']==212892069
 assert v['source_potential']==42 and v['sink_potential']==0 and a['net_id']==p['net_id']==287909
 assert a['group_semantics']=='native_node_identity' and 'not_tile_intent' in a['descriptor_encoding'] and a['parallel_arcs_retained']
 widths={'node_groups.bin':(91975782,4),'groups.bin':(91975782,8),'reverse_offsets.bin':(91975783,8),'reverse_sources.bin':(212892069,4)}
 total=0;artifacts={}
 for name,(count,width) in widths.items():
  f=P/'identity_quotient'/name
  with f.open('rb') as s:h=s.read(64)
  assert h[:8]==b'FPGAACCP' and struct.unpack_from('<Q',h,16)[0]==count and struct.unpack_from('<Q',h,24)[0]==count*width and f.stat().st_size==64+count*width
  total+=f.stat().st_size;artifacts[str(f)]=sha(f)
 files=[P/'protocol.json',P/'launch_protocol.json',P/'manifest.json',P/'fixture_audit.json',P/'build.stdout',P/'build.stderr',P/'verify.stdout',P/'verify.stderr',P/'identity_quotient/audit.json',Path(__file__).resolve()]
 report=dict(status='full_policy_identity_reverse_graph_and_hop_consistency_verified',nodes=v['nodes'],original_arcs=a['original_arcs'],eligible_edges=v['consistent_edges'],source_potential=42,sink_potential=0,preparation_BFS_expanded=v['BFS_expanded'],preparation_BFS_edges=v['BFS_edges'],serialized_bytes=total,group_semantics=a['group_semantics'],artifacts=artifacts,source_sha256={str(f):sha(f) for f in files},scope='Every eligible original CSR edge including parallel multiplicity checked against serialized identity reverse graph, identities checked for every original node, clamped hop inequality checked globally. Dynamic resource costs not used in preprocessing; original route graph unchanged. Large CPU preprocessing/storage/BFS burden must be counted. No search, commit, XRT, end-to-end speed or adoption claim.',adopted=False,board_result=False,research_complete=False)
 with (P/'independent_audit.json').open('x') as f:json.dump(report,f,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in report.items() if k not in ['source_sha256','artifacts']}))
if __name__=='__main__':main()
