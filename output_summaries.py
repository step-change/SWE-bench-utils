import json
from collections import Counter, defaultdict
import typer

import json
import pandas as pd
import os
from dotenv import load_dotenv
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

app = typer.Typer()

load_dotenv()
DATA_FILE_PATH = os.getenv("DATA_FILE_PATH")


def get_earliest_and_latest_dates(df, summaries):
    """
    Find the earliest and latest dates among a list of summaries.

    Parameters:
        df (pd.DataFrame): DataFrame containing the dataset.
        summaries (list): A list of summary objects.

    Returns:
        tuple: A tuple containing the earliest and latest dates
    """
    dates = []
    for summary in summaries:
        instance_id = summary.get("instance_id")
        date = find_django_date_by_instance_id(df, instance_id)
        if date:
            dates.append(date)

    if dates:
        earliest_date = min(dates)
        latest_date = max(dates)
        return earliest_date, latest_date
    else:
        return None, None


def find_django_date_by_instance_id(df, instance_id):
    """
    Finds the creation date of a Django issue given its instance ID.

    Parameters:
        df (pd.DataFrame): DataFrame containing the dataset.
        instance_id (str): The unique identifier for the issue.

    Returns:
        str: The creation date of the issue, if found; otherwise, None.
    """
    entry = df[df["instance_id"] == instance_id]

    if not entry.empty:
        # Extracting the 'created_at' date for the entry
        created_at_date = entry.iloc[0]["created_at"]
        return created_at_date
    else:
        return None


# Function to create and save pie chart from category counts
def create_pie_chart(category_counts, title, label_threshold, output_filename):
    """
    Creates a pie chart from category counts.

    Parameters:
        category_counts (Counter): A counter object with category counts.
        title (str): The title of the pie chart.
        label_threshold (int): The threshold for displaying labels.
        output_filename (str): Path to save the pie chart image.
    """
    labels = [
        label if count >= label_threshold else ""
        for label, count in category_counts.items()
    ]
    sizes = list(category_counts.values())

    # Define your colors here, one for each category
    colors = [
        "#ff9999",
        "#66b3ff",
        "#99ff99",
        "#ffcc99",
        "#c2c2f0",
        "#ffb3e6",
        "#c4e17f",
        "#76d7c4",
        "#fffcc4",
        "#ffeb3b",
    ]

    # Ensure that there are enough colors to match the categories
    if len(colors) < len(category_counts):
        print(
            f"Not enough colors provided. Only {len(colors)} colors provided for {len(category_counts)} categories."
        )
        return

    fig, ax = plt.subplots()
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        colors=colors[
            : len(category_counts)
        ],  # Slice the colors list to match the number of categories
    )

    for autotext in autotexts:
        if autotext.get_text() == "0.0%":
            autotext.set_visible(False)

    ax.axis("equal")  # Equal aspect ratio ensures that pie is drawn as a circle.
    plt.title(title)
    plt.tight_layout()

    # Save the figure
    plt.savefig(output_filename)
    # plt.show()


def print_summaries(summaries):
    """
    Prints summaries categorized by their category type.

    Parameters:
        summaries (list): A list of summary objects.
    """
    # Organize summaries by category
    summaries_by_category = defaultdict(list)
    for summary in summaries:
        category = summary.get("category", "No Category")
        summaries_by_category[category].append(summary)

    # Iterate through each category and print the summaries
    for category, summaries in summaries_by_category.items():
        print(f"{category}:")
        for summary in summaries:
            instance_id = summary.get("instance_id", "No ID")
            summary_text = summary.get("summary", "No Summary")
            tags = ", ".join(summary.get("tags", []))

            print(f"  - Instance ID: {instance_id}")
            print(f"    Summary: {summary_text}")
            print(f"    Tags: {tags}\n")


def find_matches_in_summaries(summaries, django_fail, django_pass):
    """
    Finds summaries that match given Django fail and pass identifiers.

    Parameters:
        summaries (list): A list of summary objects.
        django_fail (list): Identifiers for failed Django tasks.
        django_pass (list): Identifiers for passed Django tasks.

    Returns:
        tuple: Two lists of matched fail and pass summaries.
    """
    # Initialize dictionaries to hold matching summaries
    fail_summaries = []
    pass_summaries = []

    # Mapping for easy ID lookup
    summaries_dict = {summary["instance_id"]: summary for summary in summaries}

    # Search for fail matches
    for fail_id in django_fail:
        if fail_id in summaries_dict:
            fail_summaries.append(summaries_dict[fail_id])

    # Search for pass matches
    for pass_id in django_pass:
        if pass_id in summaries_dict:
            pass_summaries.append(summaries_dict[pass_id])

    return fail_summaries, pass_summaries


