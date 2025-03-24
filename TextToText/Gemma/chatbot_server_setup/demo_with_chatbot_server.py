"""
Two extra things you need to do here
 - login to huggingface for access
   - (echo "Your hugging face key" | podman secret create huggingface_token -) on your Linux box
   - add --secret huggingface_token to your podman run command
   - add reading the secret to your code from your /run/secrets library
 - install the Gemma 3 specific transformers library (included in the Dockerfile)
 - you have to run the ServerSetup/ChatInterface/deploy_and_run_server.sh script as well
 - you have to open up another ssh connection and run this Dockerfile
 - if you want to access this from your macbook and you're running on a server, you have to
 listen on 0.0.0.0. I'm using port 12322 so you then have to map 12322 and open it up with your
 firewall meaning sudo ufw allow 12322 and then you can visit it from whatever your ifconfig says is
 your local address something like 192.168.x.x:12322
 - You now also need to create a local podman network so that your containers can talk to each
 other. That means running something like `podman network create gemma-test-network`. Then you
 need to add two things to your podman run commands: --network=gemma-test-network to both run
 commands for the python and golang containers, and you need to add names to each container.
 meaning --name=gemma_golang_webserver and --name=gemma_python_llm_server. Then you can use those
 names to connect. So you go to the Golang code and add
 LOCAL_GEMMA_URL="http://gemma_python_llm_server:12322"

"""
import torch
import math
import uvicorn

from huggingface_hub import login
from transformers import AutoProcessor, Gemma3ForConditionalGeneration
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime




class Message(BaseModel):
    request_time: int
    chat_content: str

class Response(BaseModel):
    llm_response: str
    llm_response_time: int

class Gemma3BTextToTextDemoWithServer:
    def __init__(self):
        try:
            with open("/run/secrets/huggingface_token") as f:
                huggingface_token = f.read().strip()
                login(token=huggingface_token)
        except FileNotFoundError:
            print("Huggingface Secret Token not found")
        # we want the -it version because it's already tuned for instructions (good for demos).
        # use -pt if you want a base model to fine-tune or doing RAG like iterations on.
        model_name = "google/gemma-3-4b-it"
        model_base = Gemma3ForConditionalGeneration.from_pretrained(
            model_name,
            device_map="cuda",
            torch_dtype=torch.bfloat16,
            attn_implementation="eager",)
        self.model = model_base.eval()
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.conversation_history = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a helpful assistant."
                    }
                ]
            },
        ]

    def run(self, prompt: str):
        self.conversation_history.append({
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
        })
        inputs = self.build_inputs()
        input_len = inputs["input_ids"].shape[-1]
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, max_new_tokens=2048,
                do_sample=False
            )[0][input_len:]

        decoded = self.processor.decode(outputs, skip_special_tokens=True)
        self.conversation_history.append({
            "role": "assistant",
            "content": [{"type": "text", "text": decoded}]
        })
        return decoded

    def build_inputs(self) -> dict:
        return self.processor.apply_chat_template(
            self.conversation_history,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(
            self.model.device,
            dtype=torch.bfloat16,
        )

if __name__ == "__main__":
    app = FastAPI()
    demo = Gemma3BTextToTextDemoWithServer()
    @app.post("/chat", response_model=Response)
    async def chat(message: Message):
        try:
            llm_response_time = math.floor(datetime.now().timestamp())
            response = demo.run(message.chat_content)
            return {"llm_response": response, "llm_response_time": llm_response_time}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    uvicorn.run(app, host="0.0.0.0", port=12322)

