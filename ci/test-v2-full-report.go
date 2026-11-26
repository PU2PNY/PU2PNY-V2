package main

import "testing"

func TestV2ReportOnlyReturnsKnownValues(t *testing.T) {
	for _, value := range []string{"YSF\npassword=example", "Bearer example", ""} {
		config := map[string]any{"protocol": value, "token": "example"}
		if got := reportProtocol(config); got != "unknown" {
			t.Fatalf("unrecognized protocol was returned: %q", got)
		}
		if got := reportServiceState(value); got != "unknown" {
			t.Fatalf("unrecognized service state was returned: %q", got)
		}
	}
	if got := reportProtocol(map[string]any{"protocol": " ysf "}); got != "YSF" {
		t.Fatalf("YSF protocol was lost: %q", got)
	}
	if got := reportServiceState("failed\n"); got != "failed" {
		t.Fatalf("failed service state was lost: %q", got)
	}
}

func TestV2ReportMatchesOnlyLocalUDPPort(t *testing.T) {
	output := "UNCONN 0 0 127.0.0.1:4200 0.0.0.0:*\nUNCONN 0 0 [::]:20010 [::]:*\n"
	for _, port := range []string{"4200", "20010"} {
		if got := reportUDPSocketState(output, port); got != "listening" {
			t.Fatalf("expected socket for port %s, got %q", port, got)
		}
	}
	if got := reportUDPSocketState("UNCONN 0 0 *:42000 127.0.0.1:4200", "4200"); got != "not listening" {
		t.Fatalf("mistook peer port for local port: %q", got)
	}
}
