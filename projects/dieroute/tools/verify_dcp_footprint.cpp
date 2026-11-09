// Independent, read-only verification of DcpRouteFootprint LE tables.
// This checks the exported used-resource graph, not available routing choices.
#include <algorithm>
#include <array>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>

namespace fs = std::filesystem;
constexpr uint32_t absent = UINT32_MAX;
void require(bool ok, const std::string& message) { if (!ok) throw std::runtime_error(message); }
struct Table {
    int fd; const unsigned char* data; size_t bytes, width, count;
    Table(const fs::path& p, size_t w): width(w) {
        fd=open(p.c_str(),O_RDONLY); require(fd>=0,"open " + p.string());
        struct stat st{}; require(fstat(fd,&st)==0,"stat failed"); bytes=st.st_size;
        require(bytes%(4*w)==0,"truncated table " + p.string()); count=bytes/(4*w);
        data=bytes?static_cast<const unsigned char*>(mmap(nullptr,bytes,PROT_READ,MAP_PRIVATE,fd,0)):nullptr;
        require(!bytes || data!=MAP_FAILED,"mmap failed");
    }
    ~Table(){ if(bytes)munmap(const_cast<unsigned char*>(data),bytes); close(fd); }
    uint32_t at(size_t row,size_t col) const {
        require(row<count && col<width,"table bounds"); const auto* p=data+4*(row*width+col);
        return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);
    }
};
std::vector<std::string> csv(const std::string& s) {
    std::vector<std::string> result; std::string field; bool quoted=false;
    for(size_t i=0;i<s.size();i++) {
        if(s[i]=='"') { if(quoted && i+1<s.size() && s[i+1]=='"'){field+='"';i++;}else quoted=!quoted; }
        else if(s[i]==',' && !quoted){result.push_back(field);field.clear();}
        else if(s[i]!='\r')field+=s[i];
    }
    require(!quoted,"unterminated CSV field");result.push_back(field);return result;
}
uint32_t number(const std::string& s) {
    size_t end=0; auto n=std::stoull(s,&end);require(end==s.size() && n<=UINT32_MAX,"bad u32");return n;
}
struct Tile {uint32_t die,wires;};
struct Member {uint64_t key;uint32_t node;bool operator<(const Member& b)const{return key<b.key;}};
uint64_t key(uint32_t tile,uint32_t wire){return (uint64_t(tile)<<32)|wire;}

