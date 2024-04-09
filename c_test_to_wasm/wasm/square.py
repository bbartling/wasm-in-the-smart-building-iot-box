
import wasmtime

'''
TROUBLESHOOTING
on windows with Emscrpten vir env enabled
see if you can square a number from py
passed to the wasm output from this command.

WASM approach
> emcc square.c -s EXPORTED_FUNCTIONS='["_square"]' -o square.js

'''

# Load the WASM module.
engine = wasmtime.Engine()
store = wasmtime.Store(engine)
module = wasmtime.Module.from_file(engine, 'square.wasm')

# Create a linking environment and instantiate the module.
linker = wasmtime.Linker(engine)
instance = linker.instantiate(store, module)

# Get the `square` function from the module.
square_func = instance.exports(store)["square"]

# Call the `square` function with an integer argument.
num = 4
result = square_func(store, num)

print(f"The square of {num} is {result}.")
