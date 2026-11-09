"""Input-only all-A conflict ownership inventory and bounded no-B protocol."""
import json,xml.parsers.expat as X
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_A_only_repair_protocol_v1_2026-10-21';D.mkdir(exist_ok=False);P=R/'experiments/mmc_complete_NET_candidate_choice_diagnostic_protocol_v1_2026-10-19/protocol.json';plan=json.loads(P.read_text());F=R/'experiments/mmc_coupled_chooser_cost_and_data_scope_v1_2026-10-19/input_only_choice_protocol_v1.json';frozen=json.loads(F.read_text());graph=Path(json.loads(Path(plan['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);channels=set();stack=[]
class Done(Exception):pass
def begin(tag,a):
 parent=stack[-1] if stack else None;stack.append(tag)
 if tag=='node' and parent=='rr_nodes' and a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0:assert int(a['capacity'])==1;channels.add(int(a['id']))
def end(tag):
 assert stack.pop()==tag
 if tag=='rr_nodes':raise Done
parser=X.ParserCreate();parser.StartElementHandler=begin;parser.EndElementHandler=end
try:
 with graph.open('rb') as f:
  while b:=f.read(8*1024*1024):parser.Parse(b,False)
except Done:pass
assert len(channels)==258720;bindings={str(p):sha(p) for p in [P,F,graph,Path(__file__)]};rows=[]
for item in plan['cases']:
 case=item['case'];bp=R/'experiments/mmc_candidate_ownership_implications_v1_2026-10-19'/case/'banks.jsonl';assert sha(bp)==frozen['bindings'][str(bp)];owners=defaultdict(list);nets=set()
 for bank in map(json.loads,bp.open()):
  net=bank['net_id'];assert net not in nets;nets.add(net)
  for n in set(bank['A'])&channels:owners[n].append(net)
 assert len(nets)==55300;conflicts=[{'channel':n,'owners':sorted(ns)} for n,ns in sorted(owners.items()) if len(ns)>1];selected=sorted({net for w in conflicts for net in w['owners']});rows.append({'case':case,'conflict_CHANNELs':len(conflicts),'overflow_units':sum(len(w['owners'])-1 for w in conflicts),'reroutable_NETs':selected,'reroutable_NET_count':len(selected),'initial_conflicts':conflicts,'frame_A':item['candidate_A'],'endpoint':item['endpoint']});bindings[str(bp)]=sha(bp);bindings[item['candidate_A']]=sha(item['candidate_A'])
# Limits are fixed before any new route search or future result evaluation.
protocol={'status':'A_ONLY_CONFLICT_OWNERSHIP_INVENTORY_AND_BOUNDED_REPAIR_REGISTERED','hypothesis':'Fix all unaffected complete A trees and jointly reroute only initial all-A conflict owners. Eliminate B acquisition and the mixed A/B choice stage; preserve all original endpoint budgets. Can this restricted no-B pipeline produce legal full-domain candidates that retain previous-native quality? Failure closes this exact owner set, not general routing.','rows':rows,'limits_per_case':{'max_states':64,'max_queries':128,'max_seconds':60,'max_reroutable_NETs':64},'eligibility':{r['case']:r['reroutable_NET_count']<=64 for r in rows},'fixed_ownership':'All positive CHANNEL support of every unselected A NET is blocked for each reroutable NET. All initial A-conflict owners selected, no data-dependent additions after failure. No old A/B keeper-cover restrictions; changed plan explicitly registered.','initialization':'Each selected tree starts at the original complete A path; it must avoid unselected A ownership by construction. Branch only on contested CHANNEL uses. No B paths, B choices or B generation in the prospective inference mechanism. Archived banks used only as an authenticated A-support transport; verify all supports from original A XML paths.','priority':'Minimize current expanded-tree CHANNEL excess, then summed raw delay; no target labels in search.','cost_policy':'A generation, cold graph/metadata preparation, search, admission/audits and native/canonical stages remain paid. Removing B is a cost hypothesis, not a speed claim. Existing A archive reuse only supports a functional diagnostic; fresh matched complete workflow required for cost acceptance.','evaluation':'Freeze all3 outputs before reading their target quality labels; original complete concrete/spatial domains, four metrics and both previous_native/raw_min_on controls unchanged. Any infeasible case fails all3 capacity; no label-based rerouting or threshold sweeps.','evidence_scope':'All MMC cases already exposed development data, strict unseen=0. Single data-motivated no-B mechanism test, not a heldout claim.','stop_loss':json.loads((R/'experiments/mmc_expanded41_conflict_first_CBS_v1_2026-10-21/research_decision_v1.json').read_text())['stop_loss'],'bindings':bindings};assert all(sha(p)==h for p,h in bindings.items());(D/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps([{'case':r['case'],'conflicts':r['conflict_CHANNELs'],'reroutable_NETs':r['reroutable_NET_count'],'within_limit':protocol['eligibility'][r['case']]} for r in rows],indent=2))
