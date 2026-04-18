import json
import os
import boto3
import base64
import requests
from datetime import datetime
from canvas_generator import (
    generate_canvas_image, 
    save_pixel, 
    get_canvas_info, 
    wipe_canvas,
    COLORS,
    COLOR_MAP
)
from discord_utils import send_discord_response

# Initialisation AWS
dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'pixel-canvas'))
BUCKET_NAME = os.environ.get('S3_BUCKET')
DISCORD_APP_ID = os.environ.get('DISCORD_APPLICATION_ID')

def check_rate_limit(user_id):
    """Vérifie le rate limiting (20 pixels/minute)"""
    one_minute_ago = int(datetime.now().timestamp() * 1000) - 60000
    
    try:
        response = table.scan(
            FilterExpression='userId = :uid AND #ts > :one_minute',
            ExpressionAttributeNames={'#ts': 'timestamp'},
            ExpressionAttributeValues={
                ':uid': user_id,
                ':one_minute': one_minute_ago
            }
        )
        return len(response.get('Items', [])) < 20
    except Exception as e:
        print(f"Erreur rate limit: {e}")
        return True  # En cas d'erreur, on autorise par sécurité

def lambda_handler(event, context):
    """Point d'entrée du worker (déclenché par SQS)"""
    
    print(f"📦 Événement SQS reçu: {json.dumps(event)}")
    
    for record in event['Records']:
        try:
            # Récupérer le message SQS
            message = json.loads(record['body'])
            interaction = message['interaction']
            command_name = interaction['data']['name']
            token = interaction['token']
            
            # Récupérer les infos utilisateur
            user = interaction.get('member', {}).get('user', {}) or interaction.get('user', {})
            user_id = user.get('id')
            username = user.get('username', 'Inconnu')
            
            print(f"🔄 Traitement: {command_name} de {username}")
            
            # Router vers le bon handler
            if command_name == 'draw':
                handle_draw(interaction, token, user_id, username)
            elif command_name == 'canvas':
                handle_canvas(interaction, token)
            elif command_name == 'snapshot':
                handle_snapshot(interaction, token)
            elif command_name == 'new':
                handle_new_canvas(interaction, token, user_id)
            elif command_name == 'session':
                handle_session(interaction, token, user_id)
            else:
                send_discord_response(token, "❌ Commande inconnue")
                
        except Exception as e:
            print(f"❌ Erreur worker: {e}")
            # Envoyer une réponse d'erreur à Discord
            try:
                send_discord_response(token, f"❌ Erreur: {str(e)[:100]}")
            except:
                pass
    
    return {'statusCode': 200}

def handle_draw(interaction, token, user_id, username):
    """Gère /draw - dessine un pixel"""
    try:
        options = {opt['name']: opt['value'] for opt in interaction['data']['options']}
        x = options['x']
        y = options['y']
        color_input = options['couleur']
        
        # Récupérer les dimensions du canvas
        canvas_info = get_canvas_info()
        max_x = canvas_info.get('width', 30) - 1
        max_y = canvas_info.get('height', 30) - 1
        
        # Valider les coordonnées
        if x > max_x or y > max_y:
            send_discord_response(
                token,
                f"❌ Coordonnées invalides. Le canvas fait {max_x+1}x{max_y+1} (max {max_x},{max_y})"
            )
            return
        
        # Convertir la couleur en hex si c'est un nom
        color_hex = COLOR_MAP.get(color_input.lower(), color_input)
        
        # Vérifier que la couleur est valide
        valid_hex = [c["hex"] for c in COLORS]
        if color_hex not in valid_hex:
            send_discord_response(
                token,
                "❌ Couleur non valide. Utilise `/couleurs` pour voir la liste."
            )
            return
        
        # Vérifier rate limit
        if not check_rate_limit(user_id):
            send_discord_response(
                token,
                "⏱️ Rate limit atteint ! Maximum 20 pixels par minute."
            )
            return
        
        # Sauvegarder le pixel
        save_pixel(x, y, color_hex, user_id, username)
        
        # Trouver le nom de la couleur
        color_name = next((c['name'] for c in COLORS if c['hex'] == color_hex), color_hex)
        
        send_discord_response(
            token,
            f"✅ Pixel placé en ({x}, {y}) - {color_name}"
        )
        
    except Exception as e:
        print(f"Erreur draw: {e}")
        send_discord_response(token, "❌ Erreur lors du dessin")

def handle_canvas(interaction, token):
    """Gère /canvas - génère et envoie l'image du canvas"""
    try:
        # Récupérer les infos du canvas pour le message
        canvas_info = get_canvas_info()
        width = canvas_info.get('width', 30)
        height = canvas_info.get('height', 30)
        
        # Générer l'image
        print("🖼️ Génération de l'image...")
        img_bytes = generate_canvas_image()
        
        # Upload sur S3
        filename = f"canvas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=filename,
            Body=img_bytes.getvalue(),
            ContentType='image/png'
        )
        print(f"✅ Image uploadée sur S3: {filename}")
        
        # Générer URL présignée (valable 1 heure)
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': filename},
            ExpiresIn=3600
        )
        
        # Envoyer à Discord
        send_discord_response(
            token,
            f"Voici le canvas ({width}x{height}) :",
            embeds=[{
                "title": "Canvas Actuel",
                "image": {"url": url},
                "timestamp": datetime.utcnow().isoformat()
            }]
        )
        
    except Exception as e:
        print(f"Erreur canvas: {e}")
        send_discord_response(token, "❌ Erreur lors de la génération du canvas")

def handle_snapshot(interaction, token):
    """Gère /snapshot - identique à /canvas pour l'instant"""
    handle_canvas(interaction, token)

def handle_new_canvas(interaction, token, user_id):
    """Gère /new - crée un nouveau canvas (admin)"""
    try:
        options = {opt['name']: opt['value'] for opt in interaction['data']['options']}
        width = options['width']
        height = options['height']
        
        # Valider les dimensions
        if width < 30 or width > 1000 or height < 30 or height > 1000:
            send_discord_response(
                token,
                "❌ Dimensions invalides. Utilise des valeurs entre 30 et 1000."
            )
            return
        
        # Créer le nouveau canvas
        wipe_canvas(width, height)
        
        send_discord_response(
            token,
            f"✅ Nouveau canvas créé : {width}x{height}"
        )
        
    except Exception as e:
        print(f"Erreur new canvas: {e}")
        send_discord_response(token, "❌ Erreur lors de la création du canvas")

def handle_session(interaction, token, user_id):
    """Gère /session (admin) - pour compatibilité"""
    try:
        action = interaction['data']['options'][0]['value']
        send_discord_response(
            token,
            f"⚙️ Session {action} (admin) - Fonctionnalité à implémenter"
        )
    except Exception as e:
        print(f"Erreur session: {e}")
        send_discord_response(token, "❌ Erreur lors de l'exécution")