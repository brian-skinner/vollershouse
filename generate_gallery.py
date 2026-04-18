import os
from pathlib import Path
from PIL import Image

# --- Configuration ---
SOURCE_DIR = Path(".") 
THUMB_DIR = Path("thumbnails")
OUTPUT_HTML = Path("index.html")
MAX_SIZE = (300, 300)

# Ensure the root thumbnail directory exists before processing
THUMB_DIR.mkdir(exist_ok=True)

# --- HTML Template Setup ---
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Photo Directory Overview</title>
    <style>
        body { font-family: sans-serif; margin: 20px; background-color: #fcfcfc; }
        h2 { border-bottom: 2px solid #ccc; padding-bottom: 5px; margin-top: 40px; }
        .gallery { display: flex; flex-wrap: wrap; gap: 15px; }
        .thumbnail { max-width: 200px; height: auto; border: 1px solid #aaa; border-radius: 4px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
        /* Added cursor pointer to indicate the image is interactive */
        .thumbnail:hover { transform: scale(1.05); transition: 0.2s ease-in-out; cursor: pointer; }
    </style>
</head>
<body>
    <h1>Site Photo Overview</h1>
"""

# --- Directory Crawling & Path Isolation ---
all_files = list(SOURCE_DIR.rglob("*.jpg")) + list(SOURCE_DIR.rglob("*.jpeg"))
original_images = [f for f in all_files if THUMB_DIR.name not in f.parts and '.git' not in f.parts]

images_by_dir = {}
for img_path in original_images:
    parent_dir = str(img_path.parent)
    if parent_dir not in images_by_dir:
        images_by_dir[parent_dir] = []
    images_by_dir[parent_dir].append(img_path)

# --- Image Processing & Parallel Routing ---
for directory, images in sorted(images_by_dir.items()):
    heading = directory if directory != "." else "Root Directory"
    # Create a safe, unique ID for the Lightbox gallery instance based on the folder name
    gallery_id = heading.replace(" ", "_").replace("/", "_").replace("\\", "_")
    
    html_content += f"\n    <h2>Directory: {heading}</h2>\n    <div class='gallery'>\n"

    for img_path in sorted(images):
        rel_path = img_path.relative_to(SOURCE_DIR)
        thumb_path = THUMB_DIR / rel_path
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        
        if not thumb_path.exists():
            print(f"Processing 5MB original: Generating parallel thumbnail for {img_path}")
            try:
                with Image.open(img_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.thumbnail(MAX_SIZE)
                    img.save(thumb_path, "JPEG", quality=85)
            except Exception as e:
                print(f"System Error processing {img_path}: {e}")
        
        web_img_path = str(img_path).replace("\\", "/")
        web_thumb_path = str(thumb_path).replace("\\", "/")
        
        # Inject the data-fslightbox attribute to bind the image to the JavaScript handler
        # Note: target="_blank" has been removed so the browser does not open a new tab
        html_content += f"""
        <a data-fslightbox="{gallery_id}" href="{web_img_path}">
            <img src="{web_thumb_path}" class="thumbnail" alt="{img_path.name}">
        </a>"""
        
    html_content += "\n    </div>\n"

# --- Finalize and Write HTML ---
# Inject the fsLightbox CDN script immediately before closing the body tag
html_content += """
    <script src="https://cdnjs.cloudflare.com/ajax/libs/fslightbox/3.3.1/index.min.js"></script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\nExecution Complete. Parallel thumbnails generated in '{THUMB_DIR}/'. HTML saved to: {OUTPUT_HTML}")