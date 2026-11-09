"""Exact whole-NET finite-bank CNF, with explicit nonunit invariance checks."""
from collections import defaultdict
from itertools import combinations

def encode(bank,capacities):
    variables=[];clauses=set();choice={};users=defaultdict(lambda:defaultdict(set));constant=[];mandatory_conflicts=[]
    def variable(kind,key):variables.append(dict(kind=kind,key=key));return len(variables)
    def clause(xs):clauses.add(tuple(sorted(set(xs))))
    for net,options in sorted(bank.items()):
        if not options:raise ValueError('empty NET bank')
        xs=[]
        for index,nodes in enumerate(options):
            x=variable('CHOICE',[net,index]);xs.append(x)
            for node in nodes:
                if type(node) is not int or not 0<=node<len(capacities) or capacities[node]<=0:raise ValueError('node domain')
                users[node][net].add(x)
        choice[net]=xs;clause(xs)
        for a,b in combinations(xs,2):clause([-a,-b])
    for node,owners in sorted(users.items()):
        cap=capacities[node]
        if cap!=1:
            if any(len(xs)!=len(choice[net]) for net,xs in owners.items()):raise ValueError('nonunit ownership changes unsupported')
            constant.append(dict(node=node,capacity=cap,NETs=sorted(owners)))
            if len(owners)>cap:clause([])
            continue
        if len(owners)<2:continue
        mandatory=[net for net,xs in owners.items() if len(xs)==len(choice[net])]
        if len(mandatory)>1:
            clause([]);mandatory_conflicts.append(dict(node=node,NETs=sorted(mandatory)));continue
        if mandatory:
            for net,xs in owners.items():
                if net!=mandatory[0]:
                    for x in xs:clause([-x])
            continue
        zs=[]
        for net,xs in sorted(owners.items()):
            z=variable('OWNER',[node,net]);zs.append(z)
            for x in sorted(xs):clause([-x,z])
            clause([-z,*sorted(xs)])
        for a,b in combinations(zs,2):clause([-a,-b])
    return dict(variables=variables,clauses=[list(c) for c in sorted(clauses)],constant_nonunit_resources=constant,mandatory_unit_conflicts=mandatory_conflicts)
