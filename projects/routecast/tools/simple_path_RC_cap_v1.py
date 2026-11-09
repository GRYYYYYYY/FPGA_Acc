"""Nonrestrictive integer delay cap for already cycle-free additive RC paths.

This cap deliberately replaces original hard timing budgets in a separate
research policy. It is not a timing allowance or a certificate of native STA.
"""
def cap(node_count, maximum_increment, source_initial):
    if any(type(v) is not int or v < 0 for v in [node_count, maximum_increment, source_initial]) or node_count < 1:
        raise ValueError('invalid additive graph domain')
    result = source_initial + (node_count - 1) * maximum_increment
    if result >= 2**64:
        raise ValueError('cap exceeds uint64 search ABI')
    return result
