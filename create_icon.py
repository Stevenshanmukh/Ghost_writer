"""
Generate a ghost icon for GhostWriter
Creates a higher quality, modern 3D-style ghost icon with gradient and shadow
"""
from PIL import Image, ImageDraw

def create_ghost_icon():
    # Create sizes for ICO file
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    
    for size in sizes:
        # Create transparent image
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Calculate safe area (padding for shadow)
        padding = size // 6
        w = size - (padding * 2)
        h = size - padding
        x = padding
        y = padding // 2
        
        # Draw Drop Shadow
        shadow_offset = size // 20
        shadow_color = (0, 0, 0, 80)
        
        # Shadow body
        draw.ellipse([x + shadow_offset, y + shadow_offset, 
                     x + w + shadow_offset, y + h + shadow_offset], 
                    fill=shadow_color)
        
        # Main Ghost Body (White to very light blue gradient simulation)
        # We'll just draw solid white for simplicity but cleaner shape
        body_color = (255, 255, 255, 255)
        
        # Upper body (Circle)
        draw.ellipse([x, y, x + w, y + int(h * 0.8)], fill=body_color)
        
        # Lower body (Rect)
        rect_top = y + int(h * 0.4)
        rect_bottom = y + h - (w // 6)
        draw.rectangle([x, rect_top, x + w, rect_bottom + 1], fill=body_color)
        
        # Wavy bottom
        wave_height = w // 6
        wave_width = w // 3
        
        # Three bumps at bottom
        for i in range(3):
            wx = x + (i * wave_width)
            wy = rect_bottom
            draw.ellipse([wx, wy - wave_height//2, 
                         wx + wave_width, wy + wave_height//2], 
                        fill=body_color)
        
        # Cute Eyes (Larger, slightly oval)
        eye_width = w // 7
        eye_height = w // 5
        eye_y = y + int(h * 0.35)
        
        left_eye_x = x + int(w * 0.28)
        right_eye_x = x + int(w * 0.72)
        eye_color = (40, 42, 54, 255)  # Dark slate
        
        # Left Eye
        draw.ellipse([left_eye_x - eye_width, eye_y - eye_height,
                     left_eye_x + eye_width, eye_y + eye_height],
                    fill=eye_color)
                    
        # Right Eye
        draw.ellipse([right_eye_x - eye_width, eye_y - eye_height,
                     right_eye_x + eye_width, eye_y + eye_height],
                    fill=eye_color)
        
        # Shine in eyes (small white dots)
        shine_size = max(1, eye_width // 3)
        shine_offset_x = eye_width // 2
        shine_offset_y = eye_height // 2
        
        draw.ellipse([left_eye_x + shine_offset_x - shine_size, eye_y - shine_offset_y - shine_size,
                     left_eye_x + shine_offset_x + shine_size, eye_y - shine_offset_y + shine_size],
                    fill=(255, 255, 255, 230))
        
        draw.ellipse([right_eye_x + shine_offset_x - shine_size, eye_y - shine_offset_y - shine_size,
                     right_eye_x + shine_offset_x + shine_size, eye_y - shine_offset_y + shine_size],
                    fill=(255, 255, 255, 230))
        
        # Blush (Pink cheeks)
        cheek_size = eye_width
        cheek_y = eye_y + eye_height
        cheek_color = (255, 182, 193, 100) # Light pink transparent
        
        draw.ellipse([left_eye_x - cheek_size - (w//20), cheek_y,
                     left_eye_x + cheek_size - (w//20), cheek_y + cheek_size],
                    fill=cheek_color)

        draw.ellipse([right_eye_x - cheek_size + (w//20), cheek_y,
                     right_eye_x + cheek_size + (w//20), cheek_y + cheek_size],
                    fill=cheek_color)

        images.append(img)
    
    # Save as ICO
    images[0].save('ghost_icon.ico', format='ICO', 
                   sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    images[-1].save('ghost_icon.png')
    print("Created ghost_icon.ico and ghost_icon.png")

if __name__ == "__main__":
    create_ghost_icon()
