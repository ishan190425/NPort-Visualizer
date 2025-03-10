from flask import Flask, render_template, request
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from flask_caching import Cache
import logging
import time
import re 
import os

app = Flask(__name__)

# Configure Caching
app.config["CACHE_TYPE"] = "simple"  # Use "redis" in production
app.config["CACHE_DEFAULT_TIMEOUT"] = 3600  # Cache for 1 hour
cache = Cache(app)

# SEC API Headers
HEADERS = {
    "User-Agent": "Ishan Rathi (rathiishan0@gmail.com)",
    "Accept": "application/json"
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

@cache.memoize(timeout=3600)  # Cache filings for 1 hour
def get_latest_nport_url(cik):
    cik = cik.zfill(10)  # Ensure CIK is 10 digits
    json_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

    try:
        time.sleep(1)  # Avoid rate limiting
        response = requests.get(json_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 403:
            logging.error("403 Forbidden - SEC blocked access. Check User-Agent headers.")
            return None, "SEC API access denied. Try again later."

        response.raise_for_status()
        data = response.json()
        fund_name = data.get('name', 'Unknown Fund')  # Default if name not found


        filings = data.get("filings", {}).get("recent", {})
        if not filings:
            return None, "No recent filings found for this CIK."

        accession_numbers = filings.get("accessionNumber", [])
        form_types = filings.get("form", [])
        filing_dates = filings.get("filingDate", [])

        latest_nport = None
        latest_date = None
        for i, form in enumerate(form_types):
            if form == "NPORT-P":
                filing_date = filing_dates[i]
                if not latest_date or filing_date > latest_date:
                    latest_date = filing_date
                    latest_nport = {
                        "accession": accession_numbers[i],
                        "date": filing_date
                    }

        if latest_nport:
            accession_no = latest_nport["accession"]
            formatted_accession = accession_no.replace("-", "")
            index_json_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession}/index.json"

            time.sleep(1)
            index_response = requests.get(index_json_url, headers=HEADERS, timeout=10)

            if index_response.status_code == 403:
                logging.error("403 Forbidden while fetching index.json")
                return None, "SEC is blocking this request. Try again later."

            index_response.raise_for_status()
            index_data = index_response.json()

            for file in index_data.get("directory", {}).get("item", []):
                if file["name"].endswith(".xml"):
                    xml_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{formatted_accession}/{file['name']}"
                    return xml_url, None, fund_name

            return None, "NPORT XML file not found in the filing directory.", fund_name

        return None, "No NPORT-P filings found in recent submissions.", fund_name

    except requests.exceptions.Timeout:
        logging.error("Request to SEC API timed out.")
        return None, "SEC API is taking too long to respond. Try again later.", fund_name

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return None, "There was a problem fetching data from the SEC. Try again later.", fund_name

    except ValueError as e:
        logging.error(f"JSON parsing error: {e}")
        return None, "Error processing SEC data. Please try again.", fund_name

@cache.memoize(timeout=3600)  # Cache parsed holdings for 1 hour
def parse_nport_holdings(xml_url, sort_by="value"):
    """Fetch and parse the NPORT XML filing, with caching and sorting."""
    try:
        response = requests.get(xml_url, headers=HEADERS, timeout=10)
        
        if response.status_code == 403:
            logging.error("403 Forbidden while fetching XML data.")
            return None, "Access denied to SEC filing. Try again later."

        response.raise_for_status()
        
        try:
            root = ET.fromstring(response.content)
        except ET.ParseError:
            logging.error("Failed to parse SEC XML document.")
            return None, "Error reading SEC filing data. Please try again later."

        namespace = {"ns": "http://www.sec.gov/edgar/nport"}
        holdings = []

        for inv in root.findall(".//ns:invstOrSec", namespace):
            holding = {
                "cusip": inv.findtext("ns:cusip", default="N/A", namespaces=namespace),
                "title": inv.findtext("ns:title", default="N/A", namespaces=namespace),
                "balance": float(inv.findtext("ns:balance", default="0", namespaces=namespace)),
                "value": float(inv.findtext("ns:valUSD", default="0", namespaces=namespace))
            }
            holdings.append(holding)

        if not holdings:
            return None, "No holdings found in the filing."

        # Sorting logic
        if sort_by == "value":
            holdings.sort(key=lambda x: x["value"], reverse=True)
        elif sort_by == "balance":
            holdings.sort(key=lambda x: x["balance"], reverse=True)
        elif sort_by == "title":
            holdings.sort(key=lambda x: x["title"])

        return holdings, None

    except requests.exceptions.Timeout:
        logging.error("Request to SEC XML API timed out.")
        return None, "The SEC server took too long to respond. Try again later."

    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return None, "Error retrieving SEC filing data. Please try again."

@app.route("/", methods=["GET", "POST"])
def index():
    holdings = None
    error = None
    cik = ""  # Default empty CIK value
    fund_name = ""
    if request.method == "POST":
        cik = request.form.get("cik").strip()
        sort_by = request.form.get("sort_by", "value")

        # Remove "CIK" prefix if present
        cik = re.sub(r'^CIK', '', cik, flags=re.IGNORECASE).strip()

        if not cik:
            error = "Please enter a valid CIK"
        else:
            cik = cik.zfill(10)
            xml_url, fetch_error, fund_name = get_latest_nport_url(cik)
            
            if fetch_error:
                error = fetch_error
            elif xml_url:
                holdings, parse_error = parse_nport_holdings(xml_url, sort_by)
                if parse_error:
                    error = parse_error
            else:
                error = "Could not find recent N-Port filing for this CIK"
    
    return render_template("index.html", holdings=holdings, error=error, cik=cik, fund_name=fund_name, current_date=datetime.now().strftime("%Y-%m-%d"))



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Default to 5000 if PORT is not set
    #app.run(host="0.0.0.0", port=port, debug=True)
    app.run()

