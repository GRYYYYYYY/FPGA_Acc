"""Bounded local placement exposure audit; never inspect route label contents."""
import pathlib,json,hashlib,sys,subprocess,re
R=pathlib.Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import placements
sha=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def signature(path,netsha):
 rows=placements(path,netsha);body=[(name,*rows[name][:4]) for name in sorted(rows)]
 return hashlib.sha256(json.dumps(body,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
def main():
 out=R/'experiments/mmc_prospective_swap_input_exposure_v1_2026-10-19';out.mkdir();base=R/'experiments/prospective_layout_swap_native_placement_v1_2026-10-18';net=base/'episode_01/design.net';netsha=sha(net);bindings={str(p):sha(p) for p in [pathlib.Path(__file__).resolve(),R/'tools/pre_route_endpoints.py',net,base/'receipt.json',R/'experiments/prospective_layout_swap_native_pin_identity_v1_2026-10-18/verification.json']};candidates=[]
 for i in range(1,4):
  p=base/f'episode_{i:02}/design.place';bindings[str(p)]=sha(p);candidates.append(dict(episode=i,placement=str(p),placement_sha256=sha(p),coordinate_signature=signature(p,netsha)))
 old=[]
 for case in ['case_01','case_02','case_03']:
  ep=R/f'experiments/mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';d=json.loads(ep.read_text());place=pathlib.Path(d['inputs']['place']['path']);assert d['inputs']['net']['sha256']==netsha;old.append(dict(case=case,coordinate_signature=signature(place,netsha)));bindings[str(ep)]=sha(ep)
 command=['rg','--files','--hidden','--no-ignore','experiments','-g','*.place'];listing=subprocess.run(command,cwd=R,text=True,capture_output=True,check=True);paths=listing.stdout.splitlines();(out/'enumerated_place_paths.json').write_text(json.dumps(paths,indent=2)+'\n');wanted={x['coordinate_signature'] for x in candidates};aliases={k:[] for k in wanted};eligible=0;errors=[];header_unknown=0
 for text in paths:
  p=R/text
  try:
   with p.open() as f:head=''.join(next(f,'') for _ in range(8))
   match=re.search(r'Netlist_ID:\s*SHA256:([0-9a-f]{64})',head)
   if not match:header_unknown+=1;continue
   if match[1]!=netsha:continue
   eligible+=1;s=signature(p,netsha)
   if s in wanted:aliases[s].append({'placement':str(p),'route_artifacts_same_directory':[str(q) for q in sorted(p.parent.glob('*.route')) if q.is_file()]})
  except (OSError,ValueError) as e:errors.append({'path':str(p),'error':str(e)})
 for candidate in candidates:
  s=candidate['coordinate_signature'];candidate['matches_current_exposed_cases']=[x['case'] for x in old if x['coordinate_signature']==s];candidate['local_aliases']=aliases[s];candidate['route_artifact_near_matching_layout']=any(x['route_artifacts_same_directory'] for x in aliases[s])
 result=dict(status='bounded_local_same_packed_epoch_layout_exposure_audit_complete',bindings=bindings,source_net_sha256=netsha,enumerated_place_files=len(paths),matching_net_epoch_files=eligible,unclassified_header_files=header_unknown,parse_errors=errors,current_exposed_cases=old,candidates=candidates,route_label_contents_read=False,new_route_jobs=0,strict_unseen_family_admitted=False,scope='Canonical coordinates ignore header formatting and block row IDs but require exact packed-net hash. Presence of a nearby route artifact is conservative exposure evidence, not proof of its execution. Absence across enumerated local files does not certify external/deleted history, unseen families or future prediction quality.')
 (out/'review.json').write_text(json.dumps(result,indent=2)+'\n');print('scanned',len(paths),'same_epoch',eligible,'errors',len(errors),flush=True)
 for x in candidates:print('episode',x['episode'],'old_cases',x['matches_current_exposed_cases'],'aliases',len(x['local_aliases']),'near_route',x['route_artifact_near_matching_layout'],flush=True)
if __name__=='__main__':main()
