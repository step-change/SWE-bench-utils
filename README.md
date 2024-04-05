# SWE-bench-utils

`SWE-bench-utils` is a collection of utilities designed to help explore SWE-bench and its results, making it easier to analyze and understand software engineering tasks and benchmarks.

## Installation

Before you begin, ensure you have Python 3.6 or higher installed on your system.

1. Clone this repository:

```bash
git clone https://github.com/yourusername/SWE-bench-utils.git
cd SWE-bench-utils
```

2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Description lang_chain.py

lang_chain.py uses langchain to iterate over all of the django tasks in the SWEBench dataset and generate summaries for each of them. The output includes a brief summary of the issue, categorizes it, and lists relevant tags for further categorization:

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

## Usage lang_chain.py

In order to run this script
To run the main script and process documents:

1. Follow install instructions.

2. Ensure the `.env` file has a `OPENAI_API_KEY` and `DATA_FILE_PATH` set.

The `DATA_FILE_PATH` refers to the data associated with the SWE-bench project, which is hosted on Hugging Face. You can access the dataset directly through this [link](https://huggingface.co/datasets/princeton-nlp/SWE-bench_bm25_40K/blob/main/data/test-00000-of-00001-b8fa8348bb47ebf6.parquet).

Download this data and point to it's location with this key.
This data is linked from the main [SWE-bench github](https://github.com/princeton-nlp/SWE-bench).

3. Run the script with:
   ```
   python lang_chain.py
   ```

If you are successful you're output will be saved to a timestamped directory under data. data/<timestamp>/summaries.json
