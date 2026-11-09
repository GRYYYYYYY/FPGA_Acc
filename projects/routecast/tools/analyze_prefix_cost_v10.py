"""Post-outcome decomposition; recorded costs and unique-net channel wire."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from native_route_ledger_import_compact import physical_paths
parent=R/'experiments/mcnc_pending_prefix_sequence_v10_2026-10-07';native=R/'experiments/mcnc_pending_prefix_native_validation_v10_2026-10-07';out=R/'experiments/prefix_cost_diagnostic_v1_2026-10-07';out.mkdir();files=[parent/'receipt.json',native/'receipt.json',native/'verification.json',native/'bigkey/candidate/output.route',native/'bigkey/cold/output.route'];ep=json.loads((R/'experiments/mcnc_prospective_v1_2026-10-07/bigkey/endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);files.append(graph);bindings={str(p):sha(p) for p in files};bindings.update(closure([Path(__file__)]));(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Post-outcome cost and wire attribution only; no producer modification, native labels never producer input. Recorded sequence includes cache and logging; component times overlap, not additive disjoint profile.'))+'\n');rows=[]
for row in json.loads((parent/'receipt.json').read_text())['rows']:
 cache=row['cache_summary'];rows.append({k:row[k] for k in ('name','total_seconds','construction_seconds','floor_seconds','sequence_seconds','completed','required','stop')}|dict(cache_build_archive_seconds=cache['build_and_archive_seconds'],cache_hits=cache['hits'],cache_misses=cache['misses'],cache_evictions=cache['evictions']))
spans={};stack=[]
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':stack.append(e);continue
 par=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and par=='rr_nodes' and e.get('type') in ('CHANX','CHANY'):
  l=e.find('loc');spans[int(e.get('id'))]=1+int(l.get('xhigh'))-int(l.get('xlow'))+int(l.get('yhigh'))-int(l.get('ylow'))
 if (e.tag,par) in {('node','rr_nodes'),('edge','rr_edges')}:stack[-2].remove(e);e.clear()
 stack.pop()
def wires(file):
 paths=physical_paths(file);return {net:sum(spans.get(n,0) for n in {n for p in ps for n,_ in p}) for net,ps in paths.items() if ps}
a=wires(native/'bigkey/candidate/output.route');b=wires(native/'bigkey/cold/output.route');assert set(a)==set(b);row=json.loads((native/'receipt.json').read_text())['rows'][0];assert sum(a.values())==row['candidate_wirelength'] and sum(b.values())==row['cold_wirelength'];d=sorted([dict(net=net,candidate=a[net],cold=b[net],delta=a[net]-b[net]) for net in a],key=lambda x:(-x['delta'],x['net']));assert sum(x['delta'] for x in d)==717
assert all(sha(k)==v for k,v in bindings.items());result=dict(bindings=bindings,cost_rows=rows,wire_by_net=d,total_wire_delta=717,positive_wire_delta=sum(max(0,x['delta']) for x in d),negative_wire_delta=sum(min(0,x['delta']) for x in d),scope='Native comparison attribution, not causal or heldout evidence; overlapping costs cannot be summed.');(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('cost',rows,flush=True);print('wire top',d[:10],flush=True)
