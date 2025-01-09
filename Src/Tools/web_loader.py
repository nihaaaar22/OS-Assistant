import hashlib
import logging
import re
import requests
import pdfplumber
from io import BytesIO
try:
    from bs4 import BeautifulSoup
except ImportError:
    raise ImportError(
        'Webpage requires extra dependencies. Install with `pip install --upgrade "embedchain[dataloaders]"`'
    ) from None


def clean_string(text):
    """
    This function takes in a string and performs a series of text cleaning operations.

    Args:
        text (str): The text to be cleaned. This is expected to be a string.

    Returns:
        cleaned_text (str): The cleaned text after all the cleaning operations
        have been performed.
    """
    # Replacement of newline characters:
    text = text.replace("\n", " ")

    # Stripping and reducing multiple spaces to single:
    cleaned_text = re.sub(r"\s+", " ", text.strip())

    # Removing backslashes:
    cleaned_text = cleaned_text.replace("\\", "")

    # Replacing hash characters:
    cleaned_text = cleaned_text.replace("#", " ")

    # Eliminating consecutive non-alphanumeric characters:
    # This regex identifies consecutive non-alphanumeric characters (i.e., not
    # a word character [a-zA-Z0-9_] and not a whitespace) in the string
    # and replaces each group of such characters with a single occurrence of
    # that character.
    # For example, "!!! hello !!!" would become "! hello !".
    cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)

    return cleaned_text


def get_clean_content(html, url) -> str:
    """
    Clean and extract text from HTML content.

    Args:
        html (bytes): The HTML content to be cleaned.
        url (str): The URL of the webpage (for logging purposes).

    Returns:
        str: The cleaned text content.
    """
    soup = BeautifulSoup(html, "html.parser")
    original_size = len(str(soup.get_text()))

    tags_to_exclude = [
        "nav",
        "aside",
        "form",
        "header",
        "noscript",
        "svg",
        "canvas",
        "footer",
        "script",
        "style",
    ]
    for tag in soup(tags_to_exclude):
        tag.decompose()

    ids_to_exclude = ["sidebar", "main-navigation", "menu-main-menu"]
    for id in ids_to_exclude:
        tags = soup.find_all(id=id)
        for tag in tags:
            tag.decompose()

    classes_to_exclude = [
        "elementor-location-header",
        "navbar-header",
        "nav",
        "header-sidebar-wrapper",
        "blog-sidebar-wrapper",
        "related-posts",
    ]
    for class_name in classes_to_exclude:
        tags = soup.find_all(class_=class_name)
        for tag in tags:
            tag.decompose()

    content = soup.get_text()
    content = clean_string(content)

    cleaned_size = len(content)
    if original_size != 0:
        logging.info(
            f"[{url}] Cleaned page size: {cleaned_size} characters, down from {original_size} (shrunk: {original_size-cleaned_size} chars, {round((1-(cleaned_size/original_size)) * 100, 2)}%)"
        )

    return content


def load_data(url, session=None):
    """
    Load data from a web page or PDF using a requests session.

    Args:
        url (str): The URL to fetch data from.
        session (requests.Session, optional): A shared requests session. If None, a new session is created.

    Returns:
        dict: A dictionary containing the document ID, content, and metadata.
    """
    if session is None:
        session = requests.Session()

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_4) AppleWebKit/537.36 (KHTML like Gecko) Chrome/52.0.2743.116 Safari/537.36"
    }
    web_data = {}
    content = ""
    try:
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.content
        # Check content type
        content_type = response.headers.get("Content-Type", "")
        if "html" in content_type:
            content = get_clean_content(data, url)
        elif "pdf" in content_type:
            # Open the PDF file using pdfplumber
            with pdfplumber.open(BytesIO(response.content)) as pdf:
                # Extract text from each page and combine it
                content = "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

        meta_data = {"url": url}
        doc_id = hashlib.sha256((content + url).encode()).hexdigest()
        web_data = {
            "doc_id": doc_id,
            "data": [
                {
                    "content": content,
                    "meta_data": meta_data,
                }
            ],
        }
    except Exception as e:
        logging.error(f"Error loading data from {url}: {e}")
        web_data = {
            "data": [
                {
                    "content": "",
                    "meta_data": "",
                }
            ],
        }
    return web_data


def close_session(session):
    """
    Close the requests session.

    Args:
        session (requests.Session): The session to close.
    """
    session.close()