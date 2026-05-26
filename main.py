import os
import asyncio
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

# Enable logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Conversion Formulas & Logic
def perform_conversion(value: float, category: str, direction: str) -> str:
    try:
        if category == "temp":
            if direction == "c_to_f":
                res = (value * 9/5) + 32
                return f"{value}°C = {res:.2f}°F"
            else:
                res = (value - 32) * 5/9
                return f"{value}°F = {res:.2f}°C"
                
        elif category == "weight":
            if direction == "kg_to_lbs":
                return f"{value} kg = {value * 2.20462:.2f} lbs"
            else:
                return f"{value} lbs = {value / 2.20462:.2f} kg"
                
        elif category == "length":
            if direction == "m_to_ft":
                return f"{value} m = {value * 3.28084:.2f} ft"
            else:
                return f"{value} ft = {value / 3.28084:.2f} m"
                
        elif category == "data":
            if direction == "gb_to_mb":
                return f"{value} GB = {value * 1024:.0f} MB"
            else:
                return f"{value} MB = {value / 1024:.4f} GB"
    except Exception as e:
        return "⚠️ Calculation error. Please try again."
    return "Unknown conversion."

# Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌡️ Temperature", callback_data="cat_temp")],
        [InlineKeyboardButton("⚖️ Weight", callback_data="cat_weight")],
        [InlineKeyboardButton("📏 Length", callback_data="cat_length")],
        [InlineKeyboardButton("💾 Digital Data", callback_data="cat_data")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    msg = "⚡ **Welcome to VeloShift!** ⚡\n\nSelect a metric category below to begin your conversion:"
    if update.message:
        await update.message.reply_text(msg, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup, parse_mode="Markdown")

# Handle Category Selection
async def handle_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split("_")[1]
    
    buttons = []
    if category == "temp":
        buttons = [
            [InlineKeyboardButton("Celsius (°C) ➡️ Fahrenheit (°F)", callback_data="conv_temp_c_to_f")],
            [InlineKeyboardButton("Fahrenheit (°F) ➡️ Celsius (°C)", callback_data="conv_temp_f_to_c")]
        ]
    elif category == "weight":
        buttons = [
            [InlineKeyboardButton("Kilograms (kg) ➡️ Pounds (lbs)", callback_data="conv_weight_kg_to_lbs")],
            [InlineKeyboardButton("Pounds (lbs) ➡️ Kilograms (kg)", callback_data="conv_weight_lbs_to_kg")]
        ]
    elif category == "length":
        buttons = [
            [InlineKeyboardButton("Meters (m) ➡️ Feet (ft)", callback_data="conv_length_m_to_ft")],
            [InlineKeyboardButton("Feet (ft) ➡️ Meters (m)", callback_data="conv_length_ft_to_m")]
        ]
    elif category == "data":
        buttons = [
            [InlineKeyboardButton("Gigabytes (GB) ➡️ Megabytes (MB)", callback_data="conv_data_gb_to_mb")],
            [InlineKeyboardButton("Megabytes (MB) ➡️ Gigabytes (GB)", callback_data="conv_data_mb_to_gb")]
        ]
        
    buttons.append([InlineKeyboardButton("🔙 Back to Menu", callback_data="back_main")])
    reply_markup = InlineKeyboardMarkup(buttons)
    await query.message.edit_text("👉 Choose your precise conversion direction:", reply_markup=reply_markup)

# Handle Specific Conversion Choice
async def handle_conversion_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split("_")
    category = parts[1]
    direction = "_".join(parts[2:])
    
    context.user_data["current_category"] = category
    context.user_data["current_direction"] = direction
    
    keyboard = [[InlineKeyboardButton("❌ Cancel", callback_data="back_main")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.message.edit_text(
        "🔢 **Excellent.** Now type or send the numeric value you wish to convert:", 
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

# Process Numeric Input
async def process_value(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = context.user_data.get("current_category")
    direction = context.user_data.get("current_direction")
    
    if not category or not direction:
        await update.message.reply_text("Please select a conversion type first using /start")
        return

    user_input = update.message.text.strip()
    try:
        value = float(user_input)
        result_text = perform_conversion(value, category, direction)
        
        # Build options to convert another or reset
        keyboard = [
            [InlineKeyboardButton("🔄 Convert another value", callback_data=f"conv_{category}_{direction}")],
            [InlineKeyboardButton("🏠 Main Menu", callback_data="back_main")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            f"✅ **Result:**\n`{result_text}`", 
            reply_markup=reply_markup, 
            parse_mode="Markdown"
        )
    except ValueError:
        await update.message.reply_text("❌ Invalid entry. Please reply with a valid number (e.g., `12`, `4.5`).")

def main():
    # Explicit loop initialization for Render environment compatibility
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if not TOKEN:
        logger.error("No BOT_TOKEN found in environment variables!")
        return

    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(start, pattern="^back_main$"))
    application.add_handler(CallbackQueryHandler(handle_category, pattern="^cat_"))
    application.add_handler(CallbackQueryHandler(handle_conversion_choice, pattern="^conv_"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, process_value))

    print("🤖 VeloShift is active and polling...")
    application.run_polling()

if __name__ == "__main__":
    main()
