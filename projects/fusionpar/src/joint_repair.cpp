#include "joint_state.hpp"

#include <algorithm>
#include <cstdlib>
#include <limits>
#include <map>
#include <set>
#include <stdexcept>
#include <utility>

namespace fusionpar::joint {
const char* feedback_name(FeedbackKind kind) {
    switch(kind) {
        case FeedbackKind::none:return "none";
        case FeedbackKind::routing:return "routing";
        case FeedbackKind::native_delay:return "native_delay";
        case FeedbackKind::wire_growth:return "wire_growth";
    }
    return "unknown";
}
namespace {
std::int64_t displacement(const Design& d,Id from,Id to) {
    const auto& a=d.sites.at(from);const auto& b=d.sites.at(to);
    return std::abs(std::int64_t(a.x)-b.x)+std::abs(std::int64_t(a.y)-b.y)+
           std::abs(std::int64_t(a.subtile)-b.subtile);
}
std::vector<std::pair<Id,Id>> signature(const Proposal& p) {
    std::vector<std::pair<Id,Id>> key;
    for(const auto& m:p.moves)key.emplace_back(m.instance,m.new_site);
    std::sort(key.begin(),key.end());return key;
}
}
std::vector<Proposal> propose_repairs(const Design& d,const State& s,const Proposal& failed,
                                    Status status,const FailureFeedback& feedback,std::size_t limit) {
    std::vector<Proposal> result;
    if(!limit || (status!=Status::route_failed && status!=Status::quality_rejected) ||
       feedback.kind==FeedbackKind::none || feedback.connection_ids.empty())return result;
    for(Id id:feedback.connection_ids)
        if(id>=d.connections.size())throw std::invalid_argument("repair feedback connection out of range");
    for(Id id:feedback.resource_ids)
        if(id>=d.nodes.size())throw std::invalid_argument("repair feedback resource out of range");
    std::map<Id,Move> moves;
    for(const auto& m:failed.moves) {
        if(m.instance>=s.placement.size() || m.new_site>=d.sites.size() ||
           s.placement[m.instance].site!=m.old_site || s.placement[m.instance].version!=m.observed_version ||
           !moves.emplace(m.instance,m).second)return result;
    }
    Id primary=invalid;
    for(Id witness:feedback.connection_ids) {
        const auto net=d.connections[witness].net;
        std::set<Id> members;
        for(const auto& c:d.connections)if(c.net==net) {members.insert(c.source_instance);members.insert(c.sink_instance);}
        for(const auto& m:failed.moves)if(members.count(m.instance)) {primary=m.instance;break;}
        if(primary!=invalid)break;
    }
    if(primary==invalid)return result;
    const auto& original=moves.at(primary);
    const auto radius=displacement(d,original.old_site,original.new_site);
    const auto rejected_key=signature(failed);
    // Candidate legality and HPWL ordering use the same component as the base
    // controller. Only the feedback restriction and failed radius are added.
    auto candidates=propose_moves(d,s,std::numeric_limits<std::size_t>::max());
    for(auto& candidate:candidates) {
        if(signature(candidate)==rejected_key)continue;
        auto move=std::find_if(candidate.moves.begin(),candidate.moves.end(),[&](const Move& m){return m.instance==primary;});
        if(move==candidate.moves.end() || displacement(d,move->old_site,move->new_site)>radius)continue;
        candidate.id=failed.id;result.push_back(std::move(candidate));
        if(result.size()==limit)break;
    }
    return result;
}
} // namespace fusionpar::joint
