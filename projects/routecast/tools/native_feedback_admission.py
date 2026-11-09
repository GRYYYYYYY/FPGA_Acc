"""Native feedback gate; caller supplies authenticated evidence and budgets."""
from fractions import Fraction


def decide(baseline, candidate, *, cpd_limit, wirelength_limit, pipeline_limit):
    """No mutation. Measurements must share explicitly identical context/scope."""
    limits=(cpd_limit,wirelength_limit,pipeline_limit)
    if not isinstance(cpd_limit,Fraction) or not isinstance(pipeline_limit,Fraction):
        raise ValueError('exact Fraction time/delay limits required')
    if type(wirelength_limit) is not int or any(x<0 for x in limits):
        raise ValueError('invalid limits')
    reasons=[]
    for key in ('context_sha256','timing_scope_sha256'):
        value=baseline.get(key)
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('invalid baseline identity')
        if candidate.get(key)!=value:reasons.append('mismatched_'+key)
    if baseline.get('success') is not True or baseline.get('physical_verified') is not True:
        return {'status':'INSUFFICIENT_BASELINE','reasons':['baseline_not_verified_success']}
    if candidate.get('success') is not True:reasons.append('candidate_route_failed')
    if candidate.get('physical_verified') is not True:reasons.append('candidate_route_unverified')
    for key,limit,kind in (('cpd_ns',cpd_limit,Fraction),('wirelength',wirelength_limit,int),('full_pipeline_s',pipeline_limit,Fraction)):
        value=candidate.get(key)
        if value is None:reasons.append('missing_'+key);continue
        if (kind is int and type(value) is not int) or (kind is Fraction and not isinstance(value,Fraction)) or value<0:
            raise ValueError('invalid candidate measurement '+key)
        if value>limit:reasons.append('exceeds_'+key)
    for key in ('route_sha256','measurement_receipt_sha256'):
        value=candidate.get(key)
        if not isinstance(value,str) or len(value)!=64 or any(c not in '0123456789abcdef' for c in value):reasons.append('missing_or_invalid_'+key)
    return {'status':'ACCEPT' if not reasons else 'REJECT','reasons':reasons}


def decide_recovery(baseline, candidate, contract):
    """Failed-baseline recovery with absolute protocol budgets, not fake QoR."""
    def identity(value):
        return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value)
    for key in ('context_sha256','timing_scope_sha256'):
        if not identity(baseline.get(key)):
            raise ValueError('invalid baseline identity')
    if baseline.get('success') is not False or baseline.get('failure_verified') is not True:
        return {'status':'INSUFFICIENT_BASELINE','reasons':['verified_failed_baseline_required']}
    reasons=[]
    for key in ('context_sha256','timing_scope_sha256'):
        if candidate.get(key)!=baseline[key]:reasons.append('mismatched_'+key)
    if candidate.get('success') is not True:reasons.append('candidate_route_failed')
    if candidate.get('physical_verified') is not True:reasons.append('candidate_route_unverified')
    if reasons:return {'status':'REJECT','reasons':reasons}
    if contract is None:
        return {'status':'INSUFFICIENT_BUDGET','reasons':['absolute_recovery_contract_required']}
    for key in ('protocol_sha256','context_sha256','timing_scope_sha256'):
        if not identity(contract.get(key)):
            raise ValueError('invalid contract identity '+key)
    if any(contract[key]!=baseline[key] for key in ('context_sha256','timing_scope_sha256')):
        return {'status':'REJECT','reasons':['mismatched_recovery_contract']}
    # Reuse the common candidate validator with a verified contextual reference.
    # This internal reference grants no baseline QoR or relative speedup claim.
    reference={'success':True,'physical_verified':True,
               'context_sha256':baseline['context_sha256'],
               'timing_scope_sha256':baseline['timing_scope_sha256']}
    result=decide(reference,candidate,cpd_limit=contract['cpd_limit'],
                  wirelength_limit=contract['wirelength_limit'],
                  pipeline_limit=contract['pipeline_limit'])
    return {**result,'mode':'absolute_failed_baseline_recovery',
            'contract_sha256':contract['protocol_sha256']}
