        // ROUTECAST_DENSE_POST_STA_CAPTURE_BEGIN
        if (routing_is_feasible) {
            if (const char* output = std::getenv("ROUTECAST_DENSE_POST_STA")) {
                if (is_flat) throw std::runtime_error("dense source capture requires clustered mode");
                const char* manifest = std::getenv("ROUTECAST_DENSE_POST_STA_MANIFEST");
                if (!manifest) throw std::runtime_error("dense source manifest missing");
                const auto& dense_rc = g_vpr_ctx.routing();
                const auto& dense_rr = g_vpr_ctx.device().rr_graph;
                FILE* dense = std::fopen(output, "w");
                if (!dense) throw std::runtime_error("dense source output open");
                auto dense_bits = [](float value) {
                    uint32_t bits;
                    static_assert(sizeof(value) == sizeof(bits), "float32 capture");
                    std::memcpy(&bits, &value, sizeof(bits));
                    return bits;
                };
                std::fprintf(dense, "H\t%d\t%.9g\t%.9g\t%.9g\n", itry,
                             double(pres_fac), double(router_opts.max_criticality), double(router_opts.criticality_exp));
                size_t dense_nodes = 0, dense_tree_rows = 0, dense_connections = 0;
                for (auto id : dense_rr.nodes()) {
                    const auto& info = dense_rc.rr_node_route_inf[id];
                    std::fprintf(dense, "N\t%zu\t%d\t%d\t%u\t%.9g\n", size_t(id),
                                 int(info.occ()), int(dense_rr.node_capacity(id)),
                                 dense_bits(info.acc_cost), double(info.acc_cost));
                    ++dense_nodes;
                }
                for (auto net : net_list.nets()) if (dense_rc.route_trees[net]) {
                    for (const auto& node : dense_rc.route_trees[net]->all_nodes()) {
                        auto parent = node.parent();
                        std::fprintf(dense, "T\t%zu\t%zu\t%lld\t%zu\t%u\t%.9g\n", size_t(net),
                                     size_t(node.inode), parent ? static_cast<long long>(size_t(parent->inode)) : -1LL,
                                     size_t(node.parent_switch), dense_bits(node.Tdel), double(node.Tdel));
                        ++dense_tree_rows;
                    }
                }
                std::ifstream dense_queries(manifest);
                if (!dense_queries) throw std::runtime_error("dense source manifest open");
                std::string dense_line;
                while (std::getline(dense_queries, dense_line)) {
                    if (dense_line.compare(0, 2, "Q ") != 0) continue;
                    std::istringstream fields(dense_line.substr(2));
                    unsigned long long cid, net_index, sink_index, source_node, sink_node;
                    if (!(fields >> cid >> net_index >> sink_index >> source_node >> sink_node))
                        throw std::runtime_error("dense source query parse");
                    if (net_index >= dense_rc.net_rr_terminals.size() || sink_index == 0)
                        throw std::runtime_error("dense source query domain");
                    ParentNetId dense_net{size_t(net_index)};
                    if (sink_index >= dense_rc.net_rr_terminals[dense_net].size())
                        throw std::runtime_error("dense source sink index");
                    auto dense_pin = net_list.net_pin(dense_net, int(sink_index));
                    if (net_list.pin_net(dense_pin) != dense_net ||
                        size_t(dense_rc.net_rr_terminals[dense_net][0]) != source_node ||
                        size_t(dense_rc.net_rr_terminals[dense_net][sink_index]) != sink_node)
                        throw std::runtime_error("dense source physical identity");
                    float criticality = get_net_pin_criticality(timing_info.get(), netlist_pin_lookup,
                        router_opts.max_criticality, router_opts.criticality_exp, dense_net, dense_pin, is_flat);
                    std::fprintf(dense, "C\t%llu\t%llu\t%llu\t%zu\t%llu\t%llu\t%u\t%.9g\n", cid,
                                 net_index, sink_index, size_t(dense_pin), source_node, sink_node,
                                 dense_bits(criticality), double(criticality));
                    ++dense_connections;
                }
                if (!dense_queries.eof()) throw std::runtime_error("dense source manifest read");
                std::fprintf(dense, "F\t%zu\t%zu\t%zu\n", dense_nodes, dense_tree_rows, dense_connections);
                bool failed = std::ferror(dense);
                int closed = std::fclose(dense);
                if (failed || closed) throw std::runtime_error("dense source output close");
            }
        }
        // ROUTECAST_DENSE_POST_STA_CAPTURE_END
