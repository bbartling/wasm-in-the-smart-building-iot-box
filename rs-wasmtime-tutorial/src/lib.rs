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
