# wasm-hvac-controls
concept ideas of WebAssembly in HVAC controls PLC logic

## Project Layout
```bash
wasm_vav_control/
├── Cargo.toml
└── src/
    ├── lib.rs
    ├── vav_box.rs
    ├── control_signals.rs
    ├── pid.rs
    └── sensors.rs
```

* lib.rs: The crate root, which orchestrates the module inclusion and potentially re-exports key functionalities.
* vav_box.rs: Defines the VavBox struct and its basic functionalities, like temperature updates and state management.
* control_signals.rs: Manages the control signals for heating, cooling, and airflow, possibly including the logic for opening and closing valves or adjusting dampers.
* pid.rs: Contains PID control algorithms that can be used for maintaining setpoints for temperature, airflow, and other parameters.
* sensors.rs: Handles sensor input, such as temperature sensors, airflow sensors, etc. This could include simulating sensor input or interfacing with real sensor data.