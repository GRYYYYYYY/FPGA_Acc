"""Capacity contradiction within the certified integer delay model only."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_forbidden_resource_v2_2026-10-06';r=json.loads((out/'receipt.json').read_text());v=json.loads((out/'verification.json').read_text());assert v['receipt_sha256']==sha(out/'receipt.json');rows=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':continue
 file=out/f"w{row['width']}_m{row['index']}.json";d=json.loads(file.read_text());ep=json.loads(Path(d['target']).read_text());graph=ep['inputs']['graph']['path'];assert sha(graph)==d['graph_sha256'];node=next(n for _,n in ET.iterparse(graph,events=('end',)) if n.tag=='node' and n.get('id')==str(d['physical_node_id']));capacity=int(node.get('capacity'));mandatory=sorted({a['query']['net_id'] for a in d['answers'] if not a['within_budget']});rows.append(dict(width=row['width'],index=row['index'],node=d['physical_node_id'],capacity=capacity,mandatory_NETs=mandatory,integer_model_capacity_contradiction=len(mandatory)>capacity))
(out/'necessity_summary.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verification_sha256=sha(out/'verification.json'),source_sha256=sha(Path(__file__)),rows=rows,scope='If forbidding a node raises the certified relaxed integer shortest delay above a connection budget, every budget-feasible model path uses that node. Distinct NET demand greater than XML node capacity contradicts this fixed budget vector. Not global placement unrouteability, native STA proof, or independently rederived Fraction RC model.'),indent=2)+'\n');print(rows)
