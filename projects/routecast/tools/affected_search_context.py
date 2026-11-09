"""Conservative cache invalidation for frozen, independent per-net searches.

Caller authenticates each digest against actual bytes. This planner does not
authenticate files or authorize reuse for occupancy-dependent search policies.
"""
from affected_connections import affected


FIELDS = ('graph_sha256', 'cost_manifest_sha256', 'consumer_sha256',
          'search_policy_sha256', 'packed_netlist_sha256', 'endpoint_policy_sha256')


def plan(before, after, previous_context, next_context):
    def validate(context, endpoints):
        if not isinstance(context, dict) or set(context) != set(FIELDS):
            raise ValueError('incomplete search context')
        for value in context.values():
            if (not isinstance(value, str) or len(value) != 64
                    or any(c not in '0123456789abcdef' for c in value)):
                raise ValueError('invalid context digest')
        if context['graph_sha256'] != endpoints['graph_sha256']:
            raise ValueError('endpoint/context graph mismatch')
        # Validate endpoint identities even when a full rebuild is required.
        affected(endpoints, endpoints)

    validate(previous_context, before)
    validate(next_context, after)
    changed = [key for key in FIELDS if previous_context[key] != next_context[key]]
    if changed:
        return {'mode': 'full_rebuild', 'changed_context_fields': changed,
                'discard_previous_state': True,
                'recompute_connection_ids': sorted(r['connection_id'] for r in after['connections']),
                'retained_connection_ids': [],
                'scope': 'new context requires a separate fresh ledger/cache; do not merge identities across contexts'}
    return {'mode': 'incremental', 'changed_context_fields': [],
            'discard_previous_state': False, **affected(before, after)}
