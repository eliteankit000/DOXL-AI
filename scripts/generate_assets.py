"""Generate all favicon / icon / OG-image assets for DocXL AI"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFont

PUBLIC = os.path.join(os.path.dirname(__file__), '..', 'public')
APP_DIR = os.path.join(os.path.dirname(__file__), '..', 'app')
os.makedirs(PUBLIC, exist_ok=True)

BRAND_BLUE = (37, 99, 235)   # #2563eb
WHITE = (255, 255, 255)
DARK = (30, 41, 59)

def draw_logo_icon(size):
    """Draw a simple DX branded icon."""
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Blue rounded-ish rectangle background
    draw.rounded_rectangle([0, 0, size-1, size-1], radius=size//5, fill=BRAND_BLUE)
    # Draw "DX" text
    font_size = int(size * 0.42)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except:
        font = ImageFont.load_default()
    text = "DX"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (size - tw) // 2
    y = (size - th) // 2 - bbox[1]
    draw.text((x, y), text, fill=WHITE, font=font)
    return img

# Generate icons at various sizes
sizes = {
    'icon-16.png': 16,
    'icon.png': 32,
    'icon-192.png': 192,
    'icon-512.png': 512,
    'apple-icon.png': 180,
}

for fname, sz in sizes.items():
    icon = draw_logo_icon(sz)
    icon.save(os.path.join(PUBLIC, fname), 'PNG')
    # Also save in app dir for Next.js special files
    if fname in ('icon.png', 'apple-icon.png'):
        icon.save(os.path.join(APP_DIR, fname), 'PNG')

# Generate favicon.ico (multi-size)
ico_16 = draw_logo_icon(16)
ico_32 = draw_logo_icon(32)
ico_48 = draw_logo_icon(48)
ico_16.save(os.path.join(PUBLIC, 'favicon.ico'), format='ICO',
            sizes=[(16, 16), (32, 32), (48, 48)],
            append_images=[ico_32, ico_48])

# Also put logo.png in public
logo = draw_logo_icon(512)
logo.save(os.path.join(PUBLIC, 'logo.png'), 'PNG')

# Generate OG image (1200x630)
og = Image.new('RGB', (1200, 630), WHITE)
draw = ImageDraw.Draw(og)

# Blue gradient-like left bar
for i in range(500):
    r = int(37 + (i / 500) * 20)
    g = int(99 + (i / 500) * 30)
    b = int(235 - (i / 500) * 20)
    draw.line([(i, 0), (i, 630)], fill=(r, g, b))

# Logo icon on the left
logo_small = draw_logo_icon(180)
og.paste(logo_small, (160, 225), logo_small)

# Text on the right
try:
    font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
    font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 26)
    font_brand = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
except:
    font_title = ImageFont.load_default()
    font_sub = font_title
    font_brand = font_title

draw.text((560, 180), "Convert PDF to Excel", fill=DARK, font=font_title)
draw.text((560, 240), "in Seconds", fill=DARK, font=font_title)
draw.text((560, 330), "Powered by GPT-4o AI", fill=(100, 116, 139), font=font_sub)
draw.text((560, 380), "Free to try. No signup for first conversion.", fill=(100, 116, 139), font=font_sub)
draw.text((560, 460), "DocXL AI", fill=BRAND_BLUE, font=font_brand)

og.save(os.path.join(PUBLIC, 'og-image.png'), 'PNG')

print("All assets generated successfully!")
print(f"Files in {PUBLIC}:", os.listdir(PUBLIC))
