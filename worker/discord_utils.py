import os
import requests

def send_discord_response(interaction_token, content, embeds=None):
    """Envoie une réponse via le webhook Discord"""
    app_id = os.environ.get('DISCORD_APPLICATION_ID')
    url = f"https://discord.com/api/v10/webhooks/{app_id}/{interaction_token}"
    
    payload = {"content": content}
    if embeds:
        payload["embeds"] = embeds
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code not in [200, 204]:
            print(f"⚠️ Erreur Discord: {response.status_code}")
    except Exception as e:
        print(f"❌ Erreur envoi Discord: {e}")