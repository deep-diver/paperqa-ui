import os
import json
import requests
import sseclient

from pingpong import PingPong
from pingpong.pingpong import PPManager
from pingpong.pingpong import PromptFmt
from pingpong.pingpong import UIFmt
from pingpong.gradio import GradioChatUIFmt

class MistralChatPromptFmt(PromptFmt):
    @classmethod
    def ctx(cls, context):
        if context is None or context == "":
            return ""
        else:
            return f"""{context}

"""
    
    @classmethod
    def prompt(cls, pingpong, truncate_size):
        ping = pingpong.ping[:truncate_size]
        pong = "" if pingpong.pong is None else pingpong.pong[:truncate_size] + "</s>"
        return f"""<s>[INST] {ping} [/INST] {pong}
"""    

class MistralChatPPManager(PPManager):
    def build_prompts(self, from_idx: int=0, to_idx: int=-1, fmt: PromptFmt=MistralChatPromptFmt, truncate_size: int=None):
        if to_idx == -1 or to_idx >= len(self.pingpongs):
            to_idx = len(self.pingpongs)
            
        results = fmt.ctx(self.ctx)
        
        for idx, pingpong in enumerate(self.pingpongs[from_idx:to_idx]):
            results += fmt.prompt(pingpong, truncate_size=truncate_size)
            
        return results        

class GradioMistralChatPPManager(MistralChatPPManager):
    def build_uis(self, from_idx: int=0, to_idx: int=-1, fmt: UIFmt=GradioChatUIFmt):
        if to_idx == -1 or to_idx >= len(self.pingpongs):
            to_idx = len(self.pingpongs)
        
        results = []
        
        for pingpong in self.pingpongs[from_idx:to_idx]:
            results.append(fmt.ui(pingpong))
            
        return results  


class LLaMA2ChatPromptFmt(PromptFmt):
    @classmethod
    def ctx(cls, context):
        if context is None or context == "":
            return ""
        else:
            return f"""<<SYS>>
{context}
<</SYS>>
"""

    @classmethod
    def prompt(cls, pingpong, truncate_size):
        ping = pingpong.ping[:truncate_size]
        pong = "" if pingpong.pong is None else pingpong.pong[:truncate_size]
        return f"""[INST] {ping} [/INST] {pong}"""

class LLaMA2ChatPPManager(PPManager):
    def build_prompts(self, from_idx: int=0, to_idx: int=-1, fmt: PromptFmt=LLaMA2ChatPromptFmt, truncate_size: int=None):
        if to_idx == -1 or to_idx >= len(self.pingpongs):
            to_idx = len(self.pingpongs)

        results = fmt.ctx(self.ctx)

        for idx, pingpong in enumerate(self.pingpongs[from_idx:to_idx]):
            results += fmt.prompt(pingpong, truncate_size=truncate_size)

        return results

class GradioLLaMA2ChatPPManager(LLaMA2ChatPPManager):
    def build_uis(self, from_idx: int=0, to_idx: int=-1, fmt: UIFmt=GradioChatUIFmt):
        if to_idx == -1 or to_idx >= len(self.pingpongs):
            to_idx = len(self.pingpongs)

        results = []

        for pingpong in self.pingpongs[from_idx:to_idx]:
            results.append(fmt.ui(pingpong))

        return results

async def gen_text(
    prompt, 
    hf_model='mistralai/Mistral-7B-Instruct-v0.2', # 'mistralai/Mixtral-8x7B-Instruct-v0.1', # 'mistralai/Mistral-7B-Instruct-v0.1', # 'meta-llama/Llama-2-70b-chat-hf', 
    hf_token=None, 
    parameters=None
):
  if hf_token is None:
    raise ValueError("Hugging Face Token is not set")

  if parameters is None:
    parameters = {
        'max_new_tokens': 512,
        'do_sample': True,
        'return_full_text': False,
        'temperature': 1.0,
        'top_k': 50,
        # 'top_p': 1.0,
        'repetition_penalty': 1.2
    }

  url = f'https://api-inference.huggingface.co/models/{hf_model}'
  headers={
      'Authorization': f'Bearer {hf_token}',
      'Content-type': 'application/json'
  }
  data = {
      'inputs': prompt,
      'stream': True,
      'options': {
          'use_cache': False,
      },
      'parameters': parameters
  }

  r = requests.post(
      url,
      headers=headers,
      data=json.dumps(data),
      stream=True
  )

  try:
    client = sseclient.SSEClient(r)
    for event in client.events():
        yield json.loads(event.data)['token']['text']
  except Exception as e:
      print(e)

def gen_text_none_stream(
    prompt, 
    hf_model='meta-llama/Llama-2-70b-chat-hf', 
    hf_token=None, 
):
    parameters = {
        'max_new_tokens': 64,
        'do_sample': True,
        'return_full_text': False,
        'temperature': 0.7,
        'top_k': 10,
        # 'top_p': 1.0,
        'repetition_penalty': 1.2
    }

    url = f'https://api-inference.huggingface.co/models/{hf_model}'
    headers={
        'Authorization': f'Bearer {hf_token}',
        'Content-type': 'application/json'
    }
    data = {
        'inputs': prompt,
        'stream': False,
        'options': {
            'use_cache': False,
        },
        'parameters': parameters
    }

    r = requests.post(
        url,
        headers=headers,
        data=json.dumps(data),
    )

    return json.loads(r.text)[0]["generated_text"]