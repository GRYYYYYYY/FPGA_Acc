"""Exact compression of incoming potential inequalities for positive scalar costs."""


def required_other_demand(destination_potential, incoming):
    """Return minimum nonnegative demand satisfying p(v)<=p(u)+s*(1+d)."""
    if type(destination_potential) is not int or destination_potential < 0:
        raise ValueError('nonnegative integer potential required')
    required = 0
    for source_potential, scalar in incoming:
        if type(source_potential) is not int or source_potential < 0:
            raise ValueError('nonnegative integer potential required')
        if type(scalar) is not int or scalar <= 0:
            raise ValueError('strictly positive integer scalar required')
        delta = destination_potential-source_potential
        required = max(required, -((-delta)//scalar)-1)
    return required
