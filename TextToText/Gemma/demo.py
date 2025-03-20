"""
Two extra things you need to do here
 - login to huggingface for access
   - (echo "Your hugging face key" | podman secret create huggingface_token -) on your Linux box
   - add --secret huggingface_token to your podman run command
   - add reading the secret to your code from your /run/secrets library
 - install the Gemma 3 specific transformers library (included in the Dockerfile)

"""

import torch

from huggingface_hub import login
from transformers import AutoProcessor, Gemma3ForConditionalGeneration

class Gemma3BTextToTextDemo:
    def __init__(self, prompt):
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
            model_name, device_map="cuda", torch_dtype=torch.bfloat16)
        self.model = model_base.eval()
        self.processor = AutoProcessor.from_pretrained(model_name)
        self.messages = [
            {
                "role": "system",
                "content": [
                    {
                        "type": "text",
                        "text": "You are a helpful assistant."
                    }
                ]
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

    def run(self):
        inputs = self.build_inputs()
        input_len = inputs["input_ids"].shape[-1]
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs, max_new_tokens=2048,
                do_sample=False
            )[0][input_len:]

        decoded = self.processor.decode(outputs, skip_special_tokens=True)
        print(decoded)

    def build_inputs(self) -> dict:
        return self.processor.apply_chat_template(
            self.messages,
            add_generation_prompt=True,
            tokenize=True,
            return_dict=True,
            return_tensors="pt",
        ).to(
            self.model.device,
            dtype=torch.bfloat16,
        )

if __name__ == "__main__":
    demo = Gemma3BTextToTextDemo(
        prompt="Please, compare visiting California to visiting Florida for a vacation.")
    demo.run()