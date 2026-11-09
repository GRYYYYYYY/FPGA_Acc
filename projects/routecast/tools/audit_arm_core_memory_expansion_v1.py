"""Exact archived signal-bit storage naming attribution, not memory equivalence."""
import json,re
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];S=R/'experiments/verilog_frontend_cohort_v3_2026-10-10/arm_core';rp=S/'receipt.json';r=json.loads(rp.read_text());assert r['exit_code']==0 and all(sha(k)==h for k,h in r['bindings'].items());jp=S/'design.json';m=json.loads(jp.read_text())['modules']['arm_core'];bybit={};groups={};words=Counter()
for n,d in m['netnames'].items():
 match=re.fullmatch(r'(.+)\.RAM\[(\d+)\]',n)
 if not match:continue
 group=match[1];words[group]+=1;groups.setdefault(group,set()).update(b for b in d['bits'] if type(b) is int)
 for b in d['bits']:
  if type(b) is int:bybit.setdefault(b,set()).add(group)
ff=Counter();unattributed=0;total=0
for c in m['cells'].values():
 if c['type']!='$_DFF_P_':continue
 assert len(c['connections']['Q'])==1;total+=1;b=c['connections']['Q'][0]
 if b not in bybit:unattributed+=1
 else:
  assert len(bybit[b])==1;ff[next(iter(bybit[b]))]+=1
assert total==r['cell_types']['$_DFF_P_']==309347 and sum(ff.values())+unattributed==total
D=R/'experiments/arm_core_memory_expansion_v1_2026-10-10';D.mkdir();bindings={**r['bindings'],str(rp):sha(rp),str(Path(__file__)):sha(Path(__file__))};assert all(sha(k)==h for k,h in bindings.items())
(D/'audit.json').write_text(json.dumps(dict(bindings=bindings,total_DFF_P=total,RAM_named_word_count=sum(words.values()),RAM_named_Q_DFF_count=sum(ff.values()),other_DFF_count=unattributed,RAM_named_DFF_fraction=sum(ff.values())/total,groups=[dict(prefix=g,named_words=words[g],unique_named_bits=len(groups[g]),Q_matched_DFF_count=ff[g]) for g in sorted(groups)],scope='Exact current JSON RAM-labelled netname bits matched to single-Q DFF_P cells; all counted once/no cross-group aliases. Attribution relies on preserved source names, not behavioral memory/collision proof or native resource fit. No hard-RAM mapping, source memory reduction, design projection, timing or hardware claim.'),indent=2)+'\n');print('ARM_STORAGE_Q',total,sum(ff.values()),unattributed,sum(ff.values())/total)
