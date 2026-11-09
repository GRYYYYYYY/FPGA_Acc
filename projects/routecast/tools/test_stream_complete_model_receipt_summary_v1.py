"""Receipt reader must traverse late fields and reject corrupt complete schedules."""
import json,tempfile
from pathlib import Path
from stream_complete_model_receipt_summary_v1 import summarize


def main():
    fixture={'bindings':{},'rounds':[{'round_index':0,'affected_nets':['a','b'],'events':[{'net_id':'a','status':'COMMITTED'},{'net_id':'b','status':'RETAIN_OBJECTIVE_INCREASE','fallback':{}}],'seconds':3.5,'overflow_before':8,'overflow_after':2}],'feedback_seconds':4.5,'files':{}}
    failures=0
    with tempfile.TemporaryDirectory() as directory:
        p=Path(directory)/'receipt.json';p.write_text(json.dumps(fixture))
        for chunk in (1,7,64,65536):
            s=summarize(p,chunk)
            assert s['timers']=={'feedback_seconds':4.5}
            assert s['rounds']==[dict(round_index=0,seconds=3.5,events=2,status_counts={'COMMITTED':1,'RETAIN_OBJECTIVE_INCREASE':1},fallback_calls=1,overflow_before=8,overflow_after=2)]
        good=p.read_text()
        p.write_text(good.replace('"a"','12').replace('"b"','13'));assert summarize(p,1)['rounds'][0]['events']==2
        p.write_text(good.replace('4.5','4.5e-12'));assert summarize(p,1)['timers']['feedback_seconds']==4.5e-12
        p.write_text(good)
        bad=[good+' trailing',good[:-1],good.replace('"round_index": 0','"round_index": 2'),good.replace('"net_id": "b"','"net_id": "a"'),good.replace('"affected_nets": ["a", "b"]','"affected_nets": ["b", "a"]'),good.replace('"feedback_seconds": 4.5','"feedback_seconds": NaN'),good.replace('"bindings": {}','"bindings": {}, "bindings": {}')]
        for data in bad:
            p.write_text(data)
            try:summarize(p,7)
            except (ValueError,TypeError):failures+=1
            else:raise AssertionError('corrupt receipt accepted')
    print(json.dumps(dict(chunk_sizes=4,corruptions_rejected=failures,all_pass=True)))


if __name__=='__main__':main()
