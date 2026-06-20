# src/llm_engine.py
import os
import traceback

# Cloud client
try:
    from langchain_groq import ChatGroq
except Exception:
    ChatGroq = None

# Local model (transformers)
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
except Exception:
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None


class HybridLLMEngine:
    """
    Hybrid LLM engine:
      1) Try Groq cloud (if GROQ_API_KEY present and ChatGroq import succeeded)
      2) On failure or not available -> fallback to local GPU model (transformers)
    NOTE: .invoke(prompt: str) -> returns str
    """

    def __init__(self, cloud_model="llama-3.1-8b-instant", local_model_id="Qwen/Qwen2.5-7B-Instruct"):
        self.cloud_model = cloud_model
        self.local_model_id = local_model_id

        self.cloud_available = False
        self.local_available = False

        # Initialize cloud LLM if key & ChatGroq available
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and ChatGroq is not None:
            try:
                self.cloud_llm = ChatGroq(
                    model=self.cloud_model,
                    groq_api_key=groq_key,
                    max_tokens=1800
                )
                self.cloud_available = True
                print("[HybridLLM] Groq cloud initialized.")
            except Exception as e:
                print("[HybridLLM] Groq init failed:", e)
                self.cloud_available = False
        else:
            print("[HybridLLM] Groq not configured or client missing.")

        # Initialize local model if transformers available
        if AutoTokenizer is not None and AutoModelForCausalLM is not None and torch is not None:
            try:
                # loads tokenizer & model; device_map='auto' uses available GPUs
                print(f"[HybridLLM] Loading local model {self.local_model_id} ... (this may take time)")
                self.local_tokenizer = AutoTokenizer.from_pretrained(self.local_model_id, trust_remote_code=True)
                # prefer half precision if CUDA available
                target_dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                self.local_model = AutoModelForCausalLM.from_pretrained(
                    self.local_model_id,
                    torch_dtype=target_dtype,
                    device_map="auto" if torch.cuda.is_available() else None,
                    trust_remote_code=True
                )
                self.local_available = True
                print("[HybridLLM] Local model loaded.")
            except Exception as e:
                print("[HybridLLM] Local model load failed:", e)
                traceback.print_exc()
                self.local_available = False
        else:
            print("[HybridLLM] Transformers or torch not installed — local offline mode unavailable.")

        if not self.cloud_available and not self.local_available:
            print("[HybridLLM] Warning: no LLM backend available. Please set GROQ_API_KEY or install transformers+torch and a local model.")

    def invoke(self, prompt: str, max_tokens: int = 900) -> str:
        """
        Public invoke: returns string result. Tries cloud then local.
        """
        # 1) Try cloud
        if self.cloud_available:
            try:
                # ChatGroq expects a list of messages/prompts; keep compatibility
                resp = self.cloud_llm.invoke([prompt])
                content = getattr(resp, "content", None)
                if content is None:
                    # fallback: try string-like
                    return str(resp)
                return content
            except Exception as e:
                print("[HybridLLM] Cloud call failed — falling back to local. Error:", e)

        # 2) Local fallback
        if self.local_available:
            try:
                return self._invoke_local(prompt, max_tokens=max_tokens)
            except Exception as e:
                print("[HybridLLM] Local model inference failed:", e)
                traceback.print_exc()

        # 3) Nothing available
        raise RuntimeError("No LLM backend available (cloud failed and local not available).")

    def _invoke_local(self, prompt: str, max_tokens: int = 900) -> str:
        """
        Runs the local transformers model to generate a reply string.
        Note: simple generation; for instruction models you may want to wrap prompt tokens.
        """
        if not self.local_available:
            raise RuntimeError("Local model not available")

        tokenizer = self.local_tokenizer
        model = self.local_model

        # encode
        inputs = tokenizer(prompt, return_tensors="pt")
        # move to device(s)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        # generate
        gen = model.generate(
            **inputs,
            max_new_tokens=max_tokens,
            do_sample=False,
            temperature=0.2,
            top_p=0.95,
            eos_token_id=tokenizer.eos_token_id,
            pad_token_id=tokenizer.pad_token_id
        )

        # decode
        out = tokenizer.decode(gen[0], skip_special_tokens=True)
        return out
