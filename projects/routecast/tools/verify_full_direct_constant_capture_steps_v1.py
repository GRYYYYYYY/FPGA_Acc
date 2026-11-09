"""Actual37 unreset mux lanes: capture establishes relation, holds preserve it."""
import json,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'full_original_unoptimized_proc_state_v1_2026-10-09';af=P/'constant_classes_audit.json';df=P/'direct_constant_capture_audit.json';a=json.loads(af.read_text());d=json.loads(df.read_text());classes={r['bit']:r for r in a['records']};rows=[r for r in d['records'] if classes[r['bit']]['classification']=='unreset_capture_or_guard_obligation'];assert len(rows)==37
D=E/'full_direct_constant_capture_steps_v1_2026-10-09';D.mkdir(exist_ok=True);cells={};ports={};bits=1000000;connections=[];wires=[];terms=[];negterms=[];metadata=[]
for i,r in enumerate(rows):
 info=classes[r['bit']]['data_driver'];c=info['definition'];lane=info['output_lane'];q=r['bit'];s=c['connections']['S'][0];y=c['connections']['Y'][lane]
 assert c['type']=='$mux' and len(c['connections']['S'])==1
 ports['q'+str(i)]={'direction':'input','bits':[q]};ports['s'+str(i)]={'direction':'input','bits':[s]};ports['d'+str(i)]={'direction':'output','bits':[y]}
 # Exact lane of original vector mux; selected/hold polarity unchanged.
 cells['lane'+str(i)]={'hide_name':0,'type':'$mux','parameters':{'WIDTH':'1'},'attributes':{},'port_directions':{'A':'input','B':'input','S':'input','Y':'output'},'connections':{'A':[c['connections']['A'][lane]],'B':[c['connections']['B'][lane]],'S':[s],'Y':[y]}}
 wires.append('wire d'+str(i)+';');connections+=['.q'+str(i)+'(q['+str(i)+'])','.s'+str(i)+'(selects['+str(i)+'])','.d'+str(i)+'(d'+str(i)+')']
 capture=('selects['+str(i)+']') if r['hold_side']=='A' else '(~selects['+str(i)+'])';k="1'b"+r['constant'];diff='(d'+str(i)+' ^ '+k+')'
 terms.append('('+capture+' & '+diff+') | ((q['+str(i)+']=='+k+') & '+diff+')');negterms.append(diff);metadata.append({'bit':q,'constant':r['constant'],'hold_side':r['hold_side'],'actual_select':s,'actual_data':y})
module={'attributes':{},'ports':ports,'cells':cells,'netnames':{}};(D/'cut.json').write_text(json.dumps({'modules':{'actual_lanes':module}},indent=2)+'\n')
v='module miter(input [36:0] q,selects,output bad,unconditional_bad);\n'+'\n'.join(wires)+'\nactual_lanes u('+','.join(connections)+');\nassign bad='+' | '.join(terms)+';\nassign unconditional_bad='+' | '.join(negterms)+';\nendmodule\n';(D/'miter.v').write_text(v)
y=R.parent/'tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys';results={}
for target,success in [('bad',True),('unconditional_bad',False)]:
 r=subprocess.run([str(y),'-p',f'read_json cut.json; read_verilog miter.v; prep -top miter; flatten; sat -prove {target} 0 -show-inputs -show-outputs'],cwd=D,capture_output=True,text=True,timeout=30);log=r.stdout+r.stderr;(D/(target+'.log')).write_text(log);marker='SAT proof finished - no model found: SUCCESS!' if success else 'SAT proof finished - model found: FAIL!';assert r.returncode==0 and marker in log;results[target]={'exit_code':r.returncode,'marker':marker}
out={'results':results,'bits':metadata,'count':37,'conclusion':'Selecting constant establishes Qnext=constant regardless oldQ; Q=constant implies Qnext=constant regardless select. Unconditional equality without capture/base has counterexample.','scope':'Actual37 mux lane functions with arbitrary binary oldQ/selects. Arbitrary boundary selectors with original shared IDs retained impose no reachable timing; actual selecting capture and consumer/init history not established. Not four-state or global admission.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [af,df,D/'cut.json',D/'miter.v',D/'bad.log',D/'unconditional_bad.log']}}
(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['count','results','conclusion','scope']},indent=2))
