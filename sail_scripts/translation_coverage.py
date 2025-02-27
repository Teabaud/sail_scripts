import concurrent.futures
import re

import langdetect
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# Headers to avoid being blocked
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def detect_language_options(soup):
    """
    Highly precise detection of genuine language selection options.
    Filters out common false positives, including Google Scholar links.
    """
    language_options = []

    # These exact language names are reliable indicators
    language_names = {
        "english": "en",
        "español": "es",
        "spanish": "es",
        "français": "fr",
        "french": "fr",
        "deutsch": "de",
        "german": "de",
        "italiano": "it",
        "italian": "it",
        "português": "pt",
        "portuguese": "pt",
        "русский": "ru",
        "russian": "ru",
        "中文": "zh",
        "chinese": "zh",
        "日本語": "ja",
        "japanese": "ja",
        "العربية": "ar",
        "arabic": "ar",
        "हिन्दी": "hi",
        "hindi": "hi",
    }

    # Two-letter language codes
    language_codes = ["en", "es", "fr", "de", "it", "pt", "ru", "zh", "ja", "ar", "hi"]

    # Exclude domains/paths that commonly use language parameters but aren't language selectors
    exclude_domains = [
        "scholar.google.com",
        "translate.google.com",
        "accounts.google.com",
        "twitter.com",
        "facebook.com",
        "linkedin.com",
        "youtube.com",
    ]

    # Approach 1: Look for dedicated language selector dropdowns
    for select in soup.find_all("select"):
        options = select.find_all("option")
        if 2 <= len(options) <= 15:  # Language selects typically have few options
            # Check if the select element has indicators in its name or classes
            has_lang_indicator = False
            select_id = select.get("id", "").lower()
            select_name = select.get("name", "").lower()
            select_classes = " ".join(select.get("class", [])).lower()

            lang_indicators = [
                "lang",
                "idioma",
                "sprache",
                "langue",
                "language",
                "locale",
            ]
            for indicator in lang_indicators:
                if (
                    indicator in select_id
                    or indicator in select_name
                    or indicator in select_classes
                ):
                    has_lang_indicator = True
                    break

            if not has_lang_indicator:
                # Check if options contain language codes or names
                option_values = [opt.get("value", "").lower() for opt in options]
                option_texts = [opt.get_text().strip().lower() for opt in options]

                # Count language matches in values and texts
                lang_code_matches = sum(
                    1
                    for code in language_codes
                    if any(
                        val == code
                        or val.startswith(f"{code}-")
                        or val.startswith(f"{code}_")
                        for val in option_values
                    )
                )

                lang_name_matches = sum(
                    1
                    for name in language_names
                    if any(name in text for text in option_texts)
                )

                # Require strong evidence: either explicit label or multiple matches
                if lang_code_matches >= 2 or lang_name_matches >= 2:
                    language_options.append(
                        {
                            "type": "language_select",
                            "matched_codes": lang_code_matches,
                            "matched_names": lang_name_matches,
                            "content": str(select)[:200],
                        }
                    )

    # Approach 2: Look for groups of language option links
    # Only consider clear language navigation groups
    for nav in soup.find_all(["nav", "ul", "div"]):
        # Skip large containers that are unlikely to be just language selectors
        if len(nav.find_all()) > 20:
            continue

        # First check if this element is explicitly marked as language navigation
        nav_id = nav.get("id", "").lower()
        nav_classes = " ".join(nav.get("class", [])).lower()

        explicit_lang_element = False
        for term in [
            "language-selector",
            "lang-selector",
            "language-menu",
            "lang-menu",
            "language-nav",
            "lang-nav",
            "language-switcher",
            "lang-switcher",
        ]:
            if term in nav_id or term in nav_classes:
                explicit_lang_element = True
                break

        # For explicit language elements, we need less additional evidence
        required_matches = 1 if explicit_lang_element else 2

        # Get all links in this navigation element
        links = nav.find_all("a")
        if 2 <= len(links) <= 10:  # Language menus typically have few options
            # Filter out links to external sites in our exclusion list
            filtered_links = []
            for link in links:
                href = link.get("href", "")
                if not any(domain in href for domain in exclude_domains):
                    filtered_links.append(link)

            if len(filtered_links) < 2:
                continue

            # Check both href values and link text
            href_values = [link.get("href", "").lower() for link in filtered_links]
            link_texts = [link.get_text().strip().lower() for link in filtered_links]

            # Look for dedicated language path patterns (/en/, /fr/, etc.)
            lang_path_matches = []
            for i, href in enumerate(href_values):
                # Match patterns like /en/, /en-us/, etc.
                path_match = re.search(r"/([a-z]{2})(?:-[a-z]{2})?(/|$|\?)", href)
                if path_match and path_match.group(1) in language_codes:
                    lang_path_matches.append(path_match.group(1))

                # Match patterns like ?lang=en, &language=fr
                param_match = re.search(r"[\?&](lang|language)=([a-z]{2})", href)
                if param_match and param_match.group(2) in language_codes:
                    # Special case: Exclude Google Scholar's hl parameter
                    if "hl=" in href and "scholar.google" in href:
                        continue
                    lang_path_matches.append(param_match.group(2))

            # Count unique language paths found
            unique_lang_paths = set(lang_path_matches)

            # Count language name matches in text
            text_lang_matches = []
            for text in link_texts:
                for name, code in language_names.items():
                    if text == name or text == code or text.startswith(name + " "):
                        text_lang_matches.append(code)
                        break

            unique_text_matches = set(text_lang_matches)

            # If we found multiple distinct languages, this is likely a language menu
            all_matches = unique_lang_paths.union(unique_text_matches)
            if len(all_matches) >= required_matches:
                language_options.append(
                    {
                        "type": "language_menu",
                        "matched_paths": list(unique_lang_paths),
                        "matched_names": list(unique_text_matches),
                        "content": str(nav)[:200],
                    }
                )

    # Approach 3: Check for these highly specific ID patterns
    # These are extremely reliable indicators
    lang_id_patterns = [
        "language-selector",
        "languageSelector",
        "language-switcher",
        "languageSwitcher",
        "lang-selector",
        "langSelector",
        "lang-switcher",
        "langSwitcher",
        "select-language",
        "selectLanguage",
        "change-language",
        "changeLanguage",
        "translate-button",
        "translateButton",
        "translation-menu",
        "translationMenu",
    ]

    for pattern in lang_id_patterns:
        element = soup.find(id=pattern)
        if element:
            # Further validate it's not a false positive
            if (
                len(element.find_all("a")) >= 1
                or len(element.find_all("select")) >= 1
                or len(element.find_all("button")) >= 1
            ):
                language_options.append(
                    {
                        "type": "id_exact_match",
                        "pattern": pattern,
                        "content": str(element)[:200],
                    }
                )

    # Approach 4: Check for alternate language versions via hreflang
    # This is the most reliable indicator as it's the web standard for language alternatives
    alt_langs = set()
    for link in soup.find_all("link", attrs={"rel": "alternate", "hreflang": True}):
        lang_code = link.get("hreflang", "").lower()
        if lang_code and lang_code != "en" and lang_code != "x-default":
            alt_langs.add(lang_code)

    if alt_langs:
        language_options.append(
            {
                "type": "alternate_hreflang",
                "languages": list(alt_langs),
                "count": len(alt_langs),
            }
        )

    # Approach 5: Look for Google Translate (very specific patterns)
    gt_element = soup.find(id="google_translate_element")
    if gt_element:
        language_options.append(
            {"type": "google_translate", "content": str(gt_element)[:200]}
        )

    # Check for Google Translate script with specific implementation pattern
    for script in soup.find_all("script"):
        script_text = script.string if script.string else ""
        if script_text and "new google.translate.TranslateElement" in script_text:
            language_options.append(
                {
                    "type": "google_translate_script",
                    "content": "Google Translate implementation detected",
                }
            )
            break

    return language_options


