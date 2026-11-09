"""Exact repeated preflight loop work from frozen source and actual journals."""
import json
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_query_validation_work_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_length_switch_prediction_v1_2026-10-09';r=json.loads((B/'receipt.json').read_text());assert r['status']=='COMPLETE_AUDITED_PREDICTION'
for p,h in {**r['bindings'],**r['files']}.items():assert sha(p)==h
manifest=json.loads((B/'csr/manifest.json').read_text());header=R/'include/direct_search.hpp';main=R/'tools/csr_consumer/direct_main.cpp'
source=header.read_text();assert 'for(uint64_t i=0;i<nodes;++i)if(rows[i]>rows[i+1])' in source
assert 'for(uint64_t i=0;i<edges;++i)if(destinations[i]>=nodes||edge_ids[i]>=edges)' in source
assert 'for(uint64_t i=0;i<nodes;++i){labels[i]=' in source
assert 'routecast::direct_search(' in main.read_text()
journal=[json.loads(line) for line in (B/'net_results.jsonl').read_text().splitlines()];assert len(journal)==5794
n,m=manifest['nodes'],manifest['edges'];q=len(journal);visits=sum(x['result']['edge_visits'] for x in journal)
out=dict(source_preflight_current_sha256=sha(header),queries=q,nodes=n,edges=m,repeated_row_validation_items=q*n,repeated_edge_validation_items=q*m,repeated_label_reset_items=q*n,actual_search_edge_visits=visits,preflight_edge_items_to_search_edge_visits=q*m/visits,bindings={str(p):sha(p) for p in [Path(__file__),header,main,B/'receipt.json',B/'csr/manifest.json',B/'net_results.jsonl']},scope='Exact syntactic loop counts for current source used by direct consumer. Current header identity alone does not prove historical binary build source provenance. Counts are not runtime attribution or measured speedup. Fresh immutable-context validated transport could move graph preflight once, but public untrusted kernel entry must retain validation.')
(D/'diagnosis.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
