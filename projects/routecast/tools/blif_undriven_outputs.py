"""VPR-style undriven combinational primitive output classification.

No logic value inference. Architecture model timing edges determine upstream
ports; clock/sequential outputs are excluded. Explicit nets remain connected,
including a net literally named open; only omitted assignments are undriven.
"""
import re
from pathlib import Path
import xml.etree.ElementTree as ET

def undriven_outputs(atom,architecture):
    models={}
    for m in ET.parse(architecture).getroot().findall('models/model'):
        name=m.get('name')
        if not name or name in models:raise ValueError('duplicate/invalid model')
        inputs={};outputs={}
        for parent,target in (('input_ports',inputs),('output_ports',outputs)):
            for p in m.findall(parent+'/port'):
                n=p.get('name')
                if not n or n in target:raise ValueError('duplicate/invalid model port')
                target[n]=dict(p.attrib)
        if set(inputs)&set(outputs):raise ValueError('ambiguous port direction')
        for p in inputs.values():
            if set(p.get('combinational_sink_ports','').split())-set(outputs):raise ValueError('unknown timing output')
        models[name]=(inputs,outputs)
    logical=[];pending=''
    for raw in Path(atom).read_text().splitlines():
        line=raw.split('#',1)[0].strip()
        if line.endswith('\\'):pending+=line[:-1]+' ';continue
        line=pending+line;pending=''
        if line:logical.append(line)
    if pending:raise ValueError('unterminated BLIF continuation')
    result={};drivers=set()
    for line in logical:
        tokens=line.split()
        if not tokens or tokens[0]!='.subckt':continue
        if len(tokens)<2:raise ValueError('missing subckt model')
        name=tokens[1]
        if name not in models:continue
        inputs,outputs=models[name];assignments={}
        for token in tokens[2:]:
            if token.count('=')!=1:raise ValueError('invalid subckt assignment')
            pin,net=token.split('=');port=re.sub(r'\[\d+\]$','',pin)
            if not net or port not in inputs and port not in outputs or pin in assignments:raise ValueError('unknown/duplicate subckt pin')
            assignments[pin]=(port,net)
        connected={p for p,n in assignments.values() if p in inputs}
        for port,net in assignments.values():
            if port not in outputs:continue
            if net in drivers:raise ValueError('duplicate primitive output driver')
            drivers.add(net);output=outputs[port]
            if output.get('clock','') or output.get('is_clock','0') not in ('0','false','False',''):continue
            upstream=sorted(n for n,p in inputs.items() if port in p.get('combinational_sink_ports','').split())
            if connected.intersection(upstream):continue
            result[net]={'model':name,'output_port':port,'upstream_ports':upstream,'classification':'undriven_combinational_output','constant_value':None}
    return result
