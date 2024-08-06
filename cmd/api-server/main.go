package main

import (
	api "github.com/woopzz/v2g/internal/adapters"
)

func main() {
	server := api.NewAPIServer("0.0.0.0:8000")
	server.Run()
}
