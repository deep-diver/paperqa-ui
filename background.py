import datasets
import pandas as pd
from huggingface_hub import HfApi

from utils import push_to_hf_hub
from paper.download import download_pdf_from_arxiv
from paper.download import get_papers_from_arxiv_ids
from paper.parser import extract_text_and_figures
from gen.gemini import get_basic_qa, get_deep_qa

def _filter_function(example, ids):
    ids_e = example['Requested arXiv IDs']
    for iid in ids:
        if iid in ids_e:
            ids_e.remove(iid)
            example['Requested arXiv IDs'] = ids_e

    print(example)
    return example

def process_arxiv_ids(gemini_api, hf_repo_id, req_hf_repo_id, hf_token, restart_repo_id, how_many=10):
    arxiv_ids = []

    ds1 = datasets.load_dataset(req_hf_repo_id)
    for d in ds1['train']:
        req_arxiv_ids = d['Requested arXiv IDs']
        if len(req_arxiv_ids) > 0 and req_arxiv_ids[0] != "top":
            arxiv_ids = arxiv_ids + req_arxiv_ids

    arxiv_ids = arxiv_ids[:how_many]

    if arxiv_ids is not None and len(arxiv_ids) > 0:
        print(f"1. Get metadata for the papers [{arxiv_ids}]")
        papers = get_papers_from_arxiv_ids(arxiv_ids)
        print("...DONE")
        
        print("2. Generating QAs for the paper")
        for paper in papers:
            try:
                title = paper['title']
                target_date = paper['target_date']
                abstract = paper['paper']['summary']
                arxiv_id = paper['paper']['id']
                authors = paper['paper']['authors']

                print(f"...PROCESSING ON[{arxiv_id}, {title}]")
                print(f"......Downloading the paper PDF")
                filename = download_pdf_from_arxiv(arxiv_id)
                print(f"......DONE")

                print(f"......Extracting text and figures")
                texts, figures = extract_text_and_figures(filename)
                text =' '.join(texts)
                print(f"......DONE")

                print(f"......Generating the seed(basic) QAs")
                qnas = get_basic_qa(text, gemini_api_key=gemini_api, trucate=30000)
                qnas['title'] = title
                qnas['abstract'] = abstract
                qnas['authors'] = ','.join(authors)
                qnas['arxiv_id'] = arxiv_id
                qnas['target_date'] = target_date
                qnas['full_text'] = text
                print(f"......DONE")

                print(f"......Generating the follow-up QAs")
                qnas = get_deep_qa(text, qnas, gemini_api_key=gemini_api, trucate=30000)
                del qnas["qna"]
                print(f"......DONE")

                print(f"......Exporting to HF Dataset repo at [{hf_repo_id}]")
                df = pd.DataFrame([qnas])
                ds = datasets.Dataset.from_pandas(df)
                ds = ds.cast_column("target_date", datasets.features.Value("timestamp[s]"))                
                push_to_hf_hub(ds, hf_repo_id, hf_token)
                print(f"......DONE")

                print(f"......Updating request arXiv HF Dataset repo at [{req_hf_repo_id}]")
                ds1 = ds1['train'].map(
                    lambda example: _filter_function(example, [arxiv_id])
                ).filter(
                    lambda example: len(example['Requested arXiv IDs']) > 0
                )
                ds1.push_to_hub(req_hf_repo_id, token=hf_token)
                            
                print(f"......DONE")
            except Exception as e:
                print(f".......failed due to exception {e}")
                continue

        HfApi(token=hf_token).restart_space(
            repo_id=restart_repo_id, token=hf_token
        )