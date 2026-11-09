"""Fresh TSV floats, original XML terminal classes and current native pin identity."""
from pathlib import Path
import json,hashlib,struct,math,xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def bits(s):return struct.pack('<f',float(s))
def main():
 O=R/'experiments/mmc_current_initial_timing_snapshots_v2_2026-10-19';terminal=O/'terminal.json';assert json.loads(terminal.read_text())['status']=='ALL3_CURRENT_INPUT_INITIAL_TIMING_SNAPSHOT_ONLY_PASS_INDEPENDENT_ADMISSION_PENDING';assert not (O/'independent_verification_v1.json').exists();protocol=O/'execution_protocol.json';doc=json.loads(protocol.read_text());bindings={str(p):sha(p) for p in [terminal,protocol,Path(__file__).resolve()]}
 for p,h in doc['bindings'].items():assert sha(p)==h
 graph=Path(doc['jobs'][0]['argv'][doc['jobs'][0]['argv'].index('--read_rr_graph')+1]);classes={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   if e.get('type') in ['SOURCE','SINK']:
    loc=e.find('loc');key=(e.get('type'),int(loc.get('xlow')),int(loc.get('ylow')),int(loc.get('layer','0')),int(loc.get('ptc')));assert key not in classes;classes[key]=int(e.get('id'))
   stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 oldroot=R/'experiments/mmc_native_initial_criticality_snapshot_v2_2026-10-10';old_file=oldroot/'initial_connection_criticalities.json';old={x['connection_id']:x for x in json.loads(old_file.read_text())};old_admission=json.loads((oldroot/'verification.json').read_text());assert sha(old_file)==old_admission['bindings'][str(old_file)];arch=Path(doc['jobs'][0]['argv'][1]);assert sha(arch)==old_admission['bindings'][str(arch)];rows=[]
 for plan in doc['jobs']:
  d=Path(plan['cwd']);receipt=d/'capture_receipt.json';capture=json.loads(receipt.read_text());assert capture['row']['status']=='SNAPSHOT_ONLY_EXIT0_NO_ROUTE_RAW_PIN_VALIDATION_PASS'
  for p,h in capture['bindings'].items():assert sha(p)==h
  ep=Path(plan['endpoint']);meta=json.loads(ep.read_text());id_file=Path(meta['inputs']['native_identity']['path']);assert sha(id_file)==meta['inputs']['native_identity']['sha256'];identity={}
  for line in id_file.open():
   x=json.loads(line);assert x['net_id'] not in identity and meta['net_names'][str(x['net_id'])]==x['name'];identity[x['net_id']]=x
  observed={};ignored=0
  for sequence,line in enumerate((d/'criticality.tsv').open(),1):
   w=line.split();assert len(w)==10 and w[0]=='C' and int(w[1])==sequence;net=int(w[2]);pin=int(w[4]);key=net,pin;assert key not in observed and 1<=pin<len(identity[net]['pins']) and w[8]==str(int(identity[net]['ignored']));value=struct.unpack('<f',bits(w[5]))[0];maximum=struct.unpack('<f',bits(w[6]))[0];assert math.isfinite(value) and 0<=value<=maximum<=1 and math.isfinite(float(w[7]));observed[key]=w;ignored+=int(w[8])
  assert len(observed)==119473==sum(len(x['pins'])-1 for x in identity.values()) and ignored==3901
  data=d/'initial_connection_criticalities.json';records=json.loads(data.read_text());queries={q['connection_id']:q for q in meta['connections']};assert len(records)==len(queries)==115572;seen=set();keys=set();changed=0
  for record in records:
   cid=record['connection_id'];assert cid not in seen;seen.add(cid);q=queries[cid];net=q['net_id'];pin=record['local_sink_pin'];key=net,pin;assert key not in keys;keys.add(key);w=observed[key];assert w[8]=='0';assert record['net']==net and record['global_pin']==int(w[3])==old[cid]['global_pin'] and pin==old[cid]['local_sink_pin'];assert (record['source_rr'],record['target_rr'])==(q['source'],q['sink'])
   for field,index in [('criticality_float32_text',5),('maximum_text',6),('exponent_text',7)]:assert bits(record[field])==bits(w[index])
   physical=identity[net]['pins']
   for kind,info,rr in [('SOURCE',physical[0],q['source']),('SINK',physical[pin],q['sink'])]:assert classes[kind,info['x'],info['y'],info.get('layer',0),info['class']]==rr
   changed+=bits(record['criticality_float32_text'])!=bits(old[cid]['criticality_float32_text'])
  assert seen==set(queries) and keys=={k for k,w in observed.items() if w[8]=='0'};assert not list(d.glob('*.route'));text=(d/'native.log').read_text();assert 'ROUTECAST INITIAL CRITICALITY SNAPSHOT 119473' in text and 'Successfully routed after' not in text
  rows.append({'case':plan['case'],'all_sink_pins':119473,'physical_connections':115572,'ignored_pins':ignored,'current_XML_terminal_class_identities_verified':True,'fresh_float32_values_verified':True,'changed_float32_values_vs_archived_old':changed,'no_route_generated':True})
  for f in [ep,id_file,receipt,data,d/'criticality.tsv',d/'native.log',d/'design.place',d/'design.net',d/'design.blif']:bindings[str(f)]=sha(f)
  print('CURRENT_TIMING_INDEPENDENT_PASS',plan['case'],'changed_old',changed,flush=True)
 for f in [graph,arch,old_file,oldroot/'verification.json']:bindings[str(f)]=sha(f)
 (O/'independent_verification_v1.json').write_text(json.dumps({'status':'ALL3_CURRENT_INITIAL_TIMING_FLOAT32_PINS_XML_ENDPOINTS_NO_ROUTE_PASS','rows':rows,'bindings':bindings,'scope':'Fresh initialized timing proxy only; not final route, actual setup closure, calibrated probabilities or predictor quality/gain.'},indent=2)+'\n')
if __name__=='__main__':main()
