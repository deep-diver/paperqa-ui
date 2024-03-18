import re
import copy
import json
import datasets
import gradio as gr
import pandas as pd

from pingpong import PingPong
from pingpong.context import CtxLastWindowStrategy

from gen.openllm import gen_text as open_llm_gen_text
from gen.gemini_chat import gen_text as gemini_gen_text
from gen.gemini_chat import init as gemini_init
from constants.context import DEFAULT_GLOBAL_CTX

from paper.download import get_papers_from_arxiv_ids

from init import (
    requested_arxiv_ids_df,
    date_dict,
    arxivid2data,
    dataset_repo_id,
    request_arxiv_repo_id,
    hf_token,
    gemini_api_key
)
from utils import push_to_hf_hub
gemini_init(gemini_api_key)

def get_paper_by_year(year):
    months = sorted(date_dict[year].keys())
    last_month = months[-1]
    
    days = sorted(date_dict[year][last_month].keys())
    last_day = days[-1]

    papers = list(set(
        [paper["title"] for paper in date_dict[year][last_month][last_day]]
    ))

    return (
        gr.Dropdown(choices=months, value=last_month),
        gr.Dropdown(choices=days, value=last_day),
        gr.Dropdown(choices=papers, value=papers[0])
    )

def get_paper_by_month(year, month):
    days = sorted(date_dict[year][month].keys())
    last_day = days[-1]

    papers = list(set(
        [paper["title"] for paper in date_dict[year][month][last_day]]
    ))

    return (
        gr.Dropdown(choices=days, value=last_day),
        gr.Dropdown(choices=papers, value=papers[0])
    )

def get_paper_by_day(year, month, day):
    papers = list(set(
        [paper["title"] for paper in date_dict[year][month][day]]
    ))
    return gr.Dropdown(choices=papers, value=papers[0])

# 2307.02040
def set_papers(year, month, day, title):
    title = title.split("]")[1].strip()

    papers = []
    for paper in date_dict[year][month][day]:
        papers.append(paper["title"])
        if paper["title"] == title:
            arxiv_id = paper["arxiv_id"]

    papers = list(set(papers))

    return (
        arxiv_id,
        gr.Dropdown(choices=papers, value=title),
        gr.Textbox("")
    )

def set_paper(year, month, day, paper_title):
    selected_paper = None
    for paper in date_dict[year][month][day]:
        if paper["title"] == paper_title:
            selected_paper = paper
            break

    return (
        selected_paper['arxiv_id'],
        gr.Markdown(f"# {selected_paper['title']}"), 
        gr.Markdown(
            "[![arXiv](https://img.shields.io/badge/arXiv-%s-b31b1b.svg?style=for-the-badge)](https://arxiv.org/abs/%s)" % (selected_paper['arxiv_id'], selected_paper['arxiv_id']) + " "
            "[![Paper page](https://huggingface.co/datasets/huggingface/badges/resolve/main/paper-page-lg.svg)](https://huggingface.co/papers/%s)" % selected_paper['arxiv_id']
        ),
        gr.Markdown(selected_paper["summary"]),

        gr.Markdown(f"### 🙋 {selected_paper['0_question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['0_answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['0_answers:expert']}"),
        gr.Markdown(f"### 🙋🙋 {selected_paper['0_additional_depth_q:follow up question']}"),
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['0_additional_depth_q:answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['0_additional_depth_q:answers:expert']}"),
        gr.Markdown(f"### 🙋🙋 {selected_paper['0_additional_breath_q:follow up question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['0_additional_breath_q:answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['0_additional_breath_q:answers:expert']}"),

        gr.Markdown(f"### 🙋 {selected_paper['1_question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['1_answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['1_answers:expert']}"),
        gr.Markdown(f"### 🙋🙋 {selected_paper['1_additional_depth_q:follow up question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['1_additional_depth_q:answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['1_additional_depth_q:answers:expert']}"),
        gr.Markdown(f"### 🙋🙋 {selected_paper['1_additional_breath_q:follow up question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['1_additional_breath_q:answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['1_additional_breath_q:answers:expert']}"),

        gr.Markdown(f"### 🙋 {selected_paper['2_question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['2_answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['2_answers:expert']}"),
        gr.Markdown(f"### 🙋🙋 {selected_paper['2_additional_depth_q:follow up question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['2_additional_depth_q:answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['2_additional_depth_q:answers:expert']}"),
        gr.Markdown(f"### 🙋🙋 {selected_paper['2_additional_breath_q:follow up question']}"), 
        gr.Markdown(f"↪ **(ELI5)** {selected_paper['2_additional_breath_q:answers:eli5']}"), 
        gr.Markdown(f"↪ **(Technical)** {selected_paper['2_additional_breath_q:answers:expert']}"),
    )

def set_date(title):
    title = title.split("]")[1].strip()

    for _, (year, months) in enumerate(date_dict.items()):
        for _, (month, days) in enumerate(months.items()):
            for _, (day, papers) in enumerate(days.items()):
                for paper in papers:
                    if paper['title'] == title:
                        return (
                            gr.Dropdown(value=year),
                            gr.Dropdown(choices=sorted(months), value=month),
                            gr.Dropdown(choices=sorted(days), value=day),
                        )

def change_exp_type(exp_type):
    if exp_type == "ELI5":
        return (
            gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False),
            gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False),
            gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False),
        )
    else:
        return (
            gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True),
            gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True),
            gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True), gr.Markdown(visible=False), gr.Markdown(visible=True),
        )
    
