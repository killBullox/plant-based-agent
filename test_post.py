import requests
from dotenv import load_dotenv
import os

load_dotenv()

token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
account_id = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

# Step 1 - Crea container
resp = requests.post(
    f"https://graph.facebook.com/v19.0/{account_id}/media",
    data={
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/43/Cute_dog.jpg/1280px-Cute_dog.jpg",
        "caption": "🌱 Benvenuti su Beet It! Nutrizione vegetale che spacca. #beetit #plantbased",
        "media_type": "IMAGE",
        "access_token": token,
    }
)
print("Step 1:", resp.status_code, resp.json())
container_id = resp.json().get("id")

# Step 2 - Pubblica container
if container_id:
    publish = requests.post(
        f"https://graph.facebook.com/v19.0/{account_id}/media_publish",
        data={
            "creation_id": container_id,
            "access_token": token,
        }
    )
    print("Step 2:", publish.status_code, publish.json())