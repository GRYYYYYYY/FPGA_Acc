"""Serialize host parameters and forbidden identities for strict snapshot search."""
def query(e,selector,color,forbidden=()):
 c=e.config;rows=[f'{selector} {int(color)} {c.page_width} {c.page_height} {c.candidate_limit} {c.chain_candidate_limit} {c.timing_weight} {c.routed_timing_weight} {c.congestion_weight}',str(len(e.guarded))]
 rows.extend(f'{a} {b} {d+c.critical_distance_slack}' for a,b,_,d in e.guarded)
 rows.append(str(len(forbidden)))
 for kind,units,trial in sorted(forbidden):
  rows.append(f'{kind} {len(units)}')
  rows.extend(' '.join(map(str,(len(u),*u))) for u in units)
  rows.append(str(len(trial)))
  rows.extend(' '.join(map(str,(id,*p))) for id,p in trial)
 return '\n'.join(rows)+'\n'
