"""Chunk-boundary, complete-cohort and strict-corruption contracts."""
import io
import json
from pathlib import Path
import tempfile
from bounded_model_json_stream_v1 import Reader,records,object_members,round_events


def main():
    items=[dict(net_id=i,token='nested ["{}] \\ unicode Ω',records=[{'n':i},[True,None,False]]) for i in range(30)]
    payload=dict(bindings={'x':'123'},rounds=[dict(round_index=j,events=items,seconds=.1) for j in range(2)],records=items,ledger={'0':2})
    source=json.dumps(payload)
    for chunk in [1,2,7,31,65536]:
        r=Reader(io.StringIO(source),chunk=chunk)
        assert r.value()==payload;r.finish()
    with tempfile.TemporaryDirectory() as t:
        path=Path(t)/'model.json';path.write_text(source)
        assert list(records(path))==items
        assert dict(object_members(path,'bindings'))==payload['bindings']
        assert list(round_events(path))==[(j,e) for j in range(2) for e in items]
        rejected=0
        for bad in [source[:-1],source+'{}',source.replace('"round_index": 1','"round_index": 7'),
                    source.replace('"net_id": 0','"net_id": 0, "net_id": 1',1),
                    source.replace('0.1','NaN',1),'{"rounds": [], "rounds": []}',
                    source.replace('"events":','"absent":',1)]:
            path.write_text(bad)
            try:list(round_events(path))
            except (ValueError,json.JSONDecodeError):rejected+=1
            else:raise AssertionError('invalid stream accepted')
        assert rejected==7
    r=Reader(io.StringIO('"'+'x'*100+'"'),chunk=7,max_value=32)
    try:r.value()
    except ValueError:pass
    else:raise AssertionError('value bound ignored')
    print('PASS five chunk sizes, all record/member/event identities, seven corruptions and value bound')


if __name__=='__main__':main()
