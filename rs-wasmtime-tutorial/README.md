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

## Rust Code (`src/lib.rs`)
This Rust file contains functions that will be compiled to WASM. It includes functions for creating a greeting and adding two numbers.

```rust
use std::ffi::{CString, CStr};
use std::os::raw::c_char;

// compile with
// $ cargo build --target wasm32-wasi --release

#[no_mangle]
pub extern "C" fn custom_greet(input: *const c_char) -> *mut c_char {
    let input_str = unsafe {
        assert!(!input.is_null());
        CStr::from_ptr(input).to_str().unwrap()
    };
    let greeting = format!("Hello, {}", input_str);
    let log_greeting = greeting.clone();
    let c_string = CString::new(greeting).expect("CString::new failed");
    let ptr = c_string.into_raw();
    println!("Allocated string '{}' at pointer {:?}", log_greeting, ptr);
    ptr
}

#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    unsafe {
        if s.is_null() {
            println!("Received null pointer, no action taken.");
            return;
        }
        println!("Freeing memory at pointer {:?}", s);
        let _ = CString::from_raw(s); // Reclaim and drop the CString safely
    }
}

#[no_mangle]
pub extern "C" fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

## Python Script (`run_wasm.py`)
This script loads the WASM module, calls the exported Rust functions, and handles memory management for strings returned from Rust.

```python
import wasmtime

def custom_print_greet(instance, store, input_str):
    memory = instance.exports(store)["memory"]
    greet_func = instance.exports(store)["custom_greet"]

    # Encode the input string to bytes
    input_bytes = input_str.encode('utf-8')

    # Get available memory length and calculate the position to write the input bytes
    memory_length = memory.data_len(store)
    input_ptr = memory_length - len(input_bytes) - 1

    print(f"Writing to memory: Input string bytes = {input_bytes}")
    print(f"Memory data length = {memory_length}, Input pointer = {input_ptr}")

    # Write the input bytes to memory
    if input_ptr + len(input_bytes) > memory_length:
        raise Exception("Not enough space in memory to write the input bytes")
    
    memory.write(store, input_bytes, start=input_ptr)
    print("String written to WASM memory at pointer", input_ptr)

    # Call the custom greet function with the pointer to the input string
    ptr = greet_func(store, input_ptr)
    print(f"Received pointer from custom_greet: {ptr}")

    # Read the result string from WASM memory
    result_bytes = []
    offset = 0
    while True:
        byte = memory.read(store, start=ptr + offset, stop=ptr + offset + 1)[0]
        if byte == 0:
            break
        result_bytes.append(byte)
        offset += 1
    string = bytes(result_bytes).decode('utf-8')
    print(f"Resulting string: {string}")

    # Free the allocated string in WASM
    free_func = instance.exports(store)["free_string"]
    free_func(store, ptr)
    print("Freed memory at pointer:", ptr)

# Configuration and module loading
wasi_config = wasmtime.WasiConfig()
wasi_config.inherit_stdout()

engine = wasmtime.Engine()
store = wasmtime.Store(engine)
store.set_wasi(wasi_config)

module_path = './target/wasm32-wasi/release/rs_wasmtime_tutorial.wasm'
module = wasmtime.Module.from_file(engine, module_path)

linker = wasmtime.Linker(engine)
linker.define_wasi()

instance = linker.instantiate(store, module)

# Pass a custom string and print the greeting
custom_print_greet(instance, store, "World")

# Example usage of the add function
add_func = instance.exports(store)["add"]
result = add_func(store, 5, 3)
print("5 + 3 =", result)
```

### Run the py script and you should see:
```
> py .\run_wasm.py
Writing to memory: Input string bytes = b'World'
Memory data length = 1114112, Input pointer = 1114106
String written to WASM memory at pointer 1114106
Allocated string 'Hello, World' at pointer 0x101f90
Received pointer from custom_greet: 1056656
Resulting string: Hello, World
Freeing memory at pointer 0x101f90
Freed memory at pointer: 1056656
5 + 3 = 8
```

### Explanation

**On the Rust Side:**

In this system, the Rust code is crucial for creating a secure and efficient WebAssembly module. Functions like `greet` are meticulously designed to handle string manipulation and memory management, reflecting typical system-level programming practices in Rust. Specifically, the `greet` function generates a greeting message, "Hello from WASI!", formatted as a null-terminated C-style string. This string is managed using Rust’s `CString` type, which automatically handles memory allocation. Once the string is created, its raw pointer is safely exported back to the calling environment—Python, in this case—ensuring the pointer remains valid and accessible outside the Rust scope. Additionally, Rust functions include `println!` statements that log critical information, such as memory allocation and deallocation addresses. These logs are instrumental for debugging and tracing the flow of data across the Rust and Python boundary, providing clear visibility into how memory is managed and how data moves.

**On the Python Side:**

Python leverages the Wasmtime API to dynamically interact with the compiled WebAssembly module. By loading and instantiating the module, Python can call exposed Rust functions, such as `greet`, directly. Upon calling `greet`, Python receives a pointer to the string allocated in WASM’s linear memory. Using this pointer, Python accesses the string by reading directly from the memory location, converting it into Python’s native string format. This direct interaction showcases the low-level control Python has over WebAssembly memory, akin to C-style memory management. After the string is used, Python ensures clean and efficient memory management by invoking `free_string`, a function provided by the Rust side to deallocate the memory, preventing leaks and maintaining system health. Additionally, Python's configuration uses WASI to inherit the host’s standard output settings, which helps in retaining predictable and native-like console behaviors during execution. 

The execution also includes basic numerical operations handled by Rust and communicated back to Python, demonstrating the seamless integration of Rust’s computational capabilities within Python scripts. This not only ensures efficient execution but also leverages Rust’s performance advantages in a Python environment.

**WebAssembly and WASI Integration:**

The integration of WebAssembly (WASM) and the WebAssembly System Interface (WASI) is pivotal in bridging the Rust and Python environments. WASM serves as a highly portable compilation target that allows high-level languages like Rust to compile into a module that executes at near-native speeds, regardless of the host system. WASI further enhances this capability by providing system-like functionalities such as file and console operations that are essential for outputting data to the console. The explicit management of memory in both Rust and Python mimics traditional system programming practices, ensuring robust and leak-free handling of dynamic memory. This approach underlines a foundational strategy for inter-language communication and resource management, which is vital for system-level programming across different programming environments.

This detailed description emphasizes the technical workings and integration of Rust and Python through WebAssembly and WASI, providing a clear understanding of how these technologies interact to create a robust and efficient system.