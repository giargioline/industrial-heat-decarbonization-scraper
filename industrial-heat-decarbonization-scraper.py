# -*- coding: utf-8 -*-
decarbonization_scraper.py
=================================================

This script scrapes "case studies" (i.e., projects) from the ISPT website
(Heat theme), cleans and classifies them, then generates NLP-based summaries
for relevant ones using a Hugging Face summarization pipeline.

STEPS:
1) Scraping:
   - We retrieve projects from: https://ispt.eu/projects/?theme-tag=heat
   - For each project, we follow its link to get the full detail page.

2) Data Cleaning:
   - Remove "mint background" blocks (class contains "has-mint-background-color").
   - Remove <figcaption> tags.
   - Remove everything after the heading "You might also be interested in".

3) Classification:
   - Classify each project as Relevant or Irrelevant based on a set of keywords.

4) Summarization:
   - Use Hugging Face transformers to produce a concise summary for the relevant projects.

REQUIREMENTS:
- requests
- beautifulsoup4
- transformers
- torch

USAGE:
    python decarbonization_scraper.py
"""

import requests
from bs4 import BeautifulSoup
from transformers import pipeline

# ------------------------------------------------------------
# GLOBAL: Initialize the summarization pipeline (BART Large CNN)
# This may take some time/memory if the model is large.
# ------------------------------------------------------------
summarizer = pipeline("summarization", model="facebook/bart-large-cnn")


def scrape_ispt_heat_projects(url):
    """
    Scrapes the ISPT 'heat' page to get basic project info:
    title, link, and the 'cleaned' description from the detail page.

    Parameters
    ----------
    url : str
        The main listing page URL for Heat-themed projects.

    Returns
    -------
    projects_data : list of dict
        List of project dictionaries, each with:
            'title'       - str
            'description' - str
            'link'        - str
    """
    # Add a standard User-Agent so the request isn't blocked.
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise Exception(f"Failed to retrieve data from {url}. Status code: {response.status_code}")

    # Parse the HTML
    soup = BeautifulSoup(response.text, "html.parser")

    # Each project is in an <article> tag with these classes
    project_cards = soup.select("article.post-block.project")

    projects_data = []
    for card in project_cards:
        # Extract the title
        title_tag = card.find("h2", class_="entry-title")
        title_text = title_tag.get_text(strip=True) if title_tag else "No title"

        # Extract the link (so we can scrape deeper)
        link_tag = card.find("a", class_="post-block-wrapper")
        link_href = link_tag.get("href") if link_tag else None

        # For each project, fetch the FULL description from the detail page.
        if link_href:
            full_desc = fetch_full_description(link_href)
        else:
            full_desc = "No description"

        projects_data.append({
            "title": title_text,
            "description": full_desc,
            "link": link_href
        })

    return projects_data


def fetch_full_description(detail_url):
    """
    Accesses a project's detail page to get a cleaned, final description.

    CLEANING STEPS:
    1) Remove any <div> with "has-mint-background-color" in its class.
    2) Remove all <figcaption> tags.
    3) Remove everything after "You might also be interested in".

    Parameters
    ----------
    detail_url : str
        The link to the project's detail page.

    Returns
    -------
    str
        The cleaned text content of the project, or an error message.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(detail_url, headers=headers)
    if resp.status_code != 200:
        return "Could not retrieve detail page"

    soup = BeautifulSoup(resp.text, "html.parser")

    # The main content is in a <div class="entry-content">
    content_div = soup.find("div", class_="entry-content")
    if not content_div:
        return "No detailed description found"

    # (1) Remove blocks with "has-mint-background-color"
    mint_blocks = content_div.find_all(
        "div",
        class_=lambda c: c and "has-mint-background-color" in c
    )
    for block in mint_blocks:
        block.decompose()

    # (2) Remove all <figcaption> tags
    captions = content_div.find_all("figcaption")
    for cap in captions:
        cap.decompose()

    # (3) Remove everything after "You might also be interested in"
    heading = content_div.find(
        "h2",
        string=lambda text: text and "You might also be interested in" in text
    )
    if heading:
        # Remove all siblings that appear after this heading
        for sibling in heading.find_all_next():
            sibling.decompose()
        # Remove the heading itself
        heading.decompose()

    # Get the final text (stripped of extra whitespace)
    full_text = content_div.get_text(strip=True)
    return full_text


