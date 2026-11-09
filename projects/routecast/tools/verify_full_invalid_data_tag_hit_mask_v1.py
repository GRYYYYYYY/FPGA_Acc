"""Actual source data-cache hit cone independence when tag valid is zero."""
from pathlib import Path
import json,re,hashlib,subprocess
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_invalid_data_tag_hit_mask_v1_2026-10-09';D.mkdir(exist_ok=False);F=E/'full_original_source_proc_state_v1_2026-10-09/source_proc.json';m=next(iter(json.load(open(F))['modules'].values()));nets=m['netnames'];root=nets['dataCache_1.stageA_wayHits']['bits'];valid=nets['dataCache_1.ways_0_tagsReadRsp_valid']['bits'][0];addr=nets['dataCache_1.ways_0_tagsReadRsp_address']['bits'];drv={b:(n,c) for n,c in m['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for b in bs if isinstance(b,int)};todo=root[:];used={};boundary=set()
while todo:
 b=todo.pop()
 if not isinstance(b,int):continue
 if b not in drv or re.match(r'^\$(?:[as]?dff|dlatch|mem)',drv[b][1]['type']):boundary.add(b);continue
 n,c=drv[b]
 if n in used:continue
 used[n]=c;todo.extend(b for p,bs in c['connections'].items() if c['port_directions'][p]=='input' for b in bs)
assert valid in boundary and set(addr)<=boundary;boundary=sorted(boundary);idx={b:i for i,b in enumerate(boundary)};ports={'hit':{'direction':'output','bits':root}};ports.update({'i'+str(b):{'direction':'input','bits':[b]} for b in boundary});(D/'cut.json').write_text(json.dumps({'creator':'actual source cells','modules':{'hit_cut':{'attributes':{},'ports':ports,'cells':used,'netnames':{}}}}));lines=[f'module miter(input [{len(boundary)-1}:0] shared,input [19:0] flips,output bad);wire hit0,hit1;']
for inst in range(2):
 con=[f'.hit(hit{inst})']
 for b in boundary:
  expr=f'shared[{idx[b]}]'
  if inst==1 and b in addr:expr=f'({expr} ^ flips[{addr.index(b)}])'
  con.append(f'.i{b}({expr})')
 lines.append('hit_cut u'+str(inst)+'('+','.join(con)+');')
lines.append('assign bad=(hit0 ^ hit1) | hit0 | hit1; endmodule');(D/'miter.v').write_text('\n'.join(lines)+'\n');(D/'check.ys').write_text(f'read_json cut.json\nread_verilog miter.v\nhierarchy -check -top miter\nflatten\nopt\ncheck -assert\nsat -verify -set shared[{idx[valid]}] 0 -prove bad 0 -show bad\n');Y=Path('/inspire/hdd/global_user/guoruiyuan-253208540291/FPGA_Acc/projects/tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/build_tileplace_frontend/bin/yosys');r=subprocess.run([str(Y),'-s','check.ys'],cwd=D,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=15);(D/'check.log').write_bytes(r.stdout);ok=r.returncode==0 and b'no model found: SUCCESS' in r.stdout;out={'exit_code':r.returncode,'sat_success':ok,'source_valid_bit':valid,'arbitrary_address_flips':addr,'actual_comb_cells':len(used),'scope':'Binary local DataCache stageA_wayHits is zero and unchanged for any tag address perturbation when actual visible tag valid=0. Does not prove startup invalidates every line, error/data/global outputs are masked, or weaker whole-processor relation/Full admission.','functional_admission':False,'bindings':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in [Path(__file__),F,Y,*D.iterdir()] if f.is_file()}};(D/'receipt.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'exit':r.returncode,'success':ok,'cells':len(used)}))
