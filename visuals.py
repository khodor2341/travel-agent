import requests
import re
import matplotlib.pyplot as plt
import streamlit as st

def get_unsplash_photos(destination, count=6):
    """Get free photos from LoremFlickr (no API key needed)."""
    query = destination.split(',')[0].strip().replace(' ', ',')
    photos = []
    for i in range(count):
        # LoremFlickr returns random Flickr photos by keyword
        url = f"https://loremflickr.com/800/600/{query}/all?lock={i}"
        photos.append(url)
    return photos

def parse_budget_data(text):
    """Extract numbers from budget section for chart."""
    data = {}
    patterns = {
        'Accommodation': r'[Aa]ccommodation.*?(\d+)',
        'Food': r'[Ff]ood.*?(\d+)',
        'Transport': r'[Tt]ransport.*?(\d+)',
        'Activities': r'[Aa]ctivities.*?(\d+)',
        'Buffer': r'[Bb]uffer.*?(\d+)',
    }
    for category, pattern in patterns.items():
        matches = re.findall(pattern, text)
        if matches:
            data[category] = sum(int(m) for m in matches[:2]) // len(matches[:2])
    return data

def render_budget_chart(budget_data, currency):
    """Create a matplotlib pie chart."""
    if not budget_data:
        return None
    
    fig, ax = plt.subplots(figsize=(6, 4))
    colors = ['#1E3A8A', '#3B82F6', '#60A5FA', '#93C5FD', '#DBEAFE']
    wedges, texts, autotexts = ax.pie(
        budget_data.values(), 
        labels=budget_data.keys(),
        autopct='%1.0f%%',
        colors=colors[:len(budget_data)],
        startangle=90
    )
    for autotext in autotexts:
        autotext.set_color('white')
        autotext.set_fontweight('bold')
    ax.set_title(f'Budget Breakdown ({currency})', fontsize=14, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig