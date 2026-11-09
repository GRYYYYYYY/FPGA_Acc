"""Matched posthoc min-delay versus budgeted-span candidate comparison."""
import json,collections,shutil
from pathlib import Path
from pre_route_endpoints import sha
BASE=Path('experiments')

def load(search_name,audit_name,budget_name,impact_name):
 search=BASE/search_name;audit=BASE/audit_name;budget=BASE/budget_name;impact=BASE/impact_name
 p=json.loads((search/'protocol.json').read_text());r=json.loads((search/'receipt.json').read_text());ar=json.loads((audit/'receipt.json').read_text());br=json.loads((budget/'receipt.json').read_text());ir=json.loads((impact/'report.json').read_text())
 assert r['protocol_sha256']==sha(search/'protocol.json') and r['journal_sha256']==sha(search/'queries.jsonl') and r['queries']==75
 assert all(sha(path)==h for path,h in p['inputs_sha256'].items()) and all(sha(search/'source'/n)==h for n,h in p['source_sha256'].items())
 ap=json.loads((audit/'protocol.json').read_text());bp=json.loads((budget/'protocol.json').read_text())
 assert ar['protocol_sha256']==sha(audit/'protocol.json') and ap['parent_receipt_sha256']==sha(search/'receipt.json') and ar['result']['all_physical_and_union_checks_passed']
 assert br['protocol_sha256']==sha(budget/'protocol.json') and br['budgets_sha256']==sha(budget/'budgets.json') and bp['physical_receipt_sha256']==sha(audit/'receipt.json') and br['all_candidates_within_original_exact_path_budget']
 assert all(sha(path)==h for path,h in bp['selection_sha256'].items()) and all(sha(path)==h for path,h in ir['inputs_sha256'].items())
 assert ir['incremental_equals_full_rebuild'] and not ir['repair_committed']
 rows=[json.loads(line) for line in (search/'queries.jsonl').read_text().splitlines()];assert len(rows)==75 and len({v['connection_id'] for v in rows})==75
 assert dict(collections.Counter(v['result']['status'] for v in rows))==r['statuses']
 return p,r,ir,rows,{str(path):sha(path) for path in [search/'receipt.json',audit/'receipt.json',budget/'receipt.json',impact/'report.json']}

def run():
 a=load('conv_layer_strict_channel_avoidance_2026-10-06','conv_layer_strict_channel_candidate_xml_audit_2026-10-06','conv_layer_strict_candidate_xml_budget_audit_2026-10-06','conv_layer_whole_net_candidate_impact_2026-10-06')
 b=load('conv_layer_budgeted_span_avoidance_2026-10-06','conv_layer_span_candidate_xml_audit_2026-10-06','conv_layer_span_candidate_xml_budget_audit_2026-10-06','conv_layer_span_whole_net_candidate_impact_2026-10-06')
 for key in ['inputs_sha256','graph','banned_channel_nodes','policy','order']:assert a[0][key]==b[0][key]
 fields=['connection_id','net_id','source','sink','original_opin','original_ipin'];assert [{k:r[k] for k in fields} for r in a[3]]==[{k:r[k] for k in fields} for r in b[3]]
 net_a={r['net_id']:r for r in a[2]['net_span_changes']};net_b={r['net_id']:r for r in b[2]['net_span_changes']};common=sorted(set(net_a)&set(net_b))
 for n in common:assert net_a[n]['old']==net_b[n]['old']
 reports={}
 for name,data in [('minimum_delay',a),('budgeted_span',b)]:
  impact=data[2];spans=impact['net_span_changes'];reports[name]={'statuses':data[1]['statuses'],'eligible_whole_nets':len(impact['eligible_whole_net_ids']),'overflow_before':impact['overflow_before'],'overflow_after':impact['overflow_after'],'worsened_resources':len(impact['worsened_resources']),'span_decreased_nets':sum(v['new']<v['old'] for v in spans),'span_increased_nets':sum(v['new']>v['old'] for v in spans),'eligible_net_span_before':sum(v['old'] for v in spans),'eligible_net_span_after':sum(v['new'] for v in spans)}
 report={'inputs_sha256':{**a[4],**b[4]},'matched_original_inputs_pins_budgets':True,'same_eligible_whole_net_set':set(net_a)==set(net_b),'common_eligible_nets':len(common),'common_net_span_min_delay':sum(net_a[n]['new'] for n in common),'common_net_span_budgeted_span':sum(net_b[n]['new'] for n in common),'models':reports,'source_sha256':sha(__file__),'scope':'retrospective candidate objective comparison only; unequal eligible sets disclosed; no accepted repair, native STA/QoR, runtime speedup or feedback net-benefit'}
 out=BASE/'conv_layer_candidate_objective_comparison_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':run()
