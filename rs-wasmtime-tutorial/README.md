# rs-wasmtime-tutorial

This tutorial demonstrates the construction of a very fake banking application for learning purposes utilizing Rust for backend logic and Python for interaction and execution control, all facilitated by WebAssembly (WASM) and the WebAssembly System Interface (WASI). This system exemplifies the integration of Rust's secure and efficient computation capabilities within a Python environment, harnessing the power of WebAssembly for cross-platform execution at near-native speeds.


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
use std::collections::HashMap;
use std::ffi::{CString, CStr};
use std::os::raw::c_char;
use std::sync::Mutex;
use lazy_static::lazy_static;

// compile with
// $ cargo build --target wasm32-wasi --release

#[no_mangle]
pub extern "C" fn custom_greet(input: *const c_char) -> *mut c_char {
    let input_str = unsafe {
        assert!(!input.is_null());
        CStr::from_ptr(input).to_str().unwrap()
    };
    let greeting = format!("Rust Info - Hello, {}", input_str);
    let log_greeting = greeting.clone();
    let c_string = CString::new(greeting).expect("Rust Error - CString::new failed");
    let ptr = c_string.into_raw();
    println!("Rust Info - Allocated string '{}' at pointer {:?}", log_greeting, ptr);
    ptr
}

#[no_mangle]
pub extern "C" fn free_string(s: *mut c_char) {
    unsafe {
        if s.is_null() {
            println!("Rust Error - Received null pointer, no action taken.");
            return;
        }
        println!("Rust Info - Freeing memory at pointer {:?}", s);
        let _ = CString::from_raw(s); // Reclaim and drop the CString safely
    }
}

#[no_mangle]
pub extern "C" fn plus(a: i32, b: i32) -> i32 {
    a + b
}

#[no_mangle]
pub extern "C" fn minus(a: i32, b: i32) -> i32 {
    a - b
}



struct Account {
    name: String,
    address: f64,
    acct_num: i32,
    balance: f64,
}

lazy_static! {
    static ref ACCOUNTS: Mutex<HashMap<i32, Account>> = Mutex::new(HashMap::new());
}

#[no_mangle]
pub extern "C" fn add_account(acct_num: i32, name_ptr: *const c_char, address: f64, balance: f64) {
    let name_c_str = unsafe { CStr::from_ptr(name_ptr) };
    let name = name_c_str.to_str().unwrap().to_owned();
    let account = Account { name, address, acct_num, balance };

    let mut accounts = ACCOUNTS.lock().unwrap();
    accounts.insert(acct_num, account);
    println!("Rust Info - Account {} added with initial balance: {}", acct_num, balance);
}

#[no_mangle]
pub extern "C" fn modify_balance(acct_num: i32, amount: f64) -> *mut c_char {
    let mut accounts = ACCOUNTS.lock().unwrap();
    if let Some(account) = accounts.get_mut(&acct_num) {
        account.balance += amount;
        let response = format!("Rust Info - New balance for account {}: {:.2}", acct_num, account.balance);
        let c_response = CString::new(response).expect("CString::new failed");
        let ptr = c_response.into_raw();
        println!("Rust Info - Allocated string for new balance at pointer {:?}", ptr);
        return ptr;
    }
    let error_message = "Rust Info - Account not found";
    let error_c_response = CString::new(error_message).expect("CString::new failed");
    let error_ptr = error_c_response.into_raw();
    println!("Rust Error - Error message allocated at pointer {:?}", error_ptr);
    error_ptr
}

#[no_mangle]
pub extern "C" fn get_balance(acct_num: i32) -> *mut c_char {
    let accounts = ACCOUNTS.lock().unwrap();
    if let Some(account) = accounts.get(&acct_num) {
        let response = format!("Rust Info - Balance for account {}: {:.2}", acct_num, account.balance);
        let c_response = CString::new(response).expect("CString::new failed");
        let ptr = c_response.into_raw();
        println!("Rust Info - Allocated string for balance at pointer {:?}", ptr);
        return ptr;
    }
    let error_message = "Rust Info - Account not found";
    let error_c_response = CString::new(error_message).expect("CString::new failed");
    let error_ptr = error_c_response.into_raw();
    println!("Rust Error - Error message allocated at pointer {:?}", error_ptr);
    error_ptr
}

```

## Python Script (`run_wasm.py`)
This script loads the WASM module, calls the exported Rust functions, and handles memory management for strings returned from Rust.

```python
import wasmtime

