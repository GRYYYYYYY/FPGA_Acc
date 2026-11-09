"""Current-state positive-gap whole-NET repair within own first-route wire budget."""
import sys,json,time,shutil,subprocess,re
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from serialize_shared_inventory import serialize
from loaded_native_canonical_reload import canonical_reload
from audit_shared_inventory import audit
from native_route_ledger_import_compact import physical_paths
from source_binding import closure
R=Path(__file__).resolve().parents[2];start=time.perf_counter();o=R/'experiments/native_resume_sequential_global_budget_2026-10-07';o.mkdir(exist_ok=False)
b=R/'experiments/native_resume_sequential_adder_step3_workflow_2026-10-07';d=R/'experiments/native_resume_sequential_adder_conditional_2026-10-07';ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json'
r=json.loads((b/'receipt.json').read_text());c=json.loads((d/'receipt.json').read_text());v=json.loads((d/'verification.json').read_text());assert v['receipt_sha256']==sha(d/'receipt.json') and not v['simultaneous_replacement_overflow']
files=[b/'receipt.json',b/'exchange/receipt.json',d/'receipt.json',d/'verification.json',d/'wire_comparison.json',ep]+list((b/'exchange_canonical').glob('*'))
inputs={str(p):sha(p) for p in files if p.is_file()};sources=closure([Path(__file__)])
budget=next(s['native']['wirelength'] for s in r['stages'] if s['stage']=='first');wire=r['wirelength'];wire_rows={x['net']:x for x in json.loads((d/'wire_comparison.json').read_text())['rows']}
policy='Own final worst-path NETs only, all sinks; positive current additive gap; consider in own report order, no sink delay increase; replace entire conditioned tree only if current global wire remains <= own first native route wire. Freeze unselected NETs. No cold inputs; one native FULL/STA diagnostic with no retry or tuning.'
(o/'protocol.json').write_text(json.dumps(dict(inputs=inputs,sources=sources,policy=policy,budget=budget,initial_wire=wire,scope='Prepared current diagnostic and candidate inputs; fresh context initialization/materialization/native proofs paid here; prior query and prior full sequence costs are excluded and cannot support net gain.'),indent=2)+'\n')
ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',o/'context');inv=SharedRRInventory(ctx)
records=json.loads((b/'exchange/receipt.json').read_text())['records'];byid={x['connection_id']:x for x in records};chosen=[]
for row in c['rows']:
 delta=wire_rows[row['net']]['wire_delta']
 if row['positive_current_gap_connections']==0 or wire+delta>budget:continue
 assert all(x['conditional_integer']<=x['current_path_additive_integer'] for x in row['records'])
 for x in row['records']:byid[x['query']['connection_id']]['answer']['physical_edge_ids']=x['physical_edge_ids']
 wire+=delta;chosen.append(row['net'])
assert chosen
(o/'candidate.json').write_text(json.dumps(dict(records=records,selected_nets=chosen,expected_wire=wire,budget=budget),indent=2)+'\n')
w=o/'native';w.mkdir()
for f in ('design.blif','design.net','design.place'):shutil.copyfile(b/'exchange_canonical'/f,w/f)
text,_=serialize(dict(records=records),ep,b/'exchange_canonical/identity.jsonl',w/'design.place',inv);(w/'design.route').write_text(text)
norm=lambda p:{n:Counter(ps) for n,ps in physical_paths(p).items() if ps}
expected_paths=norm(w/'design.route');audit_before=audit(ctx.graph,w/'design.route',inv);assert audit_before['overflow_units']==0
cmd=r['canonical']['command'];env=__import__('os').environ.copy();env={k:v for k,v in env.items() if not k.startswith('ROUTECAST_')}
with (w/'native.log').open('w') as stream:code=subprocess.run(cmd,cwd=w,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=120).returncode
log=(w/'native.log').read_text();assert code==0 and 'VPR succeeded' in log
cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);nativewire=int(re.findall(r'Total wirelength:\s*(\d+)',log)[-1]);assert nativewire==wire
shutil.copyfile(w/'design.route',w/'output.route');routecmd=list(cmd);routecmd[routecmd.index('--analysis')]='--route'
meta=dict(width=32,decision='R',command=routecmd,cpd_ns=cpd,files={str(p):sha(p) for p in w.iterdir() if p.is_file()})
proof=canonical_reload(meta,w,o/'canonical');assert proof['fixups']==proof['mismatches']==0 and norm(o/'canonical/design.route')==expected_paths
a=audit(ctx.graph,o/'canonical/design.route',inv);assert a['overflow_units']==0
target=json.loads(ep.read_text());expected=Counter((target['net_names'][str(q['net_id'])],q['source'],q['sink']) for q in target['connections']);actual=Counter((n,p[0][0],p[-1][0]) for n,ps in expected_paths.items() for p,count in ps.items() for _ in range(count));assert actual==expected
assert all(sha(p)==h for p,h in {**inputs,**sources}.items())
result=dict(protocol_sha256=sha(o/'protocol.json'),selected_nets=chosen,budget=budget,previous_cpd_ns=float(r['cpd_ns']),cpd_ns=cpd,previous_wire=r['wirelength'],wirelength=nativewire,diagnostic_elapsed_seconds=time.perf_counter()-start,all_endpoints_match=True,zero_overflow=True,canonical=proof,files={str(p):sha(p) for p in o.rglob('*') if p.is_file()},scope='Native legal timing diagnostic; previous query and pipeline costs excluded. No cold quality or complete net-gain claim.')
(o/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('selected_nets','previous_cpd_ns','cpd_ns','previous_wire','wirelength','diagnostic_elapsed_seconds')}),flush=True)
