package main

import (
	"bytes"
	"encoding/json"
	"io"
	"log"
	"net/http"
	"os"
)

type ChatRequest struct {
	RequestTime int    `json:"request_time"`
	ChatContent string `json:"chat_content"`
}

var (
	LOCAL_GEMMA_URL  = "http://localhost:12322"
	userRequestState = make(map[string]bool)
)

func main() {
	log.Println("starting up the chatbot")
	args := os.Args
	port := args[1]

	http.HandleFunc("/", IndexHandler)
	http.HandleFunc("/chat", GemmaChatBotRequestHandler)
	log.Println("Server running on http://localhost:" + port)
	err := http.ListenAndServe(":"+port, nil)
	if err != nil {
		return
	}

}

func IndexHandler(w http.ResponseWriter, r *http.Request) {
	http.ServeFile(w, r, "index.html")
}

func GemmaChatBotRequestHandler(w http.ResponseWriter, r *http.Request) {
	var chatRequest ChatRequest
	var chatPost []byte
	userIP := r.RemoteAddr
	if userRequestState[userIP] {
		log.Println("Request already in progress", userIP)
		http.Error(w, "Request already in progress", http.StatusTooManyRequests)
		return
	}

	// the user sends you data (in JSON format)
	res, err := io.ReadAll(r.Body)
	if err != nil {
		log.Println(err)
	}
	err = json.Unmarshal(res, &chatRequest)
	if err != nil {
		log.Println("Failed to parse the json request", err)
		http.Error(w, "Failed to parse the JSON request", http.StatusInternalServerError)
		return
	}

	chatPost, err = json.Marshal(chatRequest)
	if err != nil {
		log.Println("Failed to convert it back into bytes")
		http.Error(w, "Failed to convert the input JSON back into bytes", http.StatusInternalServerError)
		return
	}
	chatPostReader := bytes.NewReader(chatPost)

	// After checking it out and making sure it's in the right format,
	//you send it along to the backend server that's running Gemma
	resp, err := http.Post(LOCAL_GEMMA_URL, "application/json", chatPostReader)
	if err != nil {
		log.Println("failed to post to the Python Chatbot server")
		http.Error(w, "Failed to connect to the Python Chatbot server", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	// Now you take the Gemma response, package it up and send it back to the frontend.
	gemmaResponse, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Println("failed to read the gemma response", err)
		http.Error(w, "failed to read the Gemma response", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, err = w.Write(gemmaResponse)
	if err != nil {
		log.Println("error writing back to the client", err)
		http.Error(w, "error writing the Gemma response back to the client", http.StatusInternalServerError)
		return
	}
}