def write_c_string_to_memory(instance, store, string, context):
    memory = instance.exports(store)["memory"]
    string_bytes = string.encode('utf-8') + b'\x00'  # Null-terminate the string
    memory_length = memory.data_len(store)
    pointer = memory_length - len(string_bytes)  # Avoid any existing data
    memory.write(store, string_bytes, start=pointer)
    print(f"Py Info - Writing '{string}' to WASM memory at pointer {pointer} ({context})")
    return pointer

def add_account(instance, store, acct_num, name, address, balance):
    name_ptr = write_c_string_to_memory(instance, store, name, "account name")
    add_account_func = instance.exports(store)["add_account"]
    add_account_func(store, acct_num, name_ptr, address, balance)
    print(f"Py Info - Account {name} added with initial balance: {balance}")

def modify_balance(instance, store, acct_num, amount, name):
    modify_func = instance.exports(store)["modify_balance"]
    ptr = modify_func(store, acct_num, amount)
    result_str = read_c_string(instance, store, ptr)
    print(f"Py Info - Transaction for {name}. New balance: {result_str}")
    free_string(instance, store, ptr)

def get_balance(instance, store, acct_num, name):
    get_balance_func = instance.exports(store)["get_balance"]
    ptr = get_balance_func(store, acct_num)
    balance_str = read_c_string(instance, store, ptr)
    print(f"Py Info - Current balance for {name}: {balance_str}")
    free_string(instance, store, ptr)

def read_c_string(instance, store, ptr):
    memory = instance.exports(store)["memory"]
    result_bytes = []
    offset = 0
    while True:
        byte = memory.read(store, start=ptr + offset, stop=ptr + offset + 1)[0]
        if byte == 0:
            break
        result_bytes.append(byte)
        offset += 1
    string = bytes(result_bytes).decode('utf-8')
    return string

def free_string(instance, store, ptr):
    free_func = instance.exports(store)["free_string"]
    free_func(store, ptr)
    print(f"Py Info - Freed memory at pointer {ptr}")

def custom_print_greet(instance, store, input_str, name):
    memory = instance.exports(store)["memory"]
    greet_func = instance.exports(store)["custom_greet"]
    input_bytes = input_str.encode('utf-8')
    memory_length = memory.data_len(store)
    input_ptr = memory_length - len(input_bytes) - 1
    memory.write(store, input_bytes, start=input_ptr)
    print(f"Py Info - Writing greeting to memory for {name}: {input_str} at pointer {input_ptr}")
    ptr = greet_func(store, input_ptr)
    result_str = read_c_string(instance, store, ptr)
    print(f"Py Info - Greeting received for {name}: {result_str}")
    free_string(instance, store, ptr)

# WASM setup and configuration
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

# Initialize some fake accounts
accounts = [
    (101, "Alice", 1.0, 1000.0),
    (102, "Bob", 1.0, 1500.0),
    (103, "Charlie", 1.0, 500.0)
]
for acct_num, name, address, balance in accounts:
    add_account(instance, store, acct_num, name, address, balance)
    custom_print_greet(instance, store, f"Hello, {name}", name)


# Perform transactions
modify_balance(instance, store, 101, 250.0, name)
modify_balance(instance, store, 102, -750.0, name)

# Get balances
for acct_num, _, _, _ in accounts:
    get_balance(instance, store, acct_num, name)

# Example usage of the plus and minus functions
plus_func = instance.exports(store)["plus"]
result = plus_func(store, 5, 3)
print("Py Info - 5 + 3 =", result)

