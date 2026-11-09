#include "native_csr_io.hpp"
#include "native_timing_feedback.hpp"
#include <charconv>
#include <iostream>
using namespace dieroute;
using namespace dieroute::native;

template<class T> T integer(const std::string& s){
    T value{};auto r=std::from_chars(s.data(),s.data()+s.size(),value);
    check(r.ec==std::errc{}&&r.ptr==s.data()+s.size(),"invalid feedback integer");return value;
}
static std::vector<std::string> fields(std::string line,char separator){
    std::vector<std::string> out;std::string word;std::istringstream in(line);
    while(std::getline(in,word,separator))out.push_back(word);
    return out;
}
template<class F> void csv(const fs::path& path,const std::string& header,F consume){
    std::ifstream in(path);check(bool(in),"feedback CSV open");std::string line;
    check(bool(std::getline(in,line))&&line==header,"feedback CSV schema");
    while(std::getline(in,line)){auto f=fields(line,',');check(f.size()==fields(header,',').size(),"feedback CSV width");consume(f);}
    check(in.eof(),"feedback CSV read failure");
}
static void save(const fs::path& out,const NativeRouteState& state){
    check(fs::create_directory(out),"new feedback state directory required");
    std::ofstream trees(out/"trees.csv"),uses(out/"usage.csv"),identity(out/"tree_identity.txt");
    trees<<"repeat,net,node,parent,pip_key,depth\n";uses<<"repeat,node,net,history,version\n";
    for(const auto& [net,t]:state.trees())for(const auto& [n,v]:t.nodes)
        trees<<0<<','<<net<<','<<n<<','<<v.parent<<','<<v.pip<<','<<v.depth<<'\n';
    state.visit_uses([&](auto n,const auto& u){
        if(u.nets.empty())uses<<0<<','<<n<<','<<none<<','<<u.history<<','<<u.version<<'\n';
        else for(auto net:u.nets)uses<<0<<','<<n<<','<<net<<','<<u.history<<','<<u.version<<'\n';
    });
    std::ofstream ownerUses(out/"owner_usage.csv");ownerUses<<"repeat,owner,node,net,history,version\n";
    for(uint32_t die=0;die<state.owner_count();++die)for(const auto& [n,u]:state.owner_uses(die)){
        if(u.nets.empty())ownerUses<<0<<','<<die<<','<<n<<','<<none<<','<<u.history<<','<<u.version<<'\n';
        else for(auto net:u.nets)ownerUses<<0<<','<<die<<','<<n<<','<<net<<','<<u.history<<','<<u.version<<'\n';}
    ownerUses.close();check(bool(ownerUses),"feedback owner inventory write failure");
    identity<<native_tree_identity(state);trees.close();uses.close();identity.close();
    check(bool(trees)&&bool(uses)&&bool(identity),"feedback state write failure");
}
int main(int argc,char** argv){try{
    check((argc==12||argc==13),"usage: native_timing_feedback GRAPH SEARCH FOOTPRINT MAPPING ARCH ROUTE SNAPSHOTS_OR_DASH OUT SETUP_PS HOLD_PS ALLOW_UNCONSTRAINED_0_OR_1 [OWNER_PARTITION_0_OR_1]");
    fs::path graph=argv[1],search=argv[2],fp=argv[3],mapping=argv[4],route=argv[6],snapshots=argv[7],out=argv[8];
    auto arch=fingerprint(argv[5]);NativeTimingPolicy policy{integer<int64_t>(argv[9]),integer<int64_t>(argv[10]),integer<unsigned>(argv[11])==1};
    check(std::string(argv[11])=="0"||std::string(argv[11])=="1","invalid unconstrained policy");
    const auto partitioned=argc==13?integer<unsigned>(argv[12]):0;check(partitioned<=1,"invalid owner partition flag");
    check(policy.setup_floor_ps>=0&&policy.hold_floor_ps>=0,"negative policy floor");
    check(fs::create_directory(out),"new feedback output required");
    Raw nodes(graph/"nodes.bin",16),pips(graph/"pips.bin",8),tasks(fp/"tasks.bin",8),owners(fp/"owners.bin",2),nets(fp/"nets.bin",16),
        oldPips(fp/"pips.bin",8),nm(mapping/"footprint_node_map.bin",1),pm(mapping/"footprint_pip_map.bin",1);
    Container offsets(search/"offsets.bin",offsets_type,8,arch),arcs(search/"arcs.bin",arcs_type,8,arch),
        mask(search/"node_protection.bin",0x4452000a,1,arch),exclusive(search/"exclusive_net.bin",0x4452000b,4,arch);
    check(nodes.count<none&&offsets.count==nodes.count+1&&mask.count==nodes.count&&exclusive.count==nodes.count,"feedback table coverage");
    check(offsets.offset(0)==0&&offsets.offset(nodes.count)==arcs.count,"feedback CSR coverage");
    NativeOwnerLayout layout;
    if(partitioned){uint32_t topologyMask=0;for(size_t n=0;n<nodes.count;++n)topologyMask|=nodes.at(n,5);
        check(topologyMask&&topologyMask<256,"feedback SLR domain");uint32_t dies=1;while(topologyMask>>dies)++dies;
        layout=NativeOwnerLayout::from_membership(dies,[&](uint32_t n){check(n<nodes.count,"feedback owner bounds");return nodes.at(n,5);});}
    auto mapped=[&](uint32_t n){auto v=nm.at(n,0);check(v<nodes.count,"feedback node mapping");return v;};
    std::map<uint32_t,std::pair<uint32_t,uint32_t>> selectedTasks;
    std::map<uint32_t,uint32_t> roots;std::map<uint32_t,std::set<uint32_t>> sinks;
    csv(route/"selection.csv","task,net,source,sink,selection_seed",[&](const auto& f){
        auto id=integer<uint32_t>(f[0]),net=integer<uint32_t>(f[1]),src=integer<uint32_t>(f[2]),dst=integer<uint32_t>(f[3]);
        check(tasks.at(id,0)==id&&tasks.at(id,1)==net&&mapped(tasks.at(id,2))==src&&mapped(tasks.at(id,3))==dst,"feedback task identity");
        check(nets.at(net,0)==0,"feedback noncandidate net");check(selectedTasks.emplace(id,std::make_pair(net,dst)).second,"duplicate selected task");
        check(!roots.count(net)||roots.at(net)==src,"feedback multiple roots");roots[net]=src;sinks[net].insert(dst);
    });
    check(!roots.empty(),"empty feedback cohort");
    for(size_t i=0;i<tasks.count;++i)if(roots.count(tasks.at(i,1)))check(selectedTasks.count(i),"feedback partial net");
    std::vector<uint64_t> frozen((nodes.count+63)/64);
    for(size_t i=0;i<owners.count;++i)if(!roots.count(owners.at(i,1))){auto n=mapped(owners.at(i,0));frozen[n/64]|=uint64_t(1)<<(n%64);}
    auto allowed=[&](uint32_t n,uint32_t net){return n<nodes.count&&!mask.data[n]&&!(frozen[n/64]&(uint64_t(1)<<(n%64)))&&(le32(exclusive.data+4*n)==none||le32(exclusive.data+4*n)==net);};
    auto edge=[&](uint32_t src,uint32_t dst,uint32_t key){
        auto pid=key>>1,reverse=key&1;check(pid<pips.count&&pips.at(pid,0)==pid,"feedback native PIP ID");
        if(!(pips.at(pid,7)&2)&&reverse!=(pips.at(pid,7)&1))return false;
        if(pips.at(pid,reverse?2:1)!=src||pips.at(pid,reverse?1:2)!=dst)return false;
        auto lo=offsets.offset(src),end=offsets.offset(src+1),hi=end;check(lo<=hi&&hi<=arcs.count,"feedback CSR row");
        while(lo<hi){auto mid=lo+(hi-lo)/2;if(std::make_pair(arcs.dst(mid),arcs.edge(mid))<std::make_pair(dst,key))lo=mid+1;else hi=mid;}
        return lo<end&&arcs.dst(lo)==dst&&arcs.edge(lo)==key;
    };
    std::map<uint32_t,NativeTree> baselineTrees,candidateTrees;std::map<uint32_t,NativeUse> baselineUses,candidateUses;
    for(const auto& [net,src]:roots){auto& tree=baselineTrees[net];tree.source=src;tree.nodes.emplace(src,NativeTreeNode{});
        std::map<uint32_t,std::vector<uint32_t>> children;
        auto begin=nets.at(net,5),count=nets.at(net,6);
        for(uint64_t i=begin;i<uint64_t(begin)+count;++i){check(oldPips.at(i,0)==net,"original PIP net");
            auto reverse=oldPips.at(i,7)&1,parent=mapped(oldPips.at(i,reverse?2:1)),n=mapped(oldPips.at(i,reverse?1:2));
            auto pid=pm.at(i,0);check(pid<UINT32_MAX/2,"original PIP key overflow");
            check(tree.nodes.emplace(n,NativeTreeNode{parent,(pid<<1)|reverse,0}).second,"original PIP multiple parents");children[parent].push_back(n);
        }
        std::vector<uint32_t> queue{src};for(size_t i=0;i<queue.size();++i)for(auto n:children[queue[i]]){
            check(tree.nodes.at(queue[i]).depth<UINT32_MAX,"original depth overflow");tree.nodes.at(n).depth=tree.nodes.at(queue[i]).depth+1;queue.push_back(n);
            check(queue.size()<=tree.nodes.size(),"original parent cycle");}
        check(queue.size()==tree.nodes.size(),"original disconnected tree");
        for(const auto& [n,v]:tree.nodes){(void)v;baselineUses[n].nets.insert(net);baselineUses[n].version=1;}
    }
    csv(route/"trees.csv","repeat,net,node,parent,pip_key,depth",[&](const auto& f){
        if(integer<uint32_t>(f[0])!=0)return;
        auto net=integer<uint32_t>(f[1]);check(roots.count(net),"unexpected candidate net");
        auto& t=candidateTrees[net];t.source=roots.at(net);
        check(t.nodes.emplace(integer<uint32_t>(f[2]),NativeTreeNode{integer<uint32_t>(f[3]),integer<uint32_t>(f[4]),integer<uint32_t>(f[5])}).second,"duplicate candidate node");
    });
    std::set<uint32_t> empty;
    csv(route/"usage.csv","repeat,node,net,history,version",[&](const auto& f){
        if(integer<uint32_t>(f[0])!=0)return;
        auto n=integer<uint32_t>(f[1]),net=integer<uint32_t>(f[2]);
        auto history=integer<uint64_t>(f[3]),version=integer<uint64_t>(f[4]);check(n<nodes.count&&version>0,"invalid candidate usage");
        auto [it,inserted]=candidateUses.emplace(n,NativeUse{{},history,version});auto& u=it->second;
        check(inserted||(u.history==history&&u.version==version),"candidate usage version mismatch");
        if(net==none)check(inserted&&empty.insert(n).second,"duplicate empty use");
        else check(!empty.count(n)&&u.nets.insert(net).second,"duplicate/mixed candidate use");
    });
    // Validate stored owner rows before importing either checkpoint. A omitted
    // partition flag cannot silently flatten an existing multi-owner inventory.
    const auto ownerFile=route/"owner_usage.csv";
    check(!partitioned||fs::exists(ownerFile),"partitioned checkpoint requires owner inventory");
    if(fs::exists(ownerFile)){
        std::set<std::pair<uint32_t,uint32_t>> seen;
        csv(ownerFile,"repeat,owner,node,net,history,version",[&](const auto& f){
            if(integer<uint32_t>(f[0])!=0)return;
            auto die=integer<uint32_t>(f[1]),n=integer<uint32_t>(f[2]),net=integer<uint32_t>(f[3]);
            check(n<nodes.count&&die==layout.owner(n)&&candidateUses.count(n),"checkpoint owner mismatch");
            const auto& u=candidateUses.at(n);
            check(u.history==integer<uint64_t>(f[4])&&u.version==integer<uint64_t>(f[5]),"checkpoint owner history/version mismatch");
            check(net==none?u.nets.empty():u.nets.count(net),"checkpoint owner net mismatch");
            check(seen.emplace(n,net).second,"duplicate checkpoint owner row");
        });
        size_t expected=0;for(const auto& [n,u]:candidateUses){(void)n;expected+=std::max(size_t(1),u.nets.size());}
        check(seen.size()==expected,"incomplete checkpoint owner inventory");
    }
    auto baseline=NativeRouteState::checkpoint(std::move(baselineTrees),std::move(baselineUses),allowed,edge,layout);
    auto candidate=NativeRouteState::checkpoint(std::move(candidateTrees),std::move(candidateUses),allowed,edge,layout);
    auto complete=[&](const NativeRouteState& state){
        check(state.trees().size()==roots.size()&&state.overused()==0,"feedback incomplete/conflicting state");
        for(const auto& [net,src]:roots){const auto& t=state.tree(net);check(t.source==src,"feedback root mismatch");std::set<uint32_t> parents;
            for(const auto& [n,v]:t.nodes){(void)n;parents.insert(v.parent);}
            for(auto sink:sinks.at(net))check(t.nodes.count(sink),"feedback missing task sink");
            for(const auto& [n,v]:t.nodes){(void)v;check(n==src||parents.count(n)||sinks.at(net).count(n),"feedback orphan branch");}}
    };
    complete(baseline);complete(candidate);save(out/"baseline",baseline);save(out/"proposal",candidate);
    if(snapshots=="-"){std::cout<<"Prepared "<<roots.size()<<" nets and "<<selectedTasks.size()<<" tasks\n";return 0;}
    std::ifstream selected(snapshots);check(bool(selected),"restore-net list open");
    std::set<uint32_t> ids;std::string value;
    while(std::getline(selected,value)){check(!value.empty(),"empty restore-net row");auto id=integer<uint32_t>(value);check(roots.count(id)&&ids.insert(id).second,"unknown/duplicate restore net");}
    check(selected.eof()&&!ids.empty(),"invalid restore-net list");
    auto repair=restore_native_timing_nets(baseline,candidate,ids,allowed,edge);complete(repair.candidate);
    save(out/"candidate",repair.candidate);
    std::ofstream report(out/"decision.json");
    report<<"{\"status\":\"electrically_valid_repair_candidate\",\"restored_nets\":[";
    bool comma=false;for(auto id:repair.restored_nets){if(comma)report<<',';report<<id;comma=true;}
    report<<"],\"native_timing_accepted\":false,\"board_result\":false}\n";
    report.close();check(bool(report),"repair report write failure");return 0;
}catch(const std::exception& e){std::cerr<<"native timing feedback failed: "<<e.what()<<'\n';return 1;}}
