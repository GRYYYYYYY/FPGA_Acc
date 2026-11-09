"""Freeze top3 external RR feedback cohort, retaining all logical arc contributors."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/ex5p_top3_cohort_2026-10-06';out.mkdir();source=root/'experiments/ex5p_top3_rr_bindings_2026-10-06/receipt.json';r=json.loads(source.read_text());groups={}
for row in r['bindings']:
 cid=row['connection_id']
 if cid not in groups:groups[cid]={**row,'logical_contributors':[]}
 group=groups[cid];assert all(group[k]==row[k] for k in ('net_id','net_name','source','sink','physical_edge_ids','delay_integer'));group['logical_contributors'].append({'atom':row['atom'],'logical_bit':row['logical_bit'],'reported_arc_ns':row['reported_arc_ns']})
p={'source_sha256':sha(source),'top_k':3,'policy':'All external connections on frozen first3 native worstpaths, stable encounter-order connectionIDdedup. Preserve logicalcontributors/sharedfanout; internalpackedarc excluded rather than assignedRR.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');result={'bindings':list(groups.values()),'internal_or_unresolved':r['unresolved'],'source_receipt_sha256':sha(source),'protocol_sha256':sha(out/'protocol.json'),'source_sha256':sha(Path(__file__))};(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print('uniqueconnections',len(groups),'logicalarcs',len(r['bindings']),'internal/unresolved',len(r['unresolved']))
