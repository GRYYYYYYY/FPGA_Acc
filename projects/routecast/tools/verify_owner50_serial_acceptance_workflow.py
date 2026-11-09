"""All12 selected states, same-run cost accounting and fresh cold QoR comparison."""
import json,re,subprocess,sys
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'experiments/owner50_serial_acceptance_workflow_2026-10-07';TAG='owner50_serial_2026-10-07'
def read(p):return json.loads(p.read_text())
p=read(OUT/'protocol.json');r=read(OUT/'receipt.json');assert r['complete'] and r['protocol_sha256']==sha(OUT/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());assert p['joint_binary_sha256']==sha(ROOT/'build/native_joint_qor_gate_2026-10-07/gate_vpr')
assert all(s['exit_code']==0 and s['seconds']>=0 for s in r['stages']);names=[s['name'] for s in r['stages']];assert len(set(names))==len(names);assert names[-2:]==['fresh_full12_cold_baseline','fresh_full12_cold_independent_proof'];workflow_sum=sum(s['seconds'] for s in r['stages'][:-2]);assert workflow_sum<=r['workflow_wall_seconds'];bindings={str(OUT/'receipt.json'):sha(OUT/'receipt.json'),str(OUT/'protocol.json'):sha(OUT/'protocol.json')}
for suffix in ('floor','predictor','fallback','cold'):
 base=ROOT/'experiments'/(TAG+'_'+suffix);receipt=read(base/'receipt.json');verification=read(base/'verification.json');assert verification['receipt_sha256']==sha(base/'receipt.json');assert receipt['protocol_sha256']==sha(base/'protocol.json')
 for name in ('protocol.json','receipt.json','verification.json'):f=base/name;bindings[str(f)]=sha(f)
cold=ROOT/'experiments'/(TAG+'_cold');fallback=ROOT/'experiments'/(TAG+'_fallback');cr=read(cold/'receipt.json');fr=read(fallback/'receipt.json');assert len(cr['rows'])==12 and len(fr['rows'])==10
accepted={(x['width'],x['index']):x for x in r['candidates']};assert set(accepted)=={(8,2),(8,3)};fallback_rows={(x['width'],x['index']):x for x in fr['rows']};assert not set(accepted)&set(fallback_rows) and len(accepted)+len(fallback_rows)==12
rows=[]
def wire(log):return int(re.findall(r'Total wirelength:\s*(\d+)',log.read_text())[-1])
for coldrow in cr['rows']:
 w,i=coldrow['width'],coldrow['index'];assert coldrow['complete'] and coldrow['error'] is None;ref=coldrow['rounds'][0]['reload'];ref_log=next(Path(f) for f in ref['files'] if f.endswith('/reload.log'));assert sha(ref_log)==ref['files'][str(ref_log)];ref_wire=wire(ref_log)
 if (w,i) in accepted:
  item=accepted[(w,i)];snapshot=OUT/f'w8_m{i}_accepted_state.json';assert sha(snapshot)==item['snapshot_sha256'];selected=Path(item['selected_route']);assert sha(selected)==item['selected_route_sha256'];gate=ROOT/'experiments'/(TAG+f'_gate_w8m{i}');gv=read(gate/'verification.json');gr=read(gate/'receipt.json');assert gv['receipt_sha256']==sha(gate/'receipt.json') and gv['rows'][0]==item['metrics'];metrics=item['metrics'];cpd=Fraction(str(metrics['original_cpd_ns']));length=metrics['selected_wire'];assert metrics['reference_wire']==ref_wire;assert abs(Fraction(str(metrics['reference_cpd_ns']))-Fraction(str(ref['cpd_ns'])))<=Fraction('0.000051');assert metrics['selected']=='predicted'
  for n in ('protocol.json','receipt.json','verification.json'):f=gate/n;bindings[str(f)]=sha(f)
 else:
  frow=fallback_rows[(w,i)];assert frow['complete'] and frow['error'] is None;rr=frow['rounds'][0]['reload'];snapshot=fallback/f'mux_w{w}_m{i}_0/accepted_state.json';assert sha(snapshot)==frow['rounds'][0]['snapshot_sha256'];selected=next(Path(f) for f in rr['files'] if f.endswith('/design.route'));log=next(Path(f) for f in rr['files'] if f.endswith('/reload.log'));assert sha(selected)==rr['files'][str(selected)] and sha(log)==rr['files'][str(log)];cpd=Fraction(str(rr['cpd_ns']));length=wire(log)
 assert cpd<=Fraction(str(ref['cpd_ns'])) and length<=ref_wire
 s=read(snapshot);assert len(s['records'])=={8:466,16:936,32:1929}[w]
 template=(ROOT/'tools/verify_tseng_selected_reference_import.py').read_text();check=template[template.index('def check('):template.index('inc=json.loads')].replace('1234',str(len(s['records'])));tool=OUT/f'w{w}_m{i}_independent_final_snapshot.py'
 source="import sys,json\nfrom pathlib import Path\nfrom collections import Counter,defaultdict\nfrom fractions import Fraction\nsys.path.insert(0,"+repr(str(ROOT/'tools'))+")\nfrom immutable_xml_prediction_audit import ImmutableXMLAudit\nfrom buffered_rc_node_classes import read,arc_delay\nfrom native_route_ledger_import import physical_paths\n"+f"snapshot=json.loads(Path({str(snapshot)!r}).read_text());ep=snapshot['endpoint_metadata'];graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph)\n"+check+f"paths,ledger=check(snapshot,ep)\nassert paths=={{n:sorted(v) for n,v in physical_paths(Path({str(selected)!r})).items() if v}}\n";tool.write_text(source)
 with tool.with_suffix('.log').open('w') as stream:code=subprocess.run([sys.executable,str(tool)],stdout=stream,stderr=subprocess.STDOUT,timeout=180).returncode
 assert code==0
 for f in (snapshot,selected,ref_log,tool):bindings[str(f)]=sha(f)
 rows.append(dict(width=w,index=i,selected='candidate' if (w,i) in accepted else 'fallback',cpd_ns=str(cpd),cold_cpd_ns=str(ref['cpd_ns']),wirelength=length,cold_wirelength=ref_wire,connections=len(s['records'])));print(w,i,'final snapshot/QoR verified',flush=True)
assert sum(x['connections'] for x in rows)==13324
cold_stages={s['name']:s['seconds'] for s in r['stages'][-2:]};baseline=sum(cold_stages.values());assert baseline>0
(OUT/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(OUT/'receipt.json'),verifier_sha256=sha(Path(__file__)),bindings=bindings,rows=rows,workflow_wall_seconds=r['workflow_wall_seconds'],sum_disjoint_workflow_stage_seconds=workflow_sum,fresh_cold_process_and_independent_proof_seconds=baseline,observed_workflow_to_cold_ratio=r['workflow_wall_seconds']/baseline,scope='All12 same-run accepted states physically/ledger independently checked against selected native routes; native jointQoR nonregression versus freshsame-target cold proven for everycase. Serialprepared-input process-per-stage workflow timings and freshcold+proof disjoint stage clocks; extra final aggregate verification runtime excluded from both. Upstreamallfanin/oldSTA/RRconversion/frontend/initialroute excluded additional. Single serial currentimplementation observation, NOT repeated/stable, rawinput end-to-end, heldout or theoretical performance bound.'),indent=2)+'\n');print('Full12 serial acceptance proof closed',r['workflow_wall_seconds'],baseline,flush=True)
