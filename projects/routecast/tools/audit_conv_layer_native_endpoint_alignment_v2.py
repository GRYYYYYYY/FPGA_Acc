"""Evaluator-only native endpoint multiset alignment; no predictor input."""
import pathlib,json,re,hashlib,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 front=ROOT/'experiments/conv_layer_global_frontend_v2_2026-10-06';route=ROOT.parent/'persistroute/experiments/vpr9/baseline_runs/vpr_serial/koios_conv_layer_seed1_cw300/design.route';driver=ROOT/'tools/conv_layer_length_switch_prediction.py';frozen=ROOT/'experiments/conv_layer_prediction_driver_readiness_2026-10-06/source/conv_layer_length_switch_prediction.py';assert sha(driver)==sha(frozen)
 r=json.loads((front/'receipt.json').read_text());p=json.loads((front/'protocol.json').read_text());assert r['outputs']['endpoints.json']==sha(front/'endpoints.json');e=json.loads((front/'endpoints.json').read_text());expected=collections.Counter((v['net_id'],v['source'],v['sink']) for v in e['connections']);excluded={v['net_id'] for v in e['excluded_nets']};retained={v[0] for v in expected};assert not retained&excluded
 hashes={str(v):sha(v) for v in [route,front/'endpoints.json',front/'receipt.json',driver]};out=ROOT/'experiments/conv_layer_native_endpoint_alignment_v2_2026-10-06';out.mkdir();(out/'source').mkdir();(out/'source'/pathlib.Path(__file__).name).write_bytes(pathlib.Path(__file__).read_bytes())
 protocol={'inputs_sha256':hashes,'predictor_source_frozen_before_native_inspection':sha(frozen),'source_sha256':sha(pathlib.Path(__file__)),'scope':'native labels evaluator-only; retained endpoint alignment only; no arcs/occupancy/native legality audit'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 net_pattern=re.compile(r'^\s*Net\s+(\d+)\s+\((.*)\)\s*$');node_pattern=re.compile(r'^\s*Node:\s*(\d+)\s+(SOURCE|SINK|OPIN|IPIN|CHANX|CHANY)\b.*?Switch:\s*(-?\d+)');native=collections.Counter();allnets={};net=None;source=None
 with route.open() as f:
  header=f.readline();assert 'Placement_ID: SHA256:'+p['inputs']['reference_place']['sha256'] in header
  for line in f:
   n=net_pattern.match(line)
   if n:net=int(n[1]);source=None;assert net not in allnets;allnets[net]=n[2]
   n=node_pattern.match(line)
   if n:
    if n[2]=='SOURCE':source=int(n[1])
    if n[2]=='SINK' and net in retained:
     assert source is not None;native[(net,source,int(n[1]))]+=1
   elif line.lstrip().startswith('Node:'):raise ValueError('unparsed native node')
 missing=expected-native;extra=native-expected
 assert all(sha(pathlib.Path(v))==h for v,h in hashes.items())
 report={'protocol_sha256':sha(out/'protocol.json'),'expected_connections':sum(expected.values()),'native_retained_connections':sum(native.values()),'retained_endpoint_multiset_exact':expected==native,'missing':[{'net_source_sink':list(k),'count':v} for k,v in missing.items()],'extra':[{'net_source_sink':list(k),'count':v} for k,v in extra.items()],'retained_net_names_match':all(allnets.get(n)==e['net_names'][str(n)] for n in retained),'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['missing','extra']}))
 if missing or extra or not report['retained_net_names_match']:raise SystemExit(1)
if __name__=='__main__':main()
