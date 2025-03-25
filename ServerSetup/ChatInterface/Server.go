package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"strings"
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

type ClearResponse struct {
	Status string `json:"status"`
}

type ClearAction struct {
	Action string `json:"action"`
}

var (
	LOCAL_GEMMA_URL  = "http://gemma_python_llm_server:12322"
	userRequestState = make(map[string]bool)
)

func main() {
	log.Println("starting up the chatbot")
	args := os.Args
	port := args[1]

	http.HandleFunc("/", IndexHandler)
	http.HandleFunc("/chat", GemmaChatBotRequestHandler)
	http.HandleFunc("/clear", ClearChatRequestHandler)
	log.Println("Server running on http://localhost:" + port)
	err := http.ListenAndServe(":"+port, nil)
	if err != nil {
		return
	}
}

func ClearChatRequestHandler(w http.ResponseWriter, r *http.Request) {
	var clearResponseMessage ClearResponse
	var clearActionMessage = ClearAction{Action: "clear"}
	actionToGemma, err := json.Marshal(clearActionMessage)
	if err != nil {
		log.Println("Attempting to marshal the clear action.")
		http.Error(w, "Attempting to marshal the clear action", http.StatusInternalServerError)
		return
	}
	actionGemmaReader := strings.NewReader(string(actionToGemma))
	resp, err := http.Post(LOCAL_GEMMA_URL+"/clear", "application/json", actionGemmaReader)
	if err != nil {
		log.Println("Attempting to clear the chat history.")
		http.Error(w, "Error clearing the chat history", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()
	response, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Println("Attempting to read the Python server's response")
		http.Error(w, "Error when attempting to read the Python server's response", http.StatusInternalServerError)
		return
	}

	err = json.Unmarshal(response, &clearResponseMessage)
	if err != nil {
		log.Println("Failed to parse the response from the Python server")
		http.Error(w, "Failed to parse the response from the Python server", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	_, err = w.Write(response)
	if err != nil {
		log.Println("failed to reply to the UI")
		http.Error(w, "failed to reply to the UI", http.StatusInternalServerError)
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
	resp, err := http.Post(LOCAL_GEMMA_URL+"/chat", "application/json", chatPostReader)
	if err != nil {
		log.Println("failed to post to the Python Chatbot server")
		http.Error(w, "Failed to connect to the Python Chatbot server", http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	// Now you take t*he Gemma response, package it up and send it back to the frontend.
	gemmaResponse, err := io.ReadAll(resp.Body)
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
	if llmResponse.LLMResponseTime < time.Now().UnixMilli()/10 {
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
