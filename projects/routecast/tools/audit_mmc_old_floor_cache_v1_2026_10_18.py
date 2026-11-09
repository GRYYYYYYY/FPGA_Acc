"""Authenticate old floor source/domain and native compatibility; build cached fixture."""
import json,ast,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_old_floor_cache_audit_v1_2026-10-18';D.mkdir(exist_ok=False);start=time.perf_counter();oldmodel=R/'experiments/mmc_retained_tree_full_schedule_recovery_v1_2026-10-13/model';ap=oldmodel/'initial_physical_verification.json';audit=json.loads(ap.read_text());assert audit['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];assert all(sha(p)==h for p,h in audit['bindings'].items());fp=oldmodel/'floors.json';initialpath=oldmodel/'initial.json';assert audit['bindings'][str(fp)]==sha(fp) and audit['bindings'][str(initialpath)]==sha(initialpath)
rawroot=R/'experiments/mmc_native_raw_control_v1_2026-10-18';rawproofpath=rawroot/'independent_xml_verification_v2.json';rawproof=json.loads(rawproofpath.read_text());assert rawproof['all_paths_original_XML_fraction_RC_budget_singleparent_and_uniqueNET_pass'] and all(sha(p)==h for p,h in rawproof['bindings'].items());raw=json.loads((rawroot/'initial.json').read_text());oldfile=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/demand/mmc/endpoints.json';newfile=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';old=json.loads(oldfile.read_text());new=json.loads(newfile.read_text());protocol=json.loads((oldmodel/'protocol.json').read_text());assert protocol['bindings'][str(oldfile)]==sha(oldfile);assert old['graph_sha256']==new['graph_sha256'];producer=R/'tools/run_criticality_retained_tree_full_schedule_v1.py';assert protocol['bindings'][str(producer)]==sha(producer)
# Freeze and check actual zero-priced raw initialization call in generator AST.
tree=ast.parse(producer.read_text());calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='prepare'];assert any(ast.unparse(c)=="search.prepare({}, 0, structural=False)" for c in calls)
floors={}
for r in json.loads(fp.read_text()):
 key=r['source'],r['sink'];assert key not in floors and type(r['minimum_integer']) is int and r['minimum_integer']>=0;floors[key]=r['minimum_integer']
queries={q['connection_id']:q for q in old['connections']};initial=json.loads(initialpath.read_text());records={r['connection_id']:r for r in initial['records']};assert len(records)==len(initial['records'])==len(queries)==115572;assert set(floors)=={(q['source'],q['sink']) for q in queries.values()};scale=raw['scale'];assert scale==10**18
for cid,q in queries.items():
 rec=records[cid];assert all(rec[k]==v for k,v in q.items());floor=floors[q['source'],q['sink']];assert rec['floor_integer']==rec['answer']['delay']==floor;assert rec['budget_integer']==max(scale//10**9,(3*floor+1)//2)
kept=checked_old_new=anchored=0;output=[]
for rec in raw['records']:
 cid=rec['connection_id'];q=queries[cid];newrec=dict(rec)
 if rec['floor_integer'] is None:
  assert all(rec[k]==v for k,v in q.items());floor=floors[q['source'],q['sink']];delay=rec['answer']['delay'];assert floor<=delay;proxy=max(scale//10**9,(3*floor+1)//2);newrec.update(floor_integer=floor,proxy_budget_integer=proxy,budget_integer=max(proxy,delay));kept+=1;anchored+=delay>proxy
 else:
  proxy=rec['budget_integer'];newrec['proxy_budget_integer']=proxy
  if (rec['source'],rec['sink'])==(q['source'],q['sink']):assert rec['floor_integer']==floors[q['source'],q['sink']];checked_old_new+=1
 assert newrec['answer']['delay']<=newrec['budget_integer'];output.append(newrec)
assert kept==115092
# Retained raw paths/ledger unchanged; only authenticated floor/budget metadata differs.
frame=dict(raw,records=output,budget_policy='NATIVE_ANCHORED_PROXY_V1',history={},epochs={str(net):int(net in set(json.loads((rawroot/'receipt.json').read_text())['dirty_nets'])) for net in {r['net_id'] for r in output}},scope='Cached-floor correctness fixture. Original old global-floor production not timed here and is required local-only setup in fresh workflow.')
with (D/'initial.json').open('x') as f:json.dump(frame,f);f.write('\n')
bindings={str(ap):sha(ap),str(fp):sha(fp),str(initialpath):sha(initialpath),str(oldmodel/'protocol.json'):sha(oldmodel/'protocol.json'),str(oldfile):sha(oldfile),str(newfile):sha(newfile),str(producer):sha(producer),str(rawproofpath):sha(rawproofpath),str(rawroot/'initial.json'):sha(rawroot/'initial.json'),str(D/'initial.json'):sha(D/'initial.json'),str(Path(__file__)):sha(__file__)}
for key in ['experiments/soft_demand_workspace_radix_contract_v3_2026-10-08/verification.json','experiments/hybrid_bidirectional_search_contract_v1_2026-10-08/verification.json']:
 p=R/key;v=json.loads(p.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings[str(p)]=sha(p)
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,original_floor_domain_connections=115572,unchanged_native_floor_delay_compatibility_checks=kept,new_dirty_certificates_also_check_old_unchanged_endpoints=checked_old_new,native_anchored_above_proxy=anchored,all_cached_floor_records_attain_bound_by_existing_original_XML_physical_proof=True,generator_zero_price_raw_mode_AST_checked=True,new_independent_minimum_certificate_for_all_old_floors=False,scope='Old floor source/provenance/domain and independently audited attaining paths, existing engine contracts; new raw certificate independently matches subset of old endpoint minima. Not a new per-design dual certificate for all old floors, new global floor run or fresh workflow timing. Cached fixture may only support explicitly scoped correctness pilot; fresh old-floor costs remain local-only.'),f,indent=2);f.write('\n')
print('MMC OLD FLOOR AUDIT',kept,'native checks',checked_old_new,'fresh minimum crosschecks',anchored,'native anchors',flush=True)
