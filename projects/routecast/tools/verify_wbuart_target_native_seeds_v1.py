"""Independent subset selection, exact source blocks and branch endpoint verification."""
import json,re,hashlib,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';D=E/'wbuart_target_native_seeds_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def blocks(p):
 pieces=re.split(r'(?=^Net \d+ \()',Path(p).read_text(),flags=re.M);return pieces[0],{re.match(r'Net\s+\d+\s+\((.*?)\)',x)[1]:x for x in pieces[1:]}
def main():
 p=D/'verification.json';v=read(p);assert len(v['rows'])==9 and all(sha(n)==h for n,h in v['bindings'].items());workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');rows=[]
 for c in v['rows']:
  spec=read(next(x['specification'] for x in workflow['comparisons'] if x['case']==c['case']));ep=read(c['endpoint']);source=read(spec['source_frame']);old={q['connection_id']:q for q in source['records']};assert source['graph_sha256']==ep['graph_sha256']==sha(ep['inputs']['graph']['path']);dirty=set()
  for q in ep['connections']:
   a=old[q['connection_id']];assert a['net_id']==q['net_id'] and a['full_connection_id']==q['full_connection_id']
   if (a['source'],a['sink'])!=(q['source'],q['sink']):dirty.add(q['net_id'])
  assert sorted(dirty)==c['dirty_NETs'];header,src=blocks(c['source_route']);newheader,new=blocks(c['seed']);expected={ep['net_names'][str(q['net_id'])] for q in ep['connections'] if q['net_id'] not in dirty};assert set(new)==expected;assert all(new[n]==src[n] for n in expected);place=ep['inputs']['place'];assert sha(place['path'])==place['sha256']==c['target_placement_sha256'];assert newheader==re.sub(r'Placement_ID: SHA256:[0-9a-f]+','Placement_ID: SHA256:'+place['sha256'],header,count=1)
  paths=physical_paths(Path(c['seed']));observed=Counter((n,branch[0][0],branch[-1][0]) for n,branches in paths.items() for branch in branches);wanted=Counter((ep['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in ep['connections'] if q['net_id'] not in dirty);assert observed==wanted and len(new)==c['retained_NETs'] and sum(wanted.values())==c['retained_connections'];rows.append({'case':c['case'],'retained_NETs':len(new),'retained_connections':sum(wanted.values()),'source_blocks_byte_equal':True,'independent_branch_endpoint_multiset_exact':True})
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_TARGET_SEED_SELECTION_SOURCE_BLOCKS_PLACEMENT_GRAPH_AND_ENDPOINTS_VERIFIED','rows':rows,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Retained source blocks exact and source proof authenticates physical arcs; separate branch parser verifies current endpoint multiset. Native loading still pending.'},indent=2)+'\n');print('ALL9_TARGET_SEED_SELECTION_SOURCE_BLOCKS_PLACEMENT_GRAPH_AND_ENDPOINTS_VERIFIED')
if __name__=='__main__':main()
