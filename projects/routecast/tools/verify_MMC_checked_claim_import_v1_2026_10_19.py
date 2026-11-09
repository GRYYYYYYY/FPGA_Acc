#!/usr/bin/env python3
import json,hashlib,struct,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def main():
 out=R/'experiments/mmc_checked_claim_import_v1_2026-10-19';assert not (out/'real_context_verification_v1.json').exists()
 conv=json.loads((out/'conversion_receipt.json').read_text());protocol=json.loads((R/'experiments/mmc_NET_conditioned_hint_contract_protocol_v1_2026-10-19/protocol.json').read_text());bindings={}
 def bind(p,expected=None):
  value=sha(p)
  if expected is not None:assert value==expected,str(p)
  bindings[str(p)]=value
 for p,h in conv['bindings'].items():bind(p,h)
 graph=Path(json.loads(Path(protocol['cases'][0]['endpoint']).read_text())['inputs']['graph']['path']);nodes={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  if e.tag=='node' and len(stack)>1 and stack[-2].tag=='rr_nodes':
   n=int(e.get('id'));assert n not in nodes;nodes[n]=e.get('type') in ('CHANX','CHANY') and int(e.get('capacity'))==1;stack[-2].remove(e);e.clear()
  if e.tag=='rr_nodes':break
  stack.pop()
 assert set(nodes)==set(range(len(nodes)));results=[]
 exe=R/'build/net_conditioned_checked_import_v1_2026-10-19/check_real_context'
 for plan in protocol['cases']:
  case=plan['case'];meta=json.loads(Path(plan['endpoint']).read_text());ident=Path(meta['inputs']['native_identity']['path']);bind(ident,meta['inputs']['native_identity']['sha256']);native={}
  for line in ident.open():
   x=json.loads(line);assert x['net_id'] not in native;native[x['net_id']]=x
  assert set(native)==set(range(len(native)))
  risk=Path(plan['risk']);bind(risk,protocol['bindings'][str(risk)]);lines=risk.read_text().splitlines();head=lines[0].split();assert head[:3]==['RCRISK1',sha(graph),str(len(nodes))];hints={}
  for line in lines[1:]:
   n,b=map(int,line.split());assert n not in hints and nodes[n];value=struct.unpack('<f',struct.pack('<I',b))[0];assert value>0;hints[n]=struct.unpack('<I',struct.pack('<f',1+value))[0]
  assert len(hints)==int(head[3]);ctx=out/f'{case}.independent_context'
  with ctx.open('x') as f:
   f.write(f'{sha(graph)} {len(nodes)} 1 {len(native)} {len(hints)}\n')
   for n,x in sorted(native.items()):f.write(f"{n} {int(x['ignored'])} {x['name'].encode().hex()}\n")
   for n,b in sorted(hints.items()):f.write(f'{n} {b} {int(nodes[n])}\n')
  claim=out/f'{case}.rcpref2';run=subprocess.run([str(exe),str(ctx),str(claim)],capture_output=True,text=True,check=True);accepted=[tuple(map(int,l.split())) for l in run.stdout.splitlines()]
  original=R/f'experiments/mmc_preferred_NET_claims_v1_2026-10-19/{case}/claims.jsonl';expected=[(x['node'],x['preferred_net'],x['hint_bits']) for x in map(json.loads,original.read_text().splitlines())];assert accepted==expected
  # Wrong actual NET name and wrong expected risk cost must reject full real files.
  text=ctx.read_text();owner=accepted[0][1];native_line=f"{owner} {int(native[owner]['ignored'])} {native[owner]['name'].encode().hex()}\n";bad=out/f'{case}.wrong_name_context';bad.write_text(text.replace(native_line,f'{owner} 0 77726f6e67\n',1));negative=subprocess.run([str(exe),str(bad),str(claim)],capture_output=True,text=True);assert negative.returncode==2 and not negative.stdout
  for p in [ctx,claim,original,bad]:bind(p)
  results.append({'case':case,'accepted_claims':len(accepted),'all_claims_exact':True,'wrong_actual_name_rejected':True});print(case,len(accepted),'PASS',flush=True)
 for p in [exe,Path(__file__).resolve(),R/'tools/net_conditioned_checked_import_v1/check_real_context.cpp',R/'tools/net_conditioned_checked_import_v1/checked_claim_import.h']:bind(p)
 (out/'real_context_verification_v1.json').write_text(json.dumps({'status':'ALL3_CPP_IMPORT_INDEPENDENT_RECONSTRUCTED_CONTEXT_PASS','cases':results,'bindings':bindings,'scope':'Original XML node geometry, native input identity and risk bits reconstructed independently of imported file; no live native routing integration or utility claim.'},indent=2)+'\n')
if __name__=='__main__':main()
