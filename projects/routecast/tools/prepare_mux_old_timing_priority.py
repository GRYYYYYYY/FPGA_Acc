"""Map native timing paths through BLIF connectivity and packed atom ownership."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_old_timing_priority_2026-10-06';out.mkdir();rows=[];bindings={}
for width in (8,16,32):
 for mode in ('old',):
  work=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{width}_c128'
  blif=work/'design.blif';net=work/'design.net';table=ROOT/f'experiments/mux_native_identity_contract_2026-10-06/w{width}/identity.jsonl';report=work/'report_timing.setup.rpt'
  for p in (blif,net,table,report):bindings[str(p)]=sha(p)
  text=blif.read_text().replace('\\\n',' ');logic={}
  for line in text.splitlines():
   tokens=line.split()
   if tokens and tokens[0]=='.names':
    assert tokens[-1]not in logic;logic[tokens[-1]]=tokens[1:-1]
  atoms={}
  for cluster in ET.parse(net).getroot().findall('block'):
   for b in cluster.iter('block'):
    name=b.get('name')
    if name!='open' and not b.findall('block'):
     assert name not in atoms;atoms[name]=cluster.get('name')
  identities={r['name']:r for r in map(json.loads,table.read_text().splitlines())};paths=[]
  for number,body in re.findall(r'#Path (\d+)\n(.*?)(?=\n#Path |\Z)',report.read_text(),re.S):
   points=[]
   for line in body.splitlines():
    m=re.match(r'^(\S+)\.(inpad|outpad|in|out)\[(\d+)\]\s+\([^)]*\)\s+([0-9.]+)\s+([0-9.]+)\s*$',line)
    if m:points.append((m[1],m[2],int(m[3]),float(m[4]),float(m[5])))
   signal=None;source_atom=None;segments=[]
   for atom,port,bit,increment,arrival in points:
    assert atom in atoms
    if port=='inpad':signal=atom;source_atom=atom
    elif port=='out':assert atom in logic;signal=atom;source_atom=atom
    else:
     assert signal is not None
     if port=='in':assert signal in logic[atom]
     else:assert port=='outpad' and atom=='out:'+signal
     src,dst=atoms[source_atom],atoms[atom];internal=src==dst;native=None
     if not internal:
      native=identities[signal];assert native['pins'][0]['block']==src
      sinks=[p for p in native['pins'][1:]if p['block']==dst];assert len(sinks)==1
      native=dict(net_id=native['net_id'],sink_pin_index=sinks[0]['index'],source_cluster=src,sink_cluster=dst,sink_site_class=[sinks[0][k]for k in ('x','y','layer','class')])
     segments.append(dict(atom_net=signal,source_atom=source_atom,sink_atom=atom,report_sink_port=port,report_sink_bit=bit,increment_ns=increment,internal=internal,native=native))
   assert segments;paths.append(dict(rank=int(number),segments=segments))
  assert len(paths)==min(100,width*8)
  result=dict(width=width,mode=mode,paths=paths);(out/f'w{width}_{mode}.json').write_text(json.dumps(result,indent=2)+'\n');rows.append(dict(width=width,mode=mode,paths=len(paths),segments=sum(len(p['segments'])for p in paths),internal_segments=sum(s['internal']for p in paths for s in p['segments'])))
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,scope='BLIF signal connectivity and packed leaf ownership; unique native NET/sink-cluster binding. Report atom bit recorded, not assumed BLIF pin permutation. Three-decimal timing; retrospective mapping, not deployable pre-update criticality.'),indent=2)+'\n');print(rows)

for width in (8,16,32):
 ep_path=ROOT/f'experiments/mux_live_placement_updates_2026-10-06/w{width}/original_endpoints.json';ep=json.loads(ep_path.read_text());names={v:int(k)for k,v in ep['net_names'].items()};rank={}
 for path in json.loads((out/f'w{width}_old.json').read_text())['paths']:
  for segment in path['segments']:
   if not segment['internal']:
    name=segment['atom_net'];assert name in names;rank[name]=min(rank.get(name,1000000),path['rank'])
 order=sorted(ep['connections'],key=lambda q:(rank.get(ep['net_names'][str(q['net_id'])],1000000),q['net_id'],q['connection_id']))
 (out/f'w{width}_priority.json').write_text(json.dumps(dict(endpoint_sha256=sha(ep_path),net_rank_by_name=rank,connection_order=[q['connection_id']for q in order],policy='WholeNET priority by minimum old report path rank; unreportedNETs last; NETid/CID ties. No moved reference or candidate inputs.'),indent=2)+'\n')
