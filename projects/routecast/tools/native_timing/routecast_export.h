#pragma once
#include <fstream>
#include <iostream>
#include <iomanip>
#include <stdexcept>
#include "net_delay.h"
#include "AnalysisDelayCalculator.h"
#include "timing_info.h"
#include "concrete_timing_info.h"
#include "timing_util.h"
#include "clustered_netlist_utils.h"
#include "atom_netlist.h"
#include "atom_lookup.h"

static void routecast_export(const t_vpr_setup& setup) {
    if (setup.RouterOpts.flat_routing) throw std::runtime_error("flat export unsupported");
    const auto& atom=g_vpr_ctx.atom();
    const auto& clb=g_vpr_ctx.clustering().clb_nlist;
    const auto& netlist=(const Netlist<>&)clb;
    std::cerr << "RouteCast stage: auto delay=" << std::endl;
    auto delay=make_net_pins_matrix<float>(netlist);
    std::cerr << "RouteCast stage: load_net_delay_from_routing" << std::endl;
    load_net_delay_from_routing(netlist,delay);
    std::cerr << "RouteCast stage: auto calc=" << std::endl;
    auto calc=std::make_shared<AnalysisDelayCalculator>(atom.nlist,atom.lookup,delay,false);
    std::cerr << "RouteCast stage: auto timing=" << std::endl;
    auto timing=make_setup_hold_timing_info(calc,setup.AnalysisOpts.timing_update_type);
    std::cerr << "RouteCast stage: timing->update();" << std::endl;
    timing->update();
    std::cerr << "RouteCast stage: IntraLbPbPinLookup pb_lookup" << std::endl;
    IntraLbPbPinLookup pb_lookup(g_vpr_ctx.device().logical_block_types);
    std::cerr << "RouteCast stage: ClusteredPinAtomPinsLookup lookup" << std::endl;
    ClusteredPinAtomPinsLookup lookup(clb,atom.nlist,pb_lookup);
    std::cerr << "RouteCast stage: std::ofstream out" << std::endl;
    std::ofstream out("routecast_cluster_criticality.jsonl");
    if (!out) throw std::runtime_error("export open failed");
    out<<std::setprecision(9);
    for (auto net:clb.nets()) {
        for (auto pin:clb.net_sinks(net)) {
            auto block=clb.pin_block(pin);
            auto pg=pb_lookup.pb_gpin(clb.block_type(block)->index,clb.pin_logical_index(pin));
            out<<"{\"net_id\":"<<size_t(net)<<",\"net\":"<<std::quoted(clb.net_name(net))
               <<",\"cluster_pin_id\":"<<size_t(pin)<<",\"block\":"<<std::quoted(clb.block_name(block))
               <<",\"port\":"<<std::quoted(std::string(pg->port->name))<<",\"bit\":"<<pg->pin_number
               <<",\"logical_pin\":"<<clb.pin_logical_index(pin)
               <<",\"net_pin_index\":"<<clb.pin_net_index(pin)
               <<",\"native_route_delay_s\":"<<delay[ParentNetId(net)][clb.pin_net_index(pin)]
               <<",\"criticality\":"<<calculate_clb_net_pin_criticality(*timing,lookup,ParentPinId(pin),false)
               <<",\"atom_pins\":[";
            bool first=true;
            for (auto ap:lookup.connected_atom_pins(pin)) {
                if (!first) out<<",";
                first=false;
                auto tn=atom.lookup.atom_pin_tnode(ap);
                out<<"{\"atom_pin_id\":"<<size_t(ap)<<",\"tatum_node\":"<<size_t(tn)
                   <<",\"criticality\":"<<timing->setup_pin_criticality(ap)<<"}";
            }
            out<<"]}\n";
        }
    }
    if (!out.good()) throw std::runtime_error("export write failed");
}

// Atom IDs and timing-node IDs survive packing resync; avoid stale pb pointers.
static void routecast_export_atom_timing(const t_vpr_setup& setup, const char* filename) {
    const auto& atom = g_vpr_ctx.atom();
    const auto& nl = (const Netlist<>&)g_vpr_ctx.clustering().clb_nlist;
    auto delay = make_net_pins_matrix<float>(nl);
    load_net_delay_from_routing(nl, delay);
    auto calc = std::make_shared<AnalysisDelayCalculator>(atom.nlist, atom.lookup, delay, false);
    auto timing = make_setup_hold_timing_info(calc, setup.AnalysisOpts.timing_update_type);
    timing->update();
    std::ofstream out(filename);
    if (!out) throw std::runtime_error("atom export open failed");
    out << std::setprecision(9);
    for (auto pin : atom.nlist.pins()) {
        out << "{\"atom_pin_id\":" << size_t(pin)
            << ",\"tatum_node\":" << size_t(atom.lookup.atom_pin_tnode(pin))
            << ",\"criticality\":" << timing->setup_pin_criticality(pin) << "}\n";
    }
    if (!out.good()) throw std::runtime_error("atom export write failed");
}
