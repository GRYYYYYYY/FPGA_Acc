"""Full-field exhaustive reference trainer; not a scalable native engine."""
import math

def train(features, evaluate, depth=8, minleaf=64):
    if not features or not features[0] or type(depth) is not int or not 0 <= depth <= 8 or type(minleaf) is not int or minleaf < 1:
        raise ValueError('invalid tree dimensions or limits')
    columns = len(features[0])
    if any(len(row) != columns or any(not math.isfinite(v) for v in row) for row in features):
        raise ValueError('rectangular finite features required')
    points = [0]*len(features); zero = evaluate(points.copy()); one = evaluate([1]*len(points))
    state = int(one < zero); points[:] = [state]*len(points)
    nodes = []; trace = []
    def grow(members, level, state):
        index = len(nodes); nodes.append({'feature':-1,'left':-1,'right':-1,'state':state,'rows':len(members)})
        current = evaluate(points.copy()); best = current; choice = None
        if level < depth and len(members) >= 2*minleaf:
            for feature in range(columns):
                ordered = sorted(members,key=lambda i: (features[i][feature],i))
                for cut in range(minleaf,len(ordered)-minleaf+1):
                    threshold = features[ordered[cut-1]][feature]
                    if threshold == features[ordered[cut]][feature]:continue
                    left,right = ordered[:cut],ordered[cut:]
                    for a,b in [(0,0),(0,1),(1,0),(1,1)]:
                        proposal = points.copy()
                        for i in left:proposal[i]=a
                        for i in right:proposal[i]=b
                        value = evaluate(proposal)
                        if value < best:
                            best=value;choice=(feature,threshold,left,right,a,b)
        trace.append({'node':index,'before':current,'after':best,'choice':None if choice is None else (choice[0],choice[1],choice[4],choice[5])})
        if choice is not None:
            feature,threshold,left,right,a,b=choice
            for i in left:points[i]=a
            for i in right:points[i]=b
            nodes[index].update(feature=feature,threshold=threshold)
            nodes[index]['left']=grow(left,level+1,a)
            nodes[index]['right']=grow(right,level+1,b)
        return index
    grow(list(range(len(points))),0,state)
    return {'nodes':nodes,'points':points,'trace':trace,'initial_objective':min(zero,one),'final_objective':evaluate(points.copy())}
