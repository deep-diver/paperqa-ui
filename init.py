import os
import copy
import datasets
import pandas as pd
from datasets import Dataset
from collections import defaultdict

from datetime import datetime, timedelta
from background import process_arxiv_ids
from utils import create_hf_hub
from apscheduler.schedulers.background import BackgroundScheduler

def _count_nans(row):
    count = 0

    for _, (k, v) in enumerate(row.items()):
        if v is None:
            count = count + 1

    return count

def _initialize_requested_arxiv_ids(request_ds):
    requested_arxiv_ids = []

    for request_d in request_ds['train']:
        arxiv_ids = request_d['Requested arXiv IDs']
        requested_arxiv_ids = requested_arxiv_ids + arxiv_ids
    
    requested_arxiv_ids_df = pd.DataFrame({'Requested arXiv IDs': requested_arxiv_ids})
    return requested_arxiv_ids_df

def _initialize_paper_info(source_ds):
    title2qna, date2qna = {}, {}
    date_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    arxivid2data = {}
    count = 0    

    for data in source_ds["train"]:
        date = data["target_date"].strftime("%Y-%m-%d")
        arxiv_id = data["arxiv_id"]

        if date in date2qna:
            papers = copy.deepcopy(date2qna[date])
            for paper in papers:
                if paper["title"] == data["title"]:
                    if _count_nans(paper) > _count_nans(data):
                        date2qna[date].remove(paper)
            
            date2qna[date].append(data)
            del papers
        else:
            date2qna[date] = [data]

    for date in date2qna:
        year, month, day = date.split("-")
        papers = date2qna[date]
        for paper in papers:
            title2qna[paper["title"]] = paper
            arxivid2data[paper['arxiv_id']] = {"idx": count, "paper": paper}
            date_dict[year][month][day].append(paper)

    titles = [f"[{v['arxiv_id']}] {k}" for k, v in title2qna.items()]

    return titles, date_dict, arxivid2data

def initialize_data(source_data_repo_id, request_data_repo_id):
    global date_dict, arxivid2data
    global requested_arxiv_ids_df

    source_ds = datasets.load_dataset(source_data_repo_id)
    request_ds = datasets.load_dataset(request_data_repo_id)
    
    titles, date_dict, arxivid2data = _initialize_paper_info(source_ds)
    requested_arxiv_ids_df = _initialize_requested_arxiv_ids(request_ds)

    return (
        titles, date_dict, requested_arxiv_ids_df, arxivid2data
    )

def update_dataframe(request_data_repo_id):
    request_ds = datasets.load_dataset(request_data_repo_id)
    return _initialize_requested_arxiv_ids(request_ds)

def initialize_repos(
    source_data_repo_id, request_data_repo_id, hf_token
):
    if create_hf_hub(source_data_repo_id, hf_token) is False:
        print(f"{source_data_repo_id} repository already exists")

    if create_hf_hub(request_data_repo_id, hf_token) is False:
        print(f"{request_data_repo_id} repository already exists")
    else:
        df = pd.DataFrame(data={"Requested arXiv IDs": [["top"]]})
        ds = Dataset.from_df(df)
        ds.push_to_hub(request_data_repo_id, token=hf_token)

def get_secrets():
    global gemini_api_key
    global hf_token
    global request_arxiv_repo_id
    global dataset_repo_id

    gemini_api_key = os.getenv("GEMINI_API_KEY")
    hf_token = os.getenv("HF_TOKEN")
    dataset_repo_id = os.getenv("SOURCE_DATA_REPO_ID") 
    request_arxiv_repo_id = os.getenv("REQUEST_DATA_REPO_ID")
    restart_repo_id = os.getenv("RESTART_TARGET_SPACE_REPO_ID", "chansung/paper_qa")

    return (
        gemini_api_key,
        hf_token,
        dataset_repo_id,
        request_arxiv_repo_id,
        restart_repo_id
    )