int main(int argc,char** argv) {
    try {
        require(argc==3,"usage: verify_dcp_footprint INPUT_DIR NEW_OUTPUT_DIR");
        fs::path in=argv[1],out=argv[2];require(fs::create_directory(out),"output must be new");
        Table nodes(in/"nodes.bin",16),nets(in/"nets.bin",16),wires(in/"wires.bin",3),owners(in/"owners.bin",2),
              pips(in/"pips.bin",8),pins(in/"pins.bin",4),tasks(in/"tasks.bin",8);
        require(nodes.count<absent && nets.count<absent,"ID width exceeded");
        std::map<uint32_t,Tile> tiles;
        std::ifstream tilefile(in/"tiles.csv");require(bool(tilefile),"missing tiles.csv");std::string line;std::getline(tilefile,line);
        while(std::getline(tilefile,line)) {
            auto v=csv(line);require(v.size()==6,"tile CSV width");uint32_t d=number(v[2]);require(d<8,"SLR range");
            require(tiles.emplace(number(v[0]),Tile{d,number(v[5])}).second,"duplicate tile address");
        }
        std::map<uint32_t,std::string> intents;
        std::ifstream intentfile(in/"intents.csv");require(bool(intentfile),"missing intents.csv");std::getline(intentfile,line);
        while(std::getline(intentfile,line)){auto v=csv(line);require(v.size()==2,"intent CSV width");require(intents.emplace(number(v[0]),v[1]).second,"duplicate intent");}
        auto tile=[&](uint32_t id)->const Tile&{auto it=tiles.find(id);require(it!=tiles.end(),"unknown tile");return it->second;};
        std::vector<Member> members;members.reserve(wires.count);size_t wi=0;
        for(size_t id=0;id<nodes.count;id++) {
            require(nodes.at(id,0)==id,"node ID order"); uint32_t mask=0,n=nodes.at(id,6);require(n>0,"empty node");
            require(n<=wires.count-wi,"wire slice overflow");uint64_t previous=0;
            for(uint32_t j=0;j<n;j++,wi++) {
                require(wires.at(wi,0)==id,"wire grouping");uint32_t t=wires.at(wi,1),w=wires.at(wi,2);
                auto& info=tile(t);require(w<info.wires,"wire index range");mask|=1u<<info.die;uint64_t k=key(t,w);
                require(j==0 || k>previous,"wire sort/duplicate");
                if(!j)require(k==key(nodes.at(id,1),nodes.at(id,2)),"canonical representative mismatch");
                previous=k;members.push_back({k,uint32_t(id)});
            }
            require(mask==nodes.at(id,5),"SLR membership mismatch");require(intents.count(nodes.at(id,12)),"unknown intent");
            require((nodes.at(id,11)&~7u)==0,"unknown node flags");
            for(int c=13;c<16;c++)require(nodes.at(id,c)==0,"reserved node field");
        }
        require(wi==wires.count,"unclaimed wires");std::sort(members.begin(),members.end());
        for(size_t i=1;i<members.size();i++)require(members[i-1].key!=members[i].key,"member wire assigned to multiple nodes");
        auto resolve=[&](uint32_t t,uint32_t w)->uint32_t{
            Member sought{key(t,w),0};auto it=std::lower_bound(members.begin(),members.end(),sought);
            require(it!=members.end() && it->key==sought.key,"endpoint wire absent from membership");return it->node;
        };
        for(size_t id=0;id<nodes.count;id++)require(resolve(nodes.at(id,3),nodes.at(id,4))==id,"native representative mismatch");
        std::vector<unsigned char> partition(nodes.count,0);
        std::ifstream partitionfile(in/"partition_pins.csv");require(bool(partitionfile),"missing partition_pins.csv");std::getline(partitionfile,line);
        size_t partitionPins=0,missingPartitionNodes=0;
        while(std::getline(partitionfile,line)) {
            auto v=csv(line);require(v.size()==8,"partition CSV width");partitionPins++;
            if(v[0]=="-1"){missingPartitionNodes++;continue;}
            uint32_t id=number(v[0]);require(id<nodes.count,"partition node range");partition[id]=1;
        }
        for(size_t id=0;id<nodes.count;id++)require(bool(nodes.at(id,11)&4)==bool(partition[id]),"partition marker mismatch");
        std::cout<<"verified_members="<<members.size()<<" nodes="<<nodes.count<<std::endl;
        std::vector<uint32_t> own(nodes.count),bg(nodes.count),candidate(nodes.count),first(nodes.count,absent);
        std::ofstream disconnected(out/"unreachable_candidate_sinks.csv");disconnected<<"net_id,task_id,source_node,sink_node\n";
        size_t nextPin=0,nextPip=0,nextTask=0,nextOwner=0,candidateNets=0,badNets=0,badSinks=0,missingPip=0,missingPin=0,crossTasks=0;
        size_t candProtected=0;
        for(size_t net=0;net<nets.count;net++) {
            uint32_t reason=nets.at(net,0),source=nets.at(net,1),sourcePin=nets.at(net,2);
            bool isCandidate=reason==0;candidateNets+=isCandidate;
            uint32_t pb=nets.at(net,3),pc=nets.at(net,4),eb=nets.at(net,5),ec=nets.at(net,6),
                     tb=nets.at(net,7),tc=nets.at(net,8),ob=nets.at(net,9),oc=nets.at(net,10);
            require(pb==nextPin && eb==nextPip && tb==nextTask && ob==nextOwner,"noncontiguous net slices");
            nextPin+=pc;nextPip+=ec;nextTask+=tc;nextOwner+=oc;
            require(nextPin<=pins.count && nextPip<=pips.count && nextTask<=tasks.count && nextOwner<=owners.count,"net slice bounds");
            require((reason&~2047u)==0,"unknown reason");for(int c=13;c<16;c++)require(nets.at(net,c)==0,"reserved net field");
            std::vector<uint32_t> ids;ids.reserve(oc);
            for(size_t i=ob;i<nextOwner;i++) {
                uint32_t id=owners.at(i,0);require(id<nodes.count && owners.at(i,1)==net,"owner identity");
                require(ids.empty() || id>ids.back(),"duplicate/unsorted net owner");ids.push_back(id);
                own[id]++;if(first[id]==absent)first[id]=net;if(isCandidate)candidate[id]++;else bg[id]++;
            }
            std::vector<unsigned char> used(oc,0),visited(isCandidate?oc:0,0);
            std::vector<int64_t> head(isCandidate?oc:0,-1),next;
            std::vector<uint32_t> destination;
            auto local=[&](uint32_t id)->uint32_t{
                auto it=std::lower_bound(ids.begin(),ids.end(),id);require(it!=ids.end() && *it==id,"resource absent from net owners");
                size_t k=it-ids.begin();used[k]=1;return uint32_t(k);
            };
            uint32_t outputs=0,inputs=0,derived=0;bool protectedNet=false;
            std::vector<uint32_t> sinkPins;
            for(size_t i=pb;i<nextPin;i++) {
                require(pins.at(i,0)==net,"pin net mismatch");uint32_t id=pins.at(i,1),d=pins.at(i,2),o=pins.at(i,3);require(o<=1,"pin direction");
                if(id==absent || d==absent){missingPin++;derived|=256;}
                if(id!=absent){local(id);require(d<8 && (nodes.at(id,5)&(1u<<d)),"pin access outside node membership");}
                if(o)outputs++;else{inputs++;sinkPins.push_back(uint32_t(i));}
                if(!o && source!=absent && id==source)derived|=1024;
            }
            if(source==absent)derived|=8;
            else require(sourcePin>=pb && sourcePin<nextPin && pins.at(sourcePin,1)==source && pins.at(sourcePin,3)==1,"source pin mismatch");
            if(outputs!=1)derived|=16;
            if(inputs==0)derived|=512;
            require(outputs==nets.at(net,11) && inputs==nets.at(net,12),"pin count/direction mismatch");
            for(size_t i=eb;i<nextPip;i++) {
                require(pips.at(i,0)==net,"PIP net mismatch");uint32_t a=pips.at(i,1),b=pips.at(i,2),t=pips.at(i,3),d=pips.at(i,6),f=pips.at(i,7);
                require(d==tile(t).die && !(f&~255u),"PIP tile/flags");
                if(f&4)derived|=32;
                if(f&8)derived|=64;
                if(f&48)derived|=128;
                if(a==absent || b==absent){missingPip++;derived|=256;}
                if(a!=absent){local(a);require(resolve(t,pips.at(i,4))==a,"PIP start identity");}
                if(b!=absent){local(b);require(resolve(t,pips.at(i,5))==b,"PIP end identity");}
                if(isCandidate) {
                    require(a!=absent && b!=absent,"candidate missing PIP endpoint");if(f&1)std::swap(a,b);
                    uint32_t from=local(a),to=local(b);next.push_back(head[from]);destination.push_back(to);head[from]=int64_t(next.size()-1);
                }
            }
            require((reason&~7u)==derived,"candidate exclusion reason inconsistent with footprint");
            for(size_t i=0;i<ids.size();i++) {
                require(used[i],"owner has no pin or PIP footprint");
                if(nodes.at(ids[i],11)&4)protectedNet=true;
            }
            if(isCandidate) {
                candProtected+=protectedNet;require(tc==sinkPins.size(),"candidate task coverage");
                uint32_t root=local(source);visited[root]=1;std::vector<uint32_t> queue{root};
                for(size_t h=0;h<queue.size();h++)for(int64_t e=head[queue[h]];e>=0;e=next[size_t(e)]) {
                    auto v=destination[size_t(e)];if(!visited[v]){visited[v]=1;queue.push_back(v);}
                }
                bool bad=false;
                for(size_t i=tb;i<nextTask;i++) {
                    uint32_t sinkPin=sinkPins[i-tb],sink=pins.at(sinkPin,1);
                    require(tasks.at(i,0)==i && tasks.at(i,1)==net && tasks.at(i,2)==source && tasks.at(i,3)==sink,"task endpoint identity");
                    require(tasks.at(i,4)==pins.at(sourcePin,2) && tasks.at(i,5)==pins.at(sinkPin,2),"task access SLR");
                    require(tasks.at(i,6)==sourcePin && tasks.at(i,7)==sinkPin,"task pin identity");
                    crossTasks+=tasks.at(i,4)!=tasks.at(i,5);
                    if(!visited[local(sink)]){bad=true;badSinks++;disconnected<<net<<','<<i<<','<<source<<','<<sink<<'\n';}
                }
                badNets+=bad;
            } else require(tc==0,"excluded net has tasks");
            if(net%100000==0)std::cout<<"verified_nets="<<net<<std::endl;
        }
        require(nextPin==pins.count && nextPip==pips.count && nextTask==tasks.count && nextOwner==owners.count,"unclaimed table records");
        std::ofstream shared(out/"shared_resources.csv");shared<<"node_id,first_net_id,owners,background_owners,candidate_owners,intent,membership_mask\n";
        size_t multi=0,mixed=0,sll=0,protectedNodes=0,candidateSll=0,backgroundSll=0;std::map<uint32_t,size_t> sllMasks;
        for(size_t i=0;i<nodes.count;i++) {
            require(own[i]==nodes.at(i,8) && bg[i]==nodes.at(i,9) && candidate[i]==nodes.at(i,10) && first[i]==nodes.at(i,7),"owner recount mismatch");
            if(own[i]>1){multi++;shared<<i<<','<<first[i]<<','<<own[i]<<','<<bg[i]<<','<<candidate[i]<<','<<intents.at(nodes.at(i,12))<<','<<nodes.at(i,5)<<'\n';}
            if(bg[i] && candidate[i])mixed++;
            protectedNodes+=bool(nodes.at(i,11)&4);
            auto mask=nodes.at(i,5);
            if(own[i] && __builtin_popcount(mask)>1 && intents.at(nodes.at(i,12))=="NODE_LAGUNA_DATA"){
                sll++;sllMasks[mask]++;candidateSll+=candidate[i]>0;backgroundSll+=bg[i]>0;
            }
        }
        std::ofstream report(out/"audit.json");report<<"{\n  \"schema\": \"dieroute.footprint_audit.v1\",\n  \"structural_checks_passed\": true,\n"
            <<"  \"nets\": "<<nets.count<<",\n  \"nodes\": "<<nodes.count<<",\n  \"member_wires\": "<<wires.count
            <<",\n  \"pins\": "<<pins.count<<",\n  \"pips\": "<<pips.count<<",\n  \"owners\": "<<owners.count
            <<",\n  \"candidate_nets\": "<<candidateNets<<",\n  \"candidate_tasks\": "<<tasks.count<<",\n  \"cross_slr_candidate_tasks\": "<<crossTasks
            <<",\n  \"unreachable_candidate_nets\": "<<badNets<<",\n  \"unreachable_candidate_sinks\": "<<badSinks
            <<",\n  \"multi_owner_nodes\": "<<multi<<",\n  \"shared_candidate_background_nodes\": "<<mixed
            <<",\n  \"protected_partition_nodes\": "<<protectedNodes<<",\n  \"candidate_nets_touching_partition_pins\": "<<candProtected
            <<",\n  \"partition_pins\": "<<partitionPins<<",\n  \"missing_partition_nodes\": "<<missingPartitionNodes
            <<",\n  \"missing_pip_endpoints\": "<<missingPip<<",\n  \"missing_pin_nodes\": "<<missingPin
            <<",\n  \"owned_cross_slr_laguna_nodes\": "<<sll<<",\n  \"candidate_owned_sll_nodes\": "<<candidateSll
            <<",\n  \"background_owned_sll_nodes\": "<<backgroundSll<<",\n  \"sll_membership_counts\": {";
        bool comma=false;for(auto [mask,n]:sllMasks){if(comma)report<<',';comma=true;report<<'"'<<mask<<"\":"<<n;}
        report<<"},\n  \"scope\": \"used-resource identity, ownership, task coverage and directed PIP reachability; not capacity, unused adjacency, delay or rerouting validation\"\n}\n";
        std::cout<<"structural_checks_passed=true unreachable_candidate_nets="<<badNets<<" multi_owner_nodes="<<multi<<std::endl;
        return 0;
    } catch(const std::exception& e){std::cerr<<"verification failed: "<<e.what()<<std::endl;return 1;}
}
