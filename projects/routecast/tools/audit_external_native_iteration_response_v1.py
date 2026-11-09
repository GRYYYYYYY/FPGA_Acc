"""Bind existing logs and compare initial criticality bins and all numeric iterations."""
import json,re,sys
from pathlib import Path
from decimal import Decimal
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';C=E/'prospective_external_family_same_place_cold_control_v2_2026-10-19';D=E/'prospective_external_family_native_iteration_response_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def parse(path):
 text=path.read_text();start=text.index('Initial Net Connection Criticality Histogram:');section=text[start:text.index('## Initializing router criticalities took',start)];hist=[int(x) for x in re.findall(r'^\[.*?\)\s+(\d+)',section,re.M)];assert len(hist)==10
 iterations=[]
 for line in text.splitlines():
  m=re.match(r'^\s*(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\([^)]*\)\s+(\d+)\s+\([^)]*\)\s+([\d.]+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$',line)
  if m:
   x=m.groups();iterations.append(dict(iteration=int(x[0]),pres=x[2],bb_updates=int(x[3]),heap_push=int(x[4]),rerouted_nets=int(x[5]),rerouted_connections=int(x[6]),overused_nodes=int(x[7]),wirelength=int(x[8]),cpd=x[9],sTNS=x[10],sWNS=x[11],hTNS=x[12],hWNS=x[13],estimated_success=x[14]))
 n=int(re.search(r'Successfully routed after (\d+) routing iterations',text)[1]);assert [x['iteration'] for x in iterations]==list(range(1,n+1));assert iterations[-1]['overused_nodes']==0
 return dict(initial_criticality_bins=hist,iterations=iterations)
def main():
 control=read(C/'verification.json');assert all(sha(p)==h for p,h in control['bindings'].items());source=Path(read(C/'protocol.json')['source_verification']).parent;folders=[source,C/'native']+[E/'prospective_external_family_supplementary_development_v1_2026-10-19/native/w160'/f'episode_{i:02d}' for i in (1,2,3)];D.mkdir(exist_ok=False);bindings={str(Path(__file__).resolve()):sha(__file__),str(C/'verification.json'):sha(C/'verification.json')};parsed=[]
 for folder in folders:
  audit=read(folder/'verification.json');assert audit['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(sha(p)==h for p,h in audit['bindings'].items());log=folder/'native.log';assert audit['bindings'][str(log)]==sha(log);parsed.append(parse(log));bindings[str(log)]=sha(log);bindings[str(folder/'verification.json')]=sha(folder/'verification.json')
 assert parsed[0]==parsed[1];rows=[]
 for i,data in enumerate(parsed[2:],1):
  a,b=parsed[0],data;divergences=[]
  for old,new in zip(a['iterations'],b['iterations']):
   different=[k for k in old if old[k]!=new[k]]
   if different:divergences.append(dict(iteration=old['iteration'],different_fields=different))
  row=dict(case=f'w160/episode_{i:02d}',initial_histogram_delta=[y-x for x,y in zip(a['initial_criticality_bins'],b['initial_criticality_bins'])],first_aggregate_divergence=divergences[0] if divergences else None,source_iterations=len(a['iterations']),target_iterations=len(b['iterations']),first_iteration=b['iterations'][0]);rows.append(row);print(json.dumps(row))
 (D/'parsed_logs.json').write_text(json.dumps(parsed,indent=2)+'\n');bindings[str(D/'parsed_logs.json')]=sha(D/'parsed_logs.json')
 result=dict(status='ALL5_NATIVE_LOGS_PARSED_SAME_PLACE_TRACE_IDENTICAL_ALL3_EDITED_DIVERGE',rows=rows,source_initial_histogram=parsed[0]['initial_criticality_bins'],bindings=bindings,scope='Printed rounded aggregates only. Histogram cannot identify perCID changes or establish unchanged criticalities when bins match. Logs lack perNET order/first-divergence paths. No causal attribution to STA versus spatial path search or predictor acceptance.')
 (D/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
