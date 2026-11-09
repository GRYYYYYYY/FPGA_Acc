#pragma once
#include "net_commit_hbm.hpp"
#include <algorithm>
#include <array>
#include <cstring>
#include <map>
#include <set>
#include <stdexcept>
#include <string>
#include <vector>
#include <iostream>
namespace commit_test {
using namespace dieroute;
inline void check(bool v,const std::string& why){if(!v)throw std::runtime_error(why);}
struct Fixture {
 std::array<SummaryWord,2> command{};
 std::array<std::uint64_t,12> policy{};
 std::array<std::uint64_t,13> offsets{};
 std::array<std::uint64_t,64> arcs{},reads{},paths{};
 std::array<SummaryWord,16> shadows{},branches{};
 std::array<SummaryWord,48> resources{};
 std::array<SummaryWord,64> trees{};
 std::array<SummaryWord,8> nets{};
 SummaryWord control{},completion{};
 std::array<SummaryWord,256> scratch{};
 std::array<SummaryWord,32> deltas{};
 unsigned calls=0,scratch_capacity=128,delta_capacity=32;
 std::uint64_t arc_count=0,session=1;
 std::map<std::pair<unsigned,unsigned>,unsigned> edges;
 Fixture(){
  const unsigned masks[]={1,1,1,3,2,2,2,6,4,4,4,4};
  for(unsigned n=0;n<12;++n)policy[n]=UINT32_MAX|(std::uint64_t(masks[n])<<32);
  const unsigned graph[][2]={{0,1},{1,3},{3,5},{5,7},{7,9},{4,3},{4,6},{6,7},{8,10},{10,7},{0,2},{2,11},{3,1},{8,11},{4,5}};
  for(unsigned i=0;i<15;++i)edges[{graph[i][0],graph[i][1]}]=i*2;
  for(unsigned n=0;n<12;++n){offsets[n]=arc_count;for(const auto& edge:edges)if(edge.first.first==n)arcs[arc_count++]=edge.first.second|(std::uint64_t(edge.second)<<32);}
  offsets[12]=arc_count;
 }
 unsigned owner(unsigned n)const{auto mask=policy.at(n)>>32&255;unsigned d=0;while(!(mask&(1u<<d)))++d;return d;}
 const SummaryWord* resource(unsigned n)const{for(const auto& r:resources)if(r.w[0]==session&&std::uint32_t(r.w[4])==n)return &r;return nullptr;}
 std::uint64_t version(unsigned n)const{auto r=resource(n);return r?r->w[3]:0;}
 std::set<unsigned> members(unsigned n)const{std::set<unsigned> found;auto r=resource(n);if(!r)return found;auto cursor=r->w[5];for(std::uint64_t i=0;i<r->w[1];++i){check(cursor<trees.size(),"member bounds");auto e=trees[cursor];found.insert(unsigned(nets[e.w[2]].w[1]));cursor=e.w[7];}check(cursor==commit_none,"member tail");return found;}
 std::map<unsigned,SummaryWord> tree(unsigned slot)const{std::map<unsigned,SummaryWord> result;auto net=nets.at(slot);auto cursor=net.w[3];for(std::uint64_t i=0;i<net.w[4];++i){check(cursor<trees.size(),"tree bounds");auto e=trees[cursor];check(result.emplace(unsigned(e.w[1]),e).second,"duplicate net node");cursor=e.w[6];}check(cursor==commit_none,"net tail");return result;}
 std::vector<unsigned char> state()const{std::vector<unsigned char> bytes;auto add=[&](const void* p,std::size_t n){auto x=static_cast<const unsigned char*>(p);bytes.insert(bytes.end(),x,x+n);};add(resources.data(),sizeof(resources));add(trees.data(),sizeof(trees));add(nets.data(),sizeof(nets));add(&control,sizeof(control));return bytes;}
 void request(std::uint64_t op,unsigned slot=0,unsigned id=0){command={};reads={};shadows={};branches={};paths={};command[0].w[0]=session;command[0].w[1]=op;command[0].w[2]=control.w[1];command[0].w[3]=slot;command[0].w[4]=id;command[0].w[5]=(op!=commit_initialize&&op!=commit_negotiate&&nets.at(slot).w[0]==session)?nets[slot].w[5]:0;command[0].w[6]=control.w[2]?control.w[2]:1;}
 void footprint(const std::vector<unsigned>& nodes){command[1].w[0]=nodes.size();for(unsigned i=0;i<nodes.size();++i){reads[i*2]=nodes[i];reads[i*2+1]=version(nodes[i]);}}
 void branch(unsigned attachment,const std::vector<unsigned>& nodes,unsigned slot){
  auto count=command[1].w[2]++;auto& b=branches.at(count);b.w[0]=attachment;b.w[1]=nodes.empty()?attachment:nodes.back();b.w[2]=command[1].w[3];b.w[3]=nodes.size();auto values=tree(slot);auto parent=attachment;auto depth=values.at(parent).w[5];std::uint64_t cost=0;
  for(unsigned n:nodes){auto r=resource(n);cost+=1+(r?r->w[2]:0)+control.w[2]*(r?r->w[1]-members(n).count(unsigned(nets[slot].w[1])):0);auto pos=command[1].w[3]++;paths.at(pos*2)=n|(std::uint64_t(edges.at({parent,n}))<<32);paths.at(pos*2+1)=0;parent=n;++depth;}
  b.w[4]=depth;b.w[5]=cost;
 }
 void verify()const{
  check(control.w[0]==session&&control.w[3]<=trees.size(),"control domain");std::set<std::uint64_t> live,free;std::map<unsigned,std::set<unsigned>> expected;
  for(unsigned slot=0;slot<nets.size();++slot){auto n=nets[slot];if(n.w[0]!=session)continue;auto t=tree(slot);check(t.size()==n.w[4]&&n.w[5]&&t.count(unsigned(n.w[2])),"net inventory");
   auto cursor=n.w[3];for(std::uint64_t i=0;i<n.w[4];++i){auto e=trees.at(cursor);check(e.w[0]==session&&e.w[2]==slot&&live.insert(cursor).second,"live tree alias");cursor=e.w[6];}
   for(const auto& item:t){const auto& e=item.second;expected[item.first].insert(unsigned(n.w[1]));
    if(item.first==n.w[2])check(e.w[3]==UINT32_MAX&&e.w[4]==UINT32_MAX&&e.w[5]==0,"root metadata");
    else {check(t.count(unsigned(e.w[3]))&&t.at(unsigned(e.w[3])).w[5]+1==e.w[5],"tree ancestry");check(edges.at({unsigned(e.w[3]),item.first})==e.w[4],"tree PIP");}
   }
  }
  for(unsigned index=0;index<resources.size();++index){auto r=resources[index];if(r.w[0]!=session)continue;auto n=std::uint32_t(r.w[4]);check(n<policy.size()&&index/16==owner(n)&&r.w[4]==(n|((policy[n]>>32&255)<<32)),"owner shard/topology");check(r.w[3]&&r.w[2]!=UINT64_MAX&&members(n)==expected[n]&&r.w[1]==expected[n].size(),"resource memberships");}
  for(const auto& item:expected)check(resource(item.first),"missing owner record");
  auto cursor=control.w[4];while(cursor!=commit_none){check(cursor<control.w[3]&&free.insert(cursor).second&&!live.count(cursor),"free chain alias");auto e=trees.at(cursor);for(unsigned i=0;i<7;++i)check(e.w[i]==0,"free record not cleared");cursor=e.w[7];}
  check(live.size()+free.size()==control.w[3],"lost allocated tree entry");
 }
 void run(std::uint64_t status=commit_ok,bool valid_state=true){auto before=state();
  dieroute_net_commit_hbm(command.data(),policy.data(),offsets.data(),arcs.data(),reads.data(),shadows.data(),branches.data(),paths.data(),resources.data(),trees.data(),nets.data(),&control,scratch.data(),deltas.data(),&completion,12,arc_count,3,16,8,64,32,16,16,32,scratch_capacity,delta_capacity);++calls;
  check(completion.w[0]==status,"call "+std::to_string(calls)+" status "+std::to_string(completion.w[0])+" expected "+std::to_string(status));
  if(status!=commit_ok)check(state()==before,"rejected transaction changed authority");
  if(valid_state)verify();
  if(status==commit_ok)for(unsigned i=0;i<completion.w[7];++i){auto d=deltas.at(i);auto n=std::uint32_t(d.w[1]);auto r=resource(n);check(d.w[0]==session&&d.w[1]==(n|(std::uint64_t(owner(n))<<32))&&d.w[2]==(r?r->w[1]:0)&&d.w[3]==(r?r->w[2]:0)&&d.w[4]==(r?r->w[3]:0)&&d.w[5]==control.w[1]&&d.w[6]==(policy[n]>>32&255),"delta differs from hardware authority");}
 }
 void start(unsigned slot,unsigned id,unsigned root){request(commit_start,slot,id);command[0].w[7]=root;run();}
};
}
