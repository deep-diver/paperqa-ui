import gradio as gr

from init import (
    get_secrets, initialize_data, 
    update_dataframe, initialize_repos
)
from gen.openllm import GradioLLaMA2ChatPPManager, GradioMistralChatPPManager
from gen.gemini_chat import GradioGeminiChatPPManager
from constants.js import (
    UPDATE_SEARCH_RESULTS, OPEN_CHAT_IF,
    CLOSE_CHAT_IF, UPDATE_CHAT_HISTORY
)

from datetime import datetime, timedelta
from background import process_arxiv_ids
from apscheduler.schedulers.background import BackgroundScheduler

gemini_api_key, hf_token, dataset_repo_id, request_arxiv_repo_id, restart_repo_id = get_secrets()
initialize_repos(dataset_repo_id, request_arxiv_repo_id, hf_token)

titles, date_dict, requested_arxiv_ids_df, arxivid2data = initialize_data(dataset_repo_id, request_arxiv_repo_id)

from ui import (
    get_paper_by_year, get_paper_by_month, get_paper_by_day,
    set_papers, set_paper, set_date, change_exp_type, add_arxiv_ids_to_queue,
    before_chat_begin, chat_stream, chat_reset
)

sorted_year = sorted(date_dict.keys())
last_year = sorted_year[-1]
sorted_month = sorted(date_dict[last_year].keys())
last_month = sorted_month[-1]
sorted_day = sorted(date_dict[last_year][last_month].keys())
last_day = sorted_day[-1]
last_papers = date_dict[last_year][last_month][last_day]
selected_paper = last_papers[0]
visible = True if len(sorted_year) > 0 else False

