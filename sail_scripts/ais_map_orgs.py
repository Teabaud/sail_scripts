import time

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Set up headless Chrome browser
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Try to use Selenium Manager for compatibility
driver = webdriver.Chrome(options=chrome_options)
print("Using Selenium's built-in driver manager")

try:
    # Navigate to AI Safety Map
    print("Navigating to AI Safety Map...")
    driver.get("https://map.aisafety.world/")

    # Wait for the page to load fully (adjust timeout as needed)
    wait = WebDriverWait(driver, 30)

    # First try waiting for the grid
    wait.until(EC.presence_of_element_located((By.ID, "grid")))

    # Additional wait for all SVG elements to load
    print("Waiting for dynamic content to load...")
    time.sleep(10)

    # Now extract all anchor tags within the SVG
    print("Extracting organization links...")
    grid = driver.find_element(By.XPATH, "//div[@id='grid']")
    links = grid.find_elements(By.TAG_NAME, "a")
    print(f"Found {len(links)} total links on the page")

    # Take a screenshot for debugging
    driver.save_screenshot("generated/aisafety_map.png")
    print(f"Saved screenshot to aisafety_map.png")

    organizations = []
    for link in links:
        try:
            url = link.get_attribute("href")["baseVal"].strip()

            # Skip non-external links
            if not url or not (url.startswith("http://") or url.startswith("https://")):
                continue

            # Try to get the text from the link
            text = link.text.strip()
            if not text:
                # If no direct text, look for child elements with text
                text_elements = link.find_elements(By.XPATH, ".//div")
                for elem in text_elements:
                    if elem.text.strip():
                        text = elem.text.strip()
                        break

            # If still no text, use the domain name
            if not text:
                domain = url.split("//")[1].split("/")[0].replace("www.", "")
                text = domain
            organizations.append({"name": text, "url": url})
        except Exception as e:
            print(f"Error extracting link info: {str(e)}")

    print(f"Found {len(organizations)} organizations")

    # Save to CSV
    df = pd.DataFrame(organizations)
    df.to_csv("generated/ai_safety_organizations.csv", index=False)
    print("Organizations saved to ai_safety_organizations.csv")

except Exception as main_error:
    print(f"An error occurred: {main_error}")

finally:
    # Clean up
    driver.quit()

print("\nConsider the manual approach if this script isn't working reliably:")
print("1. Visit https://aisafety.com/map in your browser")
print("2. Manually identify and record 15-20 key organizations")
print("3. Check each website for language options")
print("4. This manual approach is sufficient for your blog post needs")
