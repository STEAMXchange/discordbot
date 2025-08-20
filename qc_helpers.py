"""
Helper functions for Quality Control operations.
"""

import re
import time
import platform
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Font ID mapping
CANVA_FONT_ID = {
    "YAFcfijbpbU": "Grand Cru",
    "YAFdtQJYBw": "Nunito Sans",
    "YACgEUFdPdA": "Libre Baskerville"
}

EXPECTED_FONTS = {
    "Title": "Grand Cru",
    "Subheading": "Libre Baskerville",
    "Body Text": "Nunito Sans"
}

EXPECTED_COLORS = {
    "Title": "rgb(225, 232, 241)",
    "Subheading": "rgb(225, 232, 241)",
    "Body Text": "rgb(225, 232, 241)"
}


def extract_text_and_fonts(url: str):
    """Extract text and font data from a Canva URL."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Only apply Linux path override if needed
    if platform.system() == "Linux":
        options.binary_location = "/usr/bin/google-chrome"

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    driver.get(url)
    time.sleep(2)

    script = """
    let data = { fonts: [], text_data: [] };

    let fontSet = new Set();
    performance.getEntriesByType("resource").forEach(resource => {
        if (resource.name.endsWith(".woff2")) {
            fontSet.add(resource.name);
        }
    });

    data.fonts = Array.from(fontSet);

    document.querySelectorAll('span.OYPEnA').forEach(el => { 
        let style = window.getComputedStyle(el);
        let textSize = parseFloat(style.fontSize);
        let color = style.color;
        let bgColor = style.backgroundColor;
        let fontID = style.fontFamily;
        let text = el.textContent.trim();

        if (text !== "" && textSize) {
            data.text_data.push({
                "text": text,
                "size": textSize,
                "color": color,
                "background": bgColor,
                "font_id": fontID
            });
        }
    });

    return data;
    """

    extracted_data = driver.execute_script(script)
    driver.quit()

    return extracted_data


def normalize_font_id(font_id):
    """Normalize font ID for matching."""
    normalized_id = re.sub(r'\s*\d*', '', font_id)
    normalized_id = re.sub(r'\s*,\s*_fb_,\s*auto.*', '', normalized_id)
    return normalized_id.strip('"')


def map_fonts(text_data, font_files):
    """Map fonts to text data."""
    font_mapping = {}

    for url in font_files:
        match = re.search(r"/([^/]+)\.woff2", url)
        if match:
            font_id = match.group(1)
            font_mapping[font_id] = url

    for text_obj in text_data:
        font_match = None
        normalized_font_id = normalize_font_id(text_obj["font_id"])

        for font_id in font_mapping:
            if normalized_font_id in font_id:
                font_match = font_mapping[font_id]
                break

        text_obj["matched_font"] = font_match if font_match else "Unknown"

    return text_data


def categorize_text(final_data):
    """Categorize text by size and font."""
    categorized_data = {
        "Title": [],
        "Subheading": [],
        "Body Text": []
    }

    for item in final_data:
        size = item['size']
        font_name = CANVA_FONT_ID.get(normalize_font_id(item["font_id"]), "Unknown")

        if size >= 70:
            categorized_data["Title"].append((item, font_name))
        elif 40 <= size < 70:
            categorized_data["Subheading"].append((item, font_name))
        else:
            categorized_data["Body Text"].append((item, font_name))

    return categorized_data


def calculate_score(font_name, expected_font, color, expected_color):
    """Calculate QC score for text element."""
    score = 0
    if font_name == expected_font:
        score += 5
    if color == expected_color:
        score += 5
    return score
