# SWE-bench-utils

`SWE-bench-utils` is a collection of utilities designed to help explore SWE-bench and its results, making it easier to analyze and understand software engineering tasks and benchmarks.

## Description summarize_tasks.py

summarize_tasks.py uses langchain to iterate over all of the django tasks in the SWEBench dataset and generate summaries for each of them. The output includes a brief summary of the issue, categorizes it, and lists relevant tags for further categorization:

```json
{
  "instance_id": "django__django-10680",
  "summary": "The issue proposes refactoring AutoField logic into a mixin to inherit system checks and validation checks from IntegerField and BigIntegerField. This could potentially make it easier to define new types of auto fields based on other fields in the future.",
  "category": "Feature Request",
  "tags": [
    "Refactoring",
    "AutoField",
    "IntegerField",
    "BigIntegerField",
    "Validation",
    "System Checks"
  ],
  "error": ""
}
```

If you want to save yourself some OpenAI credits the output of running this is saved in example_output/summaries.json

If you want to summarize all tasks, just remove the Django filter in the code.

## Description output_summaries.py

output_summaries.py is a set of utilities that allow you to query and explore the output of summarize_tasks, which should be saved in data/<timestamp>/summaries.json afer running summarize_tasks.py. Alternatively you can just run this command against example_output/summaries.json

Features include:

1. Filter and query by category or tag.
2. Generate pie charts and cluster charts based on different criteria
3. Print general information.

## Description example_output/devin-results.json

File derived from the results of devin the ai software engineer, published [here](https://github.com/CognitionAI/devin-swebench-results). The report contains a directory with the output diffs of those tasks that devin passed/failed at. Each task is mapped back to a task name which you can
use to map to a summary or the data stored in the original data frame.

## Installation

Before you begin, ensure you have Python 3.6 or higher installed on your system.

1. Clone this repository:

```bash
git clone https://github.com/yourusername/SWE-bench-utils.git
cd SWE-bench-utils
```

2. Creating a Virtual Environment (Optional but Recommended):

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

3. Environmental Setup:

```bash
pip install -r requirements.txt
```

2. Ensure the `.env` file has a `OPENAI_API_KEY` and `DATA_FILE_PATH` set.

The `DATA_FILE_PATH` refers to the data associated with the SWE-bench project, which is hosted on Hugging Face. You can access the dataset directly through this [link](https://huggingface.co/datasets/princeton-nlp/SWE-bench_bm25_40K/blob/main/data/test-00000-of-00001-b8fa8348bb47ebf6.parquet).

Download this data and specify the path you saved SWE-bench dataset to `DATA_FILE_PATH` in `.env`.
This data is linked from the main [SWE-bench github](https://github.com/princeton-nlp/SWE-bench).

It should look something like `DATA_FILE_PATH = "./SWE-bench_Lite_bm25_13K/data/test-00000-of-00001.parquet"`

## Usage summarize_tasks.py

In order to run this script
To run the main script and process documents:

1. Follow install instructions.

2. Run the script with:
   ```
   python summarize_tasks.py
   ```

If you are successful you're output will be saved to a timestamped directory under data. data/<timestamp>/summaries.json

## Usage summarize_tasks.py

In order to run this script
To run the main script and process documents:

1. Follow install instructions.
2. Either use the output in example_output or generate your own json file by running summarize_tasks
3. Example: Analyzing Issue Summaries by Tag:
   `python output_summaries.py print-issues-by-tag --file-path data/2024-04-05_15-08-56/summaries.json --tag Database`
4. Example: Clustering Issues by Tag:
   `python output_summaries.py cluster-issues-by-tag --file-path data/2024-04-05_15-08-56/summaries.json --tag Models`
5. Example: Generating a Pie Chart for Top Categories:
   `python output_summaries.py piechart-top-categories --file-path data/2024-04-05_15-08-56/summaries.json`
