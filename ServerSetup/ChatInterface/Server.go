package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"
)

type ChatRequest struct {
	RequestTime int    `json:"request_time"`
	ChatContent string `json:"chat_content"`
}

type ChatResponse struct {
	LLMResponse     string `json:"llm_response"`
	LLMResponseTime int64  `json:"llm_response_time"`
}

var (
	LOCAL_GEMMA_URL  = "http://gemma_python_llm_server:12322/chat"
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
	var llmResponse ChatResponse
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
	log.Println(string(res))
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

	// Now you take t*he Gemma response, package it up and send it back to the frontend.
	gemmaResponse, err := io.ReadAll(resp.Body)
	//gemmaResponse, err := json.Marshal(&ChatResponse{
	//	LLMResponse:     "We're watching you.",
	//	LLMResponseTime: time.Now().UnixMilli(),
	//})
	if err != nil {
		log.Println("failed to read the gemma response", err)
		http.Error(w, "failed to read the Gemma response", http.StatusInternalServerError)
		return
	}
	fmt.Println(string(gemmaResponse))

	err = json.Unmarshal(gemmaResponse, &llmResponse)
	if err != nil {
		log.Println("failed to unmarshal the response")
		http.Error(w, "failed to unmarshal the LLM response", http.StatusInternalServerError)
		return
	}
	if llmResponse.LLMResponseTime < time.Now().UnixMilli() {
		llmResponse.LLMResponseTime = time.Now().UnixMilli()
	}
	output, err := json.Marshal(llmResponse)
	if err != nil {
		log.Println("failed to marshal the LLM response")
		http.Error(w, "Failed to marshal the LLM response to send to the UI", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, err = w.Write(output)
	if err != nil {
		log.Println("error writing back to the client", err)
		http.Error(w, "error writing the Gemma response back to the client", http.StatusInternalServerError)
		return
	}
}
