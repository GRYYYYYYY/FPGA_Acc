"""Same logical critical paths: report increments, routed RR delays and frozen floors."""
import json,re,sys,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
from source_binding import closure
ROOT=Path(__file__).resolve().parents[2];out=ROOT/'experiments/native_resume_sequential_timing_diagnosis_2026-10-07';out.mkdir(exist_ok=False);vf=ROOT/'experiments/native_resume_sequential_adder_2026-10-07/verified/verification.json';v=json.loads(vf.read_text());assert all(sha(f)==h for f,h in v['bindings'].items());ep=ROOT/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_2_endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(ep);loc={int(n.get('id')):tuple(int(n.find('loc').get(k,'0')) for k in ('xlow','ylow','layer','ptc')) for n in nodes};slot={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};bindings={str(p):sha(p) for p in (vf,graph,ep)};bindings.update(closure([Path(__file__)]));rows=[]
point=re.compile(r'^(\S+)\.(inpad|outpad|in|out|D|Q|clk)\[(\d+)\]\s+\([^)]*\)(?:\s+\[[^]]*\])?\s+([0-9.]+)\s+([0-9.]+)\s*$')
for i in (2,3):
 data={}
 for mode in ('workflow','cold'):
  base=ROOT/f'experiments/native_resume_sequential_adder_step{i}_{mode}_2026-10-07';base=base/('exchange_canonical' if mode=='workflow' else 'canonical');report=base/'report_timing.setup.rpt';paths=physical_paths(base/'design.route');identity={x['name']:x for x in map(json.loads,(base/'identity.jsonl').read_text().splitlines())};logic={};latches={}
  for line in (base/'design.blif').read_text().replace('\\\n',' ').splitlines():
   p=line.split()
   if p and p[0]=='.names':logic[p[-1]]=p[1:-1]
   if p and p[0]=='.latch':latches[p[2]]=p[1]
  atoms={}
  for cluster in ET.parse(base/'design.net').getroot().findall('block'):
   for atom in cluster.iter('block'):
    if atom.get('name')!='open' and not atom.findall('block'):atoms[atom.get('name')]=cluster.get('name')
  reports=[]
  for body in report.read_text().split('#Path ')[1:]:
   endpoint=re.search(r'^Endpoint\s*:\s*(\S+)',body,re.M).group(1);segments=[];signal=None
   for line in body.splitlines():
    m=point.match(line)
    if not m:continue
    atom,port,bit,inc,path=m.groups();bit=int(bit)
    if port in ('Q','out','inpad'):signal=atom;continue
    if port=='clk':continue
    if port not in ('in','D','outpad') or signal is None:continue
    expected=logic[atom][bit] if port=='in' else latches[atom] if port=='D' else atom.removeprefix('out:');assert expected==signal,(expected,signal,atom)
    src,dst=atoms[signal],atoms[atom];row=dict(net=signal,sink_atom=atom,port=port,bit=bit,report_increment_ns=inc,internal=src==dst)
    if src!=dst:
     pins=[p for p in identity[signal]['pins'][1:] if p['block']==dst];assert len(pins)==1;pin=pins[0];site=tuple(pin[k] for k in ('x','y','layer','class'));ps=[p for p in paths[signal] if loc[p[-1][0]]==site];assert len(ps)==1;branch=ps[0];edges=[f['edge_ids'][slot[u,z,sw]] for (u,_),(z,sw) in zip(branch,branch[1:])];delay=F(rc.path(branch[0][0],branch[-1][0],edges),rc.scale)*10**9;row.update(source=branch[0][0],sink=branch[-1][0],additive_rr_ns=str(delay),physical_path=branch)
    segments.append(row)
   reports.append(dict(endpoint=endpoint,segments=segments))
  data[mode]=reports
  for file in (report,base/'design.route',base/'design.net',base/'design.blif',base/'identity.jsonl'):bindings[str(file)]=sha(file)
 # Compare each workflow first path to same logical endpoint/segment sequence in cold.
 own=data['workflow'][0];keys=lambda r:[(s['net'],s['sink_atom'],s['port'],s['bit']) for s in r['segments']];matching=[r for r in data['cold'] if r['endpoint']==own['endpoint'] and keys(r)==keys(own)];assert matching;other=matching[0];comparisons=[]
 floors=ROOT/f'experiments/native_resume_sequential_adder_2026-10-07/floor_context/epoch_{i}/receipt.json';floor=json.loads(floors.read_text());minima={(a['query']['source'],a['query']['sink']):a['minimum_integer'] for a in floor['answers']};bindings[str(floors)]=sha(floors)
 for a,b in zip(own['segments'],other['segments']):
  row=dict(net=a['net'],sink_atom=a['sink_atom'],internal=a['internal'],report_increment_pair=[a['report_increment_ns'],b['report_increment_ns']],report_delta_ns=str(F(a['report_increment_ns'])-F(b['report_increment_ns'])))
  assert a['internal']==b['internal']
  if not a['internal']:
   assert (a['source'],a['sink'])==(b['source'],b['sink']);lower=F(minima[a['source'],a['sink']],rc.scale)*10**9;row.update(additive_rr_pair=[a['additive_rr_ns'],b['additive_rr_ns']],additive_rr_delta_ns=str(F(a['additive_rr_ns'])-F(b['additive_rr_ns'])),unconditional_floor_ns=str(lower),own_additive_gap_ns=str(F(a['additive_rr_ns'])-lower),physical_paths_equal=a['physical_path']==b['physical_path'],source=a['source'],sink=a['sink'])
  comparisons.append(row)
 rows.append(dict(epoch=i,own_worst_endpoint=own['endpoint'],comparisons=comparisons));print(i,[(x['net'],x['report_delta_ns'],x.get('additive_rr_delta_ns')) for x in comparisons],flush=True)
assert all(sha(p)==h for p,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Same logical setup path compared in original-native printed reports (3decimalns precision). Exact original RR additive model and unconditional floors; not native route-tree/intra-cluster delay decomposition or demand-conditioned optimum. Cold comparison offline only.'),indent=2)+'\n')
