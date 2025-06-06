from flask import Flask, request
from markupsafe import Markup
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

app = Flask(__name__)

KEYWORDS = ["camper", "trailer", "van", "tent", "bike", "shelter", "free"]
MAX_SCROLLS = 10

# ──────────────────────────────────────────────────────────────
# 🎯 Browser Setup
def init_browser():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=chrome_options)

# ──────────────────────────────────────────────────────────────
# 🔍 Scraper Function
def scrape_marketplace(location):
    url = f"https://www.facebook.com/marketplace/{location}/search/?minPrice=0&maxPrice=0"
    driver = init_browser()
    driver.get(url)
    time.sleep(5)

    for _ in range(MAX_SCROLLS):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

    items = driver.find_elements(By.XPATH, "//a[contains(@href, '/marketplace/item/')]")
    seen, data = set(), []

    for item in items:
        try:
            link = item.get_attribute("href")
            title_elem = item.find_element(By.XPATH, ".//span[contains(text(),'$')]//following::span[1]")
            title = title_elem.text.lower()
            if any(k in title for k in KEYWORDS) and link not in seen:
                img = item.find_element(By.TAG_NAME, "img").get_attribute("src")
                data.append({"title": title.title(), "link": link, "image": img})
                seen.add(link)
        except:
            continue

    driver.quit()
    return data

# ──────────────────────────────────────────────────────────────
# 🧠 HTML Builder
def render_results(location, results):
    location_title = location.replace("-", " ").title()
    cards_html = ""
    for item in results:
        cards_html += f"""
        <div class="col-md-4 mb-4">
            <div class="card h-100 shadow-sm">
                <img src="{item['image']}" class="card-img-top" style="height:200px;object-fit:cover;">
                <div class="card-body">
                    <h6 class="card-title">{item['title']}</h6>
                    <a href="{item['link']}" target="_blank" class="btn btn-primary btn-sm">View on Facebook</a>
                </div>
            </div>
        </div>
        """

    return f"""
    <!doctype html>
    <html lang="en">
    <head>
        <title>Results - Free Finds</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body>
        <div class="container mt-4">
            <h2 class="mb-4">🎁 Free Items in {location_title}</h2>
            <div class="row">{cards_html}</div>
            <a href="/" class="btn btn-secondary mt-4">← Back</a>
        </div>
    </body>
    </html>
    """

# ──────────────────────────────────────────────────────────────
# 🖥️ Landing + Input Form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        city = request.form.get("city", "").strip().lower().replace(" ", "-")
        state = request.form.get("state", "").strip().lower().replace(" ", "-")
        if not city or not state:
            return "City and State are required.", 400
        location = f"{city}-{state}"
        results = scrape_marketplace(location)
        return render_results(location, results)

    return """
    <!doctype html>
    <html lang="en">
    <head>
        <title>Free Finds Marketplace Scraper</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="bg-light">
        <div class="container py-5">
            <div class="text-center mb-5">
                <h1 class="display-5 fw-bold">♻️ Free Finds Scraper</h1>
                <p class="lead">Quickly find FREE items on Facebook Marketplace near you. Zero hassle. Maximum score.</p>
            </div>
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <form method="POST" class="card p-4 shadow-sm bg-white">
                        <div class="mb-3">
                            <label class="form-label">City</label>
                            <input type="text" name="city" class="form-control" placeholder="e.g., Clinton" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label">State</label>
                            <input type="text" name="state" class="form-control" placeholder="e.g., Iowa" required>
                        </div>
                        <button type="submit" class="btn btn-success w-100">🔍 Find Free Stuff</button>
                    </form>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

# ──────────────────────────────────────────────────────────────
# 🚀 Start
if __name__ == "__main__":
    app.run(debug=True)
