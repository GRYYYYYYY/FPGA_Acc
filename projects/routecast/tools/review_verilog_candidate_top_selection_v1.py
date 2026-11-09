"""Conservative local instantiation clues; no full Verilog elaboration certificate."""
import json,re,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
ip=R/'experiments/verilog_candidate_origin_inventory_v1_2026-10-10/inventory.json';inv=json.loads(ip.read_text());pp=R/'experiments/verilog_frontend_cohort_v3_2026-10-10/protocol.json';p=json.loads(pp.read_text());assert all(sha(k)==h for k,h in p['bindings'].items());bindings={str(ip):sha(ip),str(pp):sha(pp),str(Path(__file__)):sha(Path(__file__))};rows=[]
for source,plan in zip(inv['rows'],p['plans']):
 assert Path(source['path']).stem==plan['name'];path=Path(source['path']);assert sha(path)==source['sha256'];bindings[str(path)]=sha(path);text=path.read_text();masked=re.sub(r'/\*.*?\*/|//[^\n]*',lambda m:' '*len(m[0]),text,flags=re.S);starts=list(re.finditer(r'\bmodule\s+(?:automatic\s+)?(\w+)',masked));ends=list(re.finditer(r'\bendmodule\b',masked));assert len(starts)==len(ends);modules={a[1]:masked[a.end():b.start()] for a,b in zip(starts,ends)};parents=defaultdict(list)
 for owner,body in modules.items():
  for module in modules:
   if re.search(r'\b'+re.escape(module)+r'\s*(?:#\s*\(.*?\)\s*)?[A-Za-z_][\w$]*\s*\(',body,re.S):parents[module].append(owner)
 roots=sorted(n for n in modules if not parents[n]);rows.append(dict(name=plan['name'],screened_top=plan['top'],possible_instantiation_parents=parents[plan['top']],unreferenced_module_candidates=roots,selected_top_has_parent_evidence=bool(parents[plan['top']])))
assert all(sha(k)==h for k,h in bindings.items());D=R/'experiments/verilog_top_selection_review_v1_2026-10-10';D.mkdir();(D/'review.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Comment-masked lexical module references using conservative instantiation-pattern matching, parameter/macros/generate/string/binding cases not fully parsed. Parent evidence flags possible helper-top choice, roots are candidates only. Does not prove intended design top/full logical hierarchy or certify no missing dependency. Existing screens remain scoped to selected tops; no native admission.'),indent=2)+'\n');print('TOP_SELECTION_FLAGS',[(r['name'],r['screened_top'],r['possible_instantiation_parents'],r['unreferenced_module_candidates']) for r in rows if r['selected_top_has_parent_evidence']])
