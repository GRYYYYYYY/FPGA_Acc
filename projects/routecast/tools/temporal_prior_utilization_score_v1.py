"""Exact uncalibrated temporal support score; never a physical route ledger."""
from collections import defaultdict
from fractions import Fraction

def pin_edit_fraction(old, new):
    a={r['connection_id']:r for r in old}
    b={r['connection_id']:r for r in new}
    if not a or a.keys()!=b.keys() or len(a)!=len(old) or len(b)!=len(new):
        raise ValueError('CID coverage')
    if len({r['net_id'] for r in old+new})!=1:
        raise ValueError('NET identity')
    if len({r['source'] for r in old})!=1 or len({r['source'] for r in new})!=1:
        raise ValueError('single source required')
    source_change=int(next(iter(a.values()))['source']!=next(iter(b.values()))['source'])
    return Fraction(source_change+sum(a[c]['sink']!=b[c]['sink'] for c in a),len(a)+1)

def union_scores(domain, mixtures):
    complement={n:Fraction(1) for n in domain}
    for alpha,old,new in mixtures:
        if not 0<=alpha<=1:raise ValueError('mixture weight')
        for n in (old|new)&complement.keys():
            p=(1-alpha)*int(n in old)+alpha*int(n in new)
            complement[n]*=1-p
    return {n:1-v for n,v in complement.items()}

def score_vectors(resources,bins,old_records,new_records,destinations):
    domain={r['id'] for r in resources}
    if len(domain)!=len(resources) or any(r['capacity']!=1 for r in resources):
        raise ValueError('unique unit-capacity resources required')
    old=defaultdict(list);new=defaultdict(list)
    for r in old_records:old[r['net_id']].append(r)
    for r in new_records:new[r['net_id']].append(r)
    if old.keys()!=new.keys():raise ValueError('NET coverage')
    def support(records):
        nodes={r['source'] for r in records}
        for r in records:
            if r['answer']['status']!='FOUND':raise ValueError('incomplete path')
            nodes.update(destinations[e] for e in r['answer']['physical_edge_ids'])
        return nodes&domain
    mixtures=[];weights={}
    for net in sorted(old):
        alpha=pin_edit_fraction(old[net],new[net]);weights[net]=alpha
        mixtures.append((alpha,support(old[net]),support(new[net])))
    scores=union_scores(domain,mixtures)
    totals={tuple(b['key']):Fraction(0) for b in bins}
    for r in resources:
        for key in r['bins']:totals[tuple(key)]+=scores[r['id']]
    spatial={tuple(b['key']):totals[tuple(b['key'])]/b['capacity'] for b in bins}
    return dict(resource=scores,spatial=spatial),weights
