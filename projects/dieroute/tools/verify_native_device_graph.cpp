// Read-only topology audit and DCP-to-device identity maps. No routing.
#include <algorithm>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <tuple>
#include <vector>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <unistd.h>
namespace fs=std::filesystem;
constexpr uint32_t absent=UINT32_MAX, invalid=UINT32_MAX-1;
void require(bool ok,const std::string& message){if(!ok)throw std::runtime_error(message);}
struct Table {
    int fd;const unsigned char* data;size_t bytes,width,count;
    Table(const fs::path& path,size_t w):width(w){
        fd=open(path.c_str(),O_RDONLY);require(fd>=0,"open "+path.string());struct stat st{};
        require(fstat(fd,&st)==0,"stat failed");bytes=st.st_size;require(bytes%(4*w)==0,"truncated table");count=bytes/(4*w);
        data=bytes?static_cast<const unsigned char*>(mmap(nullptr,bytes,PROT_READ,MAP_PRIVATE,fd,0)):nullptr;
        require(!bytes || data!=MAP_FAILED,"mmap failed");
    }
    ~Table(){if(bytes)munmap(const_cast<unsigned char*>(data),bytes);close(fd);}
    uint32_t at(size_t row,size_t col)const{
        require(row<count && col<width,"table bounds");auto p=data+4*(row*width+col);
        return uint32_t(p[0])|(uint32_t(p[1])<<8)|(uint32_t(p[2])<<16)|(uint32_t(p[3])<<24);
    }
};
struct Output {
    std::ofstream stream;
    explicit Output(const fs::path& path):stream(path,std::ios::binary){require(bool(stream),"output open");}
    void word(uint32_t n){char b[4]={char(n),char(n>>8),char(n>>16),char(n>>24)};stream.write(b,4);require(bool(stream),"output write");}
};
std::vector<std::string> csv(const std::string& s){
    std::vector<std::string> r;std::string f;bool quote=false;
    for(size_t i=0;i<s.size();i++){
        if(s[i]=='"'){if(quote && i+1<s.size() && s[i+1]=='"'){f+='"';i++;}else quote=!quote;}
        else if(s[i]==',' && !quote){r.push_back(f);f.clear();}else if(s[i]!='\r')f+=s[i];
    }
    require(!quote,"CSV quoting");r.push_back(f);return r;
}
uint32_t u32(const std::string& s){size_t end=0;auto n=std::stoull(s,&end);require(end==s.size() && n<=UINT32_MAX,"u32 parse");return n;}
struct Tile {
    bool present=false;uint32_t slr=absent,x=0,y=0,pipBegin=0,pipCount=0;std::vector<uint32_t> wires;
};
struct Counts{uint32_t members=0;uint8_t mask=0,bounds=0;};
int main(int argc,char** argv){
    try {
        require(argc==4,"usage: verify_native_device_graph GRAPH_DIR FOOTPRINT_DIR NEW_OUTPUT_DIR");
        fs::path graph=argv[1],footprint=argv[2],out=argv[3];require(fs::create_directory(out),"output must be new");
        Table nodes(graph/"nodes.bin",16),wires(graph/"wires.bin",3),nulls(graph/"null_wires.bin",2),pips(graph/"pips.bin",8);
        require(nodes.count<invalid && pips.count<invalid,"u32 IDs exhausted");
        std::ifstream tf(graph/"tiles.csv");require(bool(tf),"missing tiles.csv");std::string line;std::getline(tf,line);
        std::vector<Tile> tiles;size_t tileCount=0,tileWires=0,pipEnd=0;
        while(std::getline(tf,line)){
            auto v=csv(line);require(v.size()==9,"tile CSV width");uint32_t id=u32(v[0]);
            if(id>=tiles.size())tiles.resize(size_t(id)+1);
            Tile& t=tiles[id];require(!t.present,"duplicate tile");t.present=true;
            t.slr=v[3]=="-1"?absent:u32(v[3]);require(t.slr==absent || t.slr<8,"tile SLR");t.x=u32(v[4]);t.y=u32(v[5]);
            t.wires.assign(u32(v[6]),absent);t.pipBegin=u32(v[7]);t.pipCount=u32(v[8]);
            require(t.pipBegin==pipEnd,"tile PIP slice gap");pipEnd+=t.pipCount;tileWires+=t.wires.size();tileCount++;
        }
        require(pipEnd==pips.count,"tile PIP coverage");require(tileWires==wires.count+nulls.count,"wire coverage count");
        auto tile=[&](uint32_t id)->Tile&{require(id<tiles.size() && tiles[id].present,"unknown tile");return tiles[id];};
        auto mapping=[&](uint32_t t,uint32_t w)->uint32_t&{auto& a=tile(t).wires;require(w<a.size(),"wire bounds");return a[w];};
        std::map<uint32_t,std::string> intents;
        std::ifstream itf(graph/"intents.csv");require(bool(itf),"missing intents.csv");std::getline(itf,line);
        while(std::getline(itf,line)){auto v=csv(line);require(v.size()==2 && intents.emplace(u32(v[0]),v[1]).second,"intent table");}
        std::vector<Counts> counts(nodes.count);uint64_t previous=0;
        for(size_t i=0;i<wires.count;i++){
            uint32_t n=wires.at(i,0),t=wires.at(i,1),w=wires.at(i,2);require(n<nodes.count,"wire node ID");
            uint64_t key=(uint64_t(t)<<32)|w;require(!i || key>previous,"wire order/duplicate");previous=key;
            auto& slot=mapping(t,w);require(slot==absent,"wire assigned twice");slot=n;auto& c=counts[n];auto& ti=tile(t);
            require(ti.slr<8,"member SLR absent");c.mask|=1u<<ti.slr;
            if(c.members++==0)require(nodes.at(n,1)==t && nodes.at(n,2)==w,"canonical representative mismatch");
            require(ti.x>=nodes.at(n,9) && ti.y>=nodes.at(n,10) && ti.x<=nodes.at(n,11) && ti.y<=nodes.at(n,12),"member outside bbox");
            if(ti.x==nodes.at(n,9))c.bounds|=1;
            if(ti.y==nodes.at(n,10))c.bounds|=2;
            if(ti.x==nodes.at(n,11))c.bounds|=4;
            if(ti.y==nodes.at(n,12))c.bounds|=8;
        }
        previous=0;
        for(size_t i=0;i<nulls.count;i++){
            uint32_t t=nulls.at(i,0),w=nulls.at(i,1);uint64_t k=(uint64_t(t)<<32)|w;
            require(!i || k>previous,"null wire order");previous=k;auto& slot=mapping(t,w);require(slot==absent,"null/member overlap");slot=invalid;
        }
        for(auto& t:tiles)for(auto n:t.wires)require(n!=absent,"unclassified wire");
        size_t emptyNodes=0,sllNodes=0;std::map<uint32_t,size_t> sllMasks;
        for(size_t n=0;n<nodes.count;n++){
            auto& c=counts[n];require(nodes.at(n,0)==n && c.members==nodes.at(n,6) && c.members>0,"node count/ID");
            require(c.mask==nodes.at(n,5) && c.bounds==15,"node mask/bbox recount");
            require(mapping(nodes.at(n,3),nodes.at(n,4))==n,"native representative mismatch");
            require(intents.count(nodes.at(n,7)) && !(nodes.at(n,8)&~7u),"node intent/flags");
            for(int j=13;j<16;j++)require(nodes.at(n,j)==0,"reserved node fields");
            emptyNodes+=bool(nodes.at(n,8)&4);
            if(__builtin_popcount(c.mask)>1 && intents.at(nodes.at(n,7))=="NODE_LAGUNA_DATA"){sllNodes++;sllMasks[c.mask]++;}
        }
        std::cout<<"verified_nodes="<<nodes.count<<" wires="<<wires.count<<std::endl;
        std::vector<uint8_t> incident(nodes.count,0);size_t missingPips=0,routeThrus=0,bidir=0,duplicates=0,emptyListIncident=0;
        for(size_t t=0;t<tiles.size();t++)if(tiles[t].present){
            auto& ti=tiles[t];std::tuple<uint32_t,uint32_t,uint32_t> prev{};
            for(size_t i=ti.pipBegin;i<size_t(ti.pipBegin)+ti.pipCount;i++){
                uint32_t a=pips.at(i,1),b=pips.at(i,2),sw=pips.at(i,4),ew=pips.at(i,5),f=pips.at(i,7);
                require(pips.at(i,0)==i && pips.at(i,3)==t && pips.at(i,6)==ti.slr,"PIP ID/tile/SLR");require(!(f&~255u),"PIP flags");
                auto current=std::make_tuple(sw,ew,f);require(i==ti.pipBegin || current>=prev,"PIP order");
                if(i!=ti.pipBegin && current==prev)duplicates++;
                prev=current;
                for(auto pair:{std::make_pair(a,sw),std::make_pair(b,ew)}){
                    auto n=pair.first,w=pair.second;uint32_t actual=w==absent?invalid:mapping(uint32_t(t),w);
                    require((n==absent && actual==invalid) || (n<nodes.count && actual==n),"PIP endpoint identity");
                    if(n!=absent){incident[n]=1;require(ti.slr<8 && (nodes.at(n,5)&(1u<<ti.slr)),"PIP access outside membership");}
                }
                missingPips+=a==absent || b==absent;routeThrus+=bool(f&8);bidir+=bool(f&2);
            }
            if(t%100000==0)std::cout<<"verified_PIP_tiles="<<t<<std::endl;
        }
        for(size_t i=0;i<nodes.count;i++)emptyListIncident+=incident[i] && (nodes.at(i,8)&4);
        Table fn(footprint/"nodes.bin",16),fw(footprint/"wires.bin",3),fp(footprint/"pips.bin",8);
        std::vector<uint32_t> nodeMap(fn.count),reverseMap(nodes.count,absent);
        Output nodeOut(out/"footprint_node_map.bin"),pipOut(out/"footprint_pip_map.bin"),occupied(out/"occupied_nodes.bin");
        size_t usedEmpty=0,usedSll=0,bgNodes=0,candidateNodes=0,protectedNodes=0;
        for(size_t n=0;n<fn.count;n++){
            require(fn.at(n,0)==n,"footprint node order");uint32_t id=mapping(fn.at(n,1),fn.at(n,2));require(id<nodes.count,"used node missing in device graph");
            require(reverseMap[id]==absent,"multiple footprint nodes alias one device node");reverseMap[id]=n;nodeMap[n]=id;nodeOut.word(id);
            for(int j=1;j<=6;j++)require(nodes.at(id,j)==fn.at(n,j),"used node identity/membership differs");
            require(nodes.at(id,7)==fn.at(n,12) && (nodes.at(id,8)&3)==(fn.at(n,11)&3),"used intent/tied flags differ");
            usedEmpty+=bool(nodes.at(id,8)&4);bgNodes+=fn.at(n,9)>0;candidateNodes+=fn.at(n,10)>0;protectedNodes+=bool(fn.at(n,11)&4);
            if(__builtin_popcount(nodes.at(id,5))>1 && intents.at(nodes.at(id,7))=="NODE_LAGUNA_DATA")usedSll++;
            for(uint32_t x:{id,uint32_t(n),fn.at(n,7),fn.at(n,8),fn.at(n,9),fn.at(n,10),fn.at(n,11),0u})occupied.word(x);
        }
        for(size_t i=0;i<fw.count;i++)require(fw.at(i,0)<nodeMap.size() && mapping(fw.at(i,1),fw.at(i,2))==nodeMap[fw.at(i,0)],"footprint member differs");
        size_t ambiguous=0;
        for(size_t i=0;i<fp.count;i++){
            uint32_t t=fp.at(i,3),sw=fp.at(i,4),ew=fp.at(i,5),f=fp.at(i,7);auto& ti=tile(t);
            auto wanted=std::make_pair(sw,ew);size_t lo=ti.pipBegin,hi=lo+ti.pipCount;
            while(lo<hi){size_t mid=lo+(hi-lo)/2;if(std::make_pair(pips.at(mid,4),pips.at(mid,5))<wanted)lo=mid+1;else hi=mid;}
            size_t match=pips.count,nmatches=0;
            while(lo<size_t(ti.pipBegin)+ti.pipCount && std::make_pair(pips.at(lo,4),pips.at(lo,5))==wanted){
                if((pips.at(lo,7)&10)==(f&10)){if(!nmatches)match=lo;nmatches++;}lo++;
            }
            require(nmatches>0,"DCP PIP absent from native catalog at footprint PIP "+std::to_string(i));ambiguous+=nmatches>1;
            for(int j=1;j<=2;j++){uint32_t old=fp.at(i,j);require(old<nodeMap.size() && pips.at(match,j)==nodeMap[old],"DCP PIP endpoint mapping mismatch");}
            require(fp.at(i,6)==ti.slr,"DCP PIP SLR differs");pipOut.word(uint32_t(match));
        }
        std::ofstream report(out/"audit.json");report<<"{\n  \"schema\": \"dieroute.native_device_graph_audit.v1\",\n  \"structural_checks_passed\": true,\n"
            <<"  \"tiles\": "<<tileCount<<",\n  \"tile_wires\": "<<tileWires<<",\n  \"nodes\": "<<nodes.count
            <<",\n  \"member_wires\": "<<wires.count<<",\n  \"null_wires\": "<<nulls.count<<",\n  \"pips\": "<<pips.count
            <<",\n  \"pips_with_missing_node\": "<<missingPips<<",\n  \"bidirectional_pips\": "<<bidir<<",\n  \"routethru_pips\": "<<routeThrus
            <<",\n  \"duplicate_catalog_pips\": "<<duplicates<<",\n  \"empty_native_member_nodes\": "<<emptyNodes
            <<",\n  \"empty_member_nodes_incident_to_pips\": "<<emptyListIncident<<",\n  \"cross_slr_laguna_nodes\": "<<sllNodes
            <<",\n  \"used_nodes_mapped\": "<<fn.count<<",\n  \"used_member_wires_mapped\": "<<fw.count<<",\n  \"used_pips_mapped\": "<<fp.count
            <<",\n  \"used_empty_member_nodes\": "<<usedEmpty<<",\n  \"ambiguous_used_pip_catalog_matches\": "<<ambiguous
            <<",\n  \"used_sll_nodes\": "<<usedSll<<",\n  \"background_nodes\": "<<bgNodes<<",\n  \"candidate_nodes\": "<<candidateNodes
            <<",\n  \"protected_partition_nodes\": "<<protectedNodes<<",\n  \"sll_membership_counts\": {";
        bool comma=false;for(auto [mask,count]:sllMasks){if(comma)report<<',';comma=true;report<<'"'<<mask<<"\":"<<count;}
        report<<"},\n  \"scope\": \"complete raw topology and original DCP identity mapping; not design-eligible adjacency, capacity, timing or rerouting validation\"\n}\n";
        std::cout<<"structural_checks_passed=true used_nodes_mapped="<<fn.count<<" used_pips_mapped="<<fp.count<<std::endl;return 0;
    }catch(const std::exception& e){std::cerr<<"verification failed: "<<e.what()<<std::endl;return 1;}
}
