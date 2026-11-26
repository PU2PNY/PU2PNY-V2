package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
)

func TestBuildrootUpdateRejectsLegacyBundle(t *testing.T) {
	post := httptest.NewRecorder()
	updateStatusHandler(post, httptest.NewRequest(http.MethodPost, "/api/update",
		strings.NewReader(`{"action":"install","version":"5.15.000"}`)))
	if post.Code != http.StatusConflict {
		t.Fatalf("legacy update accepted or handler returned unexpected status: %d", post.Code)
	}

	get := httptest.NewRecorder()
	updateStatusHandler(get, httptest.NewRequest(http.MethodGet, "/api/update", nil))
	var status struct {
		Available bool  `json:"available"`
		Releases  []any `json:"releases"`
	}
	if err := json.Unmarshal(get.Body.Bytes(), &status); err != nil {
		t.Fatal(err)
	}
	if get.Code != http.StatusOK || status.Available || len(status.Releases) != 0 {
		t.Fatalf("legacy catalogue exposed: code %d, status %+v", get.Code, status)
	}
}
