#!/usr/bin/env python3
"""PU2PNY-V2 TEST-2 backend: TEST-1 backend + the /api/system full-report action.

TEST build. NOT approved; nothing hardware-verified.

Adds a read-only diagnostic report so the owner can send logs to root-cause the
YSF-no-audio issue: POST /api/system {action:"full-report"} returns a downloadable
text report (config, diagnostics, hardware, display, network, service states, and
the MMDVMHost / YSFGateway / DMRGateway / 2pnyd journals). No RF/gateway change.
"""
from pathlib import Path
import subprocess
import sys

repo = Path(__file__).resolve().parents[1]
out = Path(sys.argv[1]).resolve()
arch = sys.argv[2]
subprocess.run([sys.executable, str(repo / 'ci/prepare-v2-backend.py'), str(out), arch], check=True)
main = out / 'main.go'
source = main.read_text()

anchor = '\tcase "reboot":'
assert source.count(anchor) == 1, 'reboot case anchor not unique'
case = (
    '\tcase "full-report":\n'
    '\t\twriteJSON(w, 200, map[string]any{"ok": true, "report": buildFullReport(), '
    '"generated": time.Now().UTC().Format(time.RFC3339)})\n'
    '\t\treturn\n'
)
source = source.replace(anchor, case + anchor, 1)
main.write_text(source)

report_go = r'''package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// fullReportCmd runs a read-only command with a short timeout for the report.
func fullReportCmd(name string, args ...string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	out, err := exec.CommandContext(ctx, name, args...).CombinedOutput()
	t := string(out)
	if err != nil {
		t += "\n[erro ao executar " + name + ": " + err.Error() + "]"
	}
	return strings.TrimRight(t, "\n")
}

// buildFullReport assembles a human-readable diagnostic. Read-only: it never
// changes RF, gateways or any configuration. Every section is captured
// independently so one failure does not abort the whole report.
func buildFullReport() string {
	var b strings.Builder
	now := time.Now().UTC().Format(time.RFC3339)
	fmt.Fprintf(&b, "PU2PNY-V2 - RELATORIO COMPLETO (TESTE)\n")
	fmt.Fprintf(&b, "Gerado: %s\nVersao: %s\nAVISO: build de TESTE, nada validado em hardware.\n\n", now, appVersion)
	sec := func(title, body string) {
		fmt.Fprintf(&b, "===== %s =====\n%s\n\n", title, strings.TrimRight(body, "\n"))
	}
	jsonSec := func(title string, v any) {
		raw, _ := json.MarshalIndent(v, "", "  ")
		sec(title, string(raw))
	}
	fileSec := func(title, path string) {
		if data, err := os.ReadFile(path); err == nil {
			sec(title, string(data))
		} else {
			sec(title, "[indisponivel: "+err.Error()+"]")
		}
	}
	fileSec("CONFIG (config.json)", configFile)
	cfg := readPublicJSON(configFile)
	proto, _ := cfg["protocol"].(string)
	gateways := map[string]string{
		"DMR": "2pny-dmrgateway.service", "DSTAR": "2pny-dstargateway.service", "YSF": "2pny-ysfgateway.service",
		"P25": "2pny-p25gateway.service", "NXDN": "2pny-nxdngateway.service", "POCSAG": "2pny-dapnetgateway.service",
	}
	gw := gateways[strings.ToUpper(proto)]
	jsonSec("DIAGNOSTICO", map[string]any{
		"protocol":         strings.ToUpper(proto),
		"mmdvmhost_active": serviceActive("2pny-mmdvmhost.service"),
		"gateway":          gw,
		"gateway_active":   gw != "" && serviceActive(gw),
		"udp":              map[string]any{"dstar": udpDiagnostic(20010), "ysf": udpDiagnostic(4200)},
		"mqtt_preflight":   readPublicJSON("/run/2pny/mqtt-preflight.json"),
		"protocol_health":  readPublicJSON("/run/2pny/protocol-health.json"),
		"network_connect":  readPublicJSON(filepath.Join(dataDir, "network-connect.json")),
		"last_rollback":    readPublicJSON(filepath.Join(dataDir, "last-protocol-rollback.json")),
		"dmr_duplex":       readPublicJSON("/run/2pny/dmr-duplex-diagnostics.json"),
	})
	fileSec("HARDWARE (hardware.json)", hardwareFile)
	jsonSec("DISPLAY", map[string]any{
		"detection": readPublicJSON(filepath.Join(dataDir, "display-detection.json")),
		"runtime":   readPublicJSON(filepath.Join(dataDir, "display-runtime.json")),
		"settings":  readPublicJSON(filepath.Join(dataDir, "display-settings.json")),
		"override":  readPublicJSON(displayOverrideFile),
	})
	fileSec("REDE (network-radio.json)", filepath.Join(dataDir, "network-radio.json"))
	services := []string{"2pnyd", "2pny-mmdvmhost", "2pny-ysfgateway", "2pny-dmrgateway", "2pny-dstargateway",
		"2pny-p25gateway", "2pny-nxdngateway", "2pny-network-core", "2pny-timezone-apply", "2pny-ysf-linkguard", "avahi-daemon"}
	var svc []string
	for _, s := range services {
		svc = append(svc, s+": "+fullReportCmd("systemctl", "is-active", s+".service"))
	}
	sec("SERVICOS", strings.Join(svc, "\n"))
	sec("LOG MMDVMHost (ultimas 400 linhas)", fullReportCmd("journalctl", "-u", "2pny-mmdvmhost.service", "-n", "400", "--no-pager", "-o", "cat"))
	sec("LOG YSFGateway (ultimas 400 linhas)", fullReportCmd("journalctl", "-u", "2pny-ysfgateway.service", "-n", "400", "--no-pager", "-o", "cat"))
	sec("LOG DMRGateway (ultimas 200 linhas)", fullReportCmd("journalctl", "-u", "2pny-dmrgateway.service", "-n", "200", "--no-pager", "-o", "cat"))
	sec("LOG 2pnyd (ultimas 200 linhas)", fullReportCmd("journalctl", "-u", "2pnyd.service", "-n", "200", "--no-pager", "-o", "cat"))
	return b.String()
}
'''
(out / 'web_v2report.go').write_text(report_go)
print("PREPARE_V2_TEST2_BACKEND_OK", arch)
