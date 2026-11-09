"""Authenticated final-pass metrics and cumulative search cost, no bestpass choice."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];soft=root/'experiments/gf2_soft_pressure_2026-10-06';neg=root/'experiments/gf2_negotiated_pressure_metrics_2026-10-06';sr=json.loads((soft/'receipt.json').read_text());nr=json.loads((neg/'receipt.json').read_text())
for d,r in ((soft,sr),(neg,nr)):assert json.loads((d/'verification.json').read_text())['receipt_sha256']==sha(d/'receipt.json')
st=root/'experiments/gf2_capacity_forecast_2026-10-06';nt=root/'experiments/gf2_negotiated_pressure_2026-10-06';sc=json.loads((st/'receipt.json').read_text());nc=json.loads((nt/'receipt.json').read_text());assert json.loads((nt/'verification.json').read_text())['receipt_sha256']==sha(nt/'receipt.json');rows=[]
for a,b in zip(sr['rows'],nr['rows']):
 w=a['data_width'];ch=a['channels'];assert (w,ch)==(b['data_width'],b['channels']);old=next(x for x in sc['rows'] if x['data_width']==w and x['channels']==ch and x['mode']=='soft');new=next(x for x in nc['rows'] if x['data_width']==w and x['channels']==ch);search=sum(x['search_s'] for x in new['passes']);row={'data_width':w,'channels':ch,'soft_search_s':old['search_s'],'feedback_all_pass_search_s':search,'feedback_over_soft_search_ratio':search/old['search_s'],'cost_scope':'Only observed searchwalls, not full prepare/audit/native end-to-end; serial observations not randomizedpairedbenchmark.'}
 if a['status']=='SCORED_COMPLETE':
  assert b['status']=='SCORED_COMPLETE';av=json.loads((soft/f'gf2_d{w}_w{ch}_vectors.json').read_text());bv=json.loads((neg/f'gf2_d{w}_w{ch}_vectors.json').read_text());assert all((x['node'],x['capacity'],x['native'])==(y['node'],y['capacity'],y['native']) for x,y in zip(av,bv)) and len(av)==len(bv);row.update(soft_rho=a['utilization_spearman'],feedback_rho=b['utilization_spearman'],rho_delta=b['utilization_spearman']-a['utilization_spearman'],soft_MAE=a['utilization_MAE'],feedback_MAE=b['utilization_MAE'],soft_overflow_support=a['overflow_support'],feedback_overflow_support=b['overflow_support'])
 else:assert b['status']=='INCOMPLETE_NO_FULLSTATE_SCORE';row['complete_metrics_withheld']=True
 rows.append(row);print(w,ch,row.get('rho_delta'),row['feedback_over_soft_search_ratio'],flush=True)
out=root/'experiments/gf2_feedback_comparison_2026-10-06';out.mkdir();(out/'verification.json').write_text(json.dumps({'inputs_sha256':{str(p):sha(p) for d in (soft,neg,st,nt) for p in (d/'receipt.json',d/'verification.json')},'source_sha256':sha(Path(__file__)),'rows':rows,'scope':'Same nativechanneluniverse/labels authenticated; lastpass only,no threshold/bestpassselection. One developmentfamily,no time-netbenefit or generalization claim.'},indent=2)+'\n')
