#include "joint_io.hpp"
#include <fstream>
#include <limits>
#include <stdexcept>
#include <type_traits>

namespace fusionpar::joint {
namespace {
template<class T> std::vector<T> binary(const std::filesystem::path& path) {
    const auto bytes=std::filesystem::file_size(path);
    if(bytes%sizeof(T) || bytes/sizeof(T)>=invalid) throw std::invalid_argument("invalid binary dimensions: "+path.string());
    std::vector<T> result(bytes/sizeof(T));std::ifstream in(path,std::ios::binary);
    if(!in.read(reinterpret_cast<char*>(result.data()),bytes)) throw std::runtime_error("binary read failed: "+path.string());
    return result;
}
struct Reader {
    std::ifstream in;
    explicit Reader(const std::filesystem::path& p):in(p) {
        std::string header; if(!(in>>header)||header!="FUSIONPAR_TEXT_V1") throw std::invalid_argument("invalid FP text schema");
    }
    template<class T=Id> T number() {
        std::string token;if(!(in>>token)) throw std::invalid_argument("truncated FP contract");
        std::size_t consumed=0;
        if constexpr(std::is_signed<T>::value) {
            auto n=std::stoll(token,&consumed);
            if(consumed!=token.size()||n<std::numeric_limits<T>::min()||n>std::numeric_limits<T>::max())throw std::invalid_argument("integer out of range");
            return static_cast<T>(n);
        } else {
            if(token.empty()||token[0]=='-')throw std::invalid_argument("negative unsigned integer");
            auto n=std::stoull(token,&consumed);
            if(consumed!=token.size()||n>std::numeric_limits<T>::max())throw std::invalid_argument("integer out of range");
            return static_cast<T>(n);
        }
    }
    bool boolean() {auto n=number();if(n>1)throw std::invalid_argument("invalid boolean");return n!=0;}
    Id count() {auto n=number();if(n>10000000)throw std::invalid_argument("v1 text count exceeds supported limit");return n;}
};
}
std::pair<Design,State> read_bundle(const std::filesystem::path& root) {
    static_assert(sizeof(persistroute::Node)==8 && sizeof(persistroute::Edge)==8 && sizeof(persistroute::Resource)==16,"PR ABI mismatch");
    const std::uint32_t endian=1;if(*reinterpret_cast<const unsigned char*>(&endian)!=1)throw std::runtime_error("little-endian PR ABI required");
    Design d;State s;
    d.nodes=binary<persistroute::Node>(root/"graph.nodes");d.edges=binary<persistroute::Edge>(root/"graph.edges");
    s.resources=binary<persistroute::Resource>(root/"graph.resources");
    for(const auto& r:s.resources) if(r.occupancy)throw std::invalid_argument("input resource template must have no reserved occupancy");
    Reader r(root/"design.txt");auto count=r.count();d.sites.resize(count);s.site_versions.resize(count);
    for(auto& site:d.sites) {
        site.x=r.number<std::int32_t>();site.y=r.number<std::int32_t>();site.subtile=r.number<std::int32_t>();site.type=r.number();
        auto pins=r.count();for(Id j=0;j<pins;++j) {Terminal t;t.pin=r.number();t.node=r.number();t.source=r.boolean();site.terminals.push_back(t);}
    }
    count=r.count();d.instances.resize(count);s.placement.resize(count);
    for(Id i=0;i<count;++i) {
        auto& instance=d.instances[i];instance.type=r.number();instance.fixed=r.boolean();
        auto n=r.count();for(Id j=0;j<n;++j)instance.allowed_sites.push_back(r.number());
        s.placement[i].site=r.number();s.placement[i].version=r.number();
    }
    count=r.count();d.macros.resize(count);
    for(auto& macro:d.macros) {
        macro.anchor=r.number();auto n=r.count();for(Id j=0;j<n;++j) {MacroMember m;
            m.instance=r.number();m.dx=r.number<std::int32_t>();m.dy=r.number<std::int32_t>();m.dsubtile=r.number<std::int32_t>();macro.members.push_back(m);}
    }
    count=r.count();d.connections.resize(count);s.routes.resize(count);s.criticalities.resize(count);
    for(Id i=0;i<count;++i) {
        auto& c=d.connections[i];c.net=r.number();c.source_instance=r.number();c.source_pin=r.number();
        c.sink_instance=r.number();c.sink_pin=r.number();c.max_hops=r.number<std::uint16_t>();c.priority=r.number();
        s.criticalities[i]=r.number<std::uint16_t>();auto& route=s.routes[i];route.source=r.number();route.sink=r.number();route.version=r.number();
        auto n=r.count();for(Id j=0;j<n;++j)route.path.push_back(r.number());
    }
    std::string trailing;if(r.in>>trailing)throw std::invalid_argument("trailing FP contract content");
    initialize_accounting(d,s);std::string error;
    if(!validate_state(d,s,error))throw std::invalid_argument("bundle validation: "+error);
    return {std::move(d),std::move(s)};
}
void write_state(const State& s,const std::filesystem::path& path) {
    std::ofstream out(path);out.exceptions(std::ios::badbit|std::ios::failbit);
    out<<"FUSIONPAR_STATE_V1\n"<<s.placement.size()<<'\n';
    for(Id i=0;i<s.placement.size();++i)out<<i<<' '<<s.placement[i].site<<' '<<s.placement[i].version<<'\n';
    out<<s.routes.size()<<'\n';
    for(Id i=0;i<s.routes.size();++i) {
        const auto& r=s.routes[i];out<<i<<' '<<r.source<<' '<<r.sink<<' '<<r.version<<' '<<r.path.size();
        for(auto n:r.path)out<<' '<<n;
        out<<'\n';
    }
    out<<s.resources.size()<<'\n';
    for(const auto& r:s.resources)out<<r.occupancy<<' '<<r.capacity<<' '<<r.owner<<' '<<r.version<<' '<<r.present_cost_q<<' '<<r.history_cost_q<<'\n';
    out<<s.revision<<' '<<s.timing_epoch<<' '<<s.timing_basis_revision<<'\n';
    out<<s.criticalities.size();for(auto c:s.criticalities)out<<' '<<c;out<<'\n';
    out<<s.site_versions.size();for(auto v:s.site_versions)out<<' '<<v;out<<'\n';
}
}
