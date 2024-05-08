use std::ffi::CString;
use std::os::raw::c_char;
use std::ptr;

// compile with
// $ cargo build --target wasm32-wasi --release

#[no_mangle]
pub extern "C" fn greet() -> *mut c_char {
    let greeting = "Hello from WASI!";
    let c_string = CString::new(greeting).expect("CString::new failed");
    let ptr = c_string.into_raw(); // Convert CString to a raw pointer
    println!("Allocated string '{}' at pointer {:?}", greeting, ptr);
    ptr // Return the raw pointer to the caller
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