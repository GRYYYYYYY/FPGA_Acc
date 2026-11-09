#pragma once
#include "edge_routes.hpp"
#include <memory>
#include <stdexcept>

namespace dieroute {
// Immutable design admission, distinct from negotiable PathFinder occupancy.
// Any nonzero protection mask denies traversal even when overuse is allowed.
// Terminal owners reserve physical pin nodes for one net across rip-up epochs.
struct RoutingPolicy {
    std::vector<std::uint8_t> node_protection, edge_protection;
    std::vector<std::uint32_t> terminal_net;
    bool active()const{return !node_protection.empty() || !edge_protection.empty() || !terminal_net.empty();}
    void validate(std::size_t nodes,std::size_t edges)const {
        if(active() && (node_protection.size()!=nodes || terminal_net.size()!=nodes || edge_protection.size()!=edges))
            throw std::invalid_argument("routing policy must cover every node, terminal owner and edge");
    }
    bool node_allowed(std::uint32_t node,std::uint32_t net)const {
        return !active() || (!node_protection.at(node) && (terminal_net.at(node)==persistroute::INVALID_RESOURCE || terminal_net[node]==net));
    }
    bool edge_allowed(std::uint32_t edge)const{return !active() || !edge_protection.at(edge);}
    bool frozen(std::uint32_t node)const{return active() && node_protection.at(node);}
    bool path_allowed(const persistroute::Task& task,std::uint32_t attachment,
        const std::vector<std::uint32_t>& path,const std::vector<std::uint32_t>& edges)const {
        if(!node_allowed(task.source,task.net_id)||!node_allowed(task.sink,task.net_id)||!node_allowed(attachment,task.net_id)||path.size()!=edges.size())return false;
        for(std::size_t i=0;i<path.size();++i)if(!node_allowed(path[i],task.net_id)||!edge_allowed(edges[i]))return false;
        return true;
    }
};
using RoutingPolicyPtr=std::shared_ptr<const RoutingPolicy>;
} // namespace dieroute
