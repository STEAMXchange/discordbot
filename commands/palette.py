"""
Palette command - Gets the palette for the given image.
"""

import io
import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont
from nextcord import Interaction, File


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="palette", description="Gets the palette for the given image.")
    async def palette(interaction: Interaction, file):
        await interaction.response.defer()

        try:
            # Download the image
            image_bytes = await file.read()
            image = Image.open(io.BytesIO(image_bytes))

            # Convert image to RGB mode and resize for efficiency
            image = image.convert("RGB")
            image = image.resize((150, 150))  # Slightly larger for better color sampling

            # Prepare the image data for k-means clustering
            pixels = np.float32(image).reshape(-1, 3)

            # Use k-means clustering to find dominant colors
            num_colors = 8
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 200, .1)
            flags = cv2.KMEANS_RANDOM_CENTERS
            _, labels, palette_colors = cv2.kmeans(pixels, num_colors, None, criteria, 10, flags)

            # Calculate color frequencies
            _, counts = np.unique(labels, return_counts=True)
            
            # Sort colors by frequency
            colors_sorted = [(color, count) for color, count in zip(palette_colors, counts)]
            colors_sorted.sort(key=lambda x: x[1], reverse=True)
            
            # Extract just the colors
            top_colors = [tuple(map(int, color)) for color, _ in colors_sorted]

            # Generate a preview image of the palette
            palette_width = 800
            palette_height = 100
            palette_img = Image.new("RGB", (palette_width, palette_height))
            draw = ImageDraw.Draw(palette_img)
            
            # Add color blocks and hex codes
            block_width = palette_width // len(top_colors)
            font = ImageFont.load_default(size=18)
            
            for i, color in enumerate(top_colors):
                # Draw color block
                x0 = i * block_width
                x1 = x0 + block_width
                draw.rectangle([x0, 0, x1, palette_height], fill=color)
                
                # Add hex code
                hex_code = '#{:02x}{:02x}{:02x}'.format(*color)
                # Calculate text position (centered in block)
                text_bbox = draw.textbbox((0, 0), hex_code, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = x0 + (block_width - text_width) // 2
                text_y = (palette_height - text_height) // 2
                draw.text((text_x, text_y), hex_code, fill='white' if sum(color) < 384 else 'black', font=font)

            # Convert preview image to bytes
            img_bytes = io.BytesIO()
            palette_img.save(img_bytes, format="PNG")
            img_bytes.seek(0)
            
            # Send the palette
            result_file = File(img_bytes, "palette.png")
            await interaction.followup.send("Here is the color palette:", file=result_file)
            
        except Exception as e:
            await interaction.followup.send(f"Error processing image: {str(e)}")
