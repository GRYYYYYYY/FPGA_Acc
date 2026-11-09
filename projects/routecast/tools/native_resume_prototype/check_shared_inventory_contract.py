import json,sys
from pathlib import Path
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from shared_rr_inventory import SharedRRInventory
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_shared_inventory_contract_2026-10-07';out.mkdir(exist_ok=False);graph=out/'graph.xml';text='<rr_graph><rr_nodes><node id="0" type="SOURCE" capacity="1"><loc xlow="0" xhigh="0" ylow="0" yhigh="0" ptc="0"/></node><node id="1" type="SINK" capacity="1"><loc xlow="1" xhigh="1" ylow="0" yhigh="0" ptc="0"/></node></rr_nodes><switches><switch id="0"/></switches><rr_edges><edge src_node="0" sink_node="1" switch_id="0"/></rr_edges></rr_graph>';graph.write_text(text);fields=dict(capacities=[1,1],row_offsets=[0,1,1],edge_ids=[0],dest_ranks=[1],switch_ids=[0]);ctx=SimpleNamespace(graph=graph,digest=sha(graph),n=2,fields=fields);inv=SharedRRInventory(ctx);assert inv.edges==((0,1,0),);rows=[]
def reject(name,call):
 try:call()
 except ValueError as e:rows.append(dict(case=name,rejected=str(e)));return
 raise AssertionError(name)
graph.write_text(text+'\n');reject('changed_graph_after_inventory',lambda:inv.validate(graph,ctx.digest));ctx.digest=sha(graph);ctx.fields={**fields,'capacities':[2,1]};reject('capacity_context_mismatch',lambda:SharedRRInventory(ctx));ctx.fields={**fields,'edge_ids':[1]};reject('invalid_edge_identity',lambda:SharedRRInventory(ctx));(out/'receipt.json').write_text(json.dumps(rows,indent=2)+'\n');print(rows)