def load_and_filter_devin_results(file_path):
    """
    Loads and filters Devin result file names for Django-related entries.

    Parameters:
        file_path (str): Path to the Devin results JSON file.

    Returns:
        tuple: Two sorted lists containing Django fail and pass file names.
    """
    # Load the JSON data from the specified file
    with open(file_path, "r") as f:
        data = json.load(f)

    fail_total = len(data["fail"])
    pass_total = len(data["pass"])

    # Filter and sort django filenames in fail and pass categories
    django_fail = sorted(
        [filename for filename in data["fail"] if "django" in filename]
    )
    django_pass = sorted(
        [filename for filename in data["pass"] if "django" in filename]
    )

    django_fail_count = len(django_fail)
    django_pass_count = len(django_pass)
    # Print the total counts and the django filenames
    print(f"Total Fail:  {fail_total}")
    print(f"Total Pass: {pass_total}")
    print(f"Django Fail Count: {django_fail_count}")
    print(f"Django Pass Count: {django_pass_count}")
    print("\nDjango Fail:")

    return django_fail, django_pass


def load_summaries(file_path: str):
    """
    Loads summaries from a specified JSON file.

    Parameters:
        file_path (str): The file path of the JSON file containing summaries.

    Returns:
        list: A list of summaries.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


@app.command()
def print_issues_by_tag(
    file_path: str = typer.Option(...),
    tag: str = typer.Option(...),
    filter_category: str = typer.Option(
        None, "--filter-category", help="Filter issues by category"
    ),
):
    """
    Prints issues matching a specific tag and optionally filters by category.

    Parameters:
        file_path (str): Path to the JSON file containing issues summaries.
        tag (str): The tag to filter issues by.
        filter_category (str, optional): Category to further filter issues by.
    """
    summaries = load_summaries(file_path)
    issues_with_tag = [
        summary for summary in summaries if tag in summary.get("tags", [])
    ]

    if issues_with_tag:
        # Group by category and count the number of issues per category
        category_counts = Counter(
            issue.get("category", "None") for issue in issues_with_tag
        )

        print(f"Issues with tag '{tag}':")
        # Print category counts
        for category, count in category_counts.items():
            print(f"{category}: {count}")
        print()

        # Filter by category if the filter is specified
        if filter_category:
            issues_with_tag = [
                issue
                for issue in issues_with_tag
                if issue.get("category") == filter_category
            ]

        # Now print the individual issues
        for issue in issues_with_tag:
            print(f"- Summary: {issue.get('summary')}")
            print(f"  Category: {issue.get('category')}")
            print(f"  Tags: {', '.join(issue.get('tags', []))}\n")
    else:
        print(f"No issues found with tag '{tag}'.")


def print_top_terms(vectorizer, kmeans, top_n=10):
    """
    Prints the top terms per cluster for KMeans clustering results.

    Parameters:
        vectorizer (CountVectorizer): The vectorizer used for text data.
        kmeans (KMeans): The KMeans clustering object.
        top_n (int): Number of top terms to print per cluster.
    """
    order_centroids = kmeans.cluster_centers_.argsort()[:, ::-1]
    terms = vectorizer.get_feature_names_out()
    cluster_terms = []

    for i in range(kmeans.n_clusters):
        top_terms = [terms[ind] for ind in order_centroids[i, :top_n]]
        cluster_terms.append(
            f"Cluster {i} Top Terms: " + ", ".join(f'"{term}"' for term in top_terms)
        )
    return cluster_terms


@app.command()
def cluster_issues_by_tag(
    file_path: str = typer.Option(...), tag: str = typer.Option(...)
):
    """
    Clusters issues based on their tags and saves the cluster visualization as a png.

    Parameters:
        file_path (str): Path to the JSON file containing issues summaries.
        tag (str): The tag to cluster issues by.
    """
    summaries = load_summaries(file_path)
    issues_with_tag = [
        summary for summary in summaries if tag in summary.get("tags", [])
    ]
    print("Entering cluster_issues_by_tag")

    if issues_with_tag:
        print(f"Clustering with tag '{tag}':")
        df = pd.DataFrame(issues_with_tag)
        df["tags_combined"] = df["tags"].apply(lambda x: ", ".join(x))
        vectorizer = CountVectorizer()
        X = vectorizer.fit_transform(df["tags_combined"])

        try:
            kmeans = KMeans(n_clusters=min(5, len(df)), random_state=0).fit(X)
            df["cluster"] = kmeans.labels_
            cluster_terms = print_top_terms(vectorizer, kmeans)
        except ValueError as e:
            print(f"Error during clustering: {e}")
            return

        cluster_counts = df["cluster"].value_counts().sort_index()
        plt.figure(figsize=(12, 8))
        cluster_counts.plot(kind="bar")
        plt.title("Number of Issues per Cluster")
        plt.xlabel("Cluster")
        plt.ylabel("Number of Issues")
        plt.xticks(
            range(kmeans.n_clusters), [f"Cluster {i}" for i in range(kmeans.n_clusters)]
        )

        table_data = [[term] for term in cluster_terms]
        the_table = plt.table(
            cellText=table_data,
            colLabels=["Cluster Top Terms"],
            loc="bottom",
            cellLoc="left",
            bbox=[0.0, -0.8, 1.0, 0.6],
        )

        plt.subplots_adjust(left=0.2, bottom=0.2)

        for key, cell in the_table.get_celld().items():
            cell.set_fontsize(14)
            cell.set_height(0.2)

        output_filename = f"{tag}_cluster.png"
        plt.savefig(output_filename, bbox_inches="tight")
        print(f"Cluster plot saved as {output_filename}")
    else:
        print(f"No issues found with tag '{tag}'.")


def tabulate_summaries(summaries):
    """Tabulates categories and tags from summaries, explicitly excluding summaries that are marked as errors.

    Args:
        summaries (list of dict): A list of summary dictionaries.

    Returns:
        tuple: A tuple containing category counts, tag counts, and error summaries.
    """
    category_counts = Counter()
    tag_counts = Counter()
    error_summaries = []

    for summary in summaries:
        # Determine if the summary is considered an error
        if summary.get("summary") == "" and summary.get("error"):
            error_summaries.append(summary)
        else:
            # Update category counts, avoiding empty categories
            if summary["category"]:
                category_counts[summary["category"]] += 1
            # Update tag counts, skipping empty tags
            for tag in summary["tags"]:
                if tag:  # Skip empty tags
                    tag_counts[tag] += 1

    return category_counts, tag_counts, error_summaries


@app.command()
def analyze_devin_info(
    file_path: str = typer.Option(...),
    n: int = typer.Option(10, help="Number of top categories and tags to display"),
):
    """
    Analyzes Devin's information, displaying top categories and tags.

    Parameters:
        file_path (str): Path to the JSON file containing issues summaries.
        n (int): Number of top categories and tags to display.
    """
    # Assuming the JSON file is named 'devin-results.json' and located in the current directory
    django_fail, django_pass = load_and_filter_devin_results("devin-results.json")
    # print("django_pass results: {django_pass}")
    # Now we need to search the summaries for these django issues and print information about them.

    # """Prints the top N categories and tags."""
    summaries = load_summaries(file_path)
    fail_summaries, pass_summaries = find_matches_in_summaries(
        summaries, django_fail, django_pass
    )
    fail_category_counts, fail_tag_counts, _ = tabulate_summaries(fail_summaries)
    pass_category_counts, pass_tag_counts, _ = tabulate_summaries(pass_summaries)

    # Un comment the following lines to create pie charts
    # create_pie_chart(
    #     pass_category_counts,
    #     "Django Task Pass Categories",
    #     4,
    #     "devin_pass_pie_chart.png",
    # )
    # create_pie_chart(
    #     fail_category_counts,
    #     "Django Task Fail Categories",
    #     4,
    #     "devin_fail_pie_chart.png",
    # )

    print(f"Fail Summaries Analysis:")
    print(f"Categories:")
    for category, count in fail_category_counts.most_common(n):
        print(f"{category}: {count}")

    print(f"\nTop {n} Tags:")
    for tag, count in fail_tag_counts.most_common(n):
        print(f"{tag}: {count}")

    print_summaries(fail_summaries)

    # parquet file can be found on the SWEBench hugging face dataset page
    # https://huggingface.co/datasets/princeton-nlp/SWE-bench
    df = pd.read_parquet(DATA_FILE_PATH)

    earliest_date, latest_date = get_earliest_and_latest_dates(df, pass_summaries)
    print(f"Django pass summaries date range")
    if earliest_date and latest_date:
        print(f"Earliest date: {earliest_date}")
        print(f"Latest date: {latest_date}")
    else:
        print("No dates found.")

    earliest_date, latest_date = get_earliest_and_latest_dates(df, fail_summaries)
    print(f"Django fail summaries date range")
    if earliest_date and latest_date:
        print(f"Earliest date: {earliest_date}")
        print(f"Latest date: {latest_date}")
    else:
        print("No dates found.")

    print("")
    print(f"Pass Summaries Analysis:")
    print(f"Categories:")
    for category, count in pass_category_counts.most_common(n):
        print(f"{category}: {count}")

    print(f"\nTop {n} Tags:")
    for tag, count in pass_tag_counts.most_common(n):
        print(f"{tag}: {count}")

    # print_summaries(pass_summaries)


@app.command()
def print_top(
    file_path: str = typer.Option(...),
    n: int = typer.Option(10, help="Number of top categories and tags to display"),
):
    """
    Prints the top categories and tags from summaries.

    Parameters:
        file_path (str): Path to the JSON file containing issues summaries.
        n (int): Number of top categories and tags to display.
    """
    summaries = load_summaries(file_path)
    category_counts, tag_counts, _ = tabulate_summaries(summaries)

    print(f"Categories:")
    for category, count in category_counts.most_common(n):
        print(f"{category}: {count}")

    print(f"\nTop {n} Tags:")
    for tag, count in tag_counts.most_common(n):
        print(f"{tag}: {count}")

    # TODO: Create a cli variable to specify the DATA_FILE_PATH file path
    # parquet file can be found on the SWEBench hugging face dataset page
    # https://huggingface.co/datasets/princeton-nlp/SWE-bench
    DATA_FILE_PATH = "./test-00000-of-00001-dc7762b94638c186.parquet"
    df = pd.read_parquet(DATA_FILE_PATH)

    earliest_date, latest_date = get_earliest_and_latest_dates(df, summaries)
    if earliest_date and latest_date:
        print(f"Earliest date: {earliest_date}")
        print(f"Latest date: {latest_date}")
    else:
        print("No dates found.")


@app.command()
def piechart_top_categories(
    file_path: str = typer.Option(...),
    n: int = typer.Option(10, help="Number of top categories and tags to display"),
):
    """
    Generates a pie chart for top categories in the summaries.

    Parameters:
        file_path (str): Path to the JSON file containing issues summaries.
        n (int): Number of top categories to include in the pie chart.
    """

    summaries = load_summaries(file_path)
    category_counts, tag_counts, _ = tabulate_summaries(summaries)

    print(f"Categories:")
    for category, count in category_counts.most_common(n):
        print(f"{category}: {count}")
    create_pie_chart(category_counts, "Django Task Categories", 4, "pie_chart.png")


@app.command()
def print_tag_count(file_path: str = typer.Option(...), tag: str = typer.Option(...)):
    """Prints count of issues with the specified tag."""
    summaries = load_summaries(file_path)
    _, tag_counts, _ = tabulate_summaries(summaries)

    if tag in tag_counts:
        print(f"Count of issues with tag '{tag}': {tag_counts[tag]}")
    else:
        print(f"No issues found with tag '{tag}'.")


@app.command()
def print_errors(file_path: str = typer.Option(...)):
    """Prints summaries that contain errors."""
    summaries = load_summaries(file_path)
    _, _, error_summaries = tabulate_summaries(summaries)

    if error_summaries:
        print("Summaries with Errors:")
        for summary in error_summaries:
            instance_id = summary.get("instance_id", "N/A")
            error = summary.get("error", "Error detail not provided.")
            print(f"Instance ID: {instance_id}, Error: {error}")
    else:
        print("No summaries with errors found.")


if __name__ == "__main__":
    app()
