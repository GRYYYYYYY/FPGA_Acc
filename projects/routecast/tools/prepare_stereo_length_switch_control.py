"""Freeze and prepare existing length-switch control on complete Stereo cohort."""
import json,time,subprocess,shutil,random
from pathlib import Path
from types import SimpleNamespace
import xml.etree.ElementTree as ET
from prepared_csr import read,U64
from pre_route_endpoints import sha
from semantic_sketch import Sketch

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'matched_length_switch_control';out.mkdir();(out/'source').mkdir();start=time.monotonic()
 parent=b/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';p=json.loads((parent/'protocol.json').read_text());source=b/'streaming_csr_class_cache_v3/csr';graph=p['inputs']['graph'];endpoints=p['inputs']['endpoints'];names=['prepare_stereo_length_switch_control.py','prepare_length_switch_csr.py','semantic_sketch.py','prepared_csr.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 assert sha(graph['path'])==graph['sha256'] and sha(endpoints['path'])==endpoints['sha256']
 protocol={'inputs':{'graph':graph,'endpoints':endpoints},'sources':sources,'source_csr_manifest_sha256':sha(source/'manifest.json'),'frontend_protocol_sha256':p['frontend_protocol_sha256'],'frontend_revision_scope':p['frontend_revision_scope'],'policy_sha256':p['policy_sha256'],'method':'rr_length_switch existing uncalibrated control; no tuning','cost':'semantic_sketch.Sketch: 1 + 256 * destination channel span + switch delay ps ROUND_HALF_UP','order':'ascending net, CID, distinct sink ID','scope':'matched whole Stereo cohort, existing cost rule; no geometry pruning, native labels or timing calibration; not pristine unseen-family certificate'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
 result=subprocess.run(['python3','-u','tools/prepare_length_switch_csr.py','--prepared',str(source),'--graph',graph['path'],'--output',str(out/'csr')]);assert result.returncode==0
 m,f=read(out/'csr',graph['sha256']);original=json.loads((source/'manifest.json').read_text())
 assert all(v['sha256']==original['files'][n]['sha256'] for n,v in m['files'].items() if n!='costs')
 switches={}
 for event,e in ET.iterparse(graph['path'],events=('end',)):
  if e.tag=='switch':switches[int(e.get('id'))]=ET.tostring(e,encoding='unicode')
  if e.tag=='switches':break
 rng=random.Random(3);samples=rng.sample(range(m['edges']),1000)
 for i in samples:
  d=f['dest_ranks'][i];sid=f['switch_ids'][i];loc=tuple((k,str(f[k][d])) for k in ('xlow','xhigh','ylow','yhigh'))
  kind={0:'SOURCE',1:'SINK',2:'OPIN',3:'IPIN',4:'CHANX',5:'CHANY'}[f['types'][d]]
  fixture=SimpleNamespace(nodes={0:SimpleNamespace(type='SOURCE',location=()),1:SimpleNamespace(type=kind,location=loc)},edges=[SimpleNamespace(source=0,sink=1,switch_id=sid)],switches={sid:switches[sid]})
  oracle=Sketch(fixture,'rr_length_switch',2);expected=oracle.costs[0] if f['capacities'][d]>0 else U64;assert f['costs'][i]==expected
 assert all(sha(Path('tools')/n)==h for n,h in sources.items()) and sha(graph['path'])==graph['sha256'] and sha(endpoints['path'])==endpoints['sha256']
 receipt={'nodes':m['nodes'],'edges':m['edges'],'manifest_sha256':sha(out/'csr/manifest.json'),'protocol_sha256':sha(out/'protocol.json'),'all_topology_metadata_payload_hashes_identical':True,'sampled_reference_Sketch_costs':1000,'sample_seed':3,'wall_s':time.monotonic()-start,'scope':'matched control cost preparation only; full replay and physical audit/evaluation still required'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
