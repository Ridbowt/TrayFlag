package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"time"
)

// IPifyResponse represents the JSON structure from ipify.org
type IPifyResponse struct {
	IP string `json:"ip"`
}

// FullLocationData represents the consolidated data from either service
type FullLocationData struct {
	IP          string `json:"ip"`
	CountryCode string `json:"country_code"`
	City        string `json:"city"`
	ISP         string `json:"isp"`
	Error       string `json:"error,omitempty"`
}

// This function attempts to get detailed location data from multiple services.
func getFullLocationData(ipAddress string) FullLocationData {
	if ipAddress == "N/A" || ipAddress == "" {
		return FullLocationData{Error: "Cannot get full location data for 'N/A' or empty IP address."}
	}

	services := []struct {
		URL    string
		Parser func([]byte) (FullLocationData, error)
	}{
		{
			// First priority: ip-api.com
			URL: fmt.Sprintf("http://ip-api.com/json/%s?fields=status,message,countryCode,city,isp,query", ipAddress),
			Parser: func(body []byte) (FullLocationData, error) {
				var data struct {
					Status      string `json:"status"`
					Message     string `json:"message"`
					CountryCode string `json:"countryCode"`
					City        string `json:"city"`
					ISP         string `json:"isp"`
					Query       string `json:"query"`
				}
				if err := json.Unmarshal(body, &data); err != nil {
					return FullLocationData{}, err
				}
				if data.Status != "success" {
					return FullLocationData{}, fmt.Errorf("service returned status: %s - %s", data.Status, data.Message)
				}
				return FullLocationData{
					IP:          data.Query,
					CountryCode: data.CountryCode,
					City:        data.City,
					ISP:         data.ISP,
				}, nil
			},
		},
		{
			// Second priority: ipinfo.io
			URL: fmt.Sprintf("https://ipinfo.io/%s/json", ipAddress),
			Parser: func(body []byte) (FullLocationData, error) {
				var data struct {
					IP      string `json:"ip"`
					Country string `json:"country"`
					City    string `json:"city"`
					Org     string `json:"org"`
				}
				if err := json.Unmarshal(body, &data); err != nil {
					return FullLocationData{}, err
				}
				return FullLocationData{
					IP:          data.IP,
					CountryCode: data.Country,
					City:        data.City,
					ISP:         data.Org,
				}, nil
			},
		},
	}

	for _, service := range services {
		client := http.Client{Timeout: 10 * time.Second}
		resp, err := client.Get(service.URL)
		if err != nil {
			continue // Try the next service
		}
		defer resp.Body.Close()

		if resp.StatusCode == http.StatusOK {
			body, err := ioutil.ReadAll(resp.Body)
			if err != nil {
				continue
			}
			location, err := service.Parser(body)
			if err == nil {
				return location
			}
		}
	}

	return FullLocationData{Error: "All full IP data services are unavailable."}
}

// getExternalIP gets the current external IP from ipify.org.
func getExternalIP() string {
	client := http.Client{Timeout: 5 * time.Second}
	resp, err := client.Get("https://api.ipify.org?format=json")
	if err != nil {
		return "N/A"
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "N/A"
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		return "N/A"
	}

	var ipifyResponse IPifyResponse
	if err := json.Unmarshal(body, &ipifyResponse); err != nil {
		return "N/A"
	}

	return ipifyResponse.IP
}

func main() {
	var outputData struct {
		IP   string           `json:"ip"`
		Full FullLocationData `json:"full_data,omitempty"`
	}

	// First, get the external IP from ipify.org
	outputData.IP = getExternalIP()

	// If the IP is valid, get the detailed data
	if outputData.IP != "N/A" {
		outputData.Full = getFullLocationData(outputData.IP)
	} else {
		outputData.Full = FullLocationData{Error: "No external IP detected."}
	}

	jsonData, _ := json.Marshal(outputData)
	fmt.Println(string(jsonData))
}