# RapidWright / FPGA Interchange bridge

This bridge uses public RapidWright APIs to read a DCP or an FPGA Interchange
`.phys`/`.netlist` pair, export the commercial-device PIP graph and connection
tasks, and apply a routed PIP CSV back to a DCP and physical netlist.

```powershell
$env:RAPIDWRIGHT_PATH = "D:\RapidWright"
.\build.ps1
.\run.ps1 export input.dcp export_dir
.\run.ps1 apply input.dcp routes.csv routed.dcp routed.phys
```

The Linux entry points use the RapidWright 2022.2 standalone jar and the JDK
11 bundled with Vivado 2022.2 by default:

```bash
./build.sh
./run.sh inspect input.dcp
./run.sh export input.dcp export_dir
./run.sh extract routed.dcp routes.csv [net]
./run.sh apply input.dcp routes.csv routed.dcp routed.phys
```

Override `RAPIDWRIGHT_JAR`, `RAPIDWRIGHT_JAVA_HOME`, or `RAPIDWRIGHT_PATH`
when the matching tools are installed elsewhere.  FPGA Interchange physical
input uses an exact-stem logical netlist when present; otherwise the longest
logical-netlist stem that prefixes the physical filename is selected (for
example, `logicnets_jscl.netlist` for `logicnets_jscl_unrouted.phys`).

`extract` emits one complete non-static routed net by default, or validates
and emits the explicitly named net.  `apply` rejects unknown PIPs, PIPs owned
by two nets, and routes that do not connect the RapidWright source node to
every sink node.  Vivado
`report_route_status`, `report_timing_summary`, and `report_utilization` remain
the final industrial legality/QoR checks.

API references:

- <https://www.rapidwright.io/javadoc/com/xilinx/rapidwright/design/Design.html>
- <https://www.rapidwright.io/javadoc/com/xilinx/rapidwright/design/Net.html>
- <https://www.rapidwright.io/javadoc/com/xilinx/rapidwright/device/PIP.html>
- <https://www.rapidwright.io/javadoc/com/xilinx/rapidwright/interchange/Interchange.html>
- <https://www.rapidwright.io/javadoc/com/xilinx/rapidwright/interchange/PhysNetlistWriter.html>
