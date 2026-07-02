import requests
import csv
import os
import time


def scopus_search(keywords, save_folder, api_key):
    # Format the query
    query = " AND ".join([f'"{kw}"' for kw in keywords])

    # Initialize CSV file
    filename = os.path.join(save_folder, 'Scopus_land_degradation_drivers_human_factors_natural_factors.csv')
    with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(['Title', 'Journal/Book', 'Year', 'Citations', 'Abstract'])

        # Set up API request headers
        headers = {
            "X-ELS-APIKey": api_key,
            "Accept": "application/json"
        }

        # Set the base URL and initial parameters for the search
        search_url = "https://api.elsevier.com/content/search/scopus"
        params = {
            "query": query,
            "count": 25,  # Number of results per page (maximum is 25 for Scopus)
            "start": 0  # Starting index for pagination
        }

        while True:
            # Make API request for search results
            response = requests.get(search_url, headers=headers, params=params)
            data = response.json()

            # Check for results in the response
            results = data.get("search-results", {}).get("entry", [])
            if not results:
                print("No more results found.")
                break

            # Process each result
            for result in results:
                title = result.get("dc:title", "N/A")
                journal = result.get("prism:publicationName", "N/A")
                year = result.get("prism:coverDate", "N/A").split("-")[0] if "prism:coverDate" in result else "N/A"
                citations = result.get("citedby-count", "N/A")

                # Retrieve Scopus ID to get the abstract
                scopus_id = result.get("dc:identifier", "").replace("SCOPUS_ID:", "")
                abstract = "N/A"

                if scopus_id:
                    # Fetch full article details using Scopus ID
                    article_url = f"https://api.elsevier.com/content/abstract/scopus_id/{scopus_id}"
                    article_response = requests.get(article_url, headers=headers)
                    article_data = article_response.json()

                    # Extract abstract if available
                    abstract = article_data.get("abstracts-retrieval-response", {}).get("coredata", {}).get(
                        "dc:description", "N/A")

                writer.writerow([title, journal, year, citations, abstract])
                print(f"Added: {title}")

            # Pagination: Move to the next set of results
            params["start"] += 25
            time.sleep(1)  # Be respectful of API rate limits

    print(f"Data saved to {filename}")


# Example Usage
keywords = ["land degradation", "drivers", "human factors", "natural factors"]
save_folder = r'C:\Users\nafiz\OneDrive - Mississippi State University\NSF_MSU_Project_Shared\Review_Paper\CSV\Abstracts'  # Replace with your folder path
api_key = 'YOUR_SCOPUS_API_KEY'  # Replace with your actual Scopus API key
scopus_search(keywords, save_folder, api_key)