import os
import requests
import tempfile
import imgkit
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
    total_amount = receipt_data.get("total_money", 0.0)

    # Generate line items HTML
    line_items_html = ""
    line_items = receipt_data.get("line_items", [])
    num_items = len(line_items)

    base_height = 500  # Base height of receipt
    extra_height_per_item = 50  # Additional height per item
    total_height = base_height + (num_items * extra_height_per_item)

    for item in line_items:
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
    payment_html = ""
    for payment in receipt_data.get("payments", []):
        payment_name = payment.get("name", "Payment")
        amount_paid = payment.get("money_amount", 0.0)
        payment_html += f"""
        <div class="item">
            <span>{payment_name}</span>
            <span>MVR {amount_paid:.2f}</span>
        </div>
        """
        html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Receipt - Chic Opulance</title>
         <style>
            body {{
                font-family: 'Roboto', sans-serif;
                background-color: #F5F5F5;
                margin: 0;
                padding: 5px;
                display: flex;
                justify-content: center;
            }}
            .receipt {{
                background: #ffffff;
                padding: 20px;
                border-radius: 8px;
                width: 400px;
                height: {total_height}px; /* Adjust height dynamically */
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                overflow: hidden;
            }}
            .logo {{
                display: block;
                margin: 0 auto 10px;
                height: 80px;
            }}
            h2 {{
                text-align: center;
                font-size: 15px;
                font-weight: bold;
            }}
            hr {{
                border-top: 1px dashed #aaa;
            }}
            .total {{
                font-size: 24px;
                font-weight: bold;
                text-align: center;
            }}
            .item {{
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
            }}
            .footer {{
                text-align: center;
                font-size: 14px;
                color: #666;
            }}
            .footer-inline {{
                display: flex;
                justify-content: space-between;
                font-size: 14px;
                color: #666;
                margin-bottom: 5px;
            }}
            .footer-bottom {{
                text-align: center;
                font-size: 10px;
                margin-top: 20px;
                color: #666;
            }}
             </style>
    </head>
    <body>
        <div class="receipt">
            <img class="logo" src="https://data-prod-eu-loyverse-com.s3.amazonaws.com/outlets/1356357/profile/emailLogo>
            <h2>SM Shop</h2>
            <hr>
             <p class="total">MVR {total_amount:.2f}</p>
            <hr>
            {line_items_html}
            <hr>
            <div class="item">
                <strong>Total</strong>
                <strong>MVR {total_amount:.2f}</strong>
            </div>
            {payment_html}
            <hr>
            <p class="footer">رمضان كريم<br>BML Transfer: 7730000439913<br>Account Name: SM Shop<br>Viber: 762>
            <div class="footer-inline">
                <small>{datetime.now().strftime("%b %d, %Y %H:%M")}</small>
                <span>Receipt № {receipt_data.get("receipt_number", "N/A")}</span>
            </div>
            <p class="footer-bottom"> made by @shahulyns.bot❤️</p>
        </div>
    </body>
    </html>
    """

    # Save HTML and convert to image
    html_path = tempfile.gettempdir() + "/receipt.html"
    img_path = tempfile.gettempdir() + "/receipt.png"
    with open(html_path, "w") as file:
        file.write(html_template)

    try:
        options = {"width": 450, "height": total_height, "quality": 95, "zoom": 1.5}  # Ensure correct height
        imgkit.from_file(html_path, img_path, options=options)
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