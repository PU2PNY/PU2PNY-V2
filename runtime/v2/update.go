package main

import "net/http"

// Legacy 5.x Debian bundles must not be applied to the Buildroot system.
func updateStatusHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control", "no-store")
	switch r.Method {
	case http.MethodGet:
		writeJSON(w, http.StatusOK, map[string]any{
			"current": appVersion, "available": false, "releases": []any{},
			"updater": map[string]any{
				"state": "unavailable", "backups": []any{},
				"message": "Atualização pelo painel ainda indisponível no PU2PNY-V2 leve.",
			},
		})
	case http.MethodPost:
		writeJSON(w, http.StatusConflict, map[string]any{
			"ok": false, "state": "unavailable",
			"error": "Este sistema precisa de uma atualização própria para a versão leve.",
		})
	default:
		w.Header().Set("Allow", "GET, POST")
		http.Error(w, "GET or POST required", http.StatusMethodNotAllowed)
	}
}
