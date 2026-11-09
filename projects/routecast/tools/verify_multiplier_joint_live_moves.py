"""Reauthenticate actual live move outputs; original XML audit of repeatable routes."""
import argparse,collections,json,shutil
from pathlib import Path
from pre_route_endpoints import sha,placements
from stream_native_route_audit import audit


def main():
 parser=argparse.ArgumentParser();parser.add_argument('design');args=parser.parse_args();design=args.design;base=Path('experiments')
 trial=base/'multiplier_joint_persistent_live_swap_2026-10-06'/design;work=Path('work/multiplier_joint_persistent_live_swap_2026-10-06')/design;swap=base/'multiplier_placement_swap_2026-10-06'/design;delta=base/'multiplier_moved_incremental_pressure_2026-10-06'/design;moved=base/'multiplier_moved_incremental_search_2026-10-06'/design
 out=base/'multiplier_joint_live_move_verification_2026-10-06'/design;out.mkdir(parents=True);(out/'source').mkdir();bindings={}
 def load(path):bindings[str(path)]=sha(path);return json.loads(path.read_text())
 r=load(trial/'receipt.json');p=load(trial/'protocol.json');assert r['protocol_sha256']==sha(trial/'protocol.json');assert all(sha(path)==digest for path,digest in p['bindings_sha256'].items());assert [v['mode'] for v in r['results']]==p['sequence']==['off','on','on','off']*2
 for source in (trial/'source').glob('*.py'):assert sha(source)==p['bindings_sha256'][str(Path('tools')/source.name)]
 sr=load(swap/'receipt.json');ep=load(swap/'endpoints.json');assert sha(swap/'endpoints.json')==sr['endpoint_sha256'];mr=load(moved/'receipt.json');reference=load(moved/'prediction.json');assert sha(moved/'prediction.json')==mr['prediction_sha256'];dr=load(delta/'receipt.json');payload=delta/'candidate.pressure';assert sha(payload)==dr['pressure_sha256']['candidate.pressure'];bindings[str(payload)]=sha(payload)
 expected_paths=sorted(reference['connections'],key=lambda v:v['connection_id']);expected=collections.Counter((v['net_id'],v['source'],v['sink']) for v in ep['connections']);means={};qor={};physical_results=[]
 for mode in ('off','on'):
  group=[v for v in r['results'] if v['mode']==mode];assert len(group)==4 and len({v['route_sha256'] for v in group})==1 and len({(v['cpd_ns'],v['wirelength']) for v in group})==1
  for row in group:
   tag=f"{row['run']:02d}_{mode}";route=work/tag/'design.route';log=trial/(tag+'.log');assert sha(route)==row['route_sha256'] and sha(log)==row['log_sha256'];bindings[str(route)]=sha(route);bindings[str(log)]=sha(log)
   assert row['warm_pipeline_s']>=sum(row['phases'].values());assert placements(work/tag/'design.place',p['inputs']['packed_netlist']['sha256'])==placements(swap/'swapped.place',p['inputs']['packed_netlist']['sha256'])
   if mode=='on':
    exported=trial/(tag+'.pressure');paths=trial/(tag+'_connections.json');assert sha(exported)==sha(payload) and json.loads(paths.read_text())==expected_paths;bindings[str(exported)]=sha(exported);bindings[str(paths)]=sha(paths)
  first=group[0];route=work/f"{first['run']:02d}_{mode}"/'design.route';physical=audit(p['inputs']['rr_graph']['path'],route);actual=collections.Counter((v['net_id'],v['source'],v['sink']) for v in physical['connections']);assert actual==expected and physical['all_printed_branch_arc_switch_and_union_checks_pass'] and physical['overflow_units']==0
  physical_path=out/(mode+'_physical.json');physical_path.write_text(json.dumps(physical)+'\n');physical_results.append({'mode':mode,'connections':sum(actual.values()),'physical_sha256':sha(physical_path),'overflow_units':0});means[mode]=sum(v['warm_pipeline_s'] for v in group)/4;qor[mode]={k:group[0][k] for k in ('cpd_ns','wirelength')}
 assert means==r['mean_warm_pipeline_s'] and means['on']/means['off']==r['on_over_off'] and all(sha(path)==digest for path,digest in bindings.items())
 for name in ('verify_multiplier_joint_live_moves.py','stream_native_route_audit.py','audit_native_route.py','pre_route_endpoints.py'):shutil.copyfile(Path('tools')/name,out/'source'/name)
 report={'inputs_sha256':bindings,'source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')},'mean_warm_pipeline_s':means,'on_over_off':r['on_over_off'],'qor':qor,'initialization_s':r['initialization_s'],'physical_results':physical_results,'all_checks_pass':True,'scope':r['scope']}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'all_checks_pass':True},indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ('inputs_sha256','source_sha256')}),flush=True)

if __name__=='__main__':main()
