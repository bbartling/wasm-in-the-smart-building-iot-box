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
