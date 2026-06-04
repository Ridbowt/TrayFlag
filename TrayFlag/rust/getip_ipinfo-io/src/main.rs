use serde::{Serialize, Deserialize};
use std::{thread, time::Duration, env};
use std::process;

// ← For parsing the response from ipinfo.io
#[derive(Deserialize)]
struct IpInfoResponse {
    ip: Option<String>,
    country: Option<String>,
    city: Option<String>,
    org: Option<String>,
    asn: Option<String>,
}

// ← Internal structure for full_data
#[derive(Serialize)]
struct FullData {
    ip: String,
    country_code: String,
    city: String,
    isp: String,
    asn: String,
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

fn fetch_ipinfo(ip: &str) -> Result<IpInfoResponse, String> {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(15))
        .user_agent("TrayFlag/1.17.0")
        .build()
        .map_err(|e| format!("Client build failed: {}", e))?;

    let url = format!("https://ipinfo.io/{}/json", ip);
    
    let resp = client
        .get(&url)
        .send()
        .map_err(|e| format!("Request failed: {}", e))?;

    let data: IpInfoResponse = resp
        .json()
        .map_err(|e| format!("JSON parse failed: {}", e))?;

    Ok(data)
}

fn main() {
    // ← Get IP from environment variable (like $env:TRAYFLAG_IP_TO_LOOKUP)
    let ip = match env::var("TRAYFLAG_IP_TO_LOOKUP") {
        Ok(val) => val,
        Err(_) => {
            // Env var missing — return error immediately (no retry)
            let output = Output {
                ip: String::new(),
                full_data: FullData {
                    ip: String::new(),
                    country_code: String::new(),
                    city: String::new(),
                    isp: String::new(),
                    asn: String::new(),
                    error: "IP address not provided via environment variable.".to_string(),
                },
            };
            println!("{}", serde_json::to_string(&output).unwrap());
            process::exit(1);
        }
    };

    // Parameters: 3 attempts, 1 second pause
    let result = invoke_with_retry(|| fetch_ipinfo(&ip), 3, 1);

    let output = match result {
        Ok(data) => {
            // Success: populate full_data from API response
            Output {
                ip: ip.clone(),
                full_data: FullData {
                    ip: data.ip.unwrap_or_default(),
                    country_code: data.country.unwrap_or_default(),
                    city: data.city.unwrap_or_default(),
                    isp: data.org.unwrap_or_default(),
                    asn: data.asn.unwrap_or_default(),
                    error: String::new(),
                },
            }
        }
        Err(err_msg) => {
            // Error: IP from env, error in full_data
            Output {
                ip: ip.clone(),
                full_data: FullData {
                    ip: ip.clone(),
                    country_code: String::new(),
                    city: String::new(),
                    isp: String::new(),
                    asn: String::new(),
                    error: err_msg,
                },
            }
        }
    };

    // Output as compact JSON
    println!("{}", serde_json::to_string(&output).unwrap());
    
    // Exit code: 0 = success, 1 = error
    if !output.full_data.error.is_empty() {
        process::exit(1);
    } else {
        process::exit(0);
    }
}