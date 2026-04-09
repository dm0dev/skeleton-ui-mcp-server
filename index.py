import json
import os
import re
from pathlib import Path

import httpx

try:
    from slugify import slugify
except ImportError:
    def slugify(text):
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        return re.sub(r'[-\s]+', '-', text).strip('-')

BASE_URL = "https://www.skeleton.dev/"
THEMES_API_URL = "https://api.github.com/repos/skeletonlabs/skeleton/contents/packages/skeleton/src/themes?ref=main"
RAW_THEME_URL = "https://raw.githubusercontent.com/skeletonlabs/skeleton/main/packages/skeleton/src/themes/"
STATIC_DIR = Path(__file__).parent / "skeleton_ui_mcp_server" / "static"
os.environ["REFRESH_INDEX"] = "1"


def parse_markdown(content: str):
    # Find all svelte code blocks
    examples = re.findall(r"```svelte\n(.*?)\n```", content, re.DOTALL)

    # Simple regex for headings to build outline and sections
    lines = content.split('\n')
    sections = {}
    outline = []

    current_heading = None
    current_content = []

    for line in lines:
        h_match = re.match(r"^(#{1,6})\s+(.*)$", line)
        if h_match:
            if current_heading:
                sections[current_heading] = '\n'.join(current_content).strip()

            level = len(h_match.group(1))
            current_heading = h_match.group(2).strip()
            outline.append({"heading": current_heading, "level": level})
            current_content = [line]
        else:
            current_content.append(line)

    if current_heading:
        sections[current_heading] = '\n'.join(current_content).strip()

    return outline, examples, sections


def refresh_index():
    llms_txt = httpx.get(BASE_URL + "llms.txt").text
    found_svelte = False
    with open(STATIC_DIR / '_llms.txt', 'w+') as f:
        for l in llms_txt.split('\n'):
            if found_svelte:
                f.write(l)
                f.write('\n')
                continue
            if not found_svelte and l.strip().startswith("## Svelte"):
                found_svelte = True
                continue

    index = {}
    with open(STATIC_DIR / '_llms.txt') as f:
        current_group: str = ""
        for line in f:
            if line.strip().startswith("### "):
                current_group = line.strip().replace("### ", "")
                index[current_group] = {}
            if line.strip().startswith("- ["):
                title, url = line.strip().split("](/")
                title = title.replace("- [", "")
                url = BASE_URL + url.replace(")", "")
                print(f"Fetching {title} from {url}")
                r = httpx.get(url)
                index[current_group][title] = {'url': url, 'content': r.text}
    with open(STATIC_DIR / '_index.json', 'w+') as f:
        print(f"Writing index to _index.json")
        json.dump(index, f, indent=2)


def parse_theme_css(css_content: str):
    theme_info = {
        "fonts": {},
        "colors": {},
        "radius": {},
        "spacing": {},
        "border": {}
    }

    # Extract fonts
    font_base = re.search(r"--base-font-family:\s*([^;]+);", css_content)
    if font_base:
        theme_info["fonts"]["base"] = font_base.group(1).strip()
    font_heading = re.search(r"--heading-font-family:\s*([^;]+);", css_content)
    if font_heading:
        theme_info["fonts"]["heading"] = font_heading.group(1).strip()

    # Extract radius
    radius_base = re.search(r"--radius-base:\s*([^;]+);", css_content)
    if radius_base:
        theme_info["radius"]["base"] = radius_base.group(1).strip()
    radius_container = re.search(r"--radius-container:\s*([^;]+);", css_content)
    if radius_container:
        theme_info["radius"]["container"] = radius_container.group(1).strip()

    # Extract spacing
    spacing = re.search(r"--spacing:\s*([^;]+);", css_content)
    if spacing:
        theme_info["spacing"]["base"] = spacing.group(1).strip()

    # Extract border info
    border_width = re.search(r"--default-border-width:\s*([^;]+);", css_content)
    if border_width:
        theme_info["border"]["width"] = border_width.group(1).strip()
    divide_width = re.search(r"--default-divide-width:\s*([^;]+);", css_content)
    if divide_width:
        theme_info["border"]["divide"] = divide_width.group(1).strip()
    ring_width = re.search(r"--default-ring-width:\s*([^;]+);", css_content)
    if ring_width:
        theme_info["border"]["ring"] = ring_width.group(1).strip()

    # Extract colors (all --color-*-500)
    color_matches = re.finditer(r"--color-([a-z-]+)-500:\s*([^;]+);", css_content)
    for match in color_matches:
        color_name = match.group(1)
        color_value = match.group(2).strip()
        theme_info["colors"][color_name] = color_value

    return theme_info


def refresh_themes():
    print("Fetching themes list from GitHub...")
    r = httpx.get(THEMES_API_URL)
    if r.status_code != 200:
        print(f"Failed to fetch themes list: {r.status_code}")
        return

    themes_list = r.json()
    themes_data = {}

    for theme_file in themes_list:
        name = theme_file["name"]
        if not name.endswith(".css"):
            continue
        
        theme_name = name.replace(".css", "")
        print(f"Fetching theme: {theme_name}")
        
        tr = httpx.get(RAW_THEME_URL + name)
        if tr.status_code == 200:
            themes_data[theme_name] = parse_theme_css(tr.text)
        else:
            print(f"Failed to fetch theme {theme_name}: {tr.status_code}")

    with open(STATIC_DIR / '_themes.json', 'w+') as f:
        print("Writing themes to _themes.json")
        json.dump(themes_data, f, indent=2)


def main():
    if os.environ.get("REFRESH_INDEX"):
        refresh_index()
        refresh_themes()
    
    with open(STATIC_DIR / '_index.json') as f:
        index = json.load(f)
    
    list_all = []
    for group, titles in index.items():
        for title, c in titles.items():
            filename = slugify(f"{group}-{title}")
            content = c['content']
            outline, examples, sections = parse_markdown(content)

            excerpt = [x for x in content.split('\n')[:4] if (x.strip() and not x.strip().startswith('# '))]
            list_all.append(
                {'title': title, 'excerpt': excerpt, 'group': group, 'url': c['url'], 'slug': f"{filename}"})

            with open(STATIC_DIR / f'{filename}.json', 'w+') as f:
                c['title'] = title
                c['group'] = group
                c['outline'] = outline
                c['examples'] = examples
                c['sections'] = sections
                json.dump(c, f, indent=2)
    
    with open(STATIC_DIR / '_index_list.json', 'w+') as f:
        json.dump(list_all, f, indent=2)


if __name__ == "__main__":
    main()
