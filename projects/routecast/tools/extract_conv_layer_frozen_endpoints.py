"""Independent full conv_layer pre-route frontend with explicit constant policy."""
import pathlib,json,time,shutil,sys,hashlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def main():
 manifest=ROOT.parent/'tileplace/experiments/koios_conv_layer_seed1_cw300/manifest.json';m=json.loads(manifest.read_text());inputs={k:m['inputs'][k] for k in ['architecture','packed_netlist','reference_place','rr_graph']};atom=ROOT.parent/'persistroute/experiments/vpr9/koios_conv_layer_frontend/conv_layer.pre-vpr.blif';inputs['atom']={'path':str(atom),'sha256':m['packed_netlist']['atom_netlist_id'].split(':',1)[1]}
 for v in inputs.values():assert sha(v['path'])==v['sha256']
 out=ROOT/'experiments/conv_layer_frozen_frontend_2026-10-06';out.mkdir();(out/'source').mkdir();names=['extract_conv_layer_frozen_endpoints.py','pre_route_endpoints.py','pre_route_constants.py','blif_constants.py','blif_undriven_outputs.py']
 for name in names:shutil.copyfile(ROOT/'tools'/name,out/'source'/name)
 sources={n:sha(out/'source'/n) for n in names};protocol={'manifest_sha256':sha(manifest),'inputs':inputs,'sources':sources,'constant_net_method':'global','clock_policy':'exclude_root_clocks','scope':'pre-route extraction only, architecture undriven classification with no value guess; no native route input, no unseen-family claim'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');sys.path.insert(0,str(out/'source'));from pre_route_constants import extract_with_constants
 start=time.monotonic()
 try:
  e,report=extract_with_constants(inputs['packed_netlist']['path'],inputs['reference_place']['path'],inputs['rr_graph']['path'],inputs['atom']['path'],'global',inputs['architecture']['path'])
  for name,value in [('endpoints.json',e),('mapping.json',report)]:(out/name).write_text(json.dumps(value)+'\n')
  assert all(sha(v['path'])==v['sha256'] for v in inputs.values());assert all(sha(out/'source'/n)==h for n,h in sources.items())
  receipt={'protocol_sha256':sha(out/'protocol.json'),'connections':len(e['connections']),'retained_nets':len({v['net_id'] for v in e['connections']}),'excluded_nets':e['excluded_nets'],'pin_details':len(report['pin_details']),'outputs':{n:sha(out/n) for n in ['endpoints.json','mapping.json']},'inputs_unchanged':True,'wall_s':time.monotonic()-start,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k!='excluded_nets'}),flush=True)
 except BaseException as err:
  (out/'failure.json').write_text(json.dumps({'error':repr(err),'wall_s':time.monotonic()-start,'scope':'unsupported frontend preserved; no route-derived substitution'},indent=2)+'\n');raise
if __name__=='__main__':main()
