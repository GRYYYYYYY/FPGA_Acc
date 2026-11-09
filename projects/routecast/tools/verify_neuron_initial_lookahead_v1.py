"""Independent exact explicit-pin accounting for lookahead delay capture."""
import json,math,struct,sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main(root):
 root=Path(root);old=R/'experiments/neuron_initial_timing_snapshot_v1_2026-10-17';work=root/'work'
 assert json.loads((root/'verification.json').read_text())['all_pass']
 assert json.loads((old/'terminal.json').read_text())['exit_status']==0
 for name in ['criticality.tsv','timing.tsv']:assert sha(work/name)==sha(old/'work'/name)
 manifest=json.loads((R/'experiments/titan23_neuron_native_inputs_v1_2026-10-13/criticality/initial_connection_criticalities.json').read_text())
 expected={(x['net'],x['local_sink_pin']):x['global_pin'] for x in manifest};seen=set();values=[]
 with (work/'lookahead_delay.tsv').open() as f:
  for seq,line in enumerate(f,1):
   p=line.rstrip('\n').split('\t');assert len(p)==7 and p[0]=='D' and int(p[1])==seq
   key=(int(p[2]),int(p[4]));assert key in expected and key not in seen and expected[key]==int(p[3]);seen.add(key)
   value=struct.unpack('<f',int(p[6],16).to_bytes(4,'little'))[0]
   assert math.isfinite(value) and struct.pack('<f',float(p[5]))==struct.pack('<f',value)
   values.append(value)
 assert seen==set(expected) and len(values)==77106
 assert 'ROUTECAST INITIAL LOOKAHEAD DELAY SNAPSHOT 77106 after_original_init=1' in (work/'native.log').read_text()
 bindings={str(p):sha(p) for p in [Path(__file__).resolve(),root/'verification.json',work/'lookahead_delay.tsv',work/'criticality.tsv',work/'timing.tsv',old/'work/criticality.tsv',old/'work/timing.tsv']}
 result=dict(all_pass=True,all_nonignored_explicit_connections=77106,prior_criticality_and_atom_timing_bytes_identical=True,all_finite_float32_roundtrips=True,minimum_seconds=min(values),maximum_seconds=max(values),zero_delays=sum(v==0 for v in values),negative_delays=sum(v<0 for v in values),bindings=bindings,scope='Post-original-initializer lookahead delays; not routed Tdel, proxy floor, legal timing budgets or predictive quality.',promoted=False)
 (root/'lookahead_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='bindings'},indent=2))
if __name__=='__main__':main(sys.argv[1])
