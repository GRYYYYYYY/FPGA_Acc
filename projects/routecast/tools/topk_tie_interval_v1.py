"""Exact overlap interval under prediction tie permutations; target TopK fixed."""
def interval(predicted, truth, k):
 if set(predicted)!=set(truth) or not 1<=k<=len(truth):raise ValueError('aligned domain and valid K required')
 target=set(sorted(truth,key=lambda i:(-truth[i],i))[:k]);order=sorted(predicted,key=lambda i:(-predicted[i],i));boundary=predicted[order[k-1]];above=[i for i in order if predicted[i]>boundary];tied=[i for i in order if predicted[i]==boundary];take=k-len(above);fixed=len(target.intersection(above));good=len(target.intersection(tied));lo=fixed+max(0,take-(len(tied)-good));hi=fixed+min(take,good)
 return {'minimum_hits':lo,'maximum_hits':hi,'actual_ID_hits':len(target.intersection(order[:k])),'boundary_size':len(tied),'boundary_take':take,'boundary_target_members':good}
