"""Locally authored 8x8 combinational mux family, exact selector-conditioned proof."""
import json
from pathlib import Path
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/mux_crossbar_family_freeze_2026-10-06';out.mkdir();sources={n:sha(root/'tools'/n) for n in ('pressure_capacity_forecast.py','persistent_rc_context.py','pre_route_endpoints.py','freeze_mux_crossbar_family.py')};protocol={'family':'8input words,8independent outputs eachwith3bitselector,muxbinarytree','widths':[8,16,32],'sources_sha256':sources,'policy':'Transfer unchanged onepasssoftcapacity exactRC*(1+otherNETdemand),no delaybudget/labelcap,sortedNET/CID,sameNETparents. No fourpassfeedback.','native_policy':{'channel_widths':[32,64,128],'seed':1,'workers':1,'max_iterations':100,'timeout_s':180},'scope':'New local nonlinear muxcrossbarfamily all3siblings frozenasonefamilybeforeABC/native jobs. Not proof global no prior related exposure; samearchitecture transfer,not universalholdout. No GF2-derived threshold tuning.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for width in protocol['widths']:
 data=[f'd{word}_{bit}' for word in range(8) for bit in range(width)];sels=[f's{output}_{bit}' for output in range(8) for bit in range(3)];outputs=[f'y{output}_{bit}' for output in range(8) for bit in range(width)];lines=['.model mux_crossbar_'+str(width),'.inputs '+' '.join(data+sels),'.outputs '+' '.join(outputs)];gates=[]
 for output in range(8):
  for bit in range(width):
   current=[f'd{word}_{bit}' for word in range(8)]
   for level in range(3):
    nxt=[]
    for index in range(len(current)//2):
     name=f'y{output}_{bit}' if level==2 else f'n{output}_{bit}_{level}_{index}';a,b=current[2*index:2*index+2];sel=f's{output}_{level}';gates.append((a,b,sel,name));lines.extend([f'.names {a} {b} {sel} {name}','1-0 1','-11 1']);nxt.append(name)
    current=nxt
 lines.append('.end');directory=out/f'w{width}';directory.mkdir();file=directory/'generated.blif';file.write_text('\n'.join(lines)+'\n')
 # Structural parser proves every .names gate is exactly mux truth function.
 text=file.read_text().splitlines();parsed=[]
 for i,line in enumerate(text):
  if line.startswith('.names '):
   fields=line.split()[1:];assert len(fields)==4 and text[i+1:i+3]==['1-0 1','-11 1'];parsed.append(tuple(fields))
 assert parsed==gates;assert len(gates)==8*width*7
 # For each output independently, all8selector assignments reduce the mux
 # cone to a linear map in data. Propagate complete data basis simultaneously.
 # Dependency check excludes other selectors and other output-cone nodes.
 for output in range(8):
  cone=[g for g in parsed if g[3].startswith(f'n{output}_') or g[3].startswith(f'y{output}_')]
  for choice in range(8):
   values={f'd{word}_{bit}':1<<(word*width+bit) for word in range(8) for bit in range(width)}
   for a,b,sel,name in cone:
    assert a in values and b in values and sel.startswith(f's{output}_');level=int(sel.rsplit('_',1)[1]);values[name]=values[b] if (choice>>level)&1 else values[a]
   for bit in range(width):assert values[f'y{output}_{bit}']==1<<(choice*width+bit)
 proof={'generated_blif_sha256':sha(file),'truth_tables_verified':len(parsed),'selector_assignments_per_output':8,'outputs':8*width,'data_basis_vectors_per_assignment':8*width,'zero_preserved_after_fixed_selectors':True,'proof':'Muxtruth+fixedselectorlinearcompletebasis+independentoutputcones provesall arbitrarydataandall independentselectorcombinations, no randomsampling.'};(directory/'verification.json').write_text(json.dumps(proof,indent=2)+'\n');rows.append({'width':width,'generated_blif_sha256':sha(file),'proof_sha256':sha(directory/'verification.json'),'mux_gates':len(gates)});print(width,'complete mux proof',len(gates),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'rows':rows,'ABC_or_native_started':False,'scope':'Generation and complete conditionalfunctionalproof only. ABCmapping/CEC,physicalnative/pressure/predictortransfer remainpending.'},indent=2)+'\n')
