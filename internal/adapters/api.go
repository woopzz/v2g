package api

import (
	"log"
	"net/http"
	"os"
	"os/exec"
)

type APIServer struct {
	Addr string
}

func NewAPIServer(Addr string) *APIServer {
	return &APIServer{
		Addr: Addr,
	}
}

func (s *APIServer) Run() error {
	router := http.NewServeMux()
	router.HandleFunc("POST /videos", handleUploadVideo)

	server := http.Server{
		Addr:    s.Addr,
		Handler: router,
	}

	log.Printf("Server has started http://%s", s.Addr)
	return server.ListenAndServe()
}

func handleUploadVideo(w http.ResponseWriter, r *http.Request) {
	log.Println("Upload a new video")

	// 1. Save the video to the filesystem as a temporary file.

	file, _, err := r.FormFile("video")
	if err != nil {
		log.Fatal("[Retrieving Form Video]", err)
		return
	}
	defer file.Close()

	videoFile, err := os.CreateTemp(".", "*")
	if err != nil {
		log.Fatal("[Video File Creation]", err)
		return
	}
	defer os.Remove(videoFile.Name())

	videoFile.ReadFrom(file)
	videoFile.Close()

	// 2. Run ffmpeg commands.

	gifFileName := videoFile.Name() + ".gif"
	cmd := exec.Command("ffmpeg", "-i", videoFile.Name(), gifFileName)
	if err := cmd.Run(); err != nil {
		log.Fatal("[Conversion]", err)
		return
	}

	// 3. Put GIF file content in the response.

	gifFile, err := os.Open(gifFileName)
	if err != nil {
		log.Fatal("[GIF File Reading]", err)
		return
	}
	defer os.Remove(gifFile.Name())

	gifFile.WriteTo(w)
	log.Println("Converted successfully")
}
