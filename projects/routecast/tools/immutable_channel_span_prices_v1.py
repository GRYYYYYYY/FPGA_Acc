"""Derive physical channel prices from the already authenticated XML context."""
from prepared_csr import TYPES

def channel_span_prices(context):
    channel_types = {TYPES['CHANX'], TYPES['CHANY']}
    if len(context.types) != len(context.spans):
        raise ValueError('inconsistent immutable node metadata')
    return {node: context.spans[node] for node, kind in enumerate(context.types)
            if kind in channel_types}
