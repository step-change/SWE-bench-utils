import asyncio
import json
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

CHOSEN_MODEL = "gpt-4"

summarize_problem_template = """
Given the following issues descriptions from the Django repository, perform the following tasks:

1. Provide a brief summary of each issue. For each issue, identify key components related to Django's functionality, such as models, database behavior, or inheritance. If an issue is too complex or requires deep technical understanding,
please flag it for special attention but do not skip it. If you encounter difficulties due to the issue's complexity, explain what makes it complex.
2. Categorize each issue into one of the following: 'Bug', 'Feature Request', 'Documentation', or 'Other'.
3. Identify and list relevant clustering tags that describe the issue's focus area (e.g., 'Database', 'HTML', 'Parsing', 'URL Validation', 'Admin Console', 'Model Validation'). These tags should capture the essence of each issue succinctly and be useful for categorizing these issues into specific focus areas or components of Django.

Please return the response in JSON format for easy parsing.

Issues:
{issues}

It is crucial that the response for each issue is returned as a separate JSON object within an array to ensure accurate parsing and analysis. Each JSON object must include the fields "summary", "category", and "tags".

Please format your response as a JSON array where each element is a JSON object adhering to the example format provided below:

[{{ # Note the doubled curly braces to escape them
"instance_id": "Unique identifier for the issue.",
"summary": "Brief summary of the issue.",
"category": "Category of the issue ('Bug', 'Feature Request', 'Documentation', or 'Other')",
"error": "Unable to provide a summary due to insufficient information or too complex."
"tags": ["List", "Of", "Relevant", "Tags"]
}}] # Note the doubled curly braces to escape them

For example, if the issue is related to a misleading error message in sqlmigrate without proper validation, the response should be an array of JSON objects with the format
  "instance_id": "django__django-666",
  "summary": "The issue reports a misleading error message in sqlmigrate due to lack of validation for migration existence.",
  "category": "Bug",
  "tags": ["Database", "Migration", "Error Handling"]

  If you run into a problem and can not provide a summary for a specific issue, please return an empty string for the "summary" field and provide an explanation for why in the "error" field.
  "instance_id": "django__django-666",
  "summary": "",
  "category": "",
  "tags": [""],
  "error": "Unable to provide a summary due to insufficient information or too complex."

  Even if you encounter difficulties, do not skip any issues. Instead, provide as much information as possible and explain the challenges encountered in summary and error fields.
"""


async def process_documents_in_batches(documents, batch_size):
    """
    Processes documents in batches asynchronously.

    This function sends batches of documents to a language model for processing. It uses a semaphore to limit
    the number of concurrent tasks, ensuring that the processing does not overload system resources. The function
    aggregates the responses from all batches for further analysis.

    Args:
        documents (list): A list of documents to be processed.
        batch_size (int): The number of documents to process in each batch.

    Returns:
        list: A list of aggregated responses from processing all documents.
    """

    # Initialize the language model chain with the chosen model and zero temperature for deterministic outputs.
    llm = ChatOpenAI(model=CHOSEN_MODEL, temperature=0)
    prompt = PromptTemplate.from_template(summarize_problem_template)
    chain = LLMChain(llm=llm, prompt=prompt)
    stuff_chain = StuffDocumentsChain(llm_chain=chain, document_variable_name="issues")

    # Create a semaphore to limit concurrency to three tasks at a time.
    sem = asyncio.Semaphore(3)
    aggregated_responses = []  # Placeholder for storing the aggregated responses.

    async def process_batch(batch, batch_number=0):
        """
        Processes a single batch of documents asynchronously.

        This inner function is responsible for sending a batch of documents to the language model chain for processing.
        It parses the JSON responses, cleans them up, and aggregates them for the final output.

        Args:
            batch (list): A list of documents in the current batch.
            batch_number (int): The batch number (for logging purposes).
        """
        async with sem:  # Control concurrency with the semaphore.
            print(
                f"Processing batch of {len(batch)} documents in batch {batch_number}..."
            )
            response = await stuff_chain.arun(batch)

            # Attempt to parse the JSON response and clean it up.
            try:
                parsed_response = json.loads(response.strip("```json\n"))
                print(
                    f"Batch {batch_number}: Parsed response count before cleaning: {len(parsed_response)}"
                )
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON in batch {batch_number}: {e}")
                print("Raw response:", response)
                return  # Skip further processing for this batch on parse error.

            # Filter out valid JSON objects.
            cleaned_response = [
                item for item in parsed_response if isinstance(item, dict)
            ]
            print(
                f"Batch {batch_number}: Cleaned response count after cleaning: {len(cleaned_response)}"
            )

            # Check for mismatch in document batch count and cleaned response count.
            if len(batch) != len(cleaned_response):
                print(
                    f"Warning: Mismatch in document batch count and cleaned response count in batch {batch_number}."
                )

            aggregated_responses.extend(
                cleaned_response
            )  # Aggregate cleaned responses.

    # Assemble tasks for each batch and process them concurrently.
    tasks = []
    for i in range(0, len(documents), batch_size):
        tasks.append(process_batch(documents[i : i + batch_size], i // batch_size))

    await asyncio.gather(*tasks)
    return aggregated_responses
