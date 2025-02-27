import pandas as pd

# Load the CSV file
df = pd.read_csv("generated/ai_safety_language_analysis.csv")
print(f"Loaded {len(df)} organizations")

# Calculate statistics
total_success = len(df[df["status"] == "success"])
english_sites = len(df[(df["status"] == "success") & (df["primary_language"] == "en")])
sites_with_language_options = len(df[df["has_language_options"] == True])
sites_with_non_english_resources = len(df[df["has_non_english_resources"] == True])

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

# Return key stats for the blog post
stats = {
    "total_orgs": len(df),
    "successful_analysis": total_success,
    "english_percent": english_sites / total_success * 100 if total_success > 0 else 0,
    "multilingual_percent": (
        sites_with_language_options / total_success * 100 if total_success > 0 else 0
    ),
    "non_english_resources_percent": (
        sites_with_non_english_resources / total_success * 100
        if total_success > 0
        else 0
    ),
}

print("\nKey statistics for your blog post:")
print(f"- Analyzed {stats['total_orgs']} AI safety organizations")
print(
    f"- {stats['english_percent']:.1f}% of AI safety organizations have English-only websites"
)
print(f"- Only {stats['multilingual_percent']:.1f}% offer language selection options")
print(
    f"- Just {stats['non_english_resources_percent']:.1f}% provide substantive non-English resources"
)
print(
    "\nThese findings highlight the significant language barrier in AI safety discourse."
)
