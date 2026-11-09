"""Independent direct CID-map path equality, including absent-member enumeration."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];D=R/'experiments/wbuart_small_group_membership_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=D/'verification.json';v=read(p);assert all(sha(n)==h for n,h in v['bindings'].items());summary=[]
 for c in v['rows']:
  saved=read(c['payload']);refs={r['net_id']:r['native_records'] for r in read(c['native_reference_payload'])};wanted={q['net_id']:q for q in saved['NETs']};out=Path(c['model_output']);initial=defaultdict(list)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  history=defaultdict(list)
  for n in wanted:history[n].append(({'stage':'initial'},initial[n]))
  for rnd in read(out/'receipt.json')['rounds']:
   for i,e in enumerate(rnd['events']):
    if e['net_id'] not in wanted:continue
    for key in ['records','rejected_records']:
     if key in e:history[e['net_id']].append(({'round':rnd['round_index'],'index':i,'key':key,'status':e['status']},e[key]))
  def equal(a,b):
   aa={q['connection_id']:q for q in a};bb={q['connection_id']:q for q in b}
   return set(aa)==set(bb) and all(aa[n]['source']==bb[n]['source'] and aa[n]['sink']==bb[n]['sink'] and aa[n]['answer']['physical_edge_ids']==bb[n]['answer']['physical_edge_ids'] for n in aa)
  available=set()
  for n,q in wanted.items():
   matches=[where for where,records in history[n] if equal(records,refs[n])];assert len(history[n])==q['candidate_observations'] and matches==q['exact_native_tree_matches']
   if matches:available.add(n)
  for g in saved['groups']:assert g['missing_NETs']==[n for n in g['NETs'] if n not in available] and g['all_exact_native_trees_available']==set(g['NETs']).issubset(available)
  summary.append({'case':c['case'],'groups':len(saved['groups']),'groups_with_all_exact_trees':sum(g['all_exact_native_trees_available'] for g in saved['groups']),'all_positive_and_negative_memberships_verified':True})
 assert len(summary)==9
 (D/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL9_SMALL_GROUP_POSITIVE_AND_NEGATIVE_PHYSICAL_MEMBERSHIP_INDEPENDENT_PASS','rows':summary,'bindings':{str(p):sha(p),str(Path(__file__)):sha(__file__)},'scope':'Separate direct perCID equality across all recorded complete candidates, no same-snapshot joint admissibility or quality implication.'},indent=2)+'\n');print('ALL9_SMALL_GROUP_POSITIVE_AND_NEGATIVE_PHYSICAL_MEMBERSHIP_INDEPENDENT_PASS')
if __name__=='__main__':main()
