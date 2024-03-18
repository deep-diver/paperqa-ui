import datasets
import pandas as pd

from huggingface_hub import create_repo
from huggingface_hub.utils import HfHubHTTPError

def create_hf_hub(
    repo_id, hf_token
):
    try:
        create_repo(repo_id, repo_type="dataset", token=hf_token)
    except HfHubHTTPError as e:
        return False

    return True

def push_to_hf_hub(
	ds, repo_id, hf_token, append=True
):
    exist = False

    try:
        create_repo(repo_id, repo_type="dataset", token=hf_token)
    except HfHubHTTPError as e:
        exist = True
    
    if exist and append:
        existing_ds = datasets.load_dataset(repo_id)
        ds = datasets.concatenate_datasets([existing_ds['train'], ds])

    ds.push_to_hub(repo_id, token=hf_token)
