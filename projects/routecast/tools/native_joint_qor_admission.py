"""Explicit zero-tolerance native CPD/wire admission; caller owns proof binding."""
from fractions import Fraction

def decide(candidate, reference):
    """Reject malformed metrics; select reference unless candidate jointly qualifies."""
    def validate(value):
        if not isinstance(value,dict) or set(value)!={'cpd_ns','wirelength'}:
            raise ValueError('native metric pair requires CPD and wirelength')
        cpd=value['cpd_ns']
        if type(cpd) not in (str,int,Fraction):
            raise ValueError('CPD must be exact finite numeric text/int/Fraction')
        try: cpd=Fraction(cpd)
        except (ValueError,ZeroDivisionError,TypeError) as ex:
            raise ValueError('invalid finite CPD') from ex
        wire=value['wirelength']
        if cpd<0 or type(wire) is not int or wire<0:
            raise ValueError('negative CPD or noninteger/negative wirelength')
        return cpd,wire
    ref_cpd,ref_wire=validate(reference)
    if candidate is None:
        return dict(selected='reference',reason='NO_QUALIFIED_NATIVE_CANDIDATE')
    cpd,wire=validate(candidate)
    failed=[]
    if cpd>ref_cpd:failed.append('CPD_REGRESSION')
    if wire>ref_wire:failed.append('WIRE_REGRESSION')
    return dict(selected='reference' if failed else 'candidate',reason='+'.join(failed) if failed else 'JOINT_NATIVE_QOR_NONREGRESSION')
