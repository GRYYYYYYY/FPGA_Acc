"""Whole-family fixed1ns structural budget feasibility, development diagnostic."""
import json,time
from pathlib import Path
from collections import defaultdict
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from pre_route_endpoints import sha
from freeze_priority_family import closure
from static_budget_native import StaticBudgetNative
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/priority_frozen_evaluation_2026-10-07';out=ROOT/'experiments/priority_static_cap_native_diagnosis_2026-10-07';out.mkdir();v=json.loads((parent/'verification.json').read_text());assert v['receipt_sha256']==sha(parent/'receipt.json');inputs={str(parent/'verification.json'):sha(parent/'verification.json')};sources=closure([Path(__file__)]);sources.update({str(p):sha(p) for p in [ROOT/'tools/static_budget_native.cpp',ROOT/'build/static_budget_native_2026-10-07/search.so']});protocol=dict(inputs=inputs,sources=sources,cohort=[32,64,128],budget_ns=1,scope='Retrospective all-endpoint development diagnosis; exact integer buffered RC only, positivecapacity, no otherNET demand/history/wirecost/native routes or label cap. SOURCE initial included. Unsettled target has no path <=fixed1ns, not globally unroutable. Source-group reuse counts preparation/search separately. Frozen family results untouched.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for n in protocol['cohort']:
 ep=parent/f'n{n}/endpoints.json';tick=time.perf_counter();ctx=OwnerUnionWireRCContext(ep);setup=time.perf_counter()-tick;rc=ctx.rc;f=rc.fields;groups=defaultdict(list)
 for q in ctx.context[5]:groups[q['source']].append(q)
 tick=time.perf_counter();native=StaticBudgetNative(f['row_offsets'],f['dest_ranks'],rc.increments,f['capacities']);graph_prepare=time.perf_counter()-tick;tick=time.perf_counter();results=[];stats=dict(settled_nodes=0,examined_edges=0);budget=rc.scale//10**9
 for source,queries in sorted(groups.items()):
  answer=native.query(source,rc.initial(source),budget,[q['sink'] for q in queries]);stats['settled_nodes']+=answer['settled_nodes'];stats['examined_edges']+=answer['examined_edges']
  for q in queries:results.append(dict(query=q,minimum_delay_scaled=answer['target_minima'][q['sink']],within_1ns=answer['target_minima'][q['sink']] is not None))
 native.close();file=out/f'n{n}.json';file.write_text(json.dumps(dict(endpoint_sha256=sha(ep),scale=rc.scale,budget=budget,connections=sorted(results,key=lambda x:x['query']['connection_id'])),indent=2)+'\n');row=dict(width=n,connections=len(results),sources=len(groups),within_1ns=sum(x['within_1ns'] for x in results),budget_infeasible=sum(not x['within_1ns'] for x in results),setup_seconds=setup,graph_prepare_seconds=graph_prepare,search_seconds=time.perf_counter()-tick,stats=stats,file_sha256=sha(file));rows.append(row);print(row,flush=True);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==3),indent=2)+'\n')
assert all(sha(p)==d for p,d in sources.items())
