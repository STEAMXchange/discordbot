"""
QC command - Runs text quality control on a Canva URL.
"""

from nextcord import Interaction
from qc_helpers import (
    extract_text_and_fonts, map_fonts, categorize_text, 
    calculate_score, EXPECTED_FONTS, EXPECTED_COLORS
)


def setup(bot, utils):
    """Setup function to register the command with the bot."""
    
    @bot.slash_command(name="qc", description="Runs text quality control on a Canva URL.")
    async def qc(interaction: Interaction, url: str):
        """Manually runs QC on a Canva URL."""
        await interaction.response.defer()

        # Check if the URL ends with `/edit`, change it to `/view`
        if url.endswith("/edit"):
            url = url.replace("/edit", "/view")
            print(f"Modified URL to: {url}")
        
        print(f"Found Canva URL: {url}")

        extracted_data = extract_text_and_fonts(url)
        final_data = map_fonts(extracted_data["text_data"], extracted_data["fonts"])
        categorized_text = categorize_text(final_data)

        total_score = 0
        total_possible_score = 0
        report = "## **Quality Control Report**\n"

        for category, items in categorized_text.items():
            report += f"\n{category}:\n"
            for item, font_name in items:
                expected_font = EXPECTED_FONTS.get(category, "Unknown")
                expected_color = EXPECTED_COLORS.get(category, "Unknown")
                match_status = "✅" if font_name == expected_font else "❌"
                score = calculate_score(font_name, expected_font, item['color'], expected_color)
                total_score += score
                total_possible_score += 10

                report += f"• `{item['text']}` ({item['size']}px) | Font: {font_name} {match_status}\n"

        final_score = (total_score / total_possible_score) * 100 if total_possible_score else 0
        report += f"\nFinal Score: {final_score:.2f}/100 🎯"

        await interaction.followup.send(report)
