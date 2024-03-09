import copy
import asyncio
import google.generativeai as genai

from pingpong import PingPong
from pingpong.pingpong import PPManager
from pingpong.pingpong import PromptFmt
from pingpong.pingpong import UIFmt
from pingpong.gradio import GradioChatUIFmt

class GeminiChatPromptFmt(PromptFmt):
    @classmethod
    def ctx(cls, context):
        if context is None or context == "":
            return None
        else:
            return  {
                "role": "system",
                "parts": [context]
            }
    
    @classmethod
    def prompt(cls, pingpong, truncate_size):
        ping = pingpong.ping[:truncate_size]
        pong = "" if pingpong.pong is None else pingpong.pong[:truncate_size]
        result = [
            {
                "role": "user",
                "parts": [ping]
            }
        ]
        if pong != "":
            result = result + [
                {
                    "role": "model",
                    "parts": [pong]
                }
            ]

        return result

class GeminiChatPPManager(PPManager):
    def build_prompts(self, from_idx: int=0, to_idx: int=-1, fmt: PromptFmt=GeminiChatPromptFmt, truncate_size: int=None):
        if to_idx == -1 or to_idx >= len(self.pingpongs):
            to_idx = len(self.pingpongs)
        
        pingpongs = copy.deepcopy(self.pingpongs)
        ctx = fmt.ctx(self.ctx)
        ctx = ctx['parts'][0] if ctx is not None else ""
        results = []
        
        for idx, pingpong in enumerate(pingpongs[from_idx:to_idx]):
            if idx == 0:
                pingpong.ping = f"SYSTEM: {ctx} ----------- \n" + pingpong.ping
            results += fmt.prompt(pingpong, truncate_size=truncate_size)
            
        return results        

class GradioGeminiChatPPManager(GeminiChatPPManager):
    def build_uis(self, from_idx: int=0, to_idx: int=-1, fmt: UIFmt=GradioChatUIFmt):
        if to_idx == -1 or to_idx >= len(self.pingpongs):
            to_idx = len(self.pingpongs)
        
        results = []
        
        for pingpong in self.pingpongs[from_idx:to_idx]:
            results.append(fmt.ui(pingpong))
            
        return results

def init(api_key):
    genai.configure(api_key=api_key)

def _default_gen_text():
    return {
        "temperature": 0.9,
        "top_p": 1,
        "top_k": 1,
        "max_output_tokens": 2048,
    }

def _default_safety_settings():
    return [
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_MEDIUM_AND_ABOVE"
        },
    ]

async def _word_generator(sentence):
    for word in sentence.split():
        yield word
        delay = 0.03 + (len(word) * 0.005)
        await asyncio.sleep(delay)  # Simulate a short delay

async def gen_text(
    prompts,
    gen_config=_default_gen_text(),
    safety_settings=_default_safety_settings(),
    stream=True
):
    model = genai.GenerativeModel(model_name="gemini-1.0-pro",
                                generation_config=gen_config,
                                safety_settings=safety_settings)
    
    user_prompt = prompts[-1]
    prompts = prompts[:-1]
    convo = model.start_chat(history=prompts)

    resps = await convo.send_message_async(
        user_prompt["parts"][0], stream=stream
    )

    async for resp in resps:
        async for word in _word_generator(resp.text):
            yield word + " "

