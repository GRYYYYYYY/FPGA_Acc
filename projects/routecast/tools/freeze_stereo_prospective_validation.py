"""Freeze local sourced inputs for prospective validation before predictor runs."""
import json,hashlib,shutil,time
from pathlib import Path
import xml.etree.ElementTree as ET

def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''):h.update(chunk)
 return h.hexdigest()
root=Path('experiments/stereo_prospective_validation_2026-10-05')
if root.exists():raise ValueError('fresh directory required')
root.mkdir();(root/'inputs').mkdir();(root/'source').mkdir();start=time.monotonic()
origin=Path('../tileplace/experiments/titan23_stereo_vision_input_capture_2026-09-02.json');d=json.loads(origin.read_text());bindings={};private={}
for key in ('architecture','circuit','packed_netlist','placement','sdc'):
 info=d['source_inputs'][key];p=Path(info['path']);assert sha(p)==info['sha256'],key
 dest=root/'inputs'/p.name;shutil.copyfile(p,dest);assert sha(dest)==info['sha256']
 bindings[str(p)]=info['sha256'];private[key]={'path':str(dest.resolve()),'sha256':info['sha256']}
graph=d['rr_graph'];assert sha(graph['path'])==graph['sha256'];bindings[graph['path']]=graph['sha256'];private['graph']={'path':graph['path'],'sha256':graph['sha256'],'access':'read-only shared snapshot; no conversion writes'}
sources={}
for p in Path('tools').glob('*.py'):
 dest=root/'source'/p.name;shutil.copyfile(p,dest);sources[p.name]=sha(dest)
arch=ET.parse(private['architecture']['path']).getroot()
switches=[dict(x.attrib) for x in arch.findall('./switchlist/switch')]
segments=[dict(x.attrib) for x in arch.findall('./segmentlist/segment')]
protocol={'case':'Titan23/stereo_vision','source_record':{'path':str(origin.resolve()),'sha256':sha(origin)},'inputs':private,'shared_input_bindings':bindings,'frozen_sources':sources,'architecture_switches':switches,'architecture_segments':segments,'selection':'local sourced Titan23 input selected before any RouteCast predictor/evaluator run on this case','family_status':'prospective cross-architecture candidate; absence in current named RouteCast tools/README/plan is not a full independent family certificate','generator_excludes':['native route','native timing labels','other-project optimized placements'],'policy':{'seed':3,'channel_width':300,'workers':1,'fanout_threshold':64,'label_cap':100000,'target_order':'ascending net/CID','budget':'original predictor-path exact buffered RC, never native route budget','pin_policy':'fixed SOURCE/current or unused explicit full-equivalent target','commit':'strict span improvement, zero capacity overuse, legal whole tree, atomic update'},'required_gates':['pre-route endpoint/constant/clock accounting','architecture and RC model compatibility','frozen unmodified predictor transfer','independent native endpoint/occupancy evaluation','hotspot rank/precision/recall and failure/RRR/WL/CPD','complete cold conversion+feedback+exact routing time'],'status':'inputs_frozen; no predictor or native job submitted','scope':'Local source/hash provenance; prospective validation only, not achieved holdout/generalization or QoR evidence'}
(root/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');(root/'receipt.json').write_text(json.dumps({'all_selected_input_hashes_verified':True,'protocol_sha256':sha(root/'protocol.json'),'source_count':len(sources),'wall_s':time.monotonic()-start,'no_predictor_run':True},indent=2)+'\n');print((root/'receipt.json').read_text())
