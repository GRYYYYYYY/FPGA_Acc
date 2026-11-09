"""Independently compare repair graph expressions and HDL trace receipts."""
import hashlib,json,functools
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'experiments/standard_parmys_ram_mapping_v2_2026-10-21';D=R/'experiments/parmys_registered_bank_select_v1_2026-10-21';S=R/'experiments/parmys_registered_bank_xsim_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for d in [D,S]:
  for p,h in json.loads((d/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 results=json.loads((S/'results.json').read_text())['rows'];assert len(results)==2;rows=[]
 for row in results:
  n=row['case'];o=json.loads((P/n/'mapped.json').read_text())['modules']['probe'];r=json.loads((D/n/'repaired.json').read_text())['modules']['probe']
  assert all(r['cells'][k]==v for k,v in o['cells'].items());extra={k:c for k,c in r['cells'].items() if k not in o['cells']};ffs=[c for c in extra.values() if c['type']=='$dff'];assert len(ffs)==1;ff=ffs[0];assert ff['connections']['CLK']==o['ports']['clk']['bits'] and int(ff['parameters']['CLK_POLARITY'],2)==1
  bank=2 if n=='dp13x32' else 5;expected=[o['ports'][f'addr{p}~{i}']['bits'][0] for p in [1,2] for i in range(bank)];assert ff['connections']['D']==expected;assert len(ff['connections']['Q'])==len(expected);replace=dict(zip(expected,ff['connections']['Q']))
  def hasher(m,sub):
   drivers={b:(c,i) for c in m['cells'].values() if c['type'] in ['$and','$reduce_or','$reduce_and','$logic_not'] for i,b in enumerate(c['connections']['Y'])}
   @functools.lru_cache(None)
   def expr(b):
    if b in sub:return ('leaf',sub[b])
    if b not in drivers:return ('leaf',b)
    c,i=drivers[b];z=c['connections'];payload=(c['type'],tuple(sorted(c['parameters'].items())),i,tuple((k,tuple(expr(x) for x in z[k])) for k in ['A','B'] if k in z));return hashlib.sha256(repr(payload).encode()).hexdigest()
   return expr
  before=hasher(o,replace);after=hasher(r,{})
  for k,p in o['ports'].items():
   if p['direction']=='input':assert r['ports'][k]==p
   else:assert [before(b) for b in p['bits']]==[after(b) for b in r['ports'][k]['bits']],k
  log=(S/n/'xsim.log').read_text();assert len(row['stages'])==3 and all(x['exit_code']==0 for x in row['stages']);assert 'ORIGINAL_COUNTEREXAMPLE_REPAIRED' in log and 'REGISTERED_BANK_TRACE_PASS cycles=512' in log;assert '$fatal' not in log
  assert log.count('EDGE_MATCH ref=')==3
  bindings={str(p.relative_to(R)):sha(p) for p in [D/n/'repaired.json',S/n/'mapped.v',S/n/'tb.v',S/n/'xsim.log']}
  # Coverage of frozen deterministic LCG is reported, never called exhaustive random coverage.
  rng=0x5a179d03;sets=[set(),set()]
  for j in range(512):
   rng=(rng*1664525+1013904223)&0xffffffff;a=rng%(1<<(bank+1));rng=(rng*1664525+1013904223)&0xffffffff;b=rng%(1<<(bank+1));b=(a+1)%(1<<(bank+1)) if a==b else b;sets[0].add(a);sets[1].add(b)
  rows.append(dict(case=n,registered_bits=2*bank,original_cells_exact=True,output_expression_substitution_exact=True,trace_cycles=512,deterministic_address_count_by_port=[len(x) for x in sets],initialization_addresses=1<<(bank+1),bindings=bindings))
 out=dict(status='ISOLATED_BANK_SELECTION_REPAIR_GRAPH_AND_HDL_TRACES_VERIFIED',rows=rows,full_equivalence_proven=False,native_admitted=False,limitations='Trace coverage restricted to two rows per bank and frozen deterministic noncollision traffic. Port2 writes disabled; same-address cross-port collisions excluded. No reset/init values assigned. Direct export does not prove full source-family behavior, arbitrary unknown-address behavior, physical RAM semantics, timing closure, packing or resource efficiency.')
 (D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
