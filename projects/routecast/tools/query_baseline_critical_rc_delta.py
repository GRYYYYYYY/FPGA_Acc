import json,time
from pathlib import Path
from collections import Counter
from fractions import Fraction
from pre_route_endpoints import sha
from prepared_csr import read
from csr_exact_buffered_rc import ExactBufferedRC
from buffered_rc_context import load as load_rc
from prepared_integer_rc_context import PreparedIntegerRC
from native_integer_rc_search import NativeIntegerRC
root=Path(__file__).resolve().parents[1];base=root/'experiments';query_path=base/'native_baseline_critical_rr_pin_2026-10-06/queries.json';q=json.loads(query_path.read_text());assert all(sha(p)==h for p,h in q['inputs_sha256'].items());assert not q['unknown'];graph=next(p for p in q['inputs_sha256'] if p.endswith('rr_graph.xml'));digest=sha(graph);out=base/'native_baseline_critical_rc_delta_2026-10-06';out.mkdir();start=time.perf_counter();m,f=read(base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr',digest);rc=PreparedIntegerRC(ExactBufferedRC(f,*load_rc(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits',digest)),base/'adder_tree_prepared_integer_rc_2026-10-06','7f8ce091f40c8f7f0f879a068293f20c76be9ebbbb3c0371462eca0f0724e617');native=NativeIntegerRC(rc);budget=(Fraction(1,10**9)*rc.scale).__floor__();protocol={'queries_sha256':sha(query_path),'graph_sha256':digest,'integer_receipt_sha256':sha(base/'adder_tree_prepared_integer_rc_2026-10-06/receipt.json'),'native_binary_sha256':sha(root/'build/rc_budget_native_2026-10-06/search.so'),'budget_seconds':[1,10**9],'integer_budget':budget,'scale':rc.scale,'max_labels':10000,'demand':'zero other-NET demand; isolated path model','scope':'Fixed 1ns RC allowance, not candidate-specific STA budget or infeasibility proof. No candidate result labels read.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');loaded=time.perf_counter();cache={};rows=[]
baseline=[{'pair_index':-1,'edge':e['edge'],'net_name':e['net_name'],'source':e['source']['rr_node'],'sink':e['sink_class']['rr_node']} for e in q['resolved']]
for i,query in enumerate([*baseline,*q['candidate_queries']]):
 key=(query['source'],query['sink'])
 if key not in cache:cache[key]=native.query(*key,budget,max_labels=10000)
 result=cache[key];row={**query,'result':result};rows.append(row)
 (out/'results.json').write_text(json.dumps({'results':rows,'unique_queries':len(cache),'protocol_sha256':sha(out/'protocol.json')},indent=2)+'\n')
 if (i+1)%20==0:print(i+1,dict(Counter(x['result']['status'] for x in rows)),flush=True)
finish=time.perf_counter();(out/'receipt.json').write_text(json.dumps({'queries':len(rows),'unique_queries':len(cache),'statuses':dict(Counter(x['result']['status'] for x in rows)),'load_s':loaded-start,'query_s':finish-loaded,'results_sha256':sha(out/'results.json'),'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope']},indent=2)+'\n');print('done')
