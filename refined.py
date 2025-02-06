import os
import requests
import imgkit
import tempfile
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables from .env file
load_dotenv()

# Loyverse and Telegram API tokens
LOYVERSE_ACCESS_TOKEN = os.getenv("LOYVERSE_ACCESS_TOKEN")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")  # Telegram chat ID to send the image
BASE_URL = "https://api.loyverse.com/v1.0"

# Ensure required environment variables exist
if not all([LOYVERSE_ACCESS_TOKEN, BOT_TOKEN, TELEGRAM_CHAT_ID]):
    raise ValueError("Missing environment variables. Check your .env file.")

# Flask application
app = Flask(__name__)

# Function to generate a receipt image
def generate_receipt_image(receipt_data):
    # Extract total amount correctly
    total_amount = receipt_data.get("total_money", 0.0)  # Now correctly taken as float

    # HTML template for the receipt
    html_template = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Receipt - Chic Opulance</title>
        <link href="https://fonts.googleapis.com/css?family=Roboto" rel="stylesheet">
        <style>
            body {
                font-family: 'Roboto', sans-serif;
                background-color: #F5F5F5;
                margin: 0;
                padding: 20px;
                display: flex;
                justify-content: center;
            }
            .receipt {
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                max-width: 400px;
                width: 100%;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            }
            .logo {
                display: block;
                margin: 0 auto 10px;
                height: 80px;
            }
            h2 {
                text-align: center;
                font-size: 15px;
                font-weight: bold;  
            }
            hr {
                border-top: 1px dotted #aaa;    
            }
            .total {
                font-size: 24px;
                font-weight: bold;
                text-align: center;
            }
            .item {
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
            }
            .footer {
                text-align: center;
                font-size: 14px;
                color: #666;
            }
            .footer-inline {
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;  
            }
            .footer-bottom {
                text-align: center;
                font-size: 10px;
                color: #666;
            }
        </style>
    </head>
    <body>
        <div class="receipt">
            <img class="logo" src="https://data-prod-eu-loyverse-com.s3.amazonaws.com/outlets/3279808/profile/emailLogo2024-07-23-09-19-35-035.png" alt="Chic Opulance">
            <h2>Chic Opulance</h2>
            <hr>
            <p class="total">MVR {total_amount:.2f}</p>
            <hr>
            {line_items_html}
            <hr>
            <div class="item">
                <strong>Total</strong>
                <strong>MVR {total_amount:.2f}</strong>
            </div>
            <div class="item">
                <span>Cash.payment type name</span>
                <span>MVR {total_amount:.2f}</span>
            </div>
            <hr>
            <p class="footer">Thank You!<br>BML Transfer: 7730000465147<br>Account Name: SM Shop<br>Viber/Telegram: 7620064</p>
            <div class="footer-inline">
                <span>{server_time}</span>
                <span>Receipt № {receipt_number}</span>
            </div>
            <p class="footer-bottom"> made by @shahulyns.bot❤️</p>
        </div>
    </body>
    </html>
    """

    # Generate line items HTML
    line_items_html = ""
    for item in receipt_data.get("line_items", []):
        item_name = item.get("item_name", "Item")
        quantity = item.get("quantity", 0)
        unit_price = item.get("price", 0.0)
        line_total = quantity * unit_price
        line_items_html += f"""
        <div class="item">
            <span>{item_name}</span>
            <span>MVR {line_total:.2f}</span>   
        </div>
        <span class="footer-inline">{quantity} × MVR {unit_price:.2f}</span>
        """

    # Fill in template
    receipt_html = html_template.format(
        receipt_number=receipt_data.get("receipt_number", "N/A"),
        server_time=datetime.now().strftime("%d/%m/%Y %H:%M"),
        line_items_html=line_items_html,
        total_amount=total_amount
    )

    # Save HTML and convert to image
    html_path = tempfile.gettempdir() + "/receipt.html"
    img_path = tempfile.gettempdir() + "/receipt.png"
    with open(html_path, "w") as file:
        file.write(receipt_html)
    
    try:
        imgkit.from_file(html_path, img_path)
        return img_path
    except Exception as e:
        print(f"Error generating image: {e}")
        return None

# Function to send image to Telegram
def send_telegram_image(chat_id, img_path):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    with open(img_path, "rb") as photo:
        response = requests.post(url, files={"photo": photo}, data={"chat_id": chat_id})
    print(f"Telegram response: {response.status_code}, {response.text}")

# Webhook to handle receipts
@app.route("/webhook", methods=["POST"])
def handle_webhook():
    data = request.json
    receipts = data.get("receipts", [])
    if receipts:
        img_path = generate_receipt_image(receipts[0])
        if img_path:
            send_telegram_image(TELEGRAM_CHAT_ID, img_path)
            os.remove(img_path)
    return jsonify({"status": "ok"}), 200

# Start Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