def classify_projects(projects, relevant_keywords):
    """
    Classifies each project as Relevant or Irrelevant based on whether
    its combined text (title + description) contains any of the keywords.

    Parameters
    ----------
    projects : list of dict
        The list of project data with 'title' and 'description'.
    relevant_keywords : list of str
        A set of words that indicate relevance.

    Returns
    -------
    classified : list of dict
        The same list, but each dict has an added "relevance" field:
        "Relevant" or "Irrelevant".
    """
    classified = []
    for proj in projects:
        combined_text = (proj['title'] + " " + proj['description']).lower()
        if any(kw.lower() in combined_text for kw in relevant_keywords):
            proj["relevance"] = "Relevant"
        else:
            proj["relevance"] = "Irrelevant"
        classified.append(proj)

    return classified


def advanced_summarize(text, max_length=130, min_length=30):
    """
    Summarizes text using the Hugging Face summarization pipeline (BART Large CNN).

    Parameters
    ----------
    text : str
        The text to summarize.
    max_length : int
        The approximate maximum number of tokens in the summary.
    min_length : int
        The approximate minimum number of tokens in the summary.

    Returns
    -------
    str
        A natural language summary of the given text.
    """
    # If it's very short, summarizing might not help
    if len(text.split()) < 40:
        return text

    # The summarizer call
    result = summarizer(text, max_length=max_length, min_length=min_length, do_sample=False)
    summary_text = result[0]['summary_text']
    return summary_text


def summarize_relevant_projects(classified_projects):
    """
    Generates an NLP-based summary for each Relevant project.

    Parameters
    ----------
    classified_projects : list of dict
        Projects with an added 'relevance' key.

    Returns
    -------
    list of dict
        A list containing 'title' and 'summary' for each relevant project.
    """
    relevant_summaries = []
    for proj in classified_projects:
        if proj["relevance"] == "Relevant":
            summary = advanced_summarize(proj["description"])
            relevant_summaries.append({
                "title": proj["title"],
                "summary": summary
            })
    return relevant_summaries


def main():
    """
    Main function to orchestrate:
      1) Scraping
      2) Classification
      3) Summarization
    and print the results.
    """
    # 1) Scrape
    url = "https://ispt.eu/projects/?theme-tag=heat"
    print(f"Scraping projects from: {url}")
    all_projects = scrape_ispt_heat_projects(url)

    # 2) Classify: I have chosen these relevant keywords based on a primitive nderstanidng of what the operations of the company are. 
    relevant_keywords = [
        "heat",
        "thermal",
        "thermo",
        "energy",
        "storage"
    ]
    classified = classify_projects(all_projects, relevant_keywords)

    # Print stats
    total_projects = len(classified)
    print(f"\nTotal number of projects scraped: {total_projects}")

    relevant_projects_count = sum(1 for p in classified if p["relevance"] == "Relevant")
    print(f"Number of relevant projects: {relevant_projects_count}")

    # Show all project info
    print("\n=== ALL PROJECTS (Title & Cleaned Description) ===")
    for proj in classified:
        print(f"TITLE: {proj['title']}")
        print(f"DESCRIPTION:\n{proj['description']}")
        print(f"RELEVANCE: {proj['relevance']}")
        print(f"LINK: {proj['link']}")
        print("--------------------------------------------------")

    # 3) Summarize relevant projects
    summaries = summarize_relevant_projects(classified)
    print("\n=== RELEVANT PROJECT SUMMARIES (NLP-based) ===")
    for s in summaries:
        print(f"TITLE: {s['title']}")
        print(f"SUMMARY: {s['summary']}")
        print("----")


if __name__ == "__main__":
    main()
