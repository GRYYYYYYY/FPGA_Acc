"""Monotone bounds for exactly two rounds and one delayed history update."""


def bounds(*,nodes,owners,max_fanout,base,weight,span,root,arc,denominator,factor):
    values=(nodes,owners,max_fanout,base,weight,span,root,arc,denominator,factor)
    if any(type(v) is not int or v<0 for v in values) or min(nodes,owners,max_fanout,denominator)<1 or factor not in (1,2,4):raise ValueError('bound domain')
    # Positive capacity: max(0,count-cap+1)<=owners. Zero capacity: count=0,
    # so the term is1<=owners. One delayed update gives history<=owners.
    semantic_price=base*(1+owners)*(1+factor*owners)+weight*span
    # Actual Context.start_round passes this deliberately looser ceiling for
    # the increment buffer; NativePrices adds the base input separately.
    prepared_ceiling=base*(1+owners)*(1+factor*(owners+1))+weight*span
    native_price=base+prepared_ceiling
    raw_simple=root+(nodes-1)*arc
    native_raw=root+nodes*arc
    queue=denominator*(raw_simple+nodes*semantic_price)
    whole_NET=denominator*(max_fanout*raw_simple+nodes*semantic_price)
    native_guard=denominator*(native_raw+nodes*native_price)
    # The legacy check adds nonnegative objective_inc too. This lower bound
    # alone suffices to establish rejection for the supplied ceiling.
    legacy_lower=2*nodes*prepared_ceiling+root
    signed_delta_bits=whole_NET.bit_length()+1
    return dict(factor=factor,maximum_semantic_total_node_price=semantic_price,prepared_increment_ceiling=prepared_ceiling,native_total_price_ceiling=native_price,raw_simple_path_upper_bound=raw_simple,native_raw_guard_upper_bound=native_raw,semantic_queue_upper_bound=queue,whole_NET_objective_upper_bound=whole_NET,native_weighted_guard_upper_bound=native_guard,legacy_prepare_lower_bound=legacy_lower,price_bits=prepared_ceiling.bit_length(),semantic_queue_bits=queue.bit_length(),native_weighted_guard_bits=native_guard.bit_length(),signed_objective_delta_bits=signed_delta_bits,chosen_common_arithmetic_lane_bits=((max(queue.bit_length(),signed_delta_bits)+31)//32)*32,price_store128_admitted=prepared_ceiling<2**128,native_raw128_admitted=native_raw<2**128,native_weighted240_admitted=native_guard<2**240,legacy120_must_reject_this_ceiling=legacy_lower>=2**120)
