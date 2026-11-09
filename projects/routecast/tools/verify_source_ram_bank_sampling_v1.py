"""Independent surgical delta and RAM-output lineage audit for source candidate."""
import json,hashlib,functools,copy
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'source_ram_bank_sampling_v1_2026-10-21';P=E/'parmys_source_provenance_replay_v1_2026-10-21'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for p,h in json.loads((D/'protocol.json').read_text())['bindings'].items():assert sha(Path(p))==h,p
 manifest=json.loads((D/'integration_manifest.json').read_text());prov={r['source']:r for r in json.loads((P/'verification_v1.json').read_text())['rows']};checks=json.loads((D/'structural_checks.json').read_text())['rows'];assert all(r['exit_code']==0 for r in checks);verified=[]
 for row in manifest['rows']:
  name=row['source'];before=json.loads((P/name/'instrumented/mapped.json').read_text());after=json.loads((D/name/'candidate.json').read_text());assert sha(D/name/'candidate.json')==row['candidate_sha256'];a=before['modules'][name];b=after['modules'][name];assert {k:v for k,v in a.items() if k!='cells'}=={k:v for k,v in b.items() if k!='cells'}
  assert set(after['modules'])==set(before['modules'])
  for n,m in before['modules'].items():
   if n!=name:assert after['modules'][n]==m
  extra=set(b['cells'])-set(a['cells']);assert extra==set(row['added_cells']);changed={n for n,c in a['cells'].items() if b['cells'][n]!=c};assert changed=={n for g in row['banked_groups'] for n in g['read_MUX_AND_cells']};assert len(changed)==row['changed_read_AND_cells']
  drivers={bit:(n,c) for n,c in b['cells'].items() for p,bs in c['connections'].items() if c['port_directions'][p]=='output' for bit in bs if isinstance(bit,int)};pgroup={g['source_instance']:g for g in prov[name]['groups']};total=0
  for idx,g in enumerate(row['banked_groups']):
   physical=pgroup[g['source_instance']];ramoutputs={bit for n in physical['descendant_cells'] for p,bs in a['cells'][n]['connections'].items() if a['cells'][n]['port_directions'][p]=='output' for bit in bs};qs=set(g['sampled_Q_bits']);invs=g['inverse_Q_bits'];selects=g['sampled_selector_bits'];assert len(qs)==len(selects);total+=len(qs)
   ffname,ff=drivers[next(iter(qs))];assert ff['type']=='$dff' and ff['connections']=={'CLK':g['clock_bits'],'D':selects,'Q':g['sampled_Q_bits']} and int(ff['parameters']['CLK_POLARITY'],2)==1
   _,inv=drivers[invs[0]];assert inv['type']=='$not' and inv['connections']=={'A':g['sampled_Q_bits'],'Y':invs}
   replacements=dict(zip(selects,zip(g['sampled_Q_bits'],invs)))
   @functools.lru_cache(None)
   def leaves(bit):
    if isinstance(bit,str):assert bit in ['0','1'];return frozenset()
    if bit in ramoutputs or bit in qs:return frozenset([bit])
    _,c=drivers[bit];assert c['type'] in ['$and','$reduce_or','$logic_not','$not'],c['type'];out=frozenset()
    for p,bs in c['connections'].items():
     if c['port_directions'][p]=='input':
      for x in bs:out=out|leaves(x)
    return out
   for n in g['read_MUX_AND_cells']:
    old=a['cells'][n];new=b['cells'][n];assert old['type']==new['type']=='$and';positive,negative=old['connections']['A'];oc=next(c for c in a['cells'].values() if c['connections'].get('Y')==[negative]);assert oc['type']=='$logic_not' and oc['connections']['A']==[positive]
    expected=copy.deepcopy(old);expected['connections']['A']=list(replacements[positive]);assert new==expected
    for bit in new['connections']['Y']:assert leaves(bit)<=ramoutputs|qs
   for n in physical['descendant_cells']:assert a['cells'][n]==b['cells'][n]
  assert total==row['sampled_bit_count'];log=(D/name/'check.log').read_text();assert 'Found and reported 0 problems.' in log
  verified.append({'source':name,'sampled_bits':total,'modified_read_AND_cells':len(changed),'all_other_original_cells_exact':True,'read_cone_terminals_only_own_RAM_outputs_and_sampled_bits':True,'bindings':{str(p.relative_to(R)):sha(p) for p in [D/name/'candidate.json',D/name/'check.log']}})
 out={'status':'ACTUAL_SOURCE_BANK_SAMPLING_DELTA_AND_READ_LINEAGE_VERIFIED','rows':verified,'scope':'Independent graph delta, preserved ports/other modules, unchanged RAM/control/clock/reset cells, and read cone lineage. Not sequential/full-source equivalence, arbitrary four-state proof, source reachability, physical RAM characterization or native admission.'};(D/'verification_v1.json').write_text(json.dumps(out,indent=2)+'\n');print(out['status'])
if __name__=='__main__':main()
