"""Exact accepted-path churn; does not establish that a search can be skipped."""
from collections import Counter,defaultdict


def paths(records):
    result={}
    for r in records:
        cid=r['connection_id']
        if cid in result:raise ValueError('duplicate connection')
        result[cid]=(r['source'],r['sink'],tuple(r['answer']['physical_edge_ids']))
    return result


class Replay:
    def __init__(self,records):
        grouped=defaultdict(list);seen=set()
        for r in records:
            cid=r['connection_id']
            if cid in seen:raise ValueError('duplicate initial connection')
            seen.add(cid);grouped[r['net_id']].append(r)
        self.current={net:paths(rs) for net,rs in grouped.items()}
        self.connections=len(seen);self.rounds=defaultdict(Counter);self.order=defaultdict(list)

    def event(self,index,event):
        net=event['net_id'];old=self.current[net];row=self.rounds[index]
        row['events']+=1;row['primary_search_calls']+=event['primary_search_calls'];row['retained_clean_connections']+=len(event['retained_connection_ids']);row['fallback_calls']+=int('fallback' in event);self.order[index].append(net)
        if event['status']!='COMMITTED':row['retained_transactions']+=1;return
        new=paths(event['records'])
        if set(new)!=set(old):raise ValueError('connection identity/count changed')
        changed=sum(new[cid]!=old[cid] for cid in old)
        row['committed_transactions']+=1;row['committed_changed_connections']+=changed
        row['committed_connection_visits']+=len(old)
        if changed:row['committed_changed_NETs']+=1
        else:
            row['committed_unchanged_NETs']+=1
            row['primary_calls_in_unchanged_commits']+=event['primary_search_calls']
            from fractions import Fraction
            if Fraction(event['objective_guard']['objective_delta'])!=0 or event['prospective_overflow_delta']!=0:raise ValueError('unchanged paths with changed objective/occupancy')
        self.current[net]=new

    def finish_round(self,index,metadata):
        order=self.order[index]
        if order!=metadata['affected_nets'] or len(set(order))!=len(order) or set(order)!=set(self.current):raise ValueError('incomplete or duplicate NET round')
        return dict(self.rounds[index])
