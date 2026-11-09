"""Isolated fixed-route native analysis under an explicit nonzero clock period."""
import hashlib,json,re,shutil,subprocess
from pathlib import Path

P=Path('work/native_joint_budget_net_repair_v2_20261016/diffeq/initial/native_validation')
D=Path('work/native_nonzero_setup_constraint_probe_v3_20261016').resolve();D.mkdir(exist_ok=False)
qfile=P/'validation.json';q=json.loads(qfile.read_text())
for name in ['circuit.net','circuit.place','native.route']:shutil.copy2(P/name,D/name)
sdc=D/'clock10.sdc';sdc.write_text('create_clock -period 10 pclk\n')
command=q['command']+['--sdc_file',str(sdc)]
inputs=[qfile,sdc,*[D/name for name in ['circuit.net','circuit.place','native.route']],Path(__file__)]
(D/'launch.json').write_text(json.dumps(dict(command=command,cwd=str(D),source_sha256={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},scope='One fixed diffeq route, explicit10ns clock, diagnostic only. Original baseline not changed.'),indent=2)+'\n')
with (D/'analysis.stdout').open('x') as stdout,(D/'analysis.stderr').open('x') as stderr:rc=subprocess.run(command,cwd=D,stdout=stdout,stderr=stderr).returncode
assert rc==0,rc
text=(D/'analysis.stdout').read_text();cpd=re.findall(r'Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns',text)
assert cpd
(D/'result.json').write_text(json.dumps(dict(status='fixed_route_nonzero_clock_native_analysis_complete',returncode=rc,native_cpd_ns=cpd[-1],report_sha256=hashlib.sha256((D/'report_timing.setup.rpt').read_bytes()).hexdigest(),research_complete=False),indent=2)+'\n');print(cpd[-1])
