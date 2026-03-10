import arxiv
import os
from tqdm import tqdm

def fetch_papers(query, max_results=5):
    """
    Searches arXiv and returns a list of paper metadata.
    """
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    results = []
    print(f"--- Searching arXiv for: '{query}' ---")
    
    # Using tqdm for a professional progress bar
    for result in tqdm(client.results(search), total=max_results):
        paper_info = {
            "title": result.title,
            "id": result.entry_id.split('/')[-1],
            "summary": result.summary,
            "pdf_url": result.pdf_url,
            "authors": [author.name for author in result.authors]
        }
        results.append(paper_info)
    
    return results

if __name__ == "__main__":
    # Feel free to change this query to something specific like "Neural Ordinary Differential Equations"
    topic = "Reinforcement learning for autonomous driving"
    papers = fetch_research_papers(query=topic, max_results=5)

    for i, p in enumerate(papers):
        print(f"\n[{i+1}] {p['title']}")
        print(f"Authors: {', '.join(p['authors'][:3])}...")
        print(f"Link: {p['pdf_url']}")

def get_paper_content(paper_id):
    """Fetches the full abstract/summary for a specific arXiv ID."""
    try:
        api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        response = requests.get(api_url)
        root = ET.fromstring(response.content)
        entry = root.find('{http://www.w3.org/2005/Atom}entry')
        if entry is not None:
            return entry.find('{http://www.w3.org/2005/Atom}summary').text.strip()
        return ""
    except Exception as e:
        print(f"Error fetching paper content: {e}")
        return ""
