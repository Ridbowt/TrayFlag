use serde::{Deserialize, Serialize};
use std::time::Duration;
use std::thread;

/// A function for retrying a function call with a specified number of retries.
///
/// This function takes a closure `f` which returns a `Result<T, E>`.
/// The function will be retried `retries` times if there is an error.
/// The function will sleep for 1 second between retries.
///
/// If all retries fail, the function will return the last error.
fn retry<F, T, E>(retries: u32, f: F) -> Result<T, E>
where
    F: Fn() -> Result<T, E>,
    E: std::fmt::Display,
{
    let mut last_error: Option<E> = None;
    for i in 0..retries {
        match f() {
            Ok(result) => return Ok(result),
            Err(e) => {
                eprintln!("[Debug] Attempt {}/{} failed: {}", i + 1, retries, e);
                last_error = Some(e);
                if i < retries - 1 {
                    thread::sleep(Duration::from_secs(1));
                }
            }
        }
    }
    Err(last_error.unwrap())
}

#[derive(Serialize)]
struct OutputData {
    #[serde(rename = "ip")]
    ip_address: String,
    #[serde(rename = "full_data")]
    full: FullLocationData,
}

#[derive(Serialize, Default)]
pub struct FullLocationData {
    #[serde(rename = "ip")]
    ip_address: String,
    #[serde(rename = "country_code")]
    country_code: String,
    city: String,
    #[serde(rename = "isp")]
    isp: String,
    #[serde(skip_serializing_if = "String::is_empty")]
    error: String,
}

#[derive(Deserialize)]
struct IpifyResponse {
    ip: String,
}

#[derive(Deserialize, Clone)]
struct MyIpResponse {
    ip: String,
    cc: String,
}

#[derive(Deserialize)]
#[allow(dead_code)]
struct IpApiResponse {
    status: String,
    message: Option<String>,
    #[serde(rename = "countryCode")]
    country_code: Option<String>,
    city: Option<String>,
    isp: Option<String>,
    query: Option<String>,
}

#[derive(Deserialize)]
struct IpInfoResponse {
    ip: Option<String>,
    country: Option<String>,
    city: Option<String>,
    org: Option<String>,
}

/// Attempts to fetch data from myip.com and parse it.
///
/// # Errors
/// - The request to myip.com failed.
/// - The response was not a valid JSON.
fn get_myip_data(client: &reqwest::blocking::Client) -> Result<MyIpResponse, String> {
    client.get("https://api.myip.com")
        .send()
        .map_err(|e| e.to_string())?
        .json::<MyIpResponse>()
        .map_err(|e| e.to_string())
}

/// Attempts to fetch external IP address from ipify.org and parse it.
///
/// # Errors
/// - The request to ipify.org failed.
/// - The response was not a valid JSON.
fn get_external_ip(client: &reqwest::blocking::Client) -> String {
    let ipify_closure = || -> Result<String, String> {
        Ok(client.get("https://api.ipify.org?format=json")
            .send()
            .map_err(|e| e.to_string())?
            .json::<IpifyResponse>()
            .map_err(|e| e.to_string())?
            .ip)
    };

    if let Ok(ip) = retry(3, ipify_closure) {
        return ip;
    }

    eprintln!("[Warning] ipify.org failed after all retries, falling back to myip.com.");
    if let Ok(data) = get_myip_data(client) {
        return data.ip;
    }

    "N/A".to_string()
}

/// Attempts to fetch the full location data for the given IP address.
///
/// # Errors
/// - The request to ip-api.com failed.
/// - The response was not a valid JSON.
/// - The request to ipinfo.io failed.
/// - The response was not a valid JSON.
/// - The request to myip.com failed.
/// - The response was not a valid JSON.
///
/// # Fallbacks
/// If ip-api.com fails, the function will fall back to ipinfo.io.
/// If ipinfo.io fails, the function will fall back to myip.com.
fn get_full_location_data(client: &reqwest::blocking::Client, ip_address: &str) -> FullLocationData {
    if ip_address == "N/A" || ip_address.is_empty() {
        return FullLocationData {
            error: "Cannot get full location data for 'N/A' or empty IP address.".to_string(),
            ..Default::default()
        };
    }

    let ip_api_closure = || -> Result<FullLocationData, String> {
        let url = format!("http://ip-api.com/json/{}?fields=status,message,countryCode,city,isp,query", ip_address);
        let response = client.get(&url).send().map_err(|e| e.to_string())?;
        let data: IpApiResponse = response.json().map_err(|e| e.to_string())?;
        if data.status == "success" {
            Ok(FullLocationData {
                ip_address: data.query.unwrap_or_default(),
                country_code: data.country_code.unwrap_or_default(),
                city: data.city.unwrap_or_default(),
                isp: data.isp.unwrap_or_default(),
                error: "".to_string(),
            })
        } else {
            Err(format!("ip-api.com status: {}", data.status))
        }
    };

    if let Ok(data) = retry(2, ip_api_closure) {
        return data;
    }

    eprintln!("[Warning] ip-api.com failed, falling back to ipinfo.io.");
    if let Ok(response) = client.get(&format!("https://ipinfo.io/{}/json", ip_address)).send() {
        if let Ok(data) = response.json::<IpInfoResponse>() {
            return FullLocationData {
                ip_address: data.ip.unwrap_or_default(),
                country_code: data.country.unwrap_or_default(),
                city: data.city.unwrap_or_default(),
                isp: data.org.unwrap_or_default(),
                error: "".to_string(),
            };
        }
    }

    eprintln!("[Warning] ipinfo.io failed, falling back to myip.com.");
    if let Ok(data) = get_myip_data(client) {
        return FullLocationData {
            ip_address: data.ip,
            country_code: data.cc,
            city: "N/A".to_string(),
            isp: "N/A".to_string(),
            error: "".to_string(),
        };
    }

    FullLocationData {
        error: "All IP data services are unavailable.".to_string(),
        ..Default::default()
    }
}


/// Main function.
fn main() {
    // Create a new `reqwest` HTTP client. This client will be used to make API requests.
    let client = reqwest::blocking::Client::builder()
        // Set the maximum time to wait for a response from any API calls.
        .timeout(Duration::from_secs(10))
        // Set the User-Agent header to identify the source of the requests.
        .user_agent(format!("TrayFlagIPLookup/2.0 (github.com/Ridbowt/TrayFlag)"))
        // Set the maximum number of idle connections to pool.
        .pool_max_idle_per_host(0)
        // Build the client.
        .build()
        .unwrap();

    // Get the external IP address.
    let ip = get_external_ip(&client);

    // Get the full location data for the IP address.
    let full_data = if ip != "N/A" {
        get_full_location_data(&client, &ip)
    } else {
        // If the IP address is "N/A", set the error message.
        FullLocationData {
            error: "No external IP detected.".to_string(),
            ..Default::default()
        }
    };

    // Create the output struct.
    let output = OutputData {
        ip_address: ip,
        full: full_data,
    };

    // Convert the output struct to JSON.
    let json_output = serde_json::to_string(&output).unwrap_or_default();

    // Print the JSON output.
    println!("{}", json_output);
}
