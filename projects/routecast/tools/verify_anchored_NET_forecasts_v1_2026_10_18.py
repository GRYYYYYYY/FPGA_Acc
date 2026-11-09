"""Inverse node owners and integer factor replacement oracle, no producer imports."""
import hashlib,json,math,sys
from array import array
from collections import Counter,defaultdict
from fractions import Fraction
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 source=Path('experiments/mmc_anchored_NET_forecasts_v1_2026-10-18');receipt_path=source/'receipt.json';receipt=json.loads(receipt_path.read_text());assert receipt['status']=='all36_source_only_anchored_vectors_materialized_independent_replay_pending'
 out=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18');out.mkdir(exist_ok=False)
 protocol=json.loads((source/'protocol.json').read_text());assert protocol['weight']=='1/2'
 bindings={**receipt['bindings'],str(receipt_path.resolve()):sha(receipt_path),str((source/'protocol.json').resolve()):sha(source/'protocol.json'),str(Path(__file__).resolve()):sha(__file__)}
 for p,h in bindings.items():assert sha(p)==h
 old=Path('experiments/mmc_typed_collision_risk_v1_2026-10-18');g=json.loads((old/'groups.json').read_text());groups=g['groups'];group_of={n:gid for gid,v in enumerate(groups) for n in v['members']};config=json.loads((old/'protocol.json').read_text())
 index=json.loads(Path('experiments/real_joint_full_score_v2_2026-10-18/graph_index.json').read_text());assert index['byteorder']==sys.byteorder
 def read(item):
  assert sha(item['path'])==item['sha256'];v=array(item.get('typecode','d'));v.frombytes(Path(item['path']).read_bytes());assert len(v)==item['values'];return v
 dest=read(index['arrays']['edge_destination']);capacity=read(index['arrays']['positive_capacity']);caps=dict(zip(g['positive_RR_ids'],capacity));manifest_path=source/'vector_manifest.json';manifest=json.loads(manifest_path.read_text());assert len(manifest)==36;bindings[str(manifest_path.resolve())]=sha(manifest_path);checked=0;rows=[]
 for case in protocol['cases']:
  for method in protocol['sources']:
   frame=json.loads(Path(config['inputs'][case]['predictions'][method]).read_text());owners=defaultdict(set)
   for record in frame['records']:
    owners[record['source']].add(record['net_id'])
    for edge in record['answer']['physical_edge_ids']:owners[dest[edge]].add(record['net_id'])
   assert {n:len(v) for n,v in owners.items()}=={int(n):v for n,v in frame['ledger'].items() if v}
   per_group=defaultdict(Counter)
   for n,nets in owners.items():
    if n in group_of:
     for net in nets:per_group[group_of[n]][net]+=1
   vectors=[read(manifest[case+'__'+method+'__'+family]) for family in protocol['families']]
   vectorpos={n:i for i,n in enumerate(g['positive_RR_ids'])};journal_path=source/(case+'__'+method+'.json');journal=json.loads(journal_path.read_text());bindings[str(journal_path.resolve())]=sha(journal_path)
   for gid,group in enumerate(groups):
    nodes=group['members'];m=len(nodes);ks=per_group.get(gid,{});q=len(ks);base=math.prod(2*m-k for k in ks.values());denominator=(2*m)**q;mass=Fraction(0);riskmass=Fraction(0)
    for n in nodes:
     numerator=base
     for net in owners.get(n,()):
      k=ks[net];factor=2*m-k;assert numerator%factor==0;numerator=numerator//factor*(m-k)
     mean=Fraction(sum(ks.values()),2*m)+Fraction(len(owners.get(n,())),2);empty=Fraction(numerator,denominator);risk=mean-1+empty;assert risk>=0
     i=vectorpos[n];assert vectors[0][i]==float(mean) and vectors[1][i]==float(risk),(case,method,n)
     mass+=mean;riskmass+=risk;checked+=2
    assert mass==sum(len(owners.get(n,())) for n in nodes)
    if ks:
     expected=journal['group_totals'][str(gid)];assert Fraction(expected['expected_occupancy_total'])==mass and Fraction(expected['expected_overflow_total'])==riskmass
    else:assert str(gid) not in journal['group_totals'] and mass==riskmass==0
   for n in g['positive_RR_ids']:
    if n in group_of:continue
    expected=Fraction(max(0,len(owners.get(n,()))-caps[n]),caps[n]);i=vectorpos[n];assert vectors[0][i]==vectors[1][i]==float(expected);checked+=2
   for family in protocol['families']:
    item=manifest[case+'__'+method+'__'+family];bindings[item['path']]=item['sha256']
   rows.append(dict(case=case,source=method,values_checked=2*len(caps)));print('ANCHORED INTEGER REPLAY PASS',case,method,flush=True)
 assert checked==36*904438
 for p,h in bindings.items():assert sha(p)==h
 with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,vector_values_checked=checked,all_group_mass_and_exact_risk_totals_checked=True,scope='Independent inverse node->NET ownership plus exact integer per-NET factor substitution; all36 vectors and exact group sums. Original XML index authentication transferred from admitted index proof; no new outcome scores, native dynamics or forecast promotion.'),f,indent=2)
 print('ALL36 ANCHORED FORECASTS VERIFIED',checked,flush=True)
if __name__=='__main__':main()
