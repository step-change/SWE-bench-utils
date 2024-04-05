import pandas as pd
import json
import os
from dotenv import load_dotenv
from collections import defaultdict
import asyncio
from langchain.schema import Document

from utils import create_timestamped_directory
from lang_chain import process_documents_in_batches

load_dotenv()
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH")

# Create a timestamped directory to store the output from this run
base_dir = create_timestamped_directory()


async def main():
    # Load the django SWEBench data from the parquet file
    df = pd.read_parquet(DATA_FILE_PATH)
    # Filter the DataFrame for entries from the Django repo, alter this to summaiize other repositories
    django_entries = df[df["repo"].str.contains("Django", case=False)]

    if not django_entries.empty:
        # Array for langchain documents which will be sent to the LLM via stuff chain
        documents = []
        # Raw output files for the problem statements
        text_output_file = os.path.join(base_dir, "output.txt")
        # JSON output file we can use to look up output via instance_id
        json_output_file = os.path.join(base_dir, "output.json")
        # Initialize a dictionary to store JSON data
        json_data = defaultdict(dict)
        with open(text_output_file, "w") as output_file:
            for index, row in django_entries.iterrows():
                instance_id = row["instance_id"]
                problem_statement = row["problem_statement"]
                # Preprocess the problem_statement to include the instance_id at the top
                id_problem_statement = (
                    f"instance_id: {instance_id}\n\n{problem_statement}"
                )
                document = Document(page_content=id_problem_statement, metadata={})
                documents.append(document)
                # Create formatted string
                output_string = f"Instance_id: {instance_id}\nproblem_statement: {problem_statement}\n\n"

                # Write to file
                output_file.write(output_string)
                # Add data to JSON dictionary
                json_data[instance_id] = {
                    "instance_id": instance_id,
                    "problem_statement": problem_statement,
                }

        doc_count = len(documents)
        print("Documents:" + str(doc_count) + " prepared and written to 'output.txt'")
        # Write JSON data to file
        with open(json_output_file, "w") as json_file:
            json.dump(json_data, json_file, indent=4)

        batch_size = 6
        all_summaries = await process_documents_in_batches(documents, batch_size)

        # # Print the count of summaries
        print("Total summaries:", len(all_summaries))
        print("First summary:", all_summaries[0])
        summaries_json_output_file = os.path.join(base_dir, "summaries.json")
        # # Write summaries to JSON file
        with open(summaries_json_output_file, "w") as json_file:
            json.dump(all_summaries, json_file, indent=4)

        # Confirm completion and provide the file path
        print("Summaries saved to './summaries.json'")
    else:
        print("No entries from the Django repository were found.")


# Running the coroutine with asyncio's event loop
if __name__ == "__main__":
    asyncio.run(main())
