import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from gradio_client import Client, handle_file
from PIL import Image
import io
from pymongo import MongoClient
import streamlit as st

# Initialize bot and Gradio client
API_TOKEN = '7601276865:AAFZjuQb9SBaHwNdmupHuX2kkB3aNjr204E'
GRADIO_API_URL = "kskkoushik135/image_detector"
bot = telebot.TeleBot(API_TOKEN)
client = Client(GRADIO_API_URL)
mongo_url = "mongodb+srv://kskkoushik135:LQCFjoGmTHFyIdRi@cluster0.zzxbiby.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

dummy = st.text_input("I am a dummy")


mongo_client = MongoClient(mongo_url)
db = mongo_client["photo_category_db"]
collection = db["images"]

user_data = {}

# Temporary directory to save downloaded images
TEMP_IMAGE_PATH = "temp_images"
if not os.path.exists(TEMP_IMAGE_PATH):
    os.makedirs(TEMP_IMAGE_PATH)

# Main category options
MAIN_OPTIONS = ["Desserts", "Mithai Scoops" ,"Savories" , "ADD-ONs", "Cards"]

# Subcategory options
OPTIONS_MITHAI_SCOOPS = [
    "Kalakand Jar",
    "Kalakand Jar with Blueberry & Almond Topping",
    "Shrikhand - Kesar Elaichi Flavour",
    "Mixed Berry Shrikhand",
    "Pista Shrikhand"
]

OPTIONS_DESSERTS = [
    "Tiramisu - Classic Flavour",
    "Tiramisu - Hazelnut Flavor",
    "Tiramisu - Strong Coffee",
    
    "Oh Fudge! Chocolate Almond",
    "Oh Fudge! Mocha Almond Fudge",
    
    "New York Cheesecake With Almond Base - Jar",
    "Chocolate infused Cheesecake with Almond base - Jar",
    "Blueberry Cheesecake With Almond base - Jar",
    "The Un-cheese Cake - Blueberry",
    "The Un-cheese Cake - Cranberry",
    "The Un-cheese Cake - Vanilla",
    "Lean Dessert: Blueberry and Cream Baked Yogurt",
    "Lean Dessert: Cranberry and Cream Baked Yogurt",
    "Lean Dessert: Vanilla and Cream Baked Yogurt"
]


OPTIONS_SAVORIES  = [
    "No-nonsense Chiwda",
    "Health trail-mix",
    "Mathari in my mouth Methi Flavor",
    "Masala Cranberries"
]

OPTIONS_ADDONS = [
    "Strawberry Compote",
    "Blueberry Compote",
    "Cranberry Compote",
    "Crushed Strawberries",
    "Crushed Blueberries",
    "Crushed Cranberries",
    "Nuts & Berries mix",
    "Nuts & Seeds mix",
    "Roasted Crushed almonds"
]

OPTIONS_CARDS =  [
    "Product replacement Card",
    "I'm sorry",
    "Best of luck to you card",
    "Congratulations card",
    "Sometimes there are no just words",
    "Happy anniversary card",
    "I love you card",
    "Thank you card",
    "Happy birthday to you card",
    "Brand's Delivery Bag",
    "Ice gels",
    "Cutlery"
]







# Handle the "/start" command
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(
        message.chat.id,
        "Welcome! Please send me a photo of product"
    )

# Handle receiving a photo
@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    file_id = message.photo[-1].file_id
    user_data[message.chat.id] = {'file_id': file_id}

    # Download and save the photo temporarily
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    temp_file_path = os.path.join(TEMP_IMAGE_PATH, f"{file_id}.jpg")
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(downloaded_file)

    # Use Gradio API to predict the label
    result = client.predict(image=handle_file(temp_file_path), api_name="/predict")
    predicted_label = result.get("label", "unknown")
    user_data[message.chat.id]['predicted_label'] = predicted_label

    # Send confirmation message with Yes/No buttons
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Yes", callback_data="yes"),
               InlineKeyboardButton("No", callback_data="no"))
    bot.send_message(
        message.chat.id,
        f"Predicted label: '{predicted_label}'. Is this correct?",
        reply_markup=markup
    )

