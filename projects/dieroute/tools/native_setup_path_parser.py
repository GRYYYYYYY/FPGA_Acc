"""Native setup report parser retaining clocked timing points and slack."""
import re
from decimal import Decimal


def parse(text):
    assert '# Unit scale: 1e-09 seconds' in text and '# Output precision: 3' in text
    expected=int(re.search(r'#Timing report of worst (\d+) path',text)[1]);paths=[]
    for match in re.finditer(r'^#Path\s+(\d+)[ \t]*\n(.*?)(?=^#Path\s|\Z)',text,re.M|re.S):
        block=match[2];start=re.search(r'^Startpoint:\s*(.*?)\s+\(',block,re.M)[1];end=re.search(r'^Endpoint\s*:\s*(.*?)\s+\(',block,re.M)[1]
        arrival=Decimal(re.search(r'^data arrival time\s+(-?\d+\.\d+)\s*$',block,re.M)[1])
        required=Decimal(re.search(r'^data required time\s+(-?\d+\.\d+)\s*$',block,re.M)[1])
        slack=Decimal(re.search(r'^slack\s+\([^)]*\)\s+(-?\d+\.\d+)\s*$',block,re.M)[1])
        assert abs(required-arrival-slack)<=Decimal('0.002')
        rows=[]
        for line in block.split('data arrival time',1)[0].splitlines():
            row=re.match(r'^(.*?)\s+(-?\d+\.\d+)\s+(-?\d+\.\d+)\s*$',line)
            if row and re.search(r'\(\.[^)]+\)',row[1]):rows.append(dict(point=row[1].strip(),increment_ns=row[2],path_ns=row[3]))
        assert rows and rows[-1]['point'].split(' (',1)[0]==end and Decimal(rows[-1]['path_ns'])==arrival
        assert any(r['point'].split(' (',1)[0]==start for r in rows)
        arcs=[];previous='<external>'
        for row in rows:arcs.append(dict(source=previous,target=row['point'],increment_ns=row['increment_ns']));previous=row['point']
        paths.append(dict(index=int(match[1]),startpoint=start,endpoint=end,arrival_ns=str(arrival),required_ns=str(required),slack_ns=str(slack),effective_delay_ns=str(-slack),arcs=arcs))
    assert len(paths)==expected
    return paths
