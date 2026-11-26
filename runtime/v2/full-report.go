package main

import (
	"context"
	"fmt"
	"net"
	"os/exec"
	"strings"
	"time"
)

func reportProtocol(config map[string]any) string {
	protocol, _ := config["protocol"].(string)
	switch protocol = strings.ToUpper(strings.TrimSpace(protocol)); protocol {
	case "DMR", "DSTAR", "YSF", "P25", "NXDN", "POCSAG":
		return protocol
	default:
		return "unknown"
	}
}

func reportServiceState(output string) string {
	switch state := strings.TrimSpace(output); state {
	case "active", "inactive", "activating", "deactivating", "reloading", "failed", "maintenance":
		return state
	default:
		return "unknown"
	}
}

func reportUDPSocketState(output string, port string) string {
	for _, line := range strings.Split(output, "\n") {
		fields := strings.Fields(line)
		if len(fields) < 5 {
			continue
		}
		_, localPort, err := net.SplitHostPort(fields[3])
		if err == nil && localPort == port {
			return "listening"
		}
	}
	return "not listening"
}

// Use only fixed status values. Config files and journal messages may contain
// credentials in fields and formats the diagnostic code cannot anticipate.
func buildFullReport(parent context.Context) string {
	ctx, cancel := context.WithTimeout(parent, 3*time.Second)
	defer cancel()

	var report strings.Builder
	fmt.Fprintf(&report, "PU2PNY-V2 - Relatório de diagnóstico\nVersão: %s\n", appVersion)
	fmt.Fprintf(&report, "Protocolo configurado: %s\n", reportProtocol(readPublicJSON(configFile)))
	fmt.Fprintln(&report, "\nServiços")
	for _, service := range []string{
		"2pnyd", "2pny-mmdvmhost", "2pny-dmrgateway", "2pny-dstargateway", "2pny-ysfgateway",
		"2pny-p25gateway", "2pny-nxdngateway", "2pny-dapnetgateway",
		"2pny-network-core", "2pny-display-core", "2pny-ysf-linkguard", "avahi-daemon",
	} {
		output, _ := exec.CommandContext(ctx, "systemctl", "is-active", service+".service").Output()
		fmt.Fprintf(&report, "%s: %s\n", service, reportServiceState(string(output)))
	}

	output, err := exec.CommandContext(ctx, "ss", "-H", "-lun").Output()
	fmt.Fprintln(&report, "\nPortas UDP locais")
	for _, port := range []string{"20010", "4200"} {
		state := "unknown"
		if err == nil {
			state = reportUDPSocketState(string(output), port)
		}
		fmt.Fprintf(&report, "%s: %s\n", port, state)
	}
	return report.String()
}
