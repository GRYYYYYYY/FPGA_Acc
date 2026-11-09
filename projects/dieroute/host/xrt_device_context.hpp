#pragma once
#include <xrt/xrt_device.h>
#include <cstdlib>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>

namespace dieroute { namespace xrt_host {
// Loading even the same image again can restart hw_emu and destroy BO state.
// One inline function-local instance is shared across adapter translation units.
struct DeviceContext {
    xrt::device device{0};
    xrt::uuid uuid;
    std::filesystem::path image;
    explicit DeviceContext(const std::filesystem::path& path):image(path) {
        uuid=device.load_xclbin(image.string());
        std::cerr<<"XRT shared device load=1 image="<<image.string()
                 <<" uuid="<<uuid.to_string()<<'\n';
    }
};
inline DeviceContext& device_context(const char* environment_name) {
    const auto path=std::getenv(environment_name);
    if(!path)throw std::runtime_error(std::string(environment_name)+" required");
    const auto requested=std::filesystem::canonical(path);
    static DeviceContext context(requested);
    if(!std::filesystem::equivalent(context.image,requested))
        throw std::runtime_error("XRT adapters must share the same image file; refusing device reload");
    return context;
}
}}
