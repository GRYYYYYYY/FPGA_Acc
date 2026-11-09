"""Expose native RAM pins as cut boundaries; keep original reconstruction records."""
from copy import deepcopy
from combinational_cut_export_v3 import export

def export_native(module):
    cut=deepcopy(module)
    macros={n:c for n,c in module['cells'].items() if c['type']=='dual_port_ram'}
    for i,(name,cell) in enumerate(macros.items()):
        assert set(cell['connections'])=={'clk','we1','we2','addr1','addr2','data1','data2','out1','out2'}
        for pin,bits in cell['connections'].items():
            direction=cell['port_directions'][pin]
            assert direction==('output' if pin in ('out1','out2') else 'input')
            assert all(type(b) is int or b in ('0','1') for b in bits)
            label=f'__rc_ram_boundary_{i}_{pin}'
            assert label not in cut['ports']
            cut['ports'][label]=dict(direction='input' if direction=='output' else 'output',bits=bits)
        del cut['cells'][name]
    text,synthetic_boundary=export(cut)
    reconstruction=dict(cells=synthetic_boundary['cells'],ports=module['ports'],native_ram=macros,
        initialized_nets={n:v for n,v in module['netnames'].items() if 'init' in v['attributes']})
    return text,reconstruction,cut,synthetic_boundary
