// pu2pnyd-lean — PU2PNY-V2 lean Buildroot Stage 2 panel daemon.
//
// A deliberately small port of the panel backend for the lean image, which has
// BusyBox init + hostapd + dnsmasq and NO systemd / NetworkManager. It serves the
// static V2 panel and the subset of /api the panel needs for LIVE data (telemetry
// from /proc and /sys, version, connectivity), a minimal full-report, and a WiFi
// wizard driven by wpa_supplicant/iw (single-radio AP<->client handoff).
//
// TEST build. Not approved. Nothing here touches RF (there is none in Stage 2).
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"sync"
	"time"
)

const appVersion = "lean-stage2"

var (
	wwwDir   = envOr("PU2PNY_WWW", "/www")
	apIface  = envOr("PU2PNY_AP_IFACE", "wlan0")
	cpuPct   atomicFloat
	wifiMu   sync.Mutex
	wifiState = map[string]any{"state": "idle", "message": ""}
)

type atomicFloat struct {
	mu sync.Mutex
	v  float64
}

func (a *atomicFloat) set(v float64) { a.mu.Lock(); a.v = v; a.mu.Unlock() }
func (a *atomicFloat) get() float64  { a.mu.Lock(); defer a.mu.Unlock(); return a.v }

func envOr(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}

func readFile(p string) string { b, _ := os.ReadFile(p); return string(b) }

func run(timeout time.Duration, name string, args ...string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	out, err := exec.CommandContext(ctx, name, args...).CombinedOutput()
	return string(out), err
}

// ---- telemetry -------------------------------------------------------------

func cpuTimes() (idle, total uint64) {
	for _, line := range strings.Split(readFile("/proc/stat"), "\n") {
		if strings.HasPrefix(line, "cpu ") {
			f := strings.Fields(line)[1:]
			for i, s := range f {
				n, _ := strconv.ParseUint(s, 10, 64)
				total += n
				if i == 3 || i == 4 { // idle + iowait
					idle += n
				}
			}
			return
		}
	}
	return
}

func sampleCPU() {
	pi, pt := cpuTimes()
	for {
		time.Sleep(2 * time.Second)
		i, t := cpuTimes()
		di, dt := float64(i-pi), float64(t-pt)
		pi, pt = i, t
		if dt > 0 {
			cpuPct.set(roundTo((1.0-di/dt)*100, 1))
		}
	}
}

func roundTo(v float64, dp int) float64 {
	p := 1.0
	for i := 0; i < dp; i++ {
		p *= 10
	}
	return float64(int(v*p+0.5)) / p
}

func temperatureC() float64 {
	raw := strings.TrimSpace(readFile("/sys/class/thermal/thermal_zone0/temp"))
	if raw == "" {
		return -1
	}
	n, err := strconv.Atoi(raw)
	if err != nil {
		return -1
	}
	return roundTo(float64(n)/1000.0, 1)
}

func memoryMB() (usedMB, totalMB int) {
	var total, avail int
	for _, line := range strings.Split(readFile("/proc/meminfo"), "\n") {
		f := strings.Fields(line)
		if len(f) < 2 {
			continue
		}
		kb, _ := strconv.Atoi(f[1])
		switch f[0] {
		case "MemTotal:":
			total = kb
		case "MemAvailable:":
			avail = kb
		}
	}
	return (total - avail) / 1024, total / 1024
}

func telemetry() map[string]any {
	uMB, tMB := memoryMB()
	return map[string]any{
		"cpu_percent":     cpuPct.get(),
		"temperature":     temperatureC(),
		"memory_used_mb":  uMB,
		"memory_total_mb": tMB,
	}
}

func hostname() string { return strings.TrimSpace(readFile("/proc/sys/kernel/hostname")) }

func uptimeSec() int {
	f := strings.Fields(readFile("/proc/uptime"))
	if len(f) == 0 {
		return 0
	}
	s, _ := strconv.ParseFloat(f[0], 64)
	return int(s)
}

// ---- connectivity ----------------------------------------------------------

func defaultIface() string {
	out, _ := run(2*time.Second, "ip", "route", "show", "default")
	f := strings.Fields(out)
	for i, w := range f {
		if w == "dev" && i+1 < len(f) {
			return f[i+1]
		}
	}
	return ""
}

func connectivity() map[string]any {
	di := defaultIface()
	online := false
	if di != "" && di != apIface {
		if _, err := run(2*time.Second, "sh", "-c", "ping -c1 -W1 1.1.1.1 >/dev/null 2>&1"); err == nil {
			online = true
		}
	}
	c := map[string]any{"default_interface": di, "internet": online}
	// client-mode wifi signal, if associated (not while we host the AP)
	if link, err := run(2*time.Second, "iw", "dev", apIface, "link"); err == nil && strings.Contains(link, "Connected to") {
		for _, l := range strings.Split(link, "\n") {
			l = strings.TrimSpace(l)
			if strings.HasPrefix(l, "SSID:") {
				c["wifi_ssid"] = strings.TrimSpace(strings.TrimPrefix(l, "SSID:"))
			}
			if strings.HasPrefix(l, "signal:") {
				c["wifi_signal_dbm"] = strings.TrimSpace(strings.TrimPrefix(l, "signal:"))
			}
		}
	}
	return c
}

// ---- handlers --------------------------------------------------------------

func dashboardHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{
		"version":         appVersion,
		"telemetry":       telemetry(),
		"connectivity":    connectivity(),
		"config":          map[string]any{},
		"network_runtime": map[string]any{},
		"active":          nil,
		"updated":         time.Now().UTC().Format(time.RFC3339),
	})
}

func statusHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"version": appVersion, "hostname": hostname(), "stage": "lean-stage2"})
}

func systemHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method == http.MethodGet {
		writeJSON(w, 200, map[string]any{
			"version": appVersion, "hostname": hostname(),
			"utc": time.Now().UTC().Format(time.RFC3339), "local": time.Now().Format(time.RFC3339),
			"timezone": strings.TrimSpace(readFile("/etc/timezone")), "operational": false,
			"uptime_sec": uptimeSec(),
		})
		return
	}
	if r.Method != http.MethodPost {
		http.Error(w, "GET or POST", 405)
		return
	}
	var in struct {
		Action string `json:"action"`
	}
	_ = json.NewDecoder(r.Body).Decode(&in)
	switch in.Action {
	case "full-report":
		writeJSON(w, 200, map[string]any{"ok": true, "report": buildReport(), "generated": time.Now().UTC().Format(time.RFC3339)})
	case "reboot":
		go func() { time.Sleep(600 * time.Millisecond); _, _ = run(5*time.Second, "reboot") }()
		writeJSON(w, 200, map[string]any{"ok": true})
	case "poweroff":
		go func() { time.Sleep(600 * time.Millisecond); _, _ = run(5*time.Second, "poweroff") }()
		writeJSON(w, 200, map[string]any{"ok": true})
	default:
		writeJSON(w, 400, map[string]any{"ok": false, "error": "ação não disponível no Stage 2 lean"})
	}
}

func buildReport() string {
	var b strings.Builder
	t := telemetry()
	fmt.Fprintf(&b, "PU2PNY-V2 lean Stage 2 — relatório (TESTE)\n")
	fmt.Fprintf(&b, "gerado: %s\nversão: %s\nhostname: %s\nuptime_s: %d\n\n",
		time.Now().UTC().Format(time.RFC3339), appVersion, hostname(), uptimeSec())
	fmt.Fprintf(&b, "[telemetria]\ncpu_percent: %v\ntemperature_c: %v\nmemory: %v/%v MB\n\n",
		t["cpu_percent"], t["temperature"], t["memory_used_mb"], t["memory_total_mb"])
	c, _ := json.MarshalIndent(connectivity(), "", "  ")
	fmt.Fprintf(&b, "[conectividade]\n%s\n\n", c)
	for _, cmd := range [][]string{{"ip", "addr"}, {"ip", "route"}, {"iw", "dev"}} {
		out, _ := run(3*time.Second, cmd[0], cmd[1:]...)
		fmt.Fprintf(&b, "[$ %s]\n%s\n", strings.Join(cmd, " "), strings.TrimRight(out, "\n"))
	}
	fmt.Fprintf(&b, "\nNota: Stage 2 lean (sem RF/MMDVM/gateways). RF é Stage 3.\n")
	return b.String()
}

func liveHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"history": []any{}, "active": nil})
}
func connectivityHandler(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, connectivity()) }
func contactsHandler(w http.ResponseWriter, r *http.Request)     { writeJSON(w, 200, []any{}) }
func configHandler(w http.ResponseWriter, r *http.Request)       { writeJSON(w, 200, map[string]any{}) }
func updateHandler(w http.ResponseWriter, r *http.Request) {
	writeJSON(w, 200, map[string]any{"available": false, "current": appVersion, "latest": appVersion, "releases": []any{}})
}

// captive-portal: send OS probes to the panel so it auto-opens.
func captiveHandler(w http.ResponseWriter, r *http.Request) {
	http.Redirect(w, r, "/", http.StatusFound)
}

func main() {
	go sampleCPU()
	mux := http.NewServeMux()
	mux.HandleFunc("/api/dashboard", dashboardHandler)
	mux.HandleFunc("/api/status", statusHandler)
	mux.HandleFunc("/api/system", systemHandler)
	mux.HandleFunc("/api/live", liveHandler)
	mux.HandleFunc("/api/live/events", liveHandler)
	mux.HandleFunc("/api/connectivity", connectivityHandler)
	mux.HandleFunc("/api/contacts", contactsHandler)
	mux.HandleFunc("/api/config", configHandler)
	mux.HandleFunc("/api/update", updateHandler)
	mux.HandleFunc("/api/wifi/scan", wifiScanHandler)
	mux.HandleFunc("/api/network/connect", wifiConnectHandler)
	mux.HandleFunc("/api/network/connect/status", wifiStatusHandler)
	for _, p := range []string{"/generate_204", "/gen_204", "/hotspot-detect.html",
		"/connecttest.txt", "/ncsi.txt", "/library/test/success.html", "/redirect"} {
		mux.HandleFunc(p, captiveHandler)
	}
	// static panel last (catch-all)
	mux.Handle("/", http.FileServer(http.Dir(wwwDir)))
	addr := envOr("PU2PNY_ADDR", ":80")
	fmt.Printf("pu2pnyd-lean %s serving %s on %s\n", appVersion, wwwDir, addr)
	srv := &http.Server{Addr: addr, Handler: mux, ReadHeaderTimeout: 5 * time.Second}
	if err := srv.ListenAndServe(); err != nil {
		fmt.Fprintln(os.Stderr, "pu2pnyd-lean:", err)
		os.Exit(1)
	}
}