def _filter_duplicate_arxiv_ids(arxiv_ids_to_be_added):
    ds1 = datasets.load_dataset(request_arxiv_repo_id)
    ds2 = datasets.load_dataset(dataset_repo_id)

    unique_arxiv_ids = set()

    for d in ds1['train']:
        arxiv_ids = d['Requested arXiv IDs']
        unique_arxiv_ids = set(list(unique_arxiv_ids) + arxiv_ids)

    if len(ds2) > 1:
        for d in ds2['train']:
            arxiv_id = d['arxiv_id']
            unique_arxiv_ids.add(arxiv_id)

    return list(set(arxiv_ids_to_be_added) - unique_arxiv_ids)

def _is_arxiv_id_valid(arxiv_id):
  pattern = r"^\d{4}\.\d{5}$" 
  return bool(re.match(pattern, arxiv_id))

def _get_valid_arxiv_ids(arxiv_ids_str):
    valid_arxiv_ids = []
    invalid_arxiv_ids = []
    
    for arxiv_id in arxiv_ids_str.split(","):
        arxiv_id = arxiv_id.strip()
        if _is_arxiv_id_valid(arxiv_id):
           valid_arxiv_ids.append(arxiv_id)
        else:
            invalid_arxiv_ids.append(arxiv_id)

    return valid_arxiv_ids, invalid_arxiv_ids

def add_arxiv_ids_to_queue(queue, arxiv_ids_str):
    valid_arxiv_ids, invalid_arxiv_ids = _get_valid_arxiv_ids(arxiv_ids_str)
    
    if len(invalid_arxiv_ids) > 0: 
        gr.Warning(f"found invalid arXiv ids as in {invalid_arxiv_ids}")

    if len(valid_arxiv_ids) > 0:
        valid_arxiv_ids = _filter_duplicate_arxiv_ids(valid_arxiv_ids)

        if len(valid_arxiv_ids) > 0:
            papers = get_papers_from_arxiv_ids(valid_arxiv_ids)
            valid_arxiv_ids = [[f"[{paper['paper']['id']}] {paper['title']}"] for paper in papers]

            gr.Warning(f"Processing [{valid_arxiv_ids}]. Other requested arXiv IDs not found on this list should be already processed or being processed...")
            valid_arxiv_ids = pd.DataFrame({'Requested arXiv IDs': valid_arxiv_ids})
            queue = pd.concat([queue, valid_arxiv_ids])
            queue.reset_index(drop=True)

            ds = datasets.Dataset.from_pandas(valid_arxiv_ids)
            push_to_hf_hub(ds, request_arxiv_repo_id, hf_token)
        else:
            gr.Warning(f"All requested arXiv IDs are already processed or being processed...")
    else:
        gr.Warning(f"No valid arXiv IDs found...")

    return (
        queue, gr.Textbox("")
    )  

# Chat

def before_chat_begin():
    return (
        gr.Button(interactive=False),
        gr.Button(interactive=False),
        gr.Button(interactive=False)
    )

def _build_prompts(ppmanager, global_context, win_size=3):
    dummy_ppm = copy.deepcopy(ppmanager)
    dummy_ppm.ctx = global_context
    lws = CtxLastWindowStrategy(win_size)
    return lws(dummy_ppm)

async def chat_stream(idx, local_data, user_prompt, chat_state, ctx_num_lconv=3):
    paper = arxivid2data[idx]['paper']
    ppm = chat_state["ppmanager_type"].from_json(json.dumps(local_data))
    ppm.add_pingpong(
        PingPong(
            user_prompt,
            ""
        )
    )
    prompt = _build_prompts(ppm, DEFAULT_GLOBAL_CTX % paper["full_text"].replace("\n", " ")[:30000], ctx_num_lconv)

    # async for result in open_llm_gen_text(
    #     prompt, 
    #     hf_model='meta-llama/Llama-2-70b-chat-hf', hf_token=hf_token,
    #     parameters={
    #         'max_new_tokens': 4906,
    #         'do_sample': True,
    #         'return_full_text': False,
    #         'temperature': 0.7,
    #         'top_k': 10,
    #         'repetition_penalty': 1.2
    #     }
    # ):
    try:
        async for result in gemini_gen_text(prompt):
            ppm.append_pong(result)
            yield "", ppm.build_uis(), str(ppm), gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)

        yield "", ppm.build_uis(), str(ppm), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
    except Exception as e:
        print(str(e))
        gr.Warning("Gemini refused to answer further. This happens because there were some safety issues in the answer.")
        yield "", ppm.build_uis(), str(ppm), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)        

def chat_reset(local_data, chat_state):
    ppm = chat_state["ppmanager_type"].from_json(json.dumps(local_data))
    ppm.pingpongs = []

    return "", ppm.build_uis(), str(ppm), gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)