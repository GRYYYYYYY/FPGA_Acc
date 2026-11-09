"""Exact case-local sparse threshold scan, preserving frozen selection order."""
import math
from collections import defaultdict
from direct_rank_sparse_state_v1 import State
from direct_rank_objective_v1 import objective

def scan(features, domains, fields, members, minleaf=64, retain_trace=False):
    if not features or not features[0] or type(minleaf) is not int or minleaf<1:
        raise ValueError('valid features/minleaf required')
    width=len(features[0]); mapping=[(c,i) for c,(_,d) in enumerate(domains) for i in range(len(d.ids))]
    if len(features)!=len(mapping) or len(fields)!=len(domains) or any(len(row)!=width or any(not math.isfinite(x) for x in row) for row in features):
        raise ValueError('aligned finite features/domains required')
    if len(set(members))!=len(members) or any(type(i) is not int or not 0<=i<len(mapping) for i in members):raise ValueError('unique valid members required')
    # Validate every input before any work; State keeps separate mutable copies.
    original=[State(domain,field) for (_,domain),field in zip(domains,fields)]
    def value(scores):return objective([{'candidate':score,'controls':domain.controls} for (_,domain),score in zip(domains,scores)])
    before=value([state.score() for state in original]);best=before;choice=None;tie_key=None;trace=[];candidates=0;case_scores=0
    for feature in range(width):
        order=sorted(members,key=lambda i:(features[i][feature],i));groups=[]
        for i in order:
            if not groups or groups[-1][0]!=features[i][feature]:groups.append((features[i][feature],[]))
            groups[-1][1].append(i)
        for a,b in [(0,0),(0,1),(1,0),(1,1)]:
            states=[State(domain,field) for (_,domain),field in zip(domains,fields)]
            updates=defaultdict(list)
            for row in members:
                c,i=mapping[row];updates[c].append((i,b))
            for c,changes in updates.items():states[c].update(changes)
            scores=[state.score() for state in states];case_scores+=len(states);cut=0
            for threshold,group in groups[:-1]:
                changed=defaultdict(list)
                if a!=b:
                    for row in group:
                        c,i=mapping[row];changed[c].append((i,a))
                for c,changes in changed.items():states[c].update(changes);scores[c]=states[c].score();case_scores+=1
                cut+=len(group)
                if not minleaf<=cut<=len(members)-minleaf:continue
                got=value(scores);key=(feature,threshold,a,b);candidates+=1
                if retain_trace:trace.append((key,got))
                if got<best or got==best and got<before and (tie_key is None or key<tie_key):
                    best=got;choice=key;tie_key=key
    trace.sort(key=lambda item:item[0])
    return {'before':before,'after':best,'choice':choice,'candidates':candidates,'case_scores':case_scores,'trace':trace}
