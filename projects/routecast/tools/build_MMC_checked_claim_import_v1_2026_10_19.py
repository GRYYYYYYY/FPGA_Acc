#!/usr/bin/env python3
"""Input-only namespace conversion; runtime validation remains the caller's duty."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def digest(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(1<<20),b''):h.update(block)
 return h.hexdigest()
def main():
 out=R/'experiments/mmc_checked_claim_import_v1_2026-10-19';out.mkdir(exist_ok=True)
 assert not (out/'conversion_receipt.json').exists()
 bound={};rows=[]
 def bind(p,expected=None):
  h=digest(p)
  if expected is not None:assert h==expected,(str(p),'hash mismatch')
  bound[str(p)]=h
 receipt=R/'experiments/mmc_preferred_NET_claims_v1_2026-10-19/receipt.json'
 old=json.loads(receipt.read_text());bind(receipt)
 for entry in old['cases']:
  case=entry['case'];ep=R/f'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/{case}/demand/endpoints.json'
  bind(ep,old['bindings'][str(ep)]);d=json.loads(ep.read_text());identity=Path(d['inputs']['native_identity']['path']);bind(identity,d['inputs']['native_identity']['sha256'])
  native={}
  for line in identity.open():
   item=json.loads(line);n=item['net_id'];assert n not in native;native[n]=item
  names={int(k):v for k,v in d['net_names'].items()};assert set(names)==set(native)==set(range(len(names)))
  assert all(names[n]==native[n]['name'] for n in names)
  cp=Path(entry['claims_file']);bind(cp,old['bindings'][str(cp)]);claims=[json.loads(l) for l in cp.open()]
  assert len(claims)==entry['claims'];owners=sorted({c['preferred_net'] for c in claims});assert all(not native[n]['ignored'] for n in owners)
  nodes=[c['node'] for c in claims];assert nodes==sorted(set(nodes))
  graph=d['inputs']['graph'];assert graph['sha256']==d['graph_sha256'];bind(graph['path'],graph['sha256'])
  target=out/f'{case}.rcpref2'
  with target.open('x') as f:
   f.write(f"RCPREF2 {d['graph_sha256']} 904438 {len(names)} 1 {len(claims)} {len(owners)}\n")
   for n in owners:f.write(f'N {n} {names[n].encode().hex()}\n')
   for c in claims:f.write(f"C {c['node']} {c['preferred_net']} {c['hint_bits']}\n")
  bind(target);rows.append({'case':case,'claims':len(claims),'owners':len(owners),'path':str(target),'native_names_and_ids_match':True})
 bind(Path(__file__).resolve())
 (out/'conversion_receipt.json').write_text(json.dumps({'status':'ALL3_INPUT_ONLY_NAMESPACE_CONVERSION_PASS','cases':rows,'bindings':bound,'limitations':'Runtime reader against actual live graph, NET context, risk bits and unit CHANNEL predicate still pending; no routing or performance claim.'},indent=2)+'\n')
 print(json.dumps(rows))
if __name__=='__main__':main()
