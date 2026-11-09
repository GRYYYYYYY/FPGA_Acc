"""Frozen larger-design transfer: normalized blend then one own-excluded pass."""
import json,time,shutil,os
from pathlib import Path
from collections import defaultdict
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from normalized_rc_base import NormalizedRCBaseSketch
from slim_fast_normalized_rc_net_pressure import SlimFastNormalizedRCNetPressure
from rr_occupancy import Occupancy
from connection_golden import Result
from physical_prediction_audit import audit
out=Path('experiments/clma_normalized_transfer_2026-10-04')
if out.exists():raise ValueError('fresh output required')
ep=Path('experiments/clma_constant_policy_2026-10-04/endpoints.json');e=json.loads(ep.read_text());capture=Path('experiments/clma_base_echo_2026-10-04/protocol.json');cp=json.loads(capture.read_text());table=Path('experiments/clma_base_echo_2026-10-04/rr_indexed_data.echo')
inputs={'endpoints':{'path':str(ep.resolve()),'sha256':sha(ep)},'graph':cp['inputs']['graph'],'cost_table':{'path':str(table.resolve()),'sha256':sha(table)},'capture_protocol':{'path':str(capture.resolve()),'sha256':sha(capture)}}
assert e['graph_sha256']==inputs['graph']['sha256']
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'inputs':inputs,'scope':'clma larger already-developed design, same architecture; not unseen-family validation. No native route/timing labels in predictors','stages':['half normalized RC+base full cohort','one frozen channel factor1 own-net union excluded pressure pass using first stage background'],'scale':10**6,'weights':'RC=1/2 base=1/2, same prior controls, no tuning','pressure_factor':1,'clock_and_constant_policy':'original endpoint identities preserved, global proven constants/root clocks excluded','budget':'all nodes','recovery':'no automatic restart or duplicate worker','supervision':'main session, no supported luna delegation tool available','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
def status(stage,**fields):
 record={'pid':os.getpid(),'stage':stage,**fields};(out/'status.json').write_text(json.dumps(record,indent=2)+'\n')
 with (out/'progress.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 print(json.dumps(record),flush=True)
status('load_graph');start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);graph_s=time.monotonic()-start;groups=defaultdict(list)
for row in e['connections']:groups[(row['net_id'],row['source'])].append(row)
receipts={};background=None
for stage in ('blend','own_excluded_pressure'):
 status(stage+'_prepare',connections=len(e['connections']),groups=len(groups));start=time.monotonic()
 if stage=='blend':engine=NormalizedRCBaseSketch(g,table.read_text(),g.sha256)
 else:engine=SlimFastNormalizedRCNetPressure(g,table.read_text(),g.sha256,background)
 prepare_s=time.monotonic()-start;ledger=Occupancy(g);rows=[];visits=0;settled=0;start=time.monotonic()
 for i,((net,source),cohort) in enumerate(sorted(groups.items()),1):
  targets={r['sink'] for r in cohort}
  result=engine.search(source,targets) if stage=='blend' else engine.query(net,source,targets,True)[0]
  visits+=result.edge_visits;settled+=result.settled_nodes
  for row in cohort:
   path=result.paths.get(row['sink']);assert path is not None
   assert ledger.update(row['connection_id'],1,net,source,row['sink'],path)==Result.COMMITTED
   rows.append({**row,'physical_edge_ids':path,'method':stage})
  if i%100==0:status(stage+'_search',completed_groups=i,total_groups=len(groups),completed_connections=len(rows),elapsed_s=time.monotonic()-start)
 query_s=time.monotonic()-start;pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(e['connections']),'completed':len(rows),'methods':{stage:len(rows)}}
 status(stage+'_audit');audit_start=time.monotonic();checked=audit(g,e,pred);audit_s=time.monotonic()-audit_start
 artifact=out/f'{stage}_prediction.json';artifact.write_text(json.dumps(pred)+'\n');receipts[stage]={'preparation_s':prepare_s,'query_ledger_s':query_s,'audit_s':audit_s,'edge_visits':visits,'settled_nodes':settled,'prediction_sha256':sha(artifact),'audit':checked}
 (out/f'{stage}_receipt.json').write_text(json.dumps(receipts[stage],indent=2)+'\n');status(stage+'_complete',receipt_sha256=sha(out/f'{stage}_receipt.json'))
 background=pred;del engine,ledger
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'graph_load_s':graph_s,'stages':receipts,'inputs_unchanged':True},indent=2)+'\n');status('complete',receipt_sha256=sha(out/'receipt.json'))
