"""Conservative BLIF .names constant propagation; no latch/subckt inference."""
from pathlib import Path


def constants(path):
    logical=[];pending=''
    for raw in Path(path).read_text().splitlines():
        line=raw.split('#',1)[0].strip()
        if line.endswith('\\'):pending+=line[:-1]+' ';continue
        line=pending+line;pending=''
        if line:logical.append(line)
    if pending:raise ValueError('unterminated BLIF continuation')
    tables=[];current=None
    for line in logical:
        if line.startswith('.'):
            current=None
            if line.startswith('.names '):
                fields=line.split()[1:];current=(fields[:-1],fields[-1],[]);tables.append(current)
        elif current is not None:current[2].append(line.split())
    drivers=[out for _,out,_ in tables]
    if len(drivers)!=len(set(drivers)):raise ValueError('duplicate .names driver')
    known={};changed=True
    while changed:
        changed=False
        for inputs,out,rows in tables:
            if out in known or any(n not in known for n in inputs):continue
            matching=[];polarities=set()
            for row in rows:
                if inputs:
                    if len(row)!=2 or len(row[0])!=len(inputs) or set(row[0])-set('01-'):raise ValueError('invalid cube')
                    pattern,value=row
                    match=all(c=='-' or int(c)==known[n] for c,n in zip(pattern,inputs))
                else:
                    if len(row)!=1:raise ValueError('invalid zero-input cube')
                    value=row[0];match=True
                if value not in {'0','1'}:raise ValueError('invalid cube output')
                polarities.add(int(value))
                if match:matching.append(int(value))
            if len(polarities)>1:raise ValueError('mixed polarity unsupported')
            value=matching[0] if matching else (1-next(iter(polarities)) if polarities else 0)
            known[out]=value;changed=True
    return known
