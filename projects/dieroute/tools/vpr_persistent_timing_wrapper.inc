void vpr_analysis(const Netlist<>& net_list,
                  t_vpr_setup& vpr_setup,
                  const t_arch& Arch,
                  const RouteStatus& route_status,
                  bool is_flat) {
    const char* request_env = std::getenv("PERSISTROUTE_VPR_TIMING_REQUEST_FIFO");
    const char* response_env = std::getenv("PERSISTROUTE_VPR_TIMING_RESPONSE_FIFO");
    if ((request_env == nullptr || *request_env == '\0') &&
        (response_env == nullptr || *response_env == '\0')) {
        vpr_analysis_once(net_list, vpr_setup, Arch, route_status, is_flat);
        return;
    }
    if (request_env == nullptr || *request_env == '\0' || response_env == nullptr || *response_env == '\0' ||
        !vpr_setup.TimingEnabled || is_flat) {
        VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Persistent timing requires two FIFOs and clustered timing analysis");
    }
    const std::string request_path(request_env), response_path(response_env);
    struct stat request_stat{}, response_stat{};
    if (request_path == response_path || stat(request_path.c_str(), &request_stat) != 0 ||
        stat(response_path.c_str(), &response_stat) != 0 || !S_ISFIFO(request_stat.st_mode) || !S_ISFIFO(response_stat.st_mode)) {
        VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Invalid persistent timing FIFO paths");
    }
    const char* old_input = std::getenv("PERSISTROUTE_VPR_TIMING_INPUT");
    const bool had_input = old_input != nullptr;
    const std::string saved_input = had_input ? old_input : "";
    const char* old_output = std::getenv("PERSISTROUTE_VPR_TIMING_OUTPUT");
    const bool had_output = old_output != nullptr;
    const std::string saved_output = had_output ? old_output : "";
    std::ifstream requests(request_path);
    std::ofstream responses(response_path);
    if (!requests || !responses) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Unable to open persistent timing FIFOs");
    responses << "READY\t1\n" << std::flush;
    std::uint64_t next_request = 0;
    std::string line;
    while (std::getline(requests, line)) {
        std::istringstream stream(line);
        std::vector<std::string> fields;
        std::string field;
        while (std::getline(stream, field, '\t')) fields.push_back(field);
        if (fields.size() < 2 || fields[1].empty() ||
            !std::all_of(fields[1].begin(), fields[1].end(), [](char c) { return c >= '0' && c <= '9'; })) {
            VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Malformed persistent timing request");
        }
        std::istringstream sequence_stream(fields[1]);
        std::uint64_t sequence = 0;
        if (!(sequence_stream >> sequence) || !(sequence_stream >> std::ws).eof() || sequence != next_request) {
            VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Persistent timing request sequence mismatch");
        }
        if (fields[0] == "STOP" && fields.size() == 2) {
            responses << "STOPPED\t" << next_request << '\n' << std::flush;
            if (!responses) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Persistent timing stop acknowledgement failed");
            if (had_input) setenv("PERSISTROUTE_VPR_TIMING_INPUT", saved_input.c_str(), 1);
            else unsetenv("PERSISTROUTE_VPR_TIMING_INPUT");
            if (had_output) setenv("PERSISTROUTE_VPR_TIMING_OUTPUT", saved_output.c_str(), 1);
            else unsetenv("PERSISTROUTE_VPR_TIMING_OUTPUT");
            return;
        }
        if (fields[0] != "ANALYZE" || fields.size() != 4 || fields[2].empty() || fields[3].empty() ||
            fields[2] == fields[3] || next_request == std::numeric_limits<std::uint64_t>::max()) {
            VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Invalid persistent timing analysis request");
        }
        if (setenv("PERSISTROUTE_VPR_TIMING_INPUT", fields[2].c_str(), 1) != 0 ||
            setenv("PERSISTROUTE_VPR_TIMING_OUTPUT", fields[3].c_str(), 1) != 0) {
            VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Unable to install persistent timing request paths");
        }
        const auto start = std::chrono::steady_clock::now();
        vpr_analysis_once(net_list, vpr_setup, Arch, route_status, is_flat);
        const auto elapsed_us = std::chrono::duration_cast<std::chrono::microseconds>(std::chrono::steady_clock::now() - start).count();
        responses << "DONE\t" << sequence << '\t' << elapsed_us << '\n' << std::flush;
        if (!responses) VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Persistent timing acknowledgement failed");
        ++next_request;
    }
    VPR_FATAL_ERROR(VPR_ERROR_ANALYSIS, "Persistent timing request channel closed without STOP");
}

