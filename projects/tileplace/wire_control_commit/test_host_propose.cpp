#include "enumerate_color_words.hpp"
#include "../wire_control/eligible_words.hpp"
#include "evaluate_batch_words.hpp"
#include "encode_rank_words.hpp"
#include "color_stats_words.hpp"
#include "full_color_words.hpp"
#include "host_propose.hpp"
#include <cassert>
#include <iostream>
#include <vector>
std::uint64_t unit_data[2][12]={{0ULL,1ULL,0ULL,0ULL,1ULL,1ULL,0ULL,0ULL,2ULL,1ULL,0ULL,0ULL},{0ULL,2ULL,0ULL,0ULL,2ULL,2ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL}};
std::uint32_t members[2][4]={{2ULL,5ULL,8ULL,0ULL},{2ULL,5ULL,8ULL,11ULL}};
std::uint64_t blocks[2][32]={{2ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,5ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,4294967296ULL,8ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,8589934592ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL},{2ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,5ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,8ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,4294967296ULL,11ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,4294967296ULL}};
std::uint64_t positions[2][8]={{0ULL,0ULL,1ULL,0ULL,2ULL,0ULL,0ULL,0ULL},{0ULL,0ULL,1ULL,0ULL,4ULL,0ULL,5ULL,0ULL}};
std::uint64_t sites[2][32]={{0ULL,0ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,0ULL,0ULL,0ULL,3ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL},{0ULL,0ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,0ULL,0ULL,0ULL,3ULL,0ULL,0ULL,0ULL,4ULL,0ULL,0ULL,0ULL,5ULL,0ULL,0ULL,0ULL,6ULL,0ULL,0ULL,0ULL,7ULL,0ULL,0ULL,0ULL}};
std::uint64_t config[2][8]={{3ULL,3ULL,4ULL,8ULL,8ULL,4ULL,4ULL,0ULL},{2ULL,4ULL,8ULL,8ULL,8ULL,8ULL,8ULL,0ULL}};
std::uint64_t expected[2][1152]={{0ULL,1ULL,0ULL,0ULL,0ULL,1ULL,2ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,1ULL,2ULL,0ULL,1ULL,0ULL,2ULL,2ULL,1ULL,0ULL,5ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,4ULL,3ULL,0ULL,1ULL,2ULL,3ULL,2ULL,1ULL,0ULL,5ULL,2ULL,0ULL,8ULL,0ULL,0ULL,0ULL,0ULL,0ULL,3ULL,2ULL,0ULL,1ULL,0ULL,2ULL,2ULL,1ULL,0ULL,5ULL,3ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,1ULL,2ULL,0ULL,2ULL,0ULL,2ULL,2ULL,2ULL,0ULL,8ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,4ULL,3ULL,0ULL,2ULL,1ULL,3ULL,2ULL,2ULL,0ULL,5ULL,0ULL,0ULL,8ULL,1ULL,0ULL,0ULL,0ULL,0ULL,3ULL,2ULL,0ULL,2ULL,0ULL,2ULL,2ULL,2ULL,0ULL,8ULL,3ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,1ULL,2ULL,3ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL},{0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,2ULL,0ULL,0ULL,5ULL,1ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,2ULL,1ULL,0ULL,5ULL,2ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,2ULL,2ULL,0ULL,5ULL,3ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,2ULL,2ULL,0ULL,1ULL,0ULL,4ULL,2ULL,4ULL,0ULL,5ULL,5ULL,0ULL,8ULL,0ULL,0ULL,11ULL,1ULL,0ULL,2ULL,2ULL,0ULL,1ULL,0ULL,4ULL,2ULL,4ULL,0ULL,5ULL,5ULL,0ULL,8ULL,0ULL,0ULL,11ULL,1ULL,0ULL,2ULL,2ULL,0ULL,1ULL,0ULL,4ULL,2ULL,4ULL,0ULL,5ULL,5ULL,0ULL,8ULL,0ULL,0ULL,11ULL,1ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,2ULL,6ULL,0ULL,5ULL,7ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,1ULL,0ULL,0ULL,0ULL,2ULL,2ULL,7ULL,0ULL,5ULL,8ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL,0ULL}};

