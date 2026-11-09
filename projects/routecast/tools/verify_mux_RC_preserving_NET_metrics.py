"""Independent XML universe, all occupation vectors, rational-rank metric checks."""
import json,math,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from stream_native_route_audit import audit
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_RC_preserving_NET_metrics_2026-10-06';p=json.loads((out/'protocol.json').read_text());r=json.loads((out/'receipt.json').read_text());assert sha(out/'protocol.json')==r['protocol_sha256'] and r['all_cases_retained'] and len(r['rows'])==9;assert p['source_sha256']==sha(root/'tools/evaluate_mux_RC_preserving_NET_metrics.py') and all(sha(root/'tools'/n)==h for n,h in p['metric_sources_sha256'].items())
def rank(values):
 order=sorted(range(len(values)),key=lambda i:values[i]);result=[None]*len(values);i=0
 while i<len(order):
  j=i+1
  while j<len(order) and values[order[j]]==values[order[i]]:j+=1
  for k in order[i:j]:result[k]=Fraction(i+j-1,2)
  i=j
 return result
def check_support(a,b,q):
 hit=len(a&b);assert (q['predicted'],q['native'],q['intersection'])==(len(a),len(b),hit)
 for key,den in [('precision',len(a)),('recall',len(b)),('jaccard',len(a|b))]:assert q[key]==(hit/den if den else None)
rows=[]
for c,row in zip(p['cases'],r['rows']):
 assert (c['data_width'],c['channels'])==(row['data_width'],row['channels']);assert all(sha(f)==h for f,h in c['bindings'].items());candidate=json.loads(Path(c['candidate']).read_text());assert c['complete']==(candidate['completed_connections']==candidate['required_connections'])
 if not c['complete']:assert row['status']=='INCOMPLETE_NO_FULLSTATE_SCORE';rows.append({'data_width':c['data_width'],'channels':c['channels'],'score_withheld_incomplete':True});continue
 vectors=out/f"gf2_d{c['data_width']}_w{c['channels']}_vectors.json";assert sha(vectors)==row['vector_sha256'];data=json.loads(vectors.read_text());xml=ET.parse(c['graph']).getroot();caps={int(n.get('id')):int(n.get('capacity')) for n in xml.find('rr_nodes') if n.get('type') in ('CHANX','CHANY') and int(n.get('capacity'))>0};native=audit(c['graph'],c['native_route']);assert len(native['connections'])==candidate['required_connections'];pred={int(n):v for n,v in candidate['ledger'].items()};truth={int(n):v for n,v in native['node_occupancy'].items()};assert data==[{'node':n,'capacity':caps[n],'predicted':pred.get(n,0),'native':truth.get(n,0)} for n in sorted(caps)];ids=sorted(caps);pv={n:Fraction(pred.get(n,0),caps[n]) for n in ids};tv={n:Fraction(truth.get(n,0),caps[n]) for n in ids};a=rank([pv[n] for n in ids]);b=rank([tv[n] for n in ids]);mean=Fraction(len(ids)-1,2);va=sum((x-mean)**2 for x in a);vb=sum((x-mean)**2 for x in b);rho=float(sum((x-mean)*(y-mean) for x,y in zip(a,b)))/math.sqrt(float(va*vb));assert math.isclose(rho,row['utilization_spearman'],abs_tol=1e-12);assert math.isclose(float(sum(abs(pv[n]-tv[n]) for n in ids)/len(ids)),row['utilization_MAE'],abs_tol=1e-12);check_support({n for n in ids if pv[n]>0},{n for n in ids if tv[n]>0},row['use_support']);check_support({n for n in ids if pv[n]>1},{n for n in ids if tv[n]>1},row['overflow_support']);k=max(1,len(ids)//20);pk=set(sorted(ids,key=lambda n:(-pv[n],n))[:k]);tk=set(sorted(ids,key=lambda n:(-tv[n],n))[:k]);check_support(pk,tk,row['top5percent_support']);assert k==row['top_k'];assert sum(tv[n]==min(tv[t] for t in tk) for n in ids)==row['native_cutoff_ties'];assert sum(max(0,pred.get(n,0)-caps[n]) for n in ids)==row['predicted_channel_overflow_units'];assert sum(max(0,truth.get(n,0)-caps[n]) for n in ids)==row['native_channel_overflow_units'];assert native['overflow_units']==row['native_alltype_overflow_units'];rows.append({'data_width':c['data_width'],'channels':c['channels'],'all_channel_vectors_verified':len(ids),'overflow_support':row['overflow_support'],'utilization_spearman':rho});print(c['data_width'],c['channels'],'all metrics verified',flush=True)
(out/'verification.json').write_text(json.dumps({'receipt_sha256':sha(out/'receipt.json'),'verifier_sha256':sha(Path(__file__)),'rows':rows,'scope':'OriginalXML universe/completepredictedandnativephysicaloccupancy/rationalrank/support/MAE/topK/overflow checked; incompletecaseswithheld. No nativefailedoccupancy interpretedaslegalfinalroute, calibratedfailurethresholdorunseenfamilygain.'},indent=2)+'\n')
