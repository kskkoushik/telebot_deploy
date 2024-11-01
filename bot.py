import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from PIL import Image
import io
from pymongo import MongoClient

# Define the folder to save temporary images (optional)
TEMP_IMAGE_PATH = "temp_images"
os.makedirs(TEMP_IMAGE_PATH, exist_ok=True)

def testfun():
    return "called testfun working succesfully"

urls = "mongodb+srv://kskkoushik135:LQCFjoGmTHFyIdRi@cluster0.zzxbiby.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Initialize MongoDB client
client = MongoClient(urls)
db = client["photo_category_db"]
collection = db["images"]

# Initialize the bot with your token
API_TOKEN = '7601276865:AAFZjuQb9SBaHwNdmupHuX2kkB3aNjr204E'
bot = telebot.TeleBot(API_TOKEN)

# Define the options
OPTIONS = [
    "card_best_of_luck",
    "card_congrations",
    "card_happy_anniversy",
    "card_happy_birthday",
    "card_i_am_sorry",
    "card_i_am_sorry_for_being",
    "card_i_love_u",
    "card_sometimes_there_r_just",
    "card_thank_you",
    "berillicious_cheesecake_jar",
    "chocolate_cheesecake_jar",
    "dessertjar_kalakand",
    "dessertfruit_and_cream_baked_yogurt_in_blueberry_flavor",
    "dessertfruit_and_cream_baked_yogurt_in_cranberry_flavor",
    "new_york_cheesecake_jar",
    "oh_fudge_dark_chocolate_almond_fudge",
    "oh_fudge_mocha_almond_fudge_dark_chocolate_coffee",
    "sugarfree_tiramisu_with_extra_strong_coffee_shot",
    "_tiramisu_classic_flavour",
    "_tiramisu_hazelnut_flavor",
    "other_cutlery",
    "other_delivery_bags",
    "other_ice_gel",
    "slice_the_uncheese_cake_blueberry",
    "slice_the_uncheese_cake_cranberry",
    "slice_the_uncheesecake_vanilla",
    "snack_masala_cranberry",
    "snack_no_nonsence_chiwada",
    "snack_peri_peri_chiwada",
    "topping_bluberry_syrup",
    "topping_blueberry_crush",
    "topping_choco_ganash",
    "topping_cofee_ganash",
    "topping_cranberry_crush",
    "topping_cranberry_syrup",
    "topping_nuts_berries",
    "topping_roatsed_almonds",
    "topping_roatsed_penuts",
    "topping_seeds_nuts"
]

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Hi! Send me a photo, and I'll help categorize it for you.")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Get the photo file ID
    file_id = message.photo[-1].file_id
    bot.send_message(message.chat.id, "Choose a category for this photo:")
    
    # Store the file ID in the user's session to use after category selection
    bot.user_data = {'file_id': file_id}

    # Create inline keyboard with options
    markup = InlineKeyboardMarkup()
    for option in OPTIONS:
        markup.add(InlineKeyboardButton(option, callback_data=option))
    
    # Send options
    bot.send_message(message.chat.id, "Please select a category:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_category_selection(call):
    category = call.data
    file_id = bot.user_data.get('file_id')
    
    if file_id:
        # Download the photo
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Save temporarily and convert image with Pillow
        temp_file_path = os.path.join(TEMP_IMAGE_PATH, f"{file_id}.jpg")
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(downloaded_file)

        # Open and convert the image
        with Image.open(temp_file_path) as img:
            img_converted = img.convert("L")  # Convert to grayscale or other format

            # Save to a BytesIO object
            image_bytes = io.BytesIO()
            img_converted.save(image_bytes, format="JPEG")
            image_bytes.seek(0)

        # Save to MongoDB
        collection.insert_one({
            "category": category,
            "file_id": file_id,
            "image_data": image_bytes.getvalue()
        })

        # Clean up temporary file
        os.remove(temp_file_path)
        
        bot.answer_callback_query(call.id, f"Photo saved under '{category}' category in MongoDB!")
        bot.send_message(call.message.chat.id, f"Photo saved in '{category}' category in MongoDB!")
    else:
        bot.send_message(call.message.chat.id, "No photo found to save.")

# Start polling
bot.infinity_polling()