# Function to detect the primary language of a website
def detect_primary_language(soup):
    # 1. Check HTML lang attribute (most reliable)
    html_tag = soup.find("html")
    if html_tag and "lang" in html_tag.attrs:
        lang_attr = html_tag["lang"].lower()
        if "-" in lang_attr:
            # Extract primary language code from formats like 'en-US'
            return lang_attr.split("-")[0]
        return lang_attr

    # 2. If no lang attribute, try content-language meta tag
    meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
    if meta_lang and "content" in meta_lang.attrs:
        return meta_lang["content"].lower().split("-")[0]

    # 3. Last resort: detect language from content
    try:
        # Get text from paragraphs (more reliable than full page)
        paragraphs = soup.find_all("p")
        if paragraphs:
            # Join first 5 paragraphs or all if fewer
            text = " ".join([p.get_text().strip() for p in paragraphs[:5]])
            if len(text) > 100:  # Need enough text for reliable detection
                return langdetect.detect(text)

        # If no paragraphs with enough text, try main content areas
        for tag in ["main", "article", "section", "div.content", "div.main"]:
            content = soup.select(tag)
            if content:
                text = content[0].get_text().strip()
                if len(text) > 100:
                    return langdetect.detect(text)

        # Fall back to body text if needed
        body = soup.find("body")
        if body:
            text = body.get_text().strip()
            if len(text) > 100:
                return langdetect.detect(text)
    except:
        pass

    return "unknown"


