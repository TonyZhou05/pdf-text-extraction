import requests
import pandas as pd
import os

# Read the table
df = pd.read_csv("drugcombo-data-main/observed_dlt.csv", sep=",")  # or sep=',' if CSV
pmids = df["PMID"].dropna().astype(str).unique()

# Set save path
os.makedirs("pdfs", exist_ok=True)

# Unpaywall requires email as identification
EMAIL = "zhiyis3@illinois.edu"


def get_doi_from_pmid(pmid):
    """Get DOI from PMID via PubMed API"""
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
    params = {"db": "pubmed", "id": pmid, "retmode": "json"}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        try:
            data = res.json()
            article = data["result"][pmid]
            for id_ in article.get("articleids", []):
                if id_["idtype"] == "doi":
                    return id_["value"]
        except Exception:
            return None
    return None


def get_pdf_link_from_doi(doi):
    """Get open access PDF link via Unpaywall API"""
    url = f"https://api.unpaywall.org/v2/{doi}"
    params = {"email": EMAIL}
    res = requests.get(url, params=params)
    if res.status_code == 200:
        data = res.json()
        if data.get("best_oa_location") and data["best_oa_location"].get("url_for_pdf"):
            return data["best_oa_location"]["url_for_pdf"]
    return None


def download_pdf(url, filename):
    """Download PDF file"""
    res = requests.get(url)
    if res.status_code == 200 and "application/pdf" in res.headers.get(
        "Content-Type", ""
    ):
        with open(filename, "wb") as f:
            f.write(res.content)
        return True
    return False


# Main logic
for pmid in pmids:
    print(f"[+] Processing PMID: {pmid}")
    doi = get_doi_from_pmid(pmid)
    if not doi:
        print(f"  [-] DOI not found")
        continue
    print(f"  [+] DOI: {doi}")
    pdf_url = get_pdf_link_from_doi(doi)
    if not pdf_url:
        print(f"  [-] No open PDF found")
        continue
    filename = f"pdfs/{pmid}.pdf"
    if download_pdf(pdf_url, filename):
        print(f"  [✓] Downloaded: {filename}")
    else:
        print(f"  [x] Failed to download PDF")

print("Done.")