int main(){for(unsigned mode=0;mode<2;++mode)for(unsigned f=0;f<2;++f){
 std::uint64_t roots[16],chain_roots[16],first[12],second[12],merged[12],descriptors[384],trials[768];std::uint32_t owners[192];unsigned count=0,owner_used=0,trial_used=0,status;bool overflow=false;
 std::uint32_t eligible[3];auto eligible_count=tileplace_wire_control::eligible(unit_data[f],config[f][0],members[f],config[f][1],nullptr,0,blocks[f],positions[f],config[f][1],8,8,0,eligible,3,status);assert(!status&&eligible_count==config[f][0]);std::uint64_t groups[6];
 tileplace_wire_control_commit::enumerate_color(eligible,eligible_count,unit_data[f],config[f][0],members[f],blocks[f],positions[f],config[f][1],sites[f],config[f][2],8,8,config[f][5],config[f][6],roots,8,chain_roots,8,first,second,merged,4,descriptors,64,owners,192,trials,256,count,owner_used,trial_used,overflow,status,groups,3);
 assert(!status&&!overflow&&count>8&&groups[0]==0&&groups[1]==8);
 for(unsigned i=0;i<8;++i){auto d=descriptors+6*i,e=expected[f]+18*i;assert(d[1]==e[0]&&d[3]==e[1]&&d[5]==e[5]);for(unsigned j=0;j<d[3];++j)assert(owners[d[2]+j]==e[2+j]);for(unsigned j=0;j<3*d[5];++j)assert(trials[3*d[4]+j]==e[6+j]);}
 // Independent analytic all-block net: singleton permutation has no HPWL gain;
 // macro owner translated to x=2 or x=6 gives HPWL 3 vs 5; identity picks x=2.
 std::uint64_t net[6]={7,0,0,config[f][1],0,0},scored[384],conflicts[384],writes[512];std::uint32_t touched[64],diagnostics[256];std::int32_t weights[3]={0,0,0};
 auto evaluated=tileplace_wire_control_commit::evaluate_batch(blocks[f],positions[f],config[f][1],sites[f],config[f][2],nullptr,0,nullptr,0,net,1,members[f],config[f][1],nullptr,0,nullptr,0,nullptr,0,nullptr,0,weights,descriptors,count,trials,trial_used,owner_used,scored,conflicts,64,writes,256,touched,64,diagnostics);
 assert(!evaluated.stage&&!evaluated.status);
 std::uint64_t candidates[448],records[832],identity_units[384],identity_trials[768],blocked[384],best7[448],compact13[832];std::uint8_t kinds[640];std::uint32_t fi[1]={2};std::uint32_t order[64],selected[64],gi[64],gathered[64],unique[64];
 auto result=tileplace_wire_control_commit::encode_rank(scored,count,owners,owner_used,unit_data[f],config[f][0],members[f],config[f][1],trials,trial_used,conflicts,writes,evaluated.writes,touched,evaluated.touched,owners,owner_used,blocks[f],config[f][1],positions[f],candidates,records,64,kinds,640,identity_units,192,identity_trials,256,order,selected,64,groups,eligible_count,fi,mode,blocked,best7,compact13,gi,gathered,unique);
 assert(!result.stage&&!result.status);
 auto stats=tileplace_wire_control_commit::color_stats(eligible_count,scored,count,selected,result);assert(!stats.status&&stats.eligible==eligible_count&&stats.proposals==(f?2U:0U)&&stats.accepted==(f?1U:0U)&&stats.rejected==(f?1U:0U)&&stats.kinds[0]==(f?1U:0U));for(unsigned k=1;k<5;++k)assert(!stats.kinds[k]);
 if(f==0){assert(result.selected==0&&result.moved==0&&positions[f][0]==0&&positions[f][2]==1&&positions[f][4]==2);}
 else{assert(result.selected==1&&selected[0]==(mode?6U:2U)&&result.moved==2&&positions[f][0]==(mode?6U:2U)&&positions[f][2]==(mode?7U:3U)&&positions[f][4]==4&&positions[f][6]==5);assert(scored[12]==std::uint64_t(-419431));}

 // Exercise the reusable full_color entry with identical initial state.
 positions[0][0]=0;positions[0][2]=1;positions[0][4]=2;positions[1][0]=0;positions[1][2]=1;positions[1][4]=4;positions[1][6]=5;
 std::uint64_t kc=0,uc=0,tc=0;for(unsigned i=0;i<count;++i){auto c=candidates+7*i;kc=std::max(kc,c[1]+c[2]);uc=std::max(uc,c[3]+c[4]);tc=std::max(tc,c[5]+c[6]);}
 std::vector<std::uint8_t> ext_kinds(kinds,kinds+kc);std::vector<std::uint64_t> ext_units(identity_units,identity_units+2*uc),ext_trials(identity_trials,identity_trials+3*tc);std::vector<std::uint32_t> ext_members(members[f],members[f]+config[f][1]);std::uint64_t ext_identity[6];for(unsigned j=0;j<6;++j)ext_identity[j]=candidates[7*2+1+j];
 tileplace_wire_control_commit::ExternalForbidden external{ext_identity,1,{ext_kinds.data(),kc,ext_units.data(),uc,ext_members.data(),ext_members.size(),ext_trials.data(),tc}};
 tileplace_wire_control_commit::ColorInput input{};
 input.blocks=blocks[f];input.units=unit_data[f];input.sites=sites[f];input.nets=net;input.positions=positions[f];input.unit_members=members[f];input.net_members=members[f];input.weights=weights;input.block_count=config[f][1];input.unit_count=config[f][0];input.site_count=config[f][2];input.net_count=1;input.unit_member_count=input.net_member_count=config[f][1];input.width=input.height=8;input.limit=config[f][5];input.chain_limit=config[f][6];input.forbidden_indices=fi;input.forbidden_count=0;if(mode)input.external_forbidden=&external;
 tileplace_wire_control_commit::ColorScratch scratch{roots,chain_roots,first,second,merged,descriptors,trials,groups,scored,conflicts,writes,candidates,records,identity_units,identity_trials,blocked,best7,compact13,eligible,owners,touched,diagnostics,order,selected,gi,gathered,unique,kinds,8,8,4,64,192,256,3,256,64,640,192};
 auto whole=tileplace_wire_control_commit::full_color(input,scratch);assert(!whole.stage&&!whole.status&&whole.enumerated==count&&whole.moved==result.moved&&whole.stats.eligible==stats.eligible&&whole.stats.proposals==stats.proposals&&whole.stats.accepted==stats.accepted&&whole.stats.rejected==stats.rejected);
 if(f)assert(selected[0]==(mode?6U:2U)&&positions[f][0]==(mode?6U:2U)&&positions[f][2]==(mode?7U:3U));
 positions[0][0]=0;positions[0][2]=1;positions[0][4]=2;positions[1][0]=0;positions[1][2]=1;positions[1][4]=4;positions[1][6]=5;

 auto proposed=tileplace_wire_control_commit::propose(input,scratch);
 assert(proposed.stats.eligible==stats.eligible&&proposed.stats.proposals==stats.proposals&&proposed.stats.accepted==stats.accepted&&proposed.stats.rejected==stats.rejected);
 assert(proposed.proposals.size()==(f?1U:0U));
 if(f){const auto& p=proposed.proposals[0];assert(p.kind=="move"&&p.score==-419431&&p.units.size()==1&&p.units[0].size()==2&&p.units[0][0]==2&&p.units[0][1]==5&&p.trial.size()==2&&p.trial.at(2).x==(mode?6:2)&&p.trial.at(5).x==(mode?7:3)&&p.write_sites.size()==4&&p.touched_nets==std::set<std::uint32_t>{7});}
 assert(positions[0][0]==0&&positions[0][2]==1&&positions[0][4]==2&&positions[1][0]==0&&positions[1][2]==1&&positions[1][4]==4&&positions[1][6]==5);
 }std::cout<<"eligible -> multi-group five-kind enumeration -> evaluation/rank/commit with forbidden fallback PASS\n";}
