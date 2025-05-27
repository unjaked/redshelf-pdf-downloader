
import os # for interacting with the operating system (like creating folders, joining paths)
import time # for sleep/delay functions (e.g. time.sleep())
import base64 # for decoding Base64-encoded data (used when saving the PDF bytes from Selenium)
from selenium import webdriver # the main Selenium module for controlling Chrome/Firefox (browser automation)
from selenium.webdriver.chrome.options import Options # for configuring Chrome (e.g. headless mode)
from selenium.webdriver.common.by import By # for selecting elements (like By.CSS_SELECTOR)
from selenium.webdriver.support.ui import WebDriverWait # to wait for elements to load (explicit wait)
from selenium.webdriver.support import expected_conditions as EC # to define the wait condition (like element presence)
from pathlib import Path     # to work with file paths in a cross-platform, cleaner way
from pypdf import PdfWriter  # for merging the downloaded PDFs together


#################### CONFIG ####################

# Authentication cookies here. See GitHub documentation for instructions on obtaining this.
# {for github}: Login to RedShelf, visit the below link, open your browser's developer tools, and copy the cookies from the "Application" tab. You should only have to replace the "value" fields.
cookies = [
    {
        "name": "csrftoken",
        "value": "kUMkZvHN4usY2Norh9Dc9HlfTY1mZnlO",
        "domain": "platform.virdocs.com",
        "path": "/"
    },
    {
        "name": "session_id",
        "value": "kl7ctc3yiwg9vq360hgar7xg37bcvfrt",
        "domain": "platform.virdocs.com",
        "path": "/"
    }
]

# Replace with your actual textbook ID. See GitHub documentation for instructions on obtaining this.
# {for github}: Visit the textbook on RedShelf, and copy the ID from the URL that's right after "/read/".
textbook_id = "2017884"

# Prefix for the name of the output files (e.g. textbook name). Also creates folder with this name.
file_prefix = "in_mixed_company"

################## END CONFIG ##################



def main():
    # Set up Chrome in headless mode with PDF printing enabled
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--disable-gpu')

    # Locate (and create) a 'pdfs' folder next to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(script_dir, file_prefix)
    os.makedirs(download_dir, exist_ok=True)

    # Launch the browser
    driver = webdriver.Chrome(options=chrome_options)

    # First visit to set cookies
    driver.get("https://platform.virdocs.com/")
    for cookie in cookies:
        driver.add_cookie(cookie)

    page_num = 0 # Page to start from, usually 0 for the first page
    while True:
        url = f"https://platform.virdocs.com/read/document/{textbook_id}/{page_num}"
        driver.get(url)

        # Wait for the web viewer to load all elements and handle network errors
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "section.chunk"))
            )
        except Exception:
            # Check if it’s a network error / 404 page
            body_cls = driver.find_element(By.TAG_NAME, "body").get_attribute("class")
            if "neterror" in body_cls:
                print(f"Page {page_num} returned 404. Stopping.")
            else:
                print(f"Timeout waiting for page {page_num}. Stopping.")
            break

        # Print to PDF via DevTools Protocol
        pdf_data = driver.execute_cdp_cmd("Page.printToPDF", {
            "printBackground": True,
            "format": "A4"
        })

        # Decode the Base64-encoded PDF and write it out
        pdf_bytes = base64.b64decode(pdf_data['data'])
        output_path = os.path.join(download_dir, f"{file_prefix}_{page_num}.pdf")
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"Saved page {page_num} → {output_path}")
        page_num += 1
        # Optional: be polite to the server
        time.sleep(0.5)

    driver.quit()
    print("All pages downloaded! Now merging PDFs...")



def merge_pdfs(download_dir, output_filename):

    # Create a PDF writer object (merged PDF is stored in this)
    pdf_writer = PdfWriter()

    # grab all pdf files and store names in list, sorted by number
    pdf_paths = sorted(
        Path(download_dir).glob("*.pdf"),
        key=lambda p: int(p.stem.rsplit("_", 1)[-1]) # extract page num from filename
    )

    # Combine PDFs in order
    for pdf_path in pdf_paths:
        pdf_writer.append(str(pdf_path))

    # Write out the merged PDF
    output_path = Path(download_dir) / output_filename
    with open(output_path, "wb") as out_f:
        pdf_writer.write(out_f)
    pdf_writer.close()

    print(f"Merged {len(pdf_paths)} files → {output_path}")
    

if __name__ == "__main__":
    main()

    # Comment out this to skip merging
    merge_pdfs( 
        download_dir=os.path.join(os.path.dirname(os.path.abspath(__file__)), file_prefix),
        output_filename=f"_{file_prefix}_full.pdf"
    )
    
