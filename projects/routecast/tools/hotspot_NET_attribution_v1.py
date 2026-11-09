"""Full-input, selected-bin NET incidence reconstruction; legality is external."""
from collections import Counter,defaultdict
from xml.parsers import expat
from bounded_model_json_stream_v1 import records
from stream_native_NET_occupancy_v1 import NET,NODE


def domain(graph,keys):
    targets=defaultdict(list)
    for key in keys:
        layer,x,y,kind,segment=key.split(',')
        targets[layer,kind,segment].append((int(x),int(y),key))
    members={};capacities={};edges={};segments={};stack=[];current=[None]
    counts=Counter()
    def start(tag,a):
        parent=stack[-1] if stack else None
        if tag=='segment' and parent=='segments':segments[a['id']]=dict(a)
        if tag=='node' and parent=='rr_nodes':
            counts['nodes']+=1
            current[0]=dict(a) if a['type'] in ['CHANX','CHANY'] and int(a['capacity'])>0 else None
        if parent=='node' and current[0] is not None and tag in ['loc','segment']:
            current[0][tag]=dict(a)
        if tag=='edge' and parent=='rr_edges':
            sink=int(a['sink_node'])
            if sink in members:edges[counts['edges']]=sink
            counts['edges']+=1
        stack.append(tag)
    def end(tag):
        parent=stack[-2] if len(stack)>1 else None
        if tag=='node' and parent=='rr_nodes' and current[0] is not None:
            n=current[0];loc=n['loc'];segment=n['segment']['segment_id']
            found={key for x,y,key in targets.get((loc.get('layer','0'),n['type'],segment),[])
                   if int(loc['xlow'])<=x<=int(loc['xhigh']) and int(loc['ylow'])<=y<=int(loc['yhigh'])}
            if found:
                nid=int(n['id']);assert nid not in members
                members[nid]=found;capacities[nid]=int(n['capacity'])
        assert stack.pop()==tag
    parser=expat.ParserCreate();parser.StartElementHandler=start;parser.EndElementHandler=end
    with open(graph,'rb') as f:parser.ParseFile(f)
    totals=Counter()
    for nid,bins in members.items():
        for key in bins:totals[key]+=capacities[nid]
    if set(totals)!=set(keys):raise ValueError('missing selected bin')
    return dict(members=members,node_capacities=capacities,edge_sink=edges,
                bin_capacities=dict(totals),counts=dict(counts),segments=segments)


def model_owners(path,selected):
    owners=defaultdict(set);connections=defaultdict(set);fanout=Counter();seen=set()
    for rec in records(path):
        cid=rec['connection_id'];net=rec['net_id']
        if cid in seen:raise ValueError('duplicate connection')
        seen.add(cid);fanout[net]+=1
        used={selected['edge_sink'][eid] for eid in rec['answer']['physical_edge_ids'] if eid in selected['edge_sink']}
        if used:owners[net].update(used);connections[net].add(cid)
    return dict(owners),dict(connections),dict(fanout),len(seen)


def native_owners(path,wanted):
    owners={};seen=set();name=None;nodes=set()
    with open(path) as f:
        for line in f:
            header=NET.match(line)
            if header:
                if name is not None and nodes:owners[name]=nodes
                nid=int(header[1]);name=header[2]
                if nid in seen:raise ValueError('duplicate native NET')
                seen.add(nid);nodes=set()
            elif line.lstrip().startswith('Net '):raise ValueError('invalid native NET header')
            if line.lstrip().startswith('Node:'):
                node=NODE.match(line)
                if node is None or name is None:raise ValueError('invalid native node')
                nid=int(node[1])
                if nid in wanted:nodes.add(nid)
    if name is not None and nodes:owners[name]=nodes
    return owners,len(seen)


def incidences(owners,members):
    result={}
    for net,nodes in owners.items():
        count=Counter()
        for node in nodes:
            for key in members[node]:count[key]+=1
        result[net]=dict(count)
    return result


def components(keys,members):
    adjacency={k:set() for k in keys}
    for bins in members.values():
        group=bins&set(keys)
        for key in group:adjacency[key].update(group-{key})
    result=[];remaining=set(keys)
    while remaining:
        queue=[min(remaining)];component=set()
        while queue:
            key=queue.pop()
            if key in component:continue
            component.add(key);queue.extend(adjacency[key]-component)
        remaining-=component;result.append(sorted(component))
    return result