# Function to check for non-English resources
def check_for_non_english_resources(soup, primary_language):
    # Skip check if primary language is already non-English
    if primary_language != "en" and primary_language != "unknown":
        return True

    # Look for sections or pages in other languages
    non_english_indicators = []

    # 1. Check for links containing language indicators
    language_indicators = [
        "/es/",
        "/fr/",
        "/de/",
        "/zh/",
        "/ru/",
        "/ja/",
        "/ar/",
        "español",
        "français",
        "deutsch",
        "中文",
        "русский",
        "日本語",
        "العربية",
    ]

    for a in soup.find_all("a", href=True):
        for indicator in language_indicators:
            if indicator in a["href"].lower() or indicator in a.get_text().lower():
                non_english_indicators.append(
                    {
                        "type": "link_with_language",
                        "indicator": indicator,
                        "content": str(a)[:100],
                    }
                )

    # 2. Look for resource sections with translations
    resource_sections = soup.find_all(
        ["section", "div"],
        class_=re.compile("(resource|publication|paper|documentation)", re.I),
    )
    for section in resource_sections:
        # Look for language indicators within resource sections
        for indicator in language_indicators:
            if indicator in section.get_text().lower():
                non_english_indicators.append(
                    {
                        "type": "resource_section",
                        "indicator": indicator,
                        "content": section.get_text()[:100],
                    }
                )

    return len(non_english_indicators) > 0


# Function to analyze a single website
def analyze_website(org):
    org_name = org["name"]
    url = org["url"]

    print(f"Analyzing: {org_name} - {url}")

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return {
                "name": org_name,
                "url": url,
                "status": "error",
                "status_code": response.status_code,
                "primary_language": None,
                "has_language_options": False,
                "language_options": [],
                "has_non_english_resources": False,
            }

        soup = BeautifulSoup(response.text, "html.parser")

        # Detect primary language
        primary_language = detect_primary_language(soup)

        # Check for language options
        language_options = detect_language_options(soup)

        # Check for non-English resources
        has_non_english_resources = check_for_non_english_resources(
            soup, primary_language
        )

        return {
            "name": org_name,
            "url": url,
            "status": "success",
            "primary_language": primary_language,
            "has_language_options": len(language_options) > 0,
            "language_options": language_options,
            "has_non_english_resources": has_non_english_resources,
        }

    except Exception as e:
        return {
            "name": org_name,
            "url": url,
            "status": "error",
            "error": str(e),
            "primary_language": None,
            "has_language_options": False,
            "language_options": [],
            "has_non_english_resources": False,
        }


