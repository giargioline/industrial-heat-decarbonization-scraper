# Industrial Heat Decarbonization Scraper

This repository contains a **Python project** that scrapes, classifies, and summarizes case studies related to **decarbonization of industrial heat** from the [ISPT Heat Projects page](https://ispt.eu/projects/?theme-tag=heat).

## Installation

Clone or Download this repository:
git clone https://github.com/your-username/industrial-heat-decarbonization-scraper.git

Install dependencies:
pip install -r requirements.txt

## Overview

### What does this project do?
1. **Scrapes** project listings from ISPT’s **Heat** page.
2. **Cleans** the scraped data, I noticed that retrieving all the text from the projects pages would lead to a lot of extra material behing included, all the extra text was either positioned after "You might also be interested in", it was part of an image caption or enclosed in a mint coloured block.
   Threfore the text is cleaned by removing:
   - “Mint background” blocks.
   - `<figcaption>` text.
   - Everything after the heading “You might also be interested in.”
3. **Classifies** each project as “Relevant” or “Irrelevant” to decarbonization based on **keyword matching**.
4. **Summarizes** the “Relevant” projects using a **Hugging Face** summarization model (*facebook/bart-large-cnn*).

---

## Rationale & Method Choices

### Web Scraping with Requests & BeautifulSoup 
  - The ISPT site is largely static (or minimally dynamic), so `requests` + `BeautifulSoup` is simpler and more lightweight than a full browser automation tool (e.g., Selenium).  
  - `requests` handles HTTP fetching efficiently, while **BeautifulSoup** is very effective for parsing the HTML structures.

### Data Cleaning & Organization 
  - Industrial heat project pages sometimes contain **unrelated** or **distracting** sections, like “You might also be interested in…” or `figcaption` elements that add minimal context.  
  - Removing extraneous sections keeps the text focused on the main description, ensuring classification and summarization are more accurate.

### Classification with Simple Keyword Matching
- For a small dataset, or early proof-of-concept, a **keyword-based** approach is quick to implement and interpret.  
- Over time, a more sophisticated ML-based classifier could and most likely should be used.
- I personally don't have enough insights into the inner workings and operations in the company to understand what criteria to base a classification on, I simply looked for the keywords "heat","thermal","thermo","energy" or "storage in the text, if one of these was included then the project is considered relevant.
- **Pros**: Easy to maintain, transparent logic (just add or remove keywords).
- **Cons**: Less precise than a full-blown machine learning text classifier.

### NLP Summarization with Transformers
  - The assignment explicitly says to use a language model or an NLP technique. I chose Hugging Face’s **`transformers`** because it provides **pre-trained** summarization models (e.g., `facebook/bart-large-cnn`) that can handle text **without** building or training your own model.  
  - Summarizing “relevant” case studies highlights the main points quickly, enabling faster reading and better knowledge transfer.
  - The current implementation uses the Hugging Face facebook/bart-large-cnn model for summarization, which requires downloading a 1.6 GB pre-trained language model. While this approach is cost-effective and keeps the         processing local, it is slow and resource-intensive, especially on machines with limited memory or CPU power.
    An alternative is using a cloud-based API like OpenAI's GPT. This approach can significantly speed up summarization tasks and reduce the disk space requirements, as the model runs on remote servers. However, APIs          like OpenAI charge per request, making the solution more expensive for frequent or large-scale usage.

---

## Project Steps

1. **Fetch Project Listings**  
   - The code is directed to the provided URL ([https://ispt.eu/projects/?theme-tag=heat](https://ispt.eu/projects/?theme-tag=heat)), retrieving the complete HTML content of each webpage using the requests library.  
   - Scrape each `<article>` block that has the classes `post-block project` to capture the initial listing data.

2. **Follow Detail Links**  
   - For each project, we parse the link to a detail page.  
   - I request that detail page to extract a **full** description.

3. **Clean the Description**  
   - **Remove** `<div>` blocks with `has-mint-background-color` in their class.  
   - **Remove** all `<figcaption>` tags.  
   - **Locate** `<h2>` containing “You might also be interested in” and remove it plus any subsequent elements.

4. **Classify**  
   - I define a list of keywords (a pretty approximate set, based on a primitive understanding of the company's processes)  
   - If any keyword is present in the combined text of `title + description`, the proejct is marked as “Relevant.” Otherwise, it’s “Irrelevant.”

5. **Summarize (NLP-based)**  
   - For each “Relevant” project, we feed its description into Hugging Face’s `facebook/bart-large-cnn` summarization pipeline.  
   - The pipeline returns a short, coherent summary.

6. **Output**  
To the console are printed:  
  - The total number of projects scraped.  
  - The number found relevant.  
  - Each project’s full cleaned description. (Even though it is not included in the required outputs, I think it is useful to see to check how the software is working) 
  - A summary for the relevant ones.

## Future Improvements
The following is a set of possible improvements to this code:
  - **More precise classification**: Instead of keywords, we could use a small machine learning or fine-tuned model to capture nuances around “heat decarbonization.”
  - **Better file management**: Currently, everything just prints to the console. We could store project data in a CSV, JSON, or database for further analysis.
  - **Using a language model API instead of downloading one locally**: The current implementation uses the Hugging Face facebook/bart-large-cnn model for summarization, which requires downloading a 1.6 GB pre-trained           language model. While this approach is cost-effective and keeps the processing local, it is slow and resource-intensive, especially on machines with limited memory or CPU power.
     An alternative is using a cloud-based API like OpenAI's GPT. This approach can significantly speed up summarization tasks and reduce the disk space requirements, as the model runs on remote servers. However, APIs          like OpenAI charge per request, making the solution more expensive for frequent or large-scale usage.
