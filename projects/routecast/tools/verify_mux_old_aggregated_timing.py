"""Verify old replay paths and rounded report component accounting."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from native_route_ledger_import import physical_paths
from stream_native_route_audit import audit
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_old_aggregated_timing_2026-10-06';r=json.loads((out/'receipt.json').read_text());assert all(sha(p)==h for p,h in r['inputs'].items());rows=[]
for row in r['rows']:
 w=row['width'];assert row['exit_code']==0 and row['mismatches']==row['fixups']==0;assert all(sha(p)==h for p,h in row['files'].items());work=out/f'w{w}/canonical';source=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128';paths=lambda p:{n:sorted(v)for n,v in physical_paths(p).items()if v};assert paths(work/'design.route')==paths(source/'design.route');a=audit(source/'rr_graph.xml',work/'design.route');assert a['overflow_units']==0 and len(a['connections'])=={8:466,16:936,32:1929}[w];reports=[]
 for rank,body in re.findall(r'#Path (\d+)\n(.*?)(?=\n#Path |\Z)',(work/'report_timing.setup.rpt').read_text(),re.S):
  arrival=float(re.search(r'^data arrival time\s+([0-9.]+)',body,re.M)[1]);components=[]
  for line in body.splitlines():
   m=re.match(r'^\|\s+\((.*?)\)\s+([0-9.]+)\s+([0-9.]+)\s*$',line)
   if m:components.append((m[1],float(m[2])))
  assert components;assert abs(sum(v for _,v in components)-arrival)<=(len(components)+1)*.0005+1e-12
  totals={kind:sum(v for name,v in components if (name=='inter-block routing'if kind=='inter'else name.startswith('intra ')if kind=='intra'else name.startswith('primitive ')))for kind in ('inter','intra','primitive')};assert abs(sum(totals.values())-arrival)<=(len(components)+1)*.0005+1e-12;reports.append(dict(rank=int(rank),arrival_ns=arrival,rounded_components_ns=totals))
 assert len(reports)==min(100,w*8);rows.append(dict(width=w,cpd_ns=row['cpd_ns'],connections_checked=len(a['connections']),report_paths=reports))
(out/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Original FULL/STA zero-fixup,3331 physicalpaths preserved/audited; rounded report component totals checked. Not yet perconnection RR versus native inter-block comparison.'),indent=2)+'\n');print([(x['width'],x['cpd_ns'])for x in rows])