minus_func = instance.exports(store)["minus"]
result = minus_func(store, 10, 5)
print("Py Info - 10 - 5 =", result)
```

### Run the py script and you should see:
```
py .\run_wasm2.py
Py Info - Writing 'Alice' to WASM memory at pointer 1114106 (account name)
Rust Info - Account 101 added with initial balance: 1000
Py Info - Account Alice added with initial balance: 1000.0
Py Info - Writing greeting to memory for Alice: Hello, Alice at pointer 1114099
Rust Info - Allocated string 'Rust Info - Hello, Hello, Alice' at pointer 0x105130
Py Info - Greeting received for Alice: Rust Info - Hello, Hello, Alice
Rust Info - Freeing memory at pointer 0x105130
Py Info - Freed memory at pointer 1069360
Py Info - Writing 'Bob' to WASM memory at pointer 1114108 (account name)
Rust Info - Account 102 added with initial balance: 1500
Py Info - Account Bob added with initial balance: 1500.0
Py Info - Writing greeting to memory for Bob: Hello, Bob at pointer 1114101
Rust Info - Allocated string 'Rust Info - Hello, Hello, Bob' at pointer 0x105140
Py Info - Greeting received for Bob: Rust Info - Hello, Hello, Bob
Rust Info - Freeing memory at pointer 0x105140
Py Info - Freed memory at pointer 1069376
Py Info - Writing 'Charlie' to WASM memory at pointer 1114104 (account name)
Rust Info - Account 103 added with initial balance: 500
Py Info - Account Charlie added with initial balance: 500.0
Py Info - Writing greeting to memory for Charlie: Hello, Charlie at pointer 1114097
Rust Info - Allocated string 'Rust Info - Hello, Hello, Charlie' at pointer 0x105150
Py Info - Greeting received for Charlie: Rust Info - Hello, Hello, Charlie
Rust Info - Freeing memory at pointer 0x105150
Py Info - Freed memory at pointer 1069392
Rust Info - Allocated string for new balance at pointer 0x105150
Py Info - Transaction for Charlie. New balance: Rust Info - New balance for account 101: 1250.00
Rust Info - Freeing memory at pointer 0x105150
Py Info - Freed memory at pointer 1069392
Rust Info - Allocated string for new balance at pointer 0x105150
Py Info - Transaction for Charlie. New balance: Rust Info - New balance for account 102: 750.00
Rust Info - Freeing memory at pointer 0x105150
Py Info - Freed memory at pointer 1069392
Rust Info - Allocated string for balance at pointer 0x105150
Py Info - Current balance for Charlie: Rust Info - Balance for account 101: 1250.00
Rust Info - Freeing memory at pointer 0x105150
Py Info - Freed memory at pointer 1069392
Rust Info - Allocated string for balance at pointer 0x105150
Py Info - Current balance for Charlie: Rust Info - Balance for account 102: 750.00
Rust Info - Freeing memory at pointer 0x105150
Py Info - Freed memory at pointer 1069392
Rust Info - Allocated string for balance at pointer 0x105150
Py Info - Current balance for Charlie: Rust Info - Balance for account 103: 500.00
Rust Info - Freeing memory at pointer 0x105150
Py Info - Freed memory at pointer 1069392
Py Info - 5 + 3 = 8
Py Info - 10 - 5 = 5
```

### Explanation

**On the Rust Side:**

The Rust component is designed to act as the computational core and memory manager of the application. It includes several key functionalities:

- **Account Management**: Rust handles the creation and manipulation of bank account data structures. Each account, identified by a unique number, includes attributes such as name, balance, and address. These accounts are stored in a global `HashMap` protected by a `Mutex` for thread-safe operations, demonstrating Rust's capability to manage concurrent accesses securely.
  
- **Memory Management for Strings**: Rust functions are responsible for creating and managing C-style strings (null-terminated) using Rust’s `CString`. For instance, functions like `add_account` and `modify_balance` handle inputs and outputs as strings for interoperability with Python, managing memory allocations and deallocations explicitly to avoid leaks.
  
- **Logging and Debugging**: Strategic logging throughout the Rust codebase provides visibility into operations such as memory allocation and string manipulation. These logs are crucial for tracing data flow and debugging, especially when dealing with the low-level aspects of memory management.

**On the Python Side:**

Python acts as the interface layer, allowing users to interact with the Rust-compiled WebAssembly module:

- **Module Interaction**: Python uses the Wasmtime API to load and instantiate the WASM module, enabling direct calls to Rust functions. This setup allows Python to handle high-level application logic, such as initiating transactions or querying account balances, while relying on Rust for the execution of these requests.
  
- **Memory and Resource Management**: Python directly manipulates WASM’s linear memory to read and write data, reflecting an advanced level of control similar to what is achievable in languages like C. This includes allocating memory for strings to be passed to Rust and freeing it once it's no longer needed, ensuring efficient resource management.

- **Direct WASM Memory Access**: By accessing and modifying the linear memory where the WASM module operates, Python can effectively communicate complex data like strings and receive computational results, which are then converted into Python’s native types for further processing or display.

**WebAssembly and WASI Integration:**

The use of WASM and WASI is crucial for ensuring that the application runs efficiently and securely across multiple platforms without modification:

- **WebAssembly (WASM)**: Provides a compilation target for the Rust code that ensures it runs at near-native speed on any platform, enhancing the portability and performance of the application.
  
- **WebAssembly System Interface (WASI)**: Enables the Rust code running within the WASM module to perform system-like operations, such as I/O operations, in a platform-independent manner. WASI is used here primarily to handle console outputs and to ensure that the standard output behaves consistently across different environments.
