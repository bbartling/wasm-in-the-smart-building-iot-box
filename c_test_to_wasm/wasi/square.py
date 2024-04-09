
import wasmtime

'''
TROUBLESHOOTING
on windows with Emscrpten vir env enabled
see if you can square a number from py
passed to the wasm output from this command.

WASI
> emcc square.c -o square.wasm -s EXPORTED_FUNCTIONS='["_square"]' -s STANDALONE_WASM

'''

# Load the WASM module.
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, 'square.wasm')

# Create a WASI environment.
wasi = wasmtime.WasiConfig()
wasi.argv = []  # No arguments
wasi.env = []  # No environment variables
wasi.preopen_dir(".", "/")  # Map the current directory to WASI's virtual root directory.
store.set_wasi(wasi)

# Create a linking environment, add WASI imports, and instantiate the module.
linker = wasmtime.Linker(engine)
linker.define_wasi()

instance = linker.instantiate(store, module)

# Get the `square` function from the module.
square_func = instance.exports(store)["square"]

# Call the `square` function with an integer argument.
num = 4
result = square_func(store, num)

print(f"The square of {num} is {result}.")
