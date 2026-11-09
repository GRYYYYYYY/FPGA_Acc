"""Fresh full two-update tails with one persistent owner per whole-family case."""
import json,shutil,subprocess,time,os
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from certified_accepted_route_state import CertifiedAcceptedRouteState
from validated_bundle_certificate import issue
from staged_placement_reroute import stage_reroute_with_repair
root=Path(__file__).resolve().parents[1];out=root/'experiments/gf2_capture_ABBA0_certified_2026-10-06';out.mkdir();work=root/'work/gf2_capture_ABBA0_certified_2026-10-06';work.mkdir();shared=root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07';cases=[]
# Freeze all cases and isolated round scripts before evaluating any new output.
for w,count in ((32,264),(64,491),(128,908)):
 original=root/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}';swapped=root/f'experiments/gf2_d{w}_placement_swap_2026-10-06';rounds=[]
 for i,target in enumerate((swapped,original)):
  sandbox=work/f'gf2_d{w}'/str(i);sandbox.mkdir(parents=True);shutil.copytree(root/'tools',sandbox/'tools',ignore=shutil.ignore_patterns('__pycache__'));(sandbox/'build').symlink_to(root/'build',target_is_directory=True);(sandbox/'work').mkdir();(sandbox/'experiments').mkdir()
  (sandbox/'work/gf2_recurrence_native_reference_2026-10-06').symlink_to(root/'work/gf2_recurrence_native_reference_2026-10-06',target_is_directory=True)
  (sandbox/'experiments/gf2_recurrence_native_reference_2026-10-06').symlink_to(root/'experiments/gf2_recurrence_native_reference_2026-10-06',target_is_directory=True)
  olddest=sandbox/f'experiments/gf2_recurrence_joint_transfer_2026-10-06/gf2_d{w}';olddest.mkdir(parents=True)
  for n in ('endpoints.json','mapping.json'):shutil.copyfile(original/n,olddest/n)
  swapdest=sandbox/f'experiments/gf2_d{w}_placement_swap_2026-10-06';swapdest.mkdir()
  for n in ('endpoints.json','mapping.json','swapped.place'):shutil.copyfile(swapped/n,swapdest/n)
  prefix='native_seeded' if i==0 else 'selected_reverse';cold='swapped_place_cold' if i==0 else 'fixed_original_cold';ref='swapped_reference_canonical_reload' if i==0 else 'fixed_original_reference_canonical_reload';stages=[]
  for stem in (cold,f'{prefix}_native_import',f'{prefix}_canonical_reload',ref):
   stages.extend([f'{kind}_gf2_d{w}_{stem}.py' for kind in ('trial','verify')])
  for name in stages:
   path=sandbox/'tools'/name;s=path.read_text().replace("root.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07'",'Path('+repr(str(shared))+')');path.write_text(s)
  parent=sandbox/f"experiments/{'gf2_native_seeded_updates' if i==0 else 'gf2_selected_reverse_updates'}_2026-10-06/gf2_d{w}";parent.mkdir(parents=True)
  rounds.append({'sandbox':str(sandbox),'target':str(target/'endpoints.json'),'parent':str(parent),'prefix':prefix,'stages':stages,'source_sha256':{n:sha(sandbox/'tools'/n) for n in stages}})
 cases.append({'width':w,'count':count,'original':str(original/'endpoints.json'),'initial_route':str(root/f'work/gf2_d{w}_fixed_original_cold_2026-10-06/design.route'),'rounds':rounds})
