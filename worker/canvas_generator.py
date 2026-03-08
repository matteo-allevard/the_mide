import io
import json
import boto3
from PIL import Image, ImageDraw
from datetime import datetime
import os
from decimal import Decimal

# Initialisation DynamoDB
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'pixel-canvas'))

# Palette de couleurs (16 couleurs)
COLORS = [
    {"name": "Blanc", "hex": "#FFFFFF", "emoji": "⬜"},
    {"name": "Gris clair", "hex": "#E4E4E4", "emoji": "🔘"},
    {"name": "Gris", "hex": "#888888", "emoji": "⚫"},
    {"name": "Noir", "hex": "#222222", "emoji": "⬛"},
    {"name": "Rose", "hex": "#FFA7D1", "emoji": "🌸"},
    {"name": "Rouge", "hex": "#E50000", "emoji": "🔴"},
    {"name": "Orange", "hex": "#E59500", "emoji": "🟠"},
    {"name": "Marron", "hex": "#A06A42", "emoji": "🟤"},
    {"name": "Jaune", "hex": "#E5D900", "emoji": "🟡"},
    {"name": "Vert clair", "hex": "#94E044", "emoji": "🟢"},
    {"name": "Vert", "hex": "#02BE01", "emoji": "🌿"},
    {"name": "Cyan", "hex": "#00D3DD", "emoji": "🔵"},
    {"name": "Bleu", "hex": "#0083C7", "emoji": "💙"},
    {"name": "Bleu foncé", "hex": "#0000EA", "emoji": "🔷"},
    {"name": "Violet clair", "hex": "#CF6EE4", "emoji": "🟣"},
    {"name": "Violet", "hex": "#820080", "emoji": "💜"}
]

COLOR_MAP = {c["name"].lower(): c["hex"] for c in COLORS}
COLOR_MAP.update({c["hex"]: c["hex"] for c in COLORS})

# Fonction pour convertir les Decimals en int
def decimal_to_int(obj):
    """Convertit récursivement les Decimal en int dans un objet"""
    if isinstance(obj, list):
        return [decimal_to_int(item) for item in obj]
    elif isinstance(obj, dict):
        return {key: decimal_to_int(value) for key, value in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj)  # Conversion cruciale !
    else:
        return obj

def get_canvas_info():
    """Récupère les infos du canvas depuis DynamoDB"""
    try:
        response = table.get_item(Key={'position': 'canvas_info'})
        item = response.get('Item', {'width': 30, 'height': 30})
        return decimal_to_int(item)  # ← Conversion ici
    except Exception as e:
        print(f"Erreur get_canvas_info: {e}")
        return {'width': 30, 'height': 30}

def save_canvas_info(width, height):
    """Sauvegarde les dimensions du canvas"""
    item = {
        'position': 'canvas_info',
        'width': int(width),  # S'assurer que c'est un int
        'height': int(height),
        'timestamp': int(datetime.now().timestamp() * 1000)
    }
    table.put_item(Item=item)

def wipe_canvas(width, height):
    """Supprime tous les pixels et crée un nouveau canvas"""
    save_canvas_info(width, height)
    return width, height

def save_pixel(x, y, color, user_id, username):
    """Sauvegarde un pixel dans DynamoDB"""
    position = f"pixel_{x}_{y}"
    timestamp = int(datetime.now().timestamp() * 1000)
    
    item = {
        'position': position,
        'x': int(x),
        'y': int(y),
        'color': color,
        'userId': user_id,
        'username': username,
        'timestamp': timestamp,
        'ttl': int(timestamp / 1000) + 31536000
    }
    
    table.put_item(Item=item)
    return item

def get_all_pixels():
    """Récupère tous les pixels du canvas"""
    try:
        response = table.scan()
        items = response.get('Items', [])
        # Filtrer canvas_info et convertir les Decimals
        pixels = []
        for item in items:
            if item.get('position') != 'canvas_info':
                pixels.append(decimal_to_int(item))
        return pixels
    except Exception as e:
        print(f"Erreur get_all_pixels: {e}")
        return []

def generate_canvas_image():
    """Génère une image PNG du canvas avec tous les pixels"""
    canvas_info = get_canvas_info()
    width = canvas_info.get('width', 30)
    height = canvas_info.get('height', 30)
    
    print(f"📐 Canvas dimensions: {width}x{height}")
    
    # Paramètres d'image
    canvas_size = 800
    pixel_size = min(canvas_size // width, canvas_size // height)
    img_width = width * pixel_size
    img_height = height * pixel_size
    
    print(f"🖼️ Image size: {img_width}x{img_height}, pixel_size: {pixel_size}")
    
    # Créer l'image
    img = Image.new('RGB', (img_width, img_height + 60), color='#f0f0f0')
    draw = ImageDraw.Draw(img)
    
    # Dessiner la grille
    for i in range(0, img_width + 1, pixel_size):
        draw.line([(i, 0), (i, img_height)], fill='#cccccc', width=1)
    for i in range(0, img_height + 1, pixel_size):
        draw.line([(0, i), (img_width, i)], fill='#cccccc', width=1)
    
    # Récupérer tous les pixels
    pixels = get_all_pixels()
    print(f"📊 Nombre de pixels récupérés: {len(pixels)}")
    
    # Garder seulement le dernier pixel pour chaque position
    latest_pixels = {}
    for pixel in pixels:
        key = (pixel['x'], pixel['y'])
        if key not in latest_pixels or pixel['timestamp'] > latest_pixels[key]['timestamp']:
            latest_pixels[key] = pixel
    
    print(f"🎨 Pixels uniques: {len(latest_pixels)}")
    
    # Dessiner chaque pixel
    for (x, y), pixel in latest_pixels.items():
        if 0 <= x < width and 0 <= y < height:
            x1 = x * pixel_size
            y1 = y * pixel_size
            x2 = x1 + pixel_size
            y2 = y1 + pixel_size
            
            color = pixel['color']
            if color not in [c["hex"] for c in COLORS]:
                color = "#000000"
            
            draw.rectangle([x1, y1, x2, y2], fill=color, outline='#333333', width=1)
    
    # Ajouter une légende des couleurs
    valid_hex = [c["hex"] for c in COLORS]
    legend_y = img_height + 10
    legend_x = 10
    
    draw.text((legend_x, img_height + 5), "Couleurs disponibles:", fill='black')
    
    for i, color in enumerate(valid_hex[:8]):
        x_pos = legend_x + i * 30
        draw.rectangle([x_pos, legend_y + 20, x_pos + 20, legend_y + 40], 
                      fill=color, outline='black', width=1)
    
    for i, color in enumerate(valid_hex[8:]):
        x_pos = legend_x + i * 30
        draw.rectangle([x_pos, legend_y + 45, x_pos + 20, legend_y + 65], 
                      fill=color, outline='black', width=1)
    
    # Statistiques
    total_pixels = len(latest_pixels)
    draw.text((legend_x, legend_y + 70), 
              f"Canvas: {width}x{height} | Pixels: {total_pixels} | {datetime.now().strftime('%d/%m/%Y %H:%M')}", 
              fill='black')
    
    # Sauvegarder
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes