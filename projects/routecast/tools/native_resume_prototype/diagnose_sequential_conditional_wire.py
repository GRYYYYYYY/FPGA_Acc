import sys,json,xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from native_route_ledger_import_compact import physical_paths
from pre_route_endpoints import sha
R=Path.cwd();o=R/'experiments/native_resume_sequential_adder_conditional_2026-10-07';p=json.loads((o/'protocol.json').read_text());r=json.loads((o/'receipt.json').read_text());ep=json.loads((R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json').read_text());graph=next(Path(f) for f in p['inputs'] if str(f).endswith('.xml'));spans={}
for _,e in ET.iterparse(graph,events=('end',)):
 if e.tag=='node':
  if e.attrib.get('type') in ('CHANX','CHANY'):
   l=e.find('loc').attrib;spans[int(e.attrib['id'])]=1+int(l['xhigh'])-int(l['xlow'])+int(l['yhigh'])-int(l['ylow'])
  e.clear()
paths=physical_paths(R/'experiments/native_resume_sequential_adder_step3_workflow_2026-10-07/exchange_canonical/design.route');rows=[]
for row in r['rows']:
 old={n for ps in paths[row['net']] for n,_ in ps};a=sum(spans.get(n,0) for n in old);b=sum(spans.get(n,0) for n in row['new_union']);rows.append(dict(net=row['net'],current_wire=a,conditional_tree_wire=b,wire_delta=b-a,positive_gap_connections=row['positive_current_gap_connections']))
x=dict(receipt_sha256=sha(o/'receipt.json'),script_sha256=sha(Path(__file__)),graph_sha256=sha(graph),rows=rows,scope='Whole-NET union CHAN spans; diagnostic only, no native timing acceptance. Independent NET replacements may conflict.')
(o/'wire_comparison.json').write_text(json.dumps(x,indent=2)+'\n');print(json.dumps(rows,indent=2))
