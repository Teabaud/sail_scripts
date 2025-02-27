# SAIL Scripts

Scripts for analyzing language accessibility in AI safety organizations.

## Overview

This project provides tools to analyze the language accessibility of AI safety organization websites. It helps identify how many AI safety resources are available in languages other than English, highlighting potential barriers to global participation in AI safety discourse.

## Features

- Scrape AI safety organization websites from the [AI Safety Map](https://map.aisafety.world/)
- Analyze websites for language options and non-English content
- Generate statistics on multilingual accessibility in the AI safety field
- Process results for publication and research

## Installation

This project uses Poetry for dependency management.

```bash
# Clone the repository
git clone https://github.com/yourusername/sail-scripts.git
cd sail-scripts

# Install dependencies
poetry install
```

## Usage

### 1. Extract AI Safety Organizations

Scrape the AI Safety Map to get a list of organizations:

```bash
poetry run python -m sail_scripts.ais_map_orgs
```

This will:
- Visit the AI Safety Map website
- Extract organization links
- Save results to `generated/ai_safety_organizations.csv`
- Take a screenshot (for debugging) at `generated/aisafety_map.png`

### 2. Analyze Language Accessibility

Once you have the list of organizations, analyze their websites for language options:

```bash
poetry run python -m sail_scripts.translation_coverage
```

This will:
- Visit each organization's website
- Detect the primary language
- Check for language selection options
- Look for non-English resources
- Save results to:
  - `generated/ai_safety_language_analysis.csv` (summary stats)
  - `generated/ai_safety_language_full_analysis.json` (detailed data)

### 3. Generate Statistics

Print statistics about the language accessibility analysis:

```bash
poetry run python -m sail_scripts.print_stats
```

## Technical Details

### Dependencies

- `requests` & `beautifulsoup4`: Web scraping
- `selenium`: Browser automation for JavaScript-heavy websites
- `langdetect`: Language detection
- `pandas`: Data manipulation
- `tqdm`: Progress bars

### Analysis Methodology

The language analysis includes:

1. **Primary language detection**:
   - HTML `lang` attribute
   - Content-language meta tag
   - Text content analysis using langdetect

2. **Language options detection**:
   - Language selection dropdowns
   - Language navigation menus
   - Alternate language links (hreflang)
   - Google Translate integration

3. **Non-English resources detection**:
   - Links to content in other languages
   - Language indicators in resource sections

## Project Structure

```
sail-scripts/
├── sail_scripts/
│   ├── __init__.py
│   ├── ais_map_orgs.py        # Extract organizations from AI Safety Map
│   ├── translation_coverage.py # Analyze website language accessibility
│   └── print_stats.py         # Generate summary statistics
├── tests/
│   └── __init__.py
├── pyproject.toml             # Project dependencies
├── .gitignore
└── README.md
```

## License

This project is licensed under the MIT License

## Author

Thibaud Veron