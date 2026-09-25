"""
Icon generator for Virtual Hand Mouse Pro.
Creates a futuristic hand-cursor icon in PNG and ICO formats.
"""

import os
from PIL import Image, ImageDraw

def generate_app_icon():
    os.makedirs("assets", exist_ok=True)
    size = (256, 256)
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer rounded glowing square background
    # Dark modern slate gradient effect
    draw.rounded_rectangle([(8, 8), (248, 248)], radius=56, fill=(18, 22, 32, 255), outline=(0, 210, 255, 255), width=6)
    
    # Inner subtle glow ring
    draw.rounded_rectangle([(18, 18), (238, 238)], radius=46, outline=(40, 100, 160, 180), width=3)

    # Stylized Cybernetic Hand & Mouse Pointer
    # Palm base
    draw.ellipse([(90, 130), (166, 200)], fill=(0, 180, 230, 240), outline=(255, 255, 255, 220), width=3)
    
    # Thumb
    draw.line([(100, 160), (70, 140), (80, 110)], fill=(0, 210, 255, 255), width=10)
    
    # Index finger pointing up (tracking cursor)
    draw.line([(110, 140), (110, 60)], fill=(0, 240, 255, 255), width=12)
    # Fingertip glow
    draw.ellipse([(100, 50), (120, 70)], fill=(255, 255, 255, 255), outline=(0, 210, 255, 255), width=3)

    # Middle finger
    draw.line([(130, 140), (130, 85)], fill=(0, 190, 220, 255), width=10)
    # Ring finger
    draw.line([(150, 145), (150, 105)], fill=(0, 170, 200, 255), width=9)
    # Pinky finger
    draw.line([(165, 155), (165, 125)], fill=(0, 150, 180, 255), width=8)

    # Glowing pinch pulse / target reticle between thumb and index
    draw.arc([(60, 45), (130, 115)], start=-45, end=90, fill=(255, 165, 0, 255), width=4)
    draw.ellipse([(88, 85), (96, 93)], fill=(255, 180, 0, 255))

    # Save PNG
    png_path = os.path.join("assets", "icon.png")
    img.save(png_path, "PNG")

    # Save ICO
    ico_path = os.path.join("assets", "icon.ico")
    img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
    print(f"[SUCCESS] Generated {png_path} and {ico_path}")

if __name__ == "__main__":
    generate_app_icon()
