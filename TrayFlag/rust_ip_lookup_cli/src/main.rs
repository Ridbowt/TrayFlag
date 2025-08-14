use serde::{Deserialize, Serialize};
use std::time::Duration;
use std::thread;

// --- НОВАЯ ФУНКЦИЯ ДЛЯ ПОВТОРНЫХ ПОПЫТОК ---
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

// --- Структуры ---
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

// --- Функции ---

fn get_myip_data(client: &reqwest::blocking::Client) -> Result<MyIpResponse, String> {
    client.get("https://api.myip.com")
        .send()
        .map_err(|e| e.to_string())?
        .json::<MyIpResponse>()
        .map_err(|e| e.to_string())
}

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

// --- Главная функция ---

fn main() {
    let client = reqwest::blocking::Client::builder()
        .timeout(Duration::from_secs(10))
        .user_agent(format!("TrayFlagIPLookup/2.0 (github.com/Ridbowt/TrayFlag)"))
        .pool_max_idle_per_host(0)
        .build()
        .unwrap();

    let ip = get_external_ip(&client);

    let full_data = if ip != "N/A" {
        get_full_location_data(&client, &ip)
    } else {
        FullLocationData {
            error: "No external IP detected.".to_string(),
            ..Default::default()
        }
    };

    let output = OutputData {
        ip_address: ip,
        full: full_data,
    };

    let json_output = serde_json::to_string(&output).unwrap_or_default();
    println!("{}", json_output);
}