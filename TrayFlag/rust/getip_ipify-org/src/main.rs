use serde::{Serialize, Deserialize};
use std::{thread, time::Duration};
use std::process;

// ← For parsing the response from ipify.org
#[derive(Deserialize)]
struct IpifyResponse {
    ip: String,
}

// ← Internal structure for full_data
#[derive(Serialize)]
struct FullData {
    ip: String,
    country_code: String,
    city: String,
    isp: String,
    error: String,
}

// ← Root response (ip + full_data)
#[derive(Serialize)]
struct Output {
    ip: String,
    full_data: FullData,
}

// ← Equivalent of Invoke-WithRetry from PowerShell
fn invoke_with_retry<F, T>(mut func: F, retries: u32, delay_secs: u64) -> Result<T, String>
where
    F: FnMut() -> Result<T, String>,
{
    let mut last_error = String::new();
    
    for attempt in 1..=retries {
        match func() {
            Ok(result) => return Ok(result),
            Err(e) => {
                eprintln!("[Debug] Attempt {}/{} failed: {}", attempt, retries, e);
                last_error = e;
                if attempt < retries {
                    thread::sleep(Duration::from_secs(delay_secs));
                }
            }
        }
    }
    Err(last_error)
}

fn fetch_ip() -> Result<String, String> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(10))
        .user_agent("TrayFlag/1.17.0")
        .build()
        .map_err(|e| format!("Client build failed: {}", e))?;

    let resp = client
        .get("https://api.ipify.org?format=json")
        .send()
        .map_err(|e| format!("Request failed: {}", e))?;

    let data: IpifyResponse = resp
        .json()
        .map_err(|e| format!("JSON parse failed: {}", e))?;

    Ok(data.ip)
}

fn main() {
    // Parameters: 3 attempts, 1 second pause
    let result = invoke_with_retry(fetch_ip, 3, 1);

    let output = match result {
        Ok(ip) => {
            // Success: populate full_data
            Output {
                ip: ip.clone(),
                full_data: FullData {
                    ip,
                    country_code: String::new(),
                    city: String::new(),
                    isp: String::new(),
                    error: String::new(),
                },
            }
        }
        Err(err_msg) => {
            // Error: ip="N/A", error in full_data
            Output {
                ip: "N/A".to_string(),
                full_data: FullData {
                    ip: String::new(),
                    country_code: String::new(),
                    city: String::new(),
                    isp: String::new(),
                    error: err_msg,
                },
            }
        }
    };

    // Output as compact JSON
    println!("{}", serde_json::to_string(&output).unwrap());
    
    // Exit code: 0 = success, 1 = error
    if output.ip == "N/A" {
        process::exit(1);
    } else {
        process::exit(0);
    }
}