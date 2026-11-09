from pathlib import Path
import json,csv,hashlib,re,importlib.util,time,sys
D=Path(sys.argv[1]).resolve();R=Path(__file__).resolve().parents[1];W=R/'work';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
E=W/'additional_circuit_full_graph_roundtrip_20261020/tools/export_native_vpr_tree.py';spec=importlib.util.spec_from_file_location('closure_native_tree',E);M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)
prepared=read(D/'capacity_preparation.json');C=D/'capacity';raw=read(C/'native_terminal.json');assert len(raw['results'])==1
finished=raw['results'][0];assert finished['label']=='execution' and len(finished['steps'])==4
repair_terminal=read(C/'execution/repair.terminal.json');repair_launch=read(C/'execution/repair.launch.json');assert repair_terminal==finished['steps'][0] and repair_terminal['returncode']==0 and repair_terminal['memory_guard_stop_reason'] is None
assert repair_terminal['command']==prepared['commands']['repair'] and all(repair_terminal[k]==repair_launch[k] for k in repair_launch)
cfg={'cases':[{'label':prepared['label'],'commands':{k:v for k,v in prepared['commands'].items() if k!='repair'}}],'source_sha256':prepared['source_sha256']}
terminal={'results':[{'label':prepared['label'],'steps':finished['steps'][1:]}]}
for p,h in cfg['source_sha256'].items():assert sha(Path(p))==h,p
refs={str(p):sha(p) for p in [D/'capacity_preparation.json',C/'native_protocol.json',C/'native_terminal.json',C/'execution/repair.terminal.json',C/'execution/repair.launch.json',Path(__file__),E]};rows=[]
for case,finished in zip(cfg['cases'],terminal['results']):
 built=read(D/'capacity/repair.json')
 label=case['label'];assert label==finished['label'];C=D/'capacity';pre=read(C/'independent_preflight.json');v=read(C/'native_validation/validation.json');B=W/'additional_circuit_full_graph_roundtrip_20261020/cases'/label;base=read(B/'native_validation/validation.json')
 for p,h in pre['source_sha256'].items():assert sha(Path(p))==h,p
 assert pre['candidate']['overused_resources']==0 and pre['candidate']['all_sinks_and_nodes_reachable']
 assert len(finished['steps'])==3
 for name,step in zip(['preflight','writer','native'],finished['steps']):
  t=read(C/'execution'/(name+'.terminal.json'));launch=read(C/'execution'/(name+'.launch.json'));assert t==step and t['returncode']==0 and t['memory_guard_stop_reason'] is None
  assert t['command']==case['commands'][name] and all(t[k]==launch[k] for k in launch)
  refs.update({str(p):sha(p) for p in [C/'execution'/(name+'.terminal.json'),C/'execution'/(name+'.launch.json'),C/'execution'/(name+'.stdout'),C/'execution'/(name+'.stderr')]})
 assert all(v[k] for k in ['legal','route_loaded','routing_consistency','successfully_routed','vpr_succeeded']) and v['vpr_exit_status']==0
 assert v['inputs']['route_sha256']==sha(C/'native.route')==sha(C/'native_validation/native.route')
 nativecmd=case['commands']['native']
 for flag,key in [('--vpr','vpr'),('--arch','arch'),('--circuit','circuit'),('--net','net'),('--place','place'),('--rr-graph','rr_graph')]:
  p=Path(nativecmd[nativecmd.index(flag)+1]);assert sha(p)==v['inputs'][key+'_sha256']==base['inputs'][key+'_sha256'],(label,key)
 log=C/'native_validation/vpr_analysis.stdout';err=C/'native_validation/vpr_analysis.stderr';assert sha(log)==v['stdout_sha256'] and sha(err)==v['stderr_sha256'];text=log.read_text()
 assert all(s in text for s in ['Finished loading route file','Completed routing consistency check successfully.','Circuit successfully routed','VPR succeeded'])
 wl=int(re.findall(r'Total wirelength:\s+(\d+)',text)[-1]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)[-1]);assert (wl,cpd)==(v['total_wirelength'],v['critical_path_delay_ns'])
 writer=json.loads((C/'execution/writer.stdout').read_text());assert writer['output_sha256']==sha(C/'native.route') and writer['route_trees_sha256']==sha(C/'repaired.route_trees.csv') and writer['ambiguous_used_rr_edges']==0
 actual=M.extract(C/'native.route');baseline=M.extract(W/'additional_circuit_frozen_baselines_20261020/cases'/label/'circuit.route');expected={}
 with (C/'repaired.route_trees.csv').open() as f:
  for r in csv.DictReader(f):
   n=int(r['net_id']);entry=expected.setdefault(n,{'source':int(r['source']),'edges':set()});assert entry['source']==int(r['source']);entry['edges'].add((int(r['parent']),int(r['child'])))
 assert set(actual)==set(expected)==set(baseline) and len(actual)==built['total_nets']
 restored=set(built['restored_nets'])
 for n,t in actual.items():
  assert t['source']==expected[n]['source'] and {(a,b) for a,b,s in t['edges']}==expected[n]['edges']
  assert sorted(t['sinks'])==sorted(baseline[n]['sinks'])
  if n in restored:assert sorted(t['edges'])==sorted(baseline[n]['edges'])
 checks={'native_legal':True,'all_net_exact_candidate_tree_writeback':True,'all_sink_pin_identity':sum(len(t['sinks']) for t in actual.values())==sum(len(t['sinks']) for t in baseline.values()),'zero_overuse':True,'model_crossings_no_increase':pre['candidate']['layer_transitions']<=pre['baseline']['layer_transitions'],'wirelength_no_increase':wl<=base['total_wirelength'],'cpd_no_increase':cpd<=base['critical_path_delay_ns']}
 rows.append({'label':label,'checks':checks,'joint_quality_pass':all(checks.values()),'wirelength':wl,'baseline_wirelength':base['total_wirelength'],'cpd_ns':cpd,'baseline_cpd_ns':base['critical_path_delay_ns'],'modeled_layer_transitions':pre['candidate']['layer_transitions'],'restored_nets':len(restored),'retained_candidate_nets':built['retained_candidate_nets']})
 for p in [C/'independent_preflight.json',C/'native_validation/validation.json',log,err,B/'native_validation/validation.json',C/'native.route']:refs[str(p)]=sha(p)
r={'status':'fresh_parent_capacity_native_quality_and_full_tree_reviewed','rows':rows,'source_sha256':refs,'scope':'One fresh-parent repair stage; original parent failures retained. Full legal sourceboundVPR/unchangedgraph+placement and complete per-case tree/sinkpin census. Not complete refinement policy or five fresh repeats. Modeled layer transitions are not physical SLL. No original denominator changes, no gate closure, no five-repeat/dataset-generalization/board claim.','research_complete':False};(D/'independent_native_review.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(rows,indent=2))
