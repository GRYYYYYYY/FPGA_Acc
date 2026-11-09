"""Joint ledger/pressure staging over all six real multiplier moves."""
import argparse,json,shutil,time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from pre_route_endpoints import sha
from prepared_csr import read
from streaming_prediction_audit import Nodes,Edges
from ledger_pressure_transaction import LedgerPressureTransaction
from incremental_channel_pressure import ChannelPressure
from connection_golden import Result


def main():
 parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();d=args.design;base=Path('experiments');oldroot=base/'multiplier_family_predictions_2026-10-06'/d/'sparse_reset';newroot=base/'multiplier_moved_incremental_search_2026-10-06'/d;prior=base/'multiplier_moved_incremental_pressure_2026-10-06'/d;prepared=base/'multiplier_family_length_switch_csr_2026-10-06'/d;out=base/'multiplier_joint_pressure_publication_2026-10-06'/d;out.mkdir(parents=True);(out/'source').mkdir();bindings={}
 def load(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
 old=load(oldroot/'prediction.json');br=load(oldroot/'receipt.json');bp=load(oldroot/'protocol.json');new=load(newroot/'prediction.json');nr=load(newroot/'receipt.json');pr=load(prior/'receipt.json')
 assert br['prediction_sha256']==sha(oldroot/'prediction.json') and nr['prediction_sha256']==sha(newroot/'prediction.json') and nr['paths_equal_full_moved_search'];assert all(sha(p)==h for p,h in nr['inputs_sha256'].items())
 closure=nr['closure'];selected=set(closure['recompute_connection_ids']);m,f=read(prepared/'csr',old['physical_graph_sha256']);assert sha(prepared/'csr/manifest.json')==bp['csr_manifest_sha256'];edges={}
 for node in range(m['nodes']):
  for slot in range(f['row_offsets'][node],f['row_offsets'][node+1]):edges[f['edge_ids'][slot]]=SimpleNamespace(source=node,sink=f['dest_ranks'][slot],switch_id=f['switch_ids'][slot])
 graph=SimpleNamespace(nodes=Nodes(f['types'],f['capacities']),edges=Edges(edges,m['edges']));joint=LedgerPressureTransaction(graph,f['types'],f['capacities'],old['physical_graph_sha256'])
 def req(row,epoch):return {k:row[k] for k in ('connection_id','net_id','source','sink')}|{'epoch':epoch,'edge_ids':row['physical_edge_ids']}
 assert joint.update_batch([req(r,1) for r in old['connections']])==Result.COMMITTED;before=joint.snapshot();updates=[req(r,2) for r in new['connections'] if r['connection_id'] in selected]
 with patch.object(ChannelPressure,'refresh',side_effect=ValueError('injected publication failure')):
  try:joint.update_batch(updates)
  except ValueError:pass
  else:raise AssertionError('injection did not reject')
 assert joint.snapshot()==before
 start=time.monotonic();assert joint.update_batch(updates)==Result.COMMITTED;commit_s=time.monotonic()-start;after=joint.snapshot();assert after['occupancy']=={int(n):v for n,v in new['node_occupancy'].items()}
 for name,expected in [('candidate.pressure',after['payload']),('original.pressure',before['payload'])]:
  assert sha(prior/name)==pr['pressure_sha256'][name] and (prior/name).read_text()==expected;bindings[str(prior/name)]=sha(prior/name)
 assert joint.update_batch(updates)==Result.STALE and joint.snapshot()==after
 assert joint.update_batch([req(r,3) for r in old['connections'] if r['connection_id'] in selected])==Result.COMMITTED;assert joint.snapshot()['payload']==before['payload'] and joint.snapshot()['occupancy']==before['occupancy']
 for name in ('audit_joint_pressure_publication.py','ledger_pressure_transaction.py','rr_local_batch_occupancy.py','rr_occupancy.py','incremental_channel_pressure.py','connection_golden.py','prepared_csr.py','streaming_prediction_audit.py','pre_route_endpoints.py'):
  shutil.copyfile(Path('tools')/name,out/'source'/name);bindings[str(Path('tools')/name)]=sha(Path('tools')/name)
 assert all(sha(path)==digest for path,digest in bindings.items());report={'inputs_sha256':bindings,'connections':len(old['connections']),'updated':len(updates),'staged_commit_s':commit_s,'pressure_failure_preserves_entire_state':True,'full_occupancy_and_payload_exact':True,'stale_preserves_pair':True,'rollback_restores_pair':True,'scope':'joint publication correctness with full-state fork/copy and serialized readers/writer; commit time excludes search/projection/index/native, not a local-cost or end-to-end optimization'}
 (out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='inputs_sha256'}),flush=True)

if __name__=='__main__':main()