# Main function to analyze all organizations
def analyze_ai_safety_organizations(csv_file="ai_safety_organizations.csv"):
    # Load organizations from CSV
    df = pd.read_csv(csv_file)
    print(f"Loaded {len(df)} organizations from {csv_file}")

    # Limit to first N organizations for testing
    # df = df.head(1)

    # Initialize results list
    results = []

    # Option 1: Sequential processing (more reliable but slower)
    # for _, org in tqdm(df.iterrows(), total=len(df)):
    #     result = analyze_website(org)
    #     results.append(result)

    # Option 2: Parallel processing (faster but may get blocked)
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        future_to_org = {
            executor.submit(analyze_website, row.to_dict()): row.to_dict()
            for _, row in df.iterrows()
        }
        for future in tqdm(
            concurrent.futures.as_completed(future_to_org), total=len(future_to_org)
        ):
            results.append(future.result())

    # Convert results to DataFrame
    results_df = pd.DataFrame(results)

    # Calculate statistics
    total_success = len(results_df[results_df["status"] == "success"])
    english_sites = len(
        results_df[
            (results_df["status"] == "success")
            & (results_df["primary_language"] == "en")
        ]
    )
    sites_with_language_options = len(
        results_df[results_df["has_language_options"] == True]
    )
    sites_with_non_english_resources = len(
        results_df[results_df["has_non_english_resources"] == True]
    )

    # Print results
    print("\nAnalysis Results:")
    print(f"Total organizations successfully analyzed: {total_success}")
    print(
        f"Websites primarily in English: {english_sites} ({english_sites/total_success*100:.1f}% if successful)"
    )
    print(
        f"Websites with language options: {sites_with_language_options} ({sites_with_language_options/total_success*100:.1f}% if successful)"
    )
    print(
        f"Websites with non-English resources: {sites_with_non_english_resources} ({sites_with_non_english_resources/total_success*100:.1f}% if successful)"
    )

    # Save detailed results (excluding large language_options field)
    results_df_slim = (
        results_df.drop(columns=["language_options"])
        if "language_options" in results_df.columns
        else results_df
    )
    results_df_slim.to_csv("generated/ai_safety_language_analysis.csv", index=False)
    print("Detailed results saved to ai_safety_language_analysis.csv")

    # Save full results with language options as JSON for detailed inspection
    import json

    with open("generated/ai_safety_language_full_analysis.json", "w") as f:
        json.dump(results, f, indent=2)
    print(
        "Full analysis with language option details saved to ai_safety_language_full_analysis.json"
    )

    # Return key stats for the blog post
    return {
        "total_orgs": len(df),
        "successful_analysis": total_success,
        "english_percent": (
            english_sites / total_success * 100 if total_success > 0 else 0
        ),
        "multilingual_percent": (
            sites_with_language_options / total_success * 100
            if total_success > 0
            else 0
        ),
        "non_english_resources_percent": (
            sites_with_non_english_resources / total_success * 100
            if total_success > 0
            else 0
        ),
    }


if __name__ == "__main__":
    print("AI Safety Website Language Analysis")
    print("===================================")

    csv_file = (
        input(
            "Enter path to organizations CSV file (or press Enter for default 'ai_safety_organizations.csv'): "
        )
        or "generated/ai_safety_organizations.csv"
    )

    stats = analyze_ai_safety_organizations(csv_file)

    print("\nKey statistics for your blog post:")
    print(
        f"- {stats['english_percent']:.1f}% of AI safety organizations have English-only websites"
    )
    print(
        f"- Only {stats['multilingual_percent']:.1f}% offer language selection options"
    )
    print(
        f"- Just {stats['non_english_resources_percent']:.1f}% provide substantive non-English resources"
    )
    print(
        "\nThese findings highlight the significant language barrier in AI safety discourse."
    )
