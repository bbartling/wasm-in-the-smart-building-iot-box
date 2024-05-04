def wasm_to_hex_c_array(wasm_file_path, hex_file_path, array_name="wasmModuleBytecode"):
    # Read the wasm file as binary
    with open(wasm_file_path, 'rb') as wasm_file:
        binary_data = wasm_file.read()

    # Convert binary data to hexadecimal format, formatted for C array initialization
    hex_array = ', '.join(f'0x{byte:02x}' for byte in binary_data)

    # Prepare the output content in C array format
    formatted_output = f"unsigned char {array_name}[] = {{\n  {hex_array}\n}};"

    # Write the formatted data to a new file
    with open(hex_file_path, 'w') as hex_file:
        hex_file.write(formatted_output)
# Example usage
wasm_to_hex_c_array('complete_sim.wasm', 'complete_sim.hex')
