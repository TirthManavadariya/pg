"""
generate_images.py
Automated asset generator for ZoloStays-inspired PG Discovery platform.
Creates high quality interior property images and mockups for room types, bathrooms, dining, and common areas.
"""

import os
import requests
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIRS = [
    os.path.join(BASE_DIR, 'static', 'images', 'properties'),
    os.path.join(BASE_DIR, 'frontend', 'static', 'images', 'properties'),
]

# Ensure directories exist
for d in IMAGE_DIRS:
    os.makedirs(d, exist_ok=True)

# Curated high-res Unsplash photography links for Co-living / PG rooms
CURATED_UNSPLASH_IMAGES = {
    "bedroom_luxury_1": "https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=800&q=80",
    "bedroom_modern_2": "https://images.unsplash.com/photo-1522771739844-6a9f6d5f14af?auto=format&fit=crop&w=800&q=80",
    "bedroom_cozy_3": "https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?auto=format&fit=crop&w=800&q=80",
    "bedroom_double_4": "https://images.unsplash.com/photo-1540518614846-7ede433c4ef0?auto=format&fit=crop&w=800&q=80",
    "bedroom_single_5": "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=800&q=80",
    "bedroom_scandi_6": "https://images.unsplash.com/photo-1512917774080-9991f1c4c750?auto=format&fit=crop&w=800&q=80",
    "bedroom_minimal_7": "https://images.unsplash.com/photo-1586023492125-27b2c045efd7?auto=format&fit=crop&w=800&q=80",
    "bedroom_studio_8": "https://images.unsplash.com/photo-1502672260266-1c1ef2d93688?auto=format&fit=crop&w=800&q=80",
    "living_lounge_1": "https://images.unsplash.com/photo-1554995207-c18c203602cb?auto=format&fit=crop&w=800&q=80",
    "living_lounge_2": "https://images.unsplash.com/photo-1567496898669-ee935f5f647a?auto=format&fit=crop&w=800&q=80",
    "living_lounge_3": "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?auto=format&fit=crop&w=800&q=80",
    "dining_kitchen_1": "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=800&q=80",
    "dining_kitchen_2": "https://images.unsplash.com/photo-1565183997392-2f6f122e5912?auto=format&fit=crop&w=800&q=80",
    "washroom_clean_1": "https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=800&q=80",
    "washroom_clean_2": "https://images.unsplash.com/photo-1620626011761-996317b8d101?auto=format&fit=crop&w=800&q=80",
    "study_workspace_1": "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?auto=format&fit=crop&w=800&q=80",
    "study_workspace_2": "https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=800&q=80",
    "balcony_view_1": "https://images.unsplash.com/photo-1513694203232-719a280e022f?auto=format&fit=crop&w=800&q=80",
}

