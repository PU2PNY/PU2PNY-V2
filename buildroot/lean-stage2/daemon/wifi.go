package main

import (
	"encoding/json"
	"net/http"
	"os"
	"regexp"
	"strings"
	"time"
)

// WiFi wizard for the lean stack (wpa_supplicant + iw + busybox udhcpc).
// Single radio: joining a home network means LEAVING AP mode, so the client that
// started the request will drop. We answer FIRST with an honest message, then do
// the handoff in the background, and restore the AP if the join fails.

func setWifi(state, msg string, extra map[string]any) {
	wifiMu.Lock()
	defer wifiMu.Unlock()
	wifiState = map[string]any{"state": state, "message": msg, "updated": time.Now().UTC().Format(time.RFC3339)}
	for k, v := range extra {
		wifiState[k] = v
	}
}

func getWifi() map[string]any {
	wifiMu.Lock()
	defer wifiMu.Unlock()
	cp := map[string]any{}
	for k, v := range wifiState {
		cp[k] = v
	}
	return cp
}

var ssidLine = regexp.MustCompile(`(?m)^\s*SSID:\s*(.+)$`)

// wifiScanHandler: scan while the AP is up if the firmware allows it; if the
// radio is busy, tell the user to type the SSID manually (single-radio limit).
func wifiScanHandler(w http.ResponseWriter, r *http.Request) {
	out, err := run(8*time.Second, "iw", "dev", apIface, "scan")
	if err != nil {
		writeJSON(w, 200, map[string]any{"ok": false, "manual": true,
			"error": "A varredura não está disponível com o AP ativo neste rádio. Informe o nome da rede (SSID) manualmente.",
			"networks": []any{}})
		return
	}
	seen := map[string]bool{}
	nets := []map[string]any{}
	for _, m := range ssidLine.FindAllStringSubmatch(out, -1) {
		s := strings.TrimSpace(m[1])
		if s == "" || seen[s] {
			continue
		}
		seen[s] = true
		nets = append(nets, map[string]any{"ssid": s})
	}
	writeJSON(w, 200, map[string]any{"ok": true, "networks": nets})
}

// wifiConnectHandler: start the AP->client handoff. Answers immediately.
func wifiConnectHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "POST required", 405)
		return
	}
	var in struct {
		SSID     string `json:"ssid"`
		Password string `json:"password"`
	}
	if json.NewDecoder(r.Body).Decode(&in) != nil || strings.TrimSpace(in.SSID) == "" {
		writeJSON(w, 400, map[string]any{"ok": false, "error": "informe o SSID"})
		return
	}
	setWifi("connecting", "Saindo do modo AP e entrando na sua rede. Reconecte seu aparelho à sua rede Wi-Fi e acesse http://pu2pny-v2.local (ou o IP do hotspot na sua rede).", nil)
	go joinNetwork(strings.TrimSpace(in.SSID), in.Password)
	writeJSON(w, 202, map[string]any{"ok": true, "state": "connecting",
		"message": "O hotspot vai entrar na sua rede Wi-Fi. Reconecte seu aparelho à SUA rede e acesse http://pu2pny-v2.local — o AP PU2PNY-V2 vai sair do ar. Se a conexão falhar, o AP volta sozinho em ~1 min."})
}

func wifiStatusHandler(w http.ResponseWriter, r *http.Request) { writeJSON(w, 200, getWifi()) }

func joinNetwork(ssid, psk string) {
	// Give the HTTP answer time to reach the client before the AP drops.
	time.Sleep(1500 * time.Millisecond)
	conf := "ctrl_interface=/var/run/wpa_supplicant\nnetwork={\n\tssid=\"" + wpaEscape(ssid) + "\"\n"
	if strings.TrimSpace(psk) == "" {
		conf += "\tkey_mgmt=NONE\n}\n"
	} else {
		conf += "\tpsk=\"" + wpaEscape(psk) + "\"\n}\n"
	}
	_ = writeConf("/etc/wpa_supplicant-wlan0.conf", conf)
	_, _ = run(10*time.Second, "/usr/local/sbin/pu2pny-ap", "stop")
	_, _ = run(5*time.Second, "pkill", "wpa_supplicant")
	_, _ = run(5*time.Second, "ip", "addr", "flush", "dev", apIface)
	_, _ = run(5*time.Second, "ip", "link", "set", apIface, "up")
	_, _ = run(8*time.Second, "wpa_supplicant", "-B", "-i", apIface, "-c", "/etc/wpa_supplicant-wlan0.conf")
	// wait for association
	associated := false
	for i := 0; i < 20; i++ {
		time.Sleep(1500 * time.Millisecond)
		link, _ := run(3*time.Second, "iw", "dev", apIface, "link")
		if strings.Contains(link, "Connected to") {
			associated = true
			break
		}
	}
	if !associated {
		_, _ = run(5*time.Second, "pkill", "wpa_supplicant")
		_, _ = run(10*time.Second, "/usr/local/sbin/pu2pny-ap", "start")
		setWifi("failed", "Não foi possível entrar na rede. O AP PU2PNY-V2 foi restaurado — reconecte ao AP e tente novamente.", nil)
		return
	}
	// DHCP on the joined network
	_, _ = run(20*time.Second, "udhcpc", "-i", apIface, "-n", "-q")
	ip := ""
	out, _ := run(3*time.Second, "sh", "-c", "ip -4 -o addr show dev "+apIface+" | awk '{print $4}' | head -1")
	ip = strings.TrimSpace(out)
	setWifi("connected", "Conectado à sua rede. Acesse http://pu2pny-v2.local"+func() string {
		if ip != "" {
			return " (IP " + strings.SplitN(ip, "/", 2)[0] + ")"
		}
		return ""
	}(), map[string]any{"ssid": ssid, "ip": ip})
}

func wpaEscape(s string) string {
	s = strings.ReplaceAll(s, "\\", "\\\\")
	s = strings.ReplaceAll(s, "\"", "\\\"")
	return s
}

func writeConf(path, data string) error {
	return os.WriteFile(path, []byte(data), 0o600)
}
