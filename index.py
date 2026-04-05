import json
import os
from pathlib import Path

import httpx
from slugify import slugify

BASE_URL = "https://www.skeleton.dev/"
STATIC_DIR = Path(__file__).parent / "skeleton_ui_mcp_server" / "static"
os.environ["REFRESH_INDEX"] = "1"

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

def main():
    if os.environ.get("REFRESH_INDEX"):
        refresh_index()
    with open(STATIC_DIR / '_index.json') as f:
        index = json.load(f)
    list_all = []
    for group, titles in index.items():
        for title, c in titles.items():
            filename = slugify(f"{group}-{title}")
            excerpt = [x for x in c['content'].split('\n')[:4] if (x.strip() and not x.strip().startswith('# '))]
            list_all.append({'title': title, 'excerpt': excerpt, 'group': group, 'url': c['url'], 'slug': f"{filename}"})
            with open(STATIC_DIR / f'{filename}.json', 'w+') as f:
                c['title'] = title
                c['group'] = group
                json.dump(c, f, indent=2)
    with open(STATIC_DIR / '_index_list.json', 'w+') as f:
        json.dump(list_all, f, indent=2)

if __name__ == "__main__":
    main()