def create_pillow_fallback(name, title, category, target_path, width=800, height=520):
    """Generates an ultra-crisp, stylized interior mockup placeholder image using Pillow."""
    palettes = {
        "bedroom": [((245, 247, 250), (220, 226, 235)), ((79, 70, 229), (99, 102, 241)), "#4f46e5"],
        "living": [((248, 250, 252), (226, 232, 240)), ((13, 148, 136), (20, 184, 166)), "#0d9488"],
        "dining": [((255, 251, 235), (254, 243, 199)), ((217, 119, 6), (245, 158, 11)), "#d97706"],
        "washroom": [((240, 249, 255), (224, 242, 254)), ((2, 132, 199), (14, 165, 233)), "#0284c7"],
        "study": [((245, 243, 255), (237, 233, 254)), ((124, 58, 237), (139, 92, 246)), "#7c3aed"],
        "balcony": [((240, 253, 244), (220, 252, 231)), ((22, 163, 74), (34, 197, 94)), "#16a34a"],
    }
    
    cat_key = "bedroom"
    for k in palettes:
        if k in category.lower() or k in name.lower():
            cat_key = k
            break
            
    (bg_top, bg_bot), (acc1, acc2), hex_color = palettes[cat_key]
    
    img = Image.new("RGB", (width, height), bg_top)
    draw = ImageDraw.Draw(img)
    
    # Draw subtle gradient / architectural room geometric shapes
    for y in range(height):
        r = int(bg_top[0] + (bg_bot[0] - bg_top[0]) * (y / height))
        g = int(bg_top[1] + (bg_bot[1] - bg_top[1]) * (y / height))
        b = int(bg_top[2] + (bg_bot[2] - bg_top[2]) * (y / height))
        draw.line([(0, y), (width, y)], fill=(r, g, b))
        
    # Draw modern interior stylized geometric walls / perspective
    draw.polygon([(0, 0), (width * 0.25, 0), (width * 0.15, height), (0, height)], fill=(230, 235, 245))
    draw.polygon([(width * 0.75, 0), (width, 0), (width, height), (width * 0.85, height)], fill=(230, 235, 245))
    
    # Floor perspective
    draw.polygon([(0, int(height * 0.68)), (width, int(height * 0.68)), (width, height), (0, height)], fill=(215, 222, 232))
    
    # Main furniture block (Bed / Sofa / Table silhouette)
    fx1 = int(width * 0.22)
    fy1 = int(height * 0.45)
    fx2 = int(width * 0.78)
    fy2 = int(height * 0.78)
    draw.rounded_rectangle([fx1, fy1, fx2, fy2], radius=16, fill=(255, 255, 255), outline=(203, 213, 225), width=2)
    
    # Cushion / Accent element
    draw.rounded_rectangle([fx1 + 25, fy1 + 20, fx2 - 25, fy1 + 85], radius=10, fill=acc1)
    
    # Badge Pill
    pill_x1, pill_y1 = int(width * 0.35), int(height * 0.12)
    pill_x2, pill_y2 = int(width * 0.65), int(height * 0.20)
    draw.rounded_rectangle([pill_x1, pill_y1, pill_x2, pill_y2], radius=20, fill=(255, 255, 255), outline=(226, 232, 240), width=2)
    
    # Text labels
    # Use default font or PIL font
    try:
        font_large = ImageFont.truetype("arial.ttf", 26)
        font_small = ImageFont.truetype("arial.ttf", 16)
        font_badge = ImageFont.truetype("arial.ttf", 15)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_badge = ImageFont.load_default()
        
    draw.text((width // 2, pill_y1 + 10), f"★ VERIFIED LIVING SPACE", fill=acc1, font=font_badge, anchor="mm")
    draw.text((width // 2, int(height * 0.86)), title.upper(), fill=(15, 23, 42), font=font_large, anchor="mm")
    draw.text((width // 2, int(height * 0.93)), f"Roomee-Standard Premium Stay • 100% Fully Furnished", fill=(100, 116, 139), font=font_small, anchor="mm")
    
    img.save(target_path, "JPEG", quality=90)


def download_or_generate_images():
    print(f"Starting image asset generation across {len(IMAGE_DIRS)} target directories...")
    
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    for key, url in CURATED_UNSPLASH_IMAGES.items():
        filename = f"{key}.jpg"
        
        # Download once to first dir
        primary_path = os.path.join(IMAGE_DIRS[0], filename)
        downloaded = False
        
        try:
            print(f"Fetching {filename} from Unsplash...")
            resp = requests.get(url, headers=headers, timeout=8)
            if resp.status_code == 200:
                with open(primary_path, 'wb') as f:
                    f.write(resp.content)
                downloaded = True
                print(f"  [OK] Downloaded {filename}")
        except Exception as e:
            print(f"  ! Network download error for {filename}: {e}, creating high quality Pillow rendering...")
            
        if not downloaded or not os.path.exists(primary_path):
            title_text = key.replace('_', ' ').title()
            create_pillow_fallback(key, title_text, key.split('_')[0], primary_path)
            print(f"  [OK] Created Pillow fallback for {filename}")
            
        # Copy / Sync to all other target directories
        for target_dir in IMAGE_DIRS[1:]:
            dest_path = os.path.join(target_dir, filename)
            try:
                with open(primary_path, 'rb') as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())
            except Exception as e:
                print(f"Error copying to {dest_path}: {e}")

    print(f"All {len(CURATED_UNSPLASH_IMAGES)} property assets successfully generated & synchronized!")

if __name__ == "__main__":
    download_or_generate_images()
