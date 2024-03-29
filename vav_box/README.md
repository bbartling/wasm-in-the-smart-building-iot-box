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

* **lib.rs**: The crate root, which orchestrates the module inclusion and potentially re-exports key functionalities.
* **vav_box.rs**: Defines the VavBox struct and its basic functionalities, like temperature updates and state management.
* **control_signals.rs**: Manages the control signals for heating, cooling, and airflow, possibly including the logic for opening and closing valves or adjusting dampers.
* **pid.rs**: Contains PID control algorithms that can be used for maintaining setpoints for temperature, airflow, and other parameters.
* **sensors.rs**: Handles sensor input, such as temperature sensors, airflow sensors, etc. This could include simulating sensor input or interfacing with real sensor data.

## VAV Box Firmware Simulation
This project demonstrates a basic simulation of a Variable Air Volume (VAV) box firmware using Rust and WebAssembly (WASM), with interactions facilitated through a Python script. The Rust portion models the VAV box, incorporating features like temperature sensing, PID control for heating and cooling, and state management. The compiled WASM module is then utilized from Python to simulate different environmental scenarios affecting the VAV box.

#### Structure
* **Rust:** The core logic, including the VAV box model (VavBox), PID controller (PIDController), and temperature sensor (TemperatureSensor), is implemented in Rust. This code is compiled to a WASM module, making it accessible from other languages like Python.
* **Python:** A Python script interacts with the WASM module, simulating external temperature changes and querying the VAV box state.

#### Prerequisites
* Rust and Cargo (latest stable version)
* Python 3.x
* wasmtime Python package for running WASM

#### Compilation
To compile the Rust code to a WASM module, navigate to the project root and run:

```bash
cargo build --target wasm32-unknown-unknown
```

This command generates a WASM binary in `target/wasm32-unknown-unknown/debug/`.

#### Interacting with the WASM Module from Python
The Python script (`py_tester.py`) demonstrates how to load the WASM module, create a new instance of the VavBox, and simulate temperature changes to observe the VAV box's responses.

1. **Loading the WASM Module**: The script uses the wasmtime package to load the compiled WASM file.
2. **Creating a VAV Box Instance**: A new VAV box instance is created with a specified setpoint temperature.
3. **Simulating Temperature Changes**: The script updates the VAV box's temperature to simulate different environmental conditions (e.g., heating, cooling, satisfied).
4. **Querying the State**: After each temperature update, the script queries and prints the VAV box's state to demonstrate how the firmware would react to the changes.

#### Running the Simulation in Py
Ensure you've installed the required Python packages:
```bash
pip install wasmtime
```

Run the Python script:
```bash
python py_tester.py
```

#### Example Output
```bash
Scenario 1: Simulate Heating
VAV Box State Code: 1
VAV Box State: Heating

Scenario 2: Simulate Cooling
VAV Box State Code: 2
VAV Box State: Cooling

Scenario 3: Simulate Satisfied
VAV Box State Code: 3
VAV Box State: Satisfied
```

This output demonstrates how the VAV box firmware, simulated through Rust and WebAssembly, responds to different temperature inputs as if it were embedded firmware controlling an actual VAV box in an HVAC system.