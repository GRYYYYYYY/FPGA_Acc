"""Full event/metadata comparison must reject subtle domain and order changes."""
import copy,json,tempfile
from pathlib import Path
from compare_complete_receipt_events_stream_v1 import compare


def main():
    ref={'rounds':[{'round_index':0,'events':[{'net_id':1,'old_epoch':1,'status':'COMMITTED','path':[2,3]}],'affected_nets':[1],'overflow_after':2,'seconds':1.2e-9,'state_file':'old'}],'total_paid_resident_seconds':1.0}
    with tempfile.TemporaryDirectory() as d:
        a=Path(d)/'a';b=Path(d)/'b';a.write_text(json.dumps(ref));same=copy.deepcopy(ref);same['rounds'][0].update(seconds=100,state_file='new');same['total_paid_resident_seconds']=300;b.write_text(json.dumps(same))
        for n in (1,7,64,65536):assert compare(a,b,n)[0]['events']==1
        mutations=[]
        for field,value in [('old_epoch',2),('old_epoch',True),('old_epoch',1.0),('path',[3,2]),('status','RETAIN')]:
            v=copy.deepcopy(same);v['rounds'][0]['events'][0][field]=value;mutations.append(json.dumps(v))
        v=copy.deepcopy(same);v['rounds'][0]['overflow_after']=3;mutations.append(json.dumps(v))
        v=copy.deepcopy(same);v['rounds'][0]['events']=[];mutations.append(json.dumps(v))
        mutations.extend([json.dumps(same)+'tail',json.dumps(same)[:-1]])
        for v in mutations:
            b.write_text(v)
            try:compare(a,b,7)
            except ValueError:pass
            else:raise AssertionError('corruption accepted')
    print(json.dumps(dict(all_pass=True,chunk_sizes=4,corruptions_rejected=len(mutations),only_timing_and_state_file_ignored=True)))


if __name__=='__main__':main()
