# Native full-color build

Configure and test the current project sources with:

```sh
cmake -S wire_full_color_search -B build/wire_full_color
cmake --build build/wire_full_color -j 2
ctest --test-dir build/wire_full_color --output-on-failure
```

Timing candidates that use `ap_wait()` require the Vitis HLS headers for native
compilation. Set their location explicitly when configuring:

```sh
cmake -S wire_full_color_search -B build/wire_full_color \
  -DTILEPLACE_HLS_INCLUDE_DIR=/path/to/Vitis_HLS/2022.2/include
```

CMake applies that directory to both native binaries and the compiler calls in
the integration tests. No compiler wrapper or global `PATH` change is needed.
For direct Python unittest execution, set the environment variable
`TILEPLACE_HLS_INCLUDE_DIR` to the same directory. Tests retain `-Werror` while
suppressing the HLS pragma and protocol-label warnings in this mode.

The Vitis HLS 2022.2 CPU definition of `ap_wait()` is empty; native tests check
functional results, while clock boundaries still require generated RTL
inspection and cosimulation. This build option does not adopt a timing
candidate or replace the full RTL, native-cohort, and routed timing gates.
