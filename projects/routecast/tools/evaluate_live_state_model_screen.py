"""Retrospective allcase live-state rule, decide before opening target labels."""
import json,time
from pathlib import Path
from collections import defaultdict
from fractions import Fraction as F
from pre_route_endpoints import sha
from freeze_priority_family import closure
from native_route_ledger_import_compact import physical_paths
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
from live_state_model_screen import screen
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/bitonic_workflow_auditcache2_resident_live_staging_2026-10-07';out=ROOT/'experiments/live_state_model_screen_2026-10-07';out.mkdir();parent=json.loads((base/'protocol.json').read_text());sources=closure([Path(__file__)]);p=dict(sources=sources,parent_protocol_sha256=sha(base/'protocol.json'),rule='Accept complete model iff uniqueNET channel-span sum and maximum connection expansion RC both <= published live state; ties accepted; no proposed-target native labels consumed until decisions written.',scope='Retrospective NEW development heuristic on existing3 swaps, fixed acrosscohort; not sourcecomplete heldout or exact STA bound. Live seed route allowed as current published state, proposed cold/native candidate QoR evaluator-only. All rejections/failures preserved, no timer stitching/netgain.');(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');decisions=[]
for case in parent['cases']:
 n=case['count'];file=base/f'n{n}/run0_resident.json';update=json.loads(file.read_text());c=update['repair'] or update['incremental'];old=json.loads(Path(case['old']).read_text());ep=json.loads(Path(case['target']).read_text());graph=Path(ep['inputs']['graph']['path']);route=Path(case['source'])/'design.route';tick=time.perf_counter();a=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph);paths=physical_paths(route);needed={(path[k-1][0],path[k][0],path[k][1]) for rows in paths.values() for path in rows for k in range(1,len(path))};edge_ids={}
 edges=a.graph.edges
 for eid,key in enumerate(zip(edges.source,edges.destination,edges.switch)):
  if key in needed:
   if key in edge_ids:raise ValueError('ambiguous native physical arc')
   edge_ids[key]=eid
 assert set(edge_ids)==needed
 def metrics(rows):
  unions=defaultdict(set);delays=[];count=0
  for net,source,sink,physical in rows:
   node=source;used={source};res,cap=classes[ids[source]];delay=res*cap/2
   for eid in physical:
    e=a.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id)
   assert node==sink;unions[net].update(used);delays.append(delay);count+=1
  return dict(connections=count,max_connection_rc_seconds=str(max(delays)),sum_connection_rc_seconds=str(sum(delays)),channel_union_wirelength=sum(a.spans[node] for used in unions.values() for node in used if a.types[node] in (4,5)))
 names={name:int(net) for net,name in old['net_names'].items()};oldrows=[]
 for name,rows in paths.items():
  for path in rows:oldrows.append((names[name],path[0][0],path[-1][0],[edge_ids[(path[k-1][0],path[k][0],path[k][1])] for k in range(1,len(path))]))
 oldmetrics=metrics(oldrows);newmetrics=metrics((r['net_id'],r['source'],r['sink'],r['answer']['physical_edge_ids']) for r in c['records']);complete=c['completed_connections']==c['required_connections'];decision=screen(oldmetrics,newmetrics) if complete else dict(model_admitted=False,reasons=['INCOMPLETE_MODEL']);row=dict(count=n,old=oldmetrics,new=newmetrics,**decision,inputs={str(f):sha(f) for f in [file,Path(case['old']),Path(case['target']),graph,route]},diagnostic_seconds=time.perf_counter()-tick);decisions.append(row);print(n,decision,oldmetrics,newmetrics,flush=True)
(out/'decisions.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=decisions),indent=2)+'\n')
# Proposed-target native outcomes opened ONLY after all model decisions are sealed.
label=ROOT/'experiments/bitonic_workflow_auditcache2_swapped_cold_2026-10-07/verification.json';labels=json.loads(label.read_text());rows=[]
for d,q in zip(decisions,labels['rows']):
 assert d['count']==q['count'];good=q['joint_nonregression'];rows.append(dict(count=d['count'],model_admitted=d['model_admitted'],native_joint_nonregression=good,false_admission=d['model_admitted'] and not good,missed_improvement=not d['model_admitted'] and good,target_quality=q))
assert all(sha(f)==v for f,v in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),decisions_sha256=sha(out/'decisions.json'),target_labels_sha256=sha(label),rows=rows,scope=p['scope']),indent=2)+'\n');print(rows)
