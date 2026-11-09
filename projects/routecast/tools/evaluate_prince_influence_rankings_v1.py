"""Post-freeze development ranking diagnosis, both static controls and all budgets."""
import json
from pathlib import Path
from fractions import Fraction as Q
from collections import defaultdict
from pre_route_endpoints import sha
from diagnose_prince_native_route_churn_v2 import native
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_influence_coverage_v1_2026-10-20'
def main():
 D.mkdir(exist_ok=False);vp=E/'prince_influence_rankings_v1_2026-10-20/verification.json';v=json.loads(vp.read_text());assert all(sha(p)==h for p,h in v['bindings'].items());bindings={str(vp):sha(vp),str(Path(__file__)):sha(__file__)};rows=[]
 for item in v['rows']:
  rp=Path(item['rankings']);assert sha(rp)==item['sha256'];r=json.loads(rp.read_text());assert r['no_target_label_inputs'] and all(sha(p)==h for p,h in r['bindings'].items());case=r['case'];width=case.split('/')[0];base=E/'prince_native_cohort_v1_2026-10-20'/width;src=base/'source';tar=E/'prince_native_cohort_v1_2026-10-20'/case;ep=tar/'pre_route_endpoints.json';meta=json.loads(ep.read_text());names={int(n):name for n,name in meta['net_names'].items()};resourcesp=E/'prince_quality_domains_v1_2026-10-20'/width/'resources.jsonl';resources={x['id'] for x in map(json.loads,resourcesp.open())};a=native(src/'output.route',src/'physical_audit.json',resources);b=native(tar/'output.route',tar/'physical_audit.json',resources);clean=set(r['clean_NETs']);mass={n:len(a.get(names[n],set())^b.get(names[n],set())) for n in clean};positive={n for n in clean if mass[n]};negative=clean-positive;methods={}
  for method,order in r['rankings'].items():
   assert set(order)==clean and len(order)==len(clean);groups=defaultdict(list)
   for n in clean:groups[Q(*r['scores'][str(n)][method])].append(n)
   wins=Q();belowneg=0
   for value,group in sorted(groups.items()):
    p=sum(n in positive for n in group);neg=len(group)-p;wins+=p*belowneg+Q(p*neg,2);belowneg+=neg
   auc=wins/(len(positive)*len(negative)) if positive and negative else None;budgets={}
   for budget in [10,25,50]:
    k=len(clean)*budget//100;selected=set(order[:k]);assert set(r['selections'][method][str(budget)])==set(r['dirty_NETs'])|selected;hits=len(selected&positive);budgets[str(budget)]=dict(k_clean=k,hits_changed_clean=hits,precision=Q(hits,k),recall=Q(hits,len(positive)),native_NET_resource_edit_mass=sum(mass[n] for n in selected),total_native_NET_resource_edit_mass=sum(mass.values()),edit_mass_recall=Q(sum(mass[n] for n in selected),sum(mass.values())))
   methods[method]=dict(AUROC=auc,budgets=budgets)
  rows.append(dict(case=case,clean_NETs=len(clean),changed_clean_NETs=len(positive),methods=methods));print('INFLUENCE_DIAGNOSIS',case,{m:round(float(d['AUROC']),4) for m,d in methods.items()},flush=True)
  for p in [rp,ep,resourcesp,src/'output.route',src/'physical_audit.json',tar/'output.route',tar/'physical_audit.json']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());result=dict(rows=rows,bindings=bindings,scope='Already exposed development label diagnostic. Changed-clean NET AUROC, fixed-budget hit coverage and sum perNET CHANNEL symmetric-difference edit mass; not aggregate occupancy prediction error. No routing/prediction quality gate, unseen evidence or fullpaid/native speedup. No score selected/promoted by this screen.')
 (D/'verification.json').write_text(json.dumps(result,indent=2,default=lambda x:dict(numerator=x.numerator,denominator=x.denominator))+'\n')
if __name__=='__main__':main()
