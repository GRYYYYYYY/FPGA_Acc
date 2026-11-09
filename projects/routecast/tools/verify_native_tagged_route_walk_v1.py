"""Pin-tag duplicate SINK and branch restore contracts, missing tags fail closed."""
import tempfile
from pathlib import Path
from native_tagged_route_walk_v1 import walk


def main():
    text='''Net 7 (data)
Node: 0 SOURCE (0,0,0) Class: 0 Switch: 1
Node: 1 OPIN (0,0,0) Pin: 0 Switch: 2
Node: 2 CHANX (0,0,0) to (1,0,0) Track: 0 Switch: 3
Node: 3 IPIN (1,0,0) Pin: 0 Switch: 0
Node: 4 SINK (1,0,0) Class: 0 Switch: -1 Net_pin_index: 1
Node: 3 IPIN (1,0,0) Pin: 0 Switch: 0
Node: 4 SINK (1,0,0) Class: 0 Switch: -1 Net_pin_index: 2
'''
    with tempfile.TemporaryDirectory(prefix='routecast_native_pin_walk_') as folder:
        p=Path(folder)/'route';p.write_text(text);events=list(walk(p))
        assert [x for x in events if x[0]=='arc']==[('arc',7,0,1,1),('arc',7,1,2,2),('arc',7,2,3,3),('arc',7,3,4,0),('arc',7,3,4,0)]
        assert [x for x in events if x[0]=='sink']==[('sink',7,0,4,1),('sink',7,0,4,2)]
        p.write_text(text.replace(' Net_pin_index: 2',''))
        try:list(walk(p))
        except ValueError as error:assert 'Missing explicit SINK' in str(error)
        else:raise AssertionError('Missing pin tag accepted')
        p.write_text(text+'Net 7 (data)\n')
        try:list(walk(p))
        except AssertionError:pass
        else:raise AssertionError('Duplicate NET header accepted')
    print('PASS duplicate SINK pin identity, branch restoration, missing tag and duplicate NET rejection')


if __name__=='__main__':main()