with gr.Blocks(css="constants/styles.css", theme=gr.themes.Soft()) as demo:
    cur_arxiv_id = gr.Textbox(selected_paper['arxiv_id'], visible=False)
    local_data = gr.JSON({}, visible=False)
    chat_state = gr.State({
        "ppmanager_type": GradioGeminiChatPPManager # GradioMistralChatPPManager # GradioLLaMA2ChatPPManager
    })

    with gr.Column(elem_id="chatbot-back"):
        with gr.Column(elem_id="chatbot", elem_classes=["hover-opacity"]):
            close = gr.Button("𝕏", elem_id="chatbot-right-button") #elem_id="chatbot-right-button")
            chatbot = gr.Chatbot(
                label="Gemini 1.0 Pro", show_label=True, 
                show_copy_button=True, show_share_button=True, 
                visible=True, elem_id="chatbot-inside"
            )

            with gr.Row(elem_id="chatbot-bottm"):
                reset = gr.Button("🗑️ Reset")
                regen = gr.Button("🔄 Regenerate", visible=False)

            prompt_txtbox = gr.Textbox(placeholder="Ask anything.....", elem_id="chatbot-txtbox", elem_classes=["textbox-no-label"])

    gr.Markdown("# Let's explore papers with auto generated Q&As")
    
    with gr.Column(elem_id="control-panel", elem_classes=["group"], visible=visible):
        with gr.Column():
            with gr.Row():
                year_dd = gr.Dropdown(sorted_year, value=last_year, label="Year", interactive=True, filterable=False)    
                month_dd = gr.Dropdown(sorted_month, value=last_month, label="Month", interactive=True, filterable=False)    
                day_dd = gr.Dropdown(sorted_day, value=last_day, label="Day", interactive=True, filterable=False)
                
            papers_dd = gr.Dropdown(
                list(set([paper["title"] for paper in last_papers])),
                value=selected_paper["title"],
                label="Select paper title", 
                interactive=True,
                filterable=False
            )

        with gr.Column(elem_classes=["no-gap"]):
            search_in = gr.Textbox("", placeholder="Enter keywords to search...", elem_classes=["textbox-no-label"])
            search_r1 = gr.Button(visible=False, elem_id="search_r1", elem_classes=["no-radius"])
            search_r2 = gr.Button(visible=False, elem_id="search_r2", elem_classes=["no-radius"])
            search_r3 = gr.Button(visible=False, elem_id="search_r3", elem_classes=["no-radius"])
            search_r4 = gr.Button(visible=False, elem_id="search_r4", elem_classes=["no-radius"])
            search_r5 = gr.Button(visible=False, elem_id="search_r5", elem_classes=["no-radius"])
            search_r6 = gr.Button(visible=False, elem_id="search_r6", elem_classes=["no-radius"])
            search_r7 = gr.Button(visible=False, elem_id="search_r7", elem_classes=["no-radius"])
            search_r8 = gr.Button(visible=False, elem_id="search_r8", elem_classes=["no-radius"])
            search_r9 = gr.Button(visible=False, elem_id="search_r9", elem_classes=["no-radius"])
            search_r10 = gr.Button(visible=False, elem_id="search_r10", elem_classes=["no-radius"])

    with gr.Column(scale=7, visible=visible):
        title = gr.Markdown(f"# {selected_paper['title']}", elem_classes=["markdown-center"])
        # with gr.Row():
        with gr.Row():
            arxiv_link = gr.Markdown(
                "[![arXiv](https://img.shields.io/badge/arXiv-%s-b31b1b.svg?style=for-the-badge)](https://arxiv.org/abs/%s)" % (selected_paper['arxiv_id'], selected_paper['arxiv_id']) + " "
                "[![Paper page](https://huggingface.co/datasets/huggingface/badges/resolve/main/paper-page-lg.svg)](https://huggingface.co/papers/%s)" % selected_paper['arxiv_id'] + " ",
                elem_id="link-md",
            )
        chat_button = gr.Button("Chat about any custom questions", interactive=True, elem_id="chat-button")
            
        summary = gr.Markdown(f"{selected_paper['summary']}", elem_classes=["small-font"])

        with gr.Column(elem_id="qna_block", visible=True):
            with gr.Row():
                with gr.Column(scale=7):
                    gr.Markdown("## Auto generated Questions & Answers")

                exp_type = gr.Radio(choices=["ELI5", "Technical"], value="ELI5", elem_classes=["exp-type"], scale=3)

            # 1
            with gr.Column(elem_classes=["group"], visible=True) as q_0:
                basic_q_0 = gr.Markdown(f"### 🙋 {selected_paper['0_question']}")
                basic_q_eli5_0 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['0_answers:eli5']}", elem_classes=["small-font"]) 
                basic_q_expert_0 = gr.Markdown(f"↪ **(Technical)** {selected_paper['0_answers:expert']}", visible=False, elem_classes=["small-font"]) 

                with gr.Accordion("Additional question #1", open=False, elem_classes=["accordion"]) as aq_0_0:
                    depth_q_0 = gr.Markdown(f"### 🙋🙋 {selected_paper['0_additional_depth_q:follow up question']}")
                    depth_q_eli5_0 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['0_additional_depth_q:answers:eli5']}", elem_classes=["small-font"])
                    depth_q_expert_0 = gr.Markdown(f"↪ **(Technical)** {selected_paper['0_additional_depth_q:answers:expert']}", visible=False, elem_classes=["small-font"])

                with gr.Accordion("Additional question #2", open=False, elem_classes=["accordion"]) as aq_0_1:
                    breath_q_0 = gr.Markdown(f"### 🙋🙋 {selected_paper['0_additional_breath_q:follow up question']}")
                    breath_q_eli5_0 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['0_additional_breath_q:answers:eli5']}", elem_classes=["small-font"])
                    breath_q_expert_0 = gr.Markdown(f"↪ **(Technical)** {selected_paper['0_additional_breath_q:answers:expert']}", visible=False, elem_classes=["small-font"])

            # 2
            with gr.Column(elem_classes=["group"], visible=True) as q_1:
                basic_q_1 = gr.Markdown(f"### 🙋 {selected_paper['1_question']}")
                basic_q_eli5_1 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['1_answers:eli5']}", elem_classes=["small-font"]) 
                basic_q_expert_1 = gr.Markdown(f"↪ **(Technical)** {selected_paper['1_answers:expert']}", visible=False, elem_classes=["small-font"]) 

                with gr.Accordion("Additional question #1", open=False, elem_classes=["accordion"]) as aq_1_0:
                    depth_q_1 = gr.Markdown(f"### 🙋🙋 {selected_paper['1_additional_depth_q:follow up question']}")
                    depth_q_eli5_1 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['1_additional_depth_q:answers:eli5']}", elem_classes=["small-font"])
                    depth_q_expert_1 = gr.Markdown(f"↪ **(Technical)** {selected_paper['1_additional_depth_q:answers:expert']}", visible=False, elem_classes=["small-font"])

                with gr.Accordion("Additional question #2", open=False, elem_classes=["accordion"]) as aq_1_1:
                    breath_q_1 = gr.Markdown(f"### 🙋🙋 {selected_paper['1_additional_breath_q:follow up question']}")
                    breath_q_eli5_1 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['1_additional_breath_q:answers:eli5']}", elem_classes=["small-font"])
                    breath_q_expert_1 = gr.Markdown(f"↪ **(Technical)** {selected_paper['1_additional_breath_q:answers:expert']}", visible=False, elem_classes=["small-font"])

            # 3
            with gr.Column(elem_classes=["group"], visible=True) as q_2:
                basic_q_2 = gr.Markdown(f"### 🙋 {selected_paper['2_question']}")
                basic_q_eli5_2 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['2_answers:eli5']}", elem_classes=["small-font"]) 
                basic_q_expert_2 = gr.Markdown(f"↪ **(Technical)** {selected_paper['2_answers:expert']}", visible=False, elem_classes=["small-font"]) 

                with gr.Accordion("Additional question #1", open=False, elem_classes=["accordion"]) as aq_2_0:
                    depth_q_2 = gr.Markdown(f"### 🙋🙋 {selected_paper['2_additional_depth_q:follow up question']}")
                    depth_q_eli5_2 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['2_additional_depth_q:answers:eli5']}", elem_classes=["small-font"])
                    depth_q_expert_2 = gr.Markdown(f"↪ **(Technical)** {selected_paper['2_additional_depth_q:answers:expert']}", visible=False, elem_classes=["small-font"])

                with gr.Accordion("Additional question #2", open=False, elem_classes=["accordion"]) as aq_2_1:
                    breath_q_2 = gr.Markdown(f"### 🙋🙋 {selected_paper['2_additional_breath_q:follow up question']}")
                    breath_q_eli5_2 = gr.Markdown(f"↪ **(ELI5)** {selected_paper['2_additional_breath_q:answers:eli5']}", elem_classes=["small-font"])
                    breath_q_expert_2 = gr.Markdown(f"↪ **(Technical)** {selected_paper['2_additional_breath_q:answers:expert']}", visible=False, elem_classes=["small-font"])

    gr.Markdown("## Request any arXiv ids")
    arxiv_queue = gr.Dataframe(
        headers=["Requested arXiv IDs"], col_count=(1, "fixed"),
        value=requested_arxiv_ids_df,
        datatype=["str"],
        interactive=False,
    )

    arxiv_id_enter = gr.Textbox(placeholder="Enter comma separated arXiv IDs...", elem_classes=["textbox-no-label"])
    arxiv_id_enter.submit(
        add_arxiv_ids_to_queue,
        [arxiv_queue, arxiv_id_enter],
        [arxiv_queue, arxiv_id_enter],
        concurrency_limit=20,
    )

    gr.DuplicateButton(value="Duplicate Space for private use", elem_id="duplicate-button")

    gr.Markdown("The target papers are collected from [Hugging Face 🤗 Daily Papers](https://huggingface.co/papers) on a daily basis. "
                "The entire data is generated by [Google's Gemini 1.0](https://deepmind.google/technologies/gemini/) Pro. "
                "If you are curious how it is done, visit the [Auto Paper Q&A Generation project repository](https://github.com/deep-diver/auto-paper-analysis) "
                "Also, the generated dataset is hosted on Hugging Face 🤗 Dataset repository as well([Link](https://huggingface.co/datasets/chansung/auto-paper-qa2)). ")
    
    search_r1.click(set_date, search_r1, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r1],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r2.click(set_date, search_r2, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r2],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r3.click(set_date, search_r3, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r3],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r4.click(set_date, search_r4, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r4],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r5.click(set_date, search_r5, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r5],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r6.click(set_date, search_r6, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r6],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r7.click(set_date, search_r7, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r7],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )    

    search_r8.click(set_date, search_r8, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r8],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r9.click(set_date, search_r9, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r9],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    search_r10.click(set_date, search_r10, [year_dd, month_dd, day_dd]).then(
        set_papers,
        inputs=[year_dd, month_dd, day_dd, search_r10],
        outputs=[cur_arxiv_id, papers_dd, search_in],
        concurrency_limit=20,
    )

    year_dd.input(get_paper_by_year, inputs=[year_dd], outputs=[month_dd, day_dd, papers_dd]).then(
        set_paper, [year_dd, month_dd, day_dd, papers_dd],
        [
            cur_arxiv_id,
            title, arxiv_link, summary,
            basic_q_0, basic_q_eli5_0, basic_q_expert_0,
            depth_q_0, depth_q_eli5_0, depth_q_expert_0,
            breath_q_0, breath_q_eli5_0, breath_q_expert_0,

            basic_q_1, basic_q_eli5_1, basic_q_expert_1,
            depth_q_1, depth_q_eli5_1, depth_q_expert_1,
            breath_q_1, breath_q_eli5_1, breath_q_expert_1,

            basic_q_2, basic_q_eli5_2, basic_q_expert_2,
            depth_q_2, depth_q_eli5_2, depth_q_expert_2,
            breath_q_2, breath_q_eli5_2, breath_q_expert_2
        ],
        concurrency_limit=20,
    )

    month_dd.input(get_paper_by_month, inputs=[year_dd, month_dd], outputs=[day_dd, papers_dd]).then(
        set_paper, [year_dd, month_dd, day_dd, papers_dd],
        [
            cur_arxiv_id,
            title, arxiv_link, summary,
            basic_q_0, basic_q_eli5_0, basic_q_expert_0,
            depth_q_0, depth_q_eli5_0, depth_q_expert_0,
            breath_q_0, breath_q_eli5_0, breath_q_expert_0,

            basic_q_1, basic_q_eli5_1, basic_q_expert_1,
            depth_q_1, depth_q_eli5_1, depth_q_expert_1,
            breath_q_1, breath_q_eli5_1, breath_q_expert_1,

            basic_q_2, basic_q_eli5_2, basic_q_expert_2,
            depth_q_2, depth_q_eli5_2, depth_q_expert_2,
            breath_q_2, breath_q_eli5_2, breath_q_expert_2
        ],
        concurrency_limit=20, 
    )

    day_dd.input(get_paper_by_day, inputs=[year_dd, month_dd, day_dd], outputs=[papers_dd]).then(
        set_paper, [year_dd, month_dd, day_dd, papers_dd],
        [
            cur_arxiv_id,
            title, arxiv_link, summary,
            basic_q_0, basic_q_eli5_0, basic_q_expert_0,
            depth_q_0, depth_q_eli5_0, depth_q_expert_0,
            breath_q_0, breath_q_eli5_0, breath_q_expert_0,

            basic_q_1, basic_q_eli5_1, basic_q_expert_1,
            depth_q_1, depth_q_eli5_1, depth_q_expert_1,
            breath_q_1, breath_q_eli5_1, breath_q_expert_1,

            basic_q_2, basic_q_eli5_2, basic_q_expert_2,
            depth_q_2, depth_q_eli5_2, depth_q_expert_2,
            breath_q_2, breath_q_eli5_2, breath_q_expert_2
        ],
        concurrency_limit=20,
    )

    papers_dd.change(set_paper, [year_dd, month_dd, day_dd, papers_dd],
        [
            cur_arxiv_id,
            title, arxiv_link, summary,
            basic_q_0, basic_q_eli5_0, basic_q_expert_0,
            depth_q_0, depth_q_eli5_0, depth_q_expert_0,
            breath_q_0, breath_q_eli5_0, breath_q_expert_0,

            basic_q_1, basic_q_eli5_1, basic_q_expert_1,
            depth_q_1, depth_q_eli5_1, depth_q_expert_1,
            breath_q_1, breath_q_eli5_1, breath_q_expert_1,

            basic_q_2, basic_q_eli5_2, basic_q_expert_2,
            depth_q_2, depth_q_eli5_2, depth_q_expert_2,
            breath_q_2, breath_q_eli5_2, breath_q_expert_2
        ],
        concurrency_limit=20,
    )

    search_in.change(
        inputs=[search_in],
        outputs=[
            search_r1, search_r2, search_r3, search_r4, search_r5,
            search_r6, search_r7, search_r8, search_r9, search_r10
        ],
        js=UPDATE_SEARCH_RESULTS % str(list(titles)),
        fn=None
    )

    exp_type.select(
        change_exp_type,
        exp_type,
        [
            basic_q_eli5_0, basic_q_expert_0, depth_q_eli5_0, depth_q_expert_0, breath_q_eli5_0, breath_q_expert_0,
            basic_q_eli5_1, basic_q_expert_1, depth_q_eli5_1, depth_q_expert_1, breath_q_eli5_1, breath_q_expert_1,
            basic_q_eli5_2, basic_q_expert_2, depth_q_eli5_2, depth_q_expert_2, breath_q_eli5_2, breath_q_expert_2
        ],
        concurrency_limit=20,
    )
    
    chat_button.click(None, [cur_arxiv_id], [local_data, chatbot], js=OPEN_CHAT_IF)
    close.click(None, None, None,js=CLOSE_CHAT_IF) 

    prompt_txtbox.submit(
        before_chat_begin, None, [close, reset, regen],
        concurrency_limit=20,
    ).then(
        chat_stream, 
        [cur_arxiv_id, local_data, prompt_txtbox, chat_state],
        [prompt_txtbox, chatbot, local_data, close, reset, regen],
        concurrency_limit=20,
    ).then(
        None, [cur_arxiv_id, local_data], None, 
        js=UPDATE_CHAT_HISTORY
    )

    reset.click(
        before_chat_begin, None, [close, reset, regen],
        concurrency_limit=20,
    ).then(
        chat_reset,
        [local_data, chat_state],
        [prompt_txtbox, chatbot, local_data, close, reset, regen],
        concurrency_limit=20,
    ).then(
        None, [cur_arxiv_id, local_data], None, 
        js=UPDATE_CHAT_HISTORY
    )

    demo.load(lambda: update_dataframe(request_arxiv_repo_id), None, arxiv_queue, every=180)
    # demo.load(None, None, [chatbot, local_data], js=GET_LOCAL_STORAGE % idx.value)

start_date = datetime.now() + timedelta(minutes=1)
scheduler = BackgroundScheduler()
scheduler.add_job(
    process_arxiv_ids,
    trigger='interval',
    seconds=3600,
    args=[
        gemini_api_key, 
        dataset_repo_id,
        request_arxiv_repo_id,
        hf_token, 
        restart_repo_id
    ],
    start_date=start_date
)
scheduler.start()

demo.queue(
    default_concurrency_limit=20,
    max_size=256
).launch(
    share=True, debug=True
)