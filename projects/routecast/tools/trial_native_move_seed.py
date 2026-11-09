import json,re,shutil,os,subprocess
from pathlib import Path
from collections import Counter,defaultdict
from audit_native_route import NET,NODE
from stream_native_route_audit import audit
from pre_route_endpoints import sha
root=Path(__file__).resolve().parents[1];out=root/'experiments/native_move_seed_v5_2026-10-06';work=root/'work/native_move_seed_v5_2026-10-06';out.mkdir();work.mkdir();src=root/'work/multiplier_family_native_capture_2026-10-06/mult_6x6';swap=root/'experiments/multiplier_placement_swap_2026-10-06/mult_6x6';protocol=json.loads((swap/'protocol.json').read_text());assert all(sha(v['path'])==v['sha256'] for v in protocol['inputs'].values());receipt=json.loads((swap/'receipt.json').read_text());assert sha(swap/'swapped.place')==receipt['swapped_place_sha256'] and sha(swap/'endpoints.json')==receipt['endpoint_sha256'];ep=json.loads((swap/'endpoints.json').read_text());expected=defaultdict(Counter)
for row in ep['connections']:expected[row['net_id']][(row['source'],row['sink'])]+=1
native=audit(src/'rr_graph.xml',src/'design.route');original=defaultdict(Counter)
for row in native['connections']:original[row['net_id']][(row['source'],row['sink'])]+=1
changed=set(receipt['changed_connection_ids']);affected={row['net_id'] for row in ep['connections'] if row['connection_id'] in changed};assert affected
table=[json.loads(line) for line in (root/'experiments/native_move_identities_2026-10-06/moved.jsonl').read_text().splitlines()];block_positions={p['block']:(p['x'],p['y'],p['layer']) for n in table for p in n['pins']};text=(src/'design.route').read_text();head=text[:re.search(r'^Net ',text,re.M).start()];head=re.sub(r'Placement_ID:\s*\S+',f"Placement_ID: SHA256:{sha(swap/'swapped.place')}",head);chunks=[];removed=0
for chunk in re.split(r'(?=^Net )',text,flags=re.M)[1:]:
 n=int(re.match(r'Net\s+(\d+)',chunk)[1])
 if ': global net connecting:' in chunk:
  def rebind(m):
   x,y,layer=block_positions[m[1]];return f'Block {m[1]} {m[2]} at ({x},{y},{layer}),'
  chunk=re.sub(r'Block (\S+) (\(#\d+\)) at \([^)]*\),',rebind,chunk)
 if n in affected:removed+=len(original[n]);chunks.append(chunk.splitlines()[0]+'\n\n')
 else:chunks.append(chunk)
for name in ('design.blif','design.net'):shutil.copyfile(src/name,work/name)
shutil.copyfile(swap/'swapped.place',work/'design.place');(work/'seed.route').write_text(head+''.join(chunks));seed=audit(src/'rr_graph.xml',work/'seed.route');assert len(seed['connections'])==129-removed and seed['overflow_units']==0
meta=json.loads((root/'experiments/native_search_seed_v3_2026-10-06/command.json').read_text());cmd=meta['command']+['--min_incremental_reroute_fanout','0'];env=os.environ.copy();env['ROUTECAST_NATIVE_SEED']=str(work/'seed.route');(out/'command.json').write_text(json.dumps({'command':cmd,'cwd':str(work),'affected_net_ids':sorted(affected),'retained_connections':129-removed,'seed_sha256':sha(work/'seed.route'),'scope':'Actual captured CLB exchange; whole affected NET removal, no new-layout route/pin label reference.'},indent=2)+'\n')
with (out/'run.log').open('w') as f:code=subprocess.run(cmd,cwd=work,env=env,stdout=f,stderr=subprocess.STDOUT,timeout=60).returncode
result={'exit_code':code,'affected_nets':len(affected),'retained_connections':129-removed,'log_sha256':sha(out/'run.log')}
if code==0:
 final=audit(src/'rr_graph.xml',work/'output.route');assert len(final['connections'])==129 and final['overflow_units']==0;(out/'physical_audit.json').write_text(json.dumps(final,indent=2)+'\n');result.update(connections=129,overflow_units=0,output_sha256=sha(work/'output.route'))
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
