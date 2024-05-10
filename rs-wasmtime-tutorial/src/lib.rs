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