p={'cases':cases,'sources_sha256':{n:sha(root/'tools'/n) for n in ('trial_gf2_capture_ABBA0_certified.py','accepted_route_state.py','certified_accepted_route_state.py','validated_bundle_certificate.py','persistent_rc_context.py','staged_placement_reroute.py','native_route_ledger_import.py')},'policy':'All3 widths,2fixedupdates,onecontext/ownerpercase,1ns/10000/max4, freshcold/candidate/canonical FULL/audits eachround; current canonical certificates reused at selection with no selected fresh reload; stop case on failure and retain allcases.','scope':'Fresh continuous update lifecycle starting at archived authenticated native original route. Includes context/import, stage, native tails/audits, certificateissue, selection/prepare/advance; no fresh selected native reload. Excludes initial original native routing, pack/place/RR/frontend/build and sandboxassembly; not full from-design end-to-end gain.'};(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');allrows=[];env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')}
for case in cases:
 begin=time.monotonic();w=case['width'];t=time.monotonic();ctx=PersistentRCContext(case['original']);owner=CertifiedAcceptedRouteState(import_native_ledger(ctx,case['initial_route']));setup=time.monotonic()-t;rows=[];error=None
 try:
  for i,rd in enumerate(case['rounds']):
   start=time.monotonic();token=owner.token();t=time.monotonic();update=stage_reroute_with_repair(owner.state,rd['target']);stage=time.monotonic()-t;assert owner.token()==token;candidate=update['repair'] or update['incremental'];assert candidate['failure'] is None and candidate['completed_connections']==case['count'];parent=Path(rd['parent']);(parent/'receipt.json').write_text(json.dumps(candidate,indent=2)+'\n')
   # Reuse independent originalXML snapshot checker; retained native paths have no new-search1ns claim.
   src=(root/'tools/verify_tseng_selected_reference_import.py').read_text();check=src[src.index('def check('):src.index('inc=json.loads')].replace('1234',str(case['count']));auditor='''import json
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
'''+f"parent=Path({str(parent)!r});ep=json.loads(Path({rd['target']!r}).read_text());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+"snapshot=json.loads((parent/'receipt.json').read_text());check(snapshot,ep)\n(parent/'verification.json').write_text(json.dumps({'receipt_sha256':sha(parent/'receipt.json'),'accepted_paths_checked':len(snapshot['records'])})+'\\n')\n"
   tool=Path(rd['sandbox'])/'tools/audit_candidate.py';tool.write_text(auditor);stages=[]
   for name in ['audit_candidate.py',*rd['stages']]:
    t=time.monotonic();log=out/f'gf2_d{w}_round{i}_{name}.log'
    with log.open('w') as f:code=subprocess.run(['python3',str(Path(rd['sandbox'])/'tools'/name)],cwd=rd['sandbox'],env=env,stdout=f,stderr=subprocess.STDOUT,timeout=180).returncode
    stages.append({'tool':name,'exit_code':code,'wall_s':time.monotonic()-t,'log_sha256':sha(log)});print(w,i,name,code,flush=True)
    if code:raise RuntimeError(name)
   gate=Path(rd['sandbox'])/f"experiments/gf2_d{w}_{rd['prefix']}_certified_quality_gate_2026-10-06";gate.mkdir();t=time.monotonic();alternatives={}
   for name in rd['stages']:
    if not name.startswith('trial_') or 'canonical_reload' not in name:continue
    label='reference' if 'reference_canonical' in name else 'predicted';canonical=Path(rd['sandbox'])/'experiments'/(name.removeprefix('trial_').removesuffix('.py')+'_2026-10-06');receipt=json.loads((canonical/'receipt.json').read_text());bundle=Path(receipt['results'][0]['cwd'])/'reload';cert=issue(canonical,bundle);cp=gate/(label+'_certificate.json');cp.write_text(json.dumps(cert,indent=2)+'\n');alternatives[label]={'certificate':str(cp),'bundle':str(bundle),'certificate_sha256':sha(cp)}
   prepared=owner.prepare_certified(rd['target'],alternatives,token);q=prepared['selection'];(gate/'selection.json').write_text(json.dumps({**q,'alternatives':alternatives},indent=2)+'\n');owner.advance(prepared);advance=time.monotonic()-t;
   statefile=out/f'gf2_d{w}_accepted{i+1}.json';statefile.write_text(json.dumps({'revision':owner.revision,'records':[owner.state.records[k] for k in sorted(owner.state.records)],'ledger':dict(owner.state.ledger),'scale':ctx.rc.scale,'endpoint_metadata':ctx.endpoint_metadata},indent=2)+'\n');rows.append({'round':i,'revision':owner.revision,'stage_s':stage,'stages':stages,'prepare_advance_s':advance,'round_wall_s':time.monotonic()-start,'selected':q['selected'],'predicted_cpd_ns':q['predicted_cpd_ns'],'reference_cpd_ns':q['reference_cpd_ns'],'snapshot_sha256':sha(statefile),'selection_sha256':sha(gate/'selection.json')})
 except Exception as ex:error=repr(ex)
 row={'width':w,'context_import_s':setup,'rounds':rows,'error':error,'complete':len(rows)==2,'case_wall_s':time.monotonic()-begin};allrows.append(row);(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':allrows,'all_cases_retained':len(allrows)==len(cases)},indent=2)+'\n');print(w,'complete',row['complete'],row['case_wall_s'],error,flush=True)