# Handle Yes/No button responses
@bot.callback_query_handler(func=lambda call: call.data in ["yes", "no"])
def handle_confirmation(call):
    chat_id = call.message.chat.id
    if call.data == "yes":
        file_id = user_data[chat_id]['file_id']
        predicted_label = user_data[chat_id]['predicted_label']
        temp_file_path = os.path.join(TEMP_IMAGE_PATH, f"{file_id}.jpg")

        # Convert image and prepare for MongoDB
        with Image.open(temp_file_path) as img:
            image_bytes = io.BytesIO()
            img.save(image_bytes, format="JPEG")
            image_bytes.seek(0)

        # Save image and label to MongoDB
        collection.insert_one({
            "category": predicted_label,
            "file_id": file_id,
            "image_data": image_bytes.getvalue()
        })

        category = ''

        if predicted_label in OPTIONS_ADDONS:
            category = "ADD-ONs"
        elif predicted_label in OPTIONS_CARDS:
            category = "Cards"
        elif predicted_label in OPTIONS_DESSERTS:
            category = "Desserts"
        elif predicted_label in OPTIONS_MITHAI_SCOOPS:
            category = "Mithai Scoops"
        elif predicted_label in OPTIONS_SAVORIES:
            category = "Savories"                

        bot.send_message(chat_id, f"Saved. Category : {category} , Product : '{predicted_label} , ID: {file_id}")
       
    
    elif call.data == "no":
        # Show main category options if user selected "No"
        markup = InlineKeyboardMarkup()
        for option in MAIN_OPTIONS:
            markup.add(InlineKeyboardButton(option, callback_data=f"main_{option}"))
        bot.send_message(chat_id, "Please select a main category:", reply_markup=markup)

# Handle main category selection
@bot.callback_query_handler(func=lambda call: call.data.startswith("main_"))
def handle_main_category_selection(call):
    main_category = call.data.split("_")[1]
    chat_id = call.message.chat.id

    # Show specific options based on the main category selected
    if main_category == "Mithai Scoops":
        options = OPTIONS_MITHAI_SCOOPS
    elif main_category == "Desserts":
        options = OPTIONS_DESSERTS
    elif main_category == "Cards":
        options = OPTIONS_CARDS
    elif main_category == "Savories":
        options = OPTIONS_SAVORIES
    elif main_category == "ADD-ONs":
        options = OPTIONS_ADDONS        
    else:
        bot.send_message(chat_id, "Invalid category selection.")
        return

    markup = InlineKeyboardMarkup()
    for option in options:
        markup.add(InlineKeyboardButton(option, callback_data=f"sub_{option}"))
    bot.send_message(chat_id, f"Please select a specific option from '{main_category}':", reply_markup=markup)

# Handle specific option selection and save to MongoDB
@bot.callback_query_handler(func=lambda call: call.data.startswith("sub_"))
def handle_specific_option_selection(call):
    product = call.data.split("_")[1]
    chat_id = call.message.chat.id
    file_id = user_data[chat_id]['file_id']
    temp_file_path = os.path.join(TEMP_IMAGE_PATH, f"{file_id}.jpg")

    # Convert and save the image in MongoDB with the selected category
    with Image.open(temp_file_path) as img:
        image_bytes = io.BytesIO()
        img.save(image_bytes, format="JPEG")
        image_bytes.seek(0)

    collection.insert_one({
        "category": product,
        "file_id": file_id,
        "image_data": image_bytes.getvalue()
    })
    category = ''

    if product in OPTIONS_ADDONS:
        category = "ADD-ONs"
    elif product in OPTIONS_CARDS:
        category = "Cards"
    elif product in OPTIONS_DESSERTS:
        category = "Desserts"
    elif product in OPTIONS_MITHAI_SCOOPS:
        category = "Mithai Scoops"
    elif product in OPTIONS_SAVORIES:
        category = "Savories"                

    bot.send_message(chat_id, f"Saved. Category : {category} , Product : '{product} , ID: {file_id}")
       
    # Clean up temporary file
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)

# Start polling for new messages
bot.infinity_polling()
