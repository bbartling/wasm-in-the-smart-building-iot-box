# rs-wasmtime-tutorial

This tutorial demonstrates how to compile Rust code to WebAssembly (WASM) that interacts with Python using Wasmtime and the WebAssembly System Interface (WASI). This example covers compiling a simple Rust application to WASM and running it from Python, where it can call Rust functions and handle memory safely across the FFI boundary.


## Requirements
* Rust with wasm32-wasi target installed
* Python 3.x
* Wasmtime Python package

## Setup
Install wasmtime with latest release of wasmtime. I am on Windows and ran the `.msi` file for release v20.0.2 from:
* https://github.com/bytecodealliance/wasmtime/releases

Run cargo command to add the wasm32-wasi target:
```bash
rustup target add wasm32-wasi
```

For python pip install wasmtime:
```bash
pip install wasmtime
```

## Project Structure
* Rust Source Code: `src/lib.rs`
* Python Script: `run_wasm.py`
* Cargo Configuration: `Cargo.toml`

## Building and Running the Project
* Compile the Rust code to WASM:
```bash
cargo build --target wasm32-wasi --release
```

Run the py script and you should see:
```
Allocated string 'Hello from WASI!' at pointer 0x101e60
Hello from WASI!
Freeing memory at pointer 0x101e60
5 + 3 = 8
```


On the Rust side, the code defines functions that are compiled to a WebAssembly module. One of these functions, greet, constructs a "Hello from WASI!" message as a C-style string (null-terminated), and safely exports this raw pointer back to the calling Python environment. Rust manages the allocation and deallocation of this memory using the CString type, ensuring no memory leaks occur. The println! statements within Rust functions provide console output indicating where strings are allocated and freed, which is crucial for debugging and understanding the flow of data across language boundaries.

On the Python side, the script uses the Wasmtime API to load and instantiate the compiled WebAssembly module. It specifically calls the greet function, receiving a pointer to the dynamically allocated string. Python then reads this string directly from the WebAssembly module's linear memory using the pointer, reconstructs the string in Python’s native format, and prints it to the console. After using the string, Python calls another Rust function, free_string, to properly deallocate the memory, preventing any potential memory leaks. This careful management of memory and use of the WASI configuration to inherit the host's standard output ensures that the application behaves predictably and efficiently. Moreover, the addition and printing of the numbers demonstrate straightforward numerical computations handled by Rust and results communicated back to Python, illustrating a practical and effective Rust-Python integration via WebAssembly.

In this tutorial, WebAssembly (WASM) and the WebAssembly System Interface (WASI) bridge the Rust and Python environments, allowing Rust-compiled functions to operate seamlessly within a Python script through Wasmtime. WASM provides a portable compilation target for high-level languages, enabling the Rust code to be compiled into a module that executes with near-native performance. WASI extends this by offering system-like functionalities, such as file and console operations, crucial for the module's output to the console. Similar to memory management in C, both Rust and Python explicitly handle memory allocation and deallocation, ensuring that the dynamic memory used to create and pass the "Hello from WASI!" message is properly managed. This prevents memory leaks and allows Python to interact directly with Rust's memory via pointers, illustrating a foundational approach to inter-language communication and efficient resource management in a system-level programming context.