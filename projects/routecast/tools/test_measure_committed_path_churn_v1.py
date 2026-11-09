import copy,json
from measure_committed_path_churn_v1 import Replay


def main():
    r=dict(net_id=2,connection_id=3,source=5,sink=9,answer=dict(physical_edge_ids=[6,7]))
    e=dict(net_id=2,status='COMMITTED',primary_search_calls=1,retained_connection_ids=[],records=[r],objective_guard=dict(objective_delta='0'),prospective_overflow_delta=0)
    a=Replay([r]);a.event(0,e);s=a.finish_round(0,dict(affected_nets=[2]));assert s['committed_unchanged_NETs']==1 and s['primary_calls_in_unchanged_commits']==1
    changed=copy.deepcopy(e);changed['records'][0]['answer']['physical_edge_ids']=[10,11];a.event(1,changed);s=a.finish_round(1,dict(affected_nets=[2]));assert s['committed_changed_NETs']==1 and s['committed_changed_connections']==1
    same=copy.deepcopy(changed);a.event(2,same);assert a.finish_round(2,dict(affected_nets=[2]))['committed_unchanged_NETs']==1
    for mutation in ('objective','overflow','duplicate','identity'):
        bad=copy.deepcopy(e)
        if mutation=='objective':bad['objective_guard']['objective_delta']='1'
        elif mutation=='overflow':bad['prospective_overflow_delta']=1
        elif mutation=='duplicate':bad['records']*=2
        else:bad['records'][0]['connection_id']=99
        try:Replay([r]).event(0,bad)
        except ValueError:pass
        else:raise AssertionError('invalid churn input accepted')
    print(json.dumps(dict(all_pass=True,accepted_noop_path_change_and_updated_old_state_pass=True,corruptions_rejected=4)))


if __name__=='__main__':main()
