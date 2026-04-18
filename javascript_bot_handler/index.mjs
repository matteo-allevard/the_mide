import { verifyKey, InteractionType, InteractionResponseType } from 'discord-interactions';
import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs';

const PUBLIC_KEY = process.env.DISCORD_PUBLIC_KEY;
const QUEUE_URL = process.env.QUEUE_URL; // Note: c'est QUEUE_URL, pas SQS_QUEUE_URL dans tes vars

const sqsClient = new SQSClient({ region: process.env.AWS_REGION });

// Liste des couleurs pour la commande /couleurs
const COLORS = [
  { name: 'Blanc', hex: '#FFFFFF', emoji: '⬜' },
  { name: 'Gris clair', hex: '#E4E4E4', emoji: '🔘' },
  { name: 'Gris', hex: '#888888', emoji: '⚫' },
  { name: 'Noir', hex: '#222222', emoji: '⬛' },
  { name: 'Rose', hex: '#FFA7D1', emoji: '🌸' },
  { name: 'Rouge', hex: '#E50000', emoji: '🔴' },
  { name: 'Orange', hex: '#E59500', emoji: '🟠' },
  { name: 'Marron', hex: '#A06A42', emoji: '🟤' },
  { name: 'Jaune', hex: '#E5D900', emoji: '🟡' },
  { name: 'Vert clair', hex: '#94E044', emoji: '🟢' },
  { name: 'Vert', hex: '#02BE01', emoji: '🌿' },
  { name: 'Cyan', hex: '#00D3DD', emoji: '🔵' },
  { name: 'Bleu', hex: '#0083C7', emoji: '💙' },
  { name: 'Bleu foncé', hex: '#0000EA', emoji: '🔷' },
  { name: 'Violet clair', hex: '#CF6EE4', emoji: '🟣' },
  { name: 'Violet', hex: '#820080', emoji: '💜' }
];

export const handler = async (event) => {
  console.log("📥 Event reçu:", JSON.stringify(event));
  
  try {
    // ============================================
    // 1. VÉRIFICATION DE SIGNATURE
    // ============================================
    const signature = event.headers['x-signature-ed25519'];
    const timestamp = event.headers['x-signature-timestamp'];
    const rawBody = event.isBase64Encoded 
      ? Buffer.from(event.body, 'base64').toString('utf-8')
      : event.body;
    
    const isValid = await verifyKey(rawBody, signature, timestamp, PUBLIC_KEY);
    if (!isValid) {
      console.log("❌ Signature invalide");
      return {
        statusCode: 401,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ error: 'Invalid signature' })
      };
    }
    console.log("✅ Signature valide");
    
    const interaction = JSON.parse(rawBody);
    
    // ============================================
    // 2. GESTION DU PING
    // ============================================
    if (interaction.type === InteractionType.PING) {
      console.log("🏓 PONG");
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: InteractionResponseType.PONG })
      };
    }
    
    // ============================================
    // 3. GESTION DES COMMANDES SLASH
    // ============================================
    if (interaction.type === InteractionType.APPLICATION_COMMAND) {
      const { name, options = [] } = interaction.data;
      const commandName = name;
      
      console.log(`📝 Commande reçue: ${commandName}`);
      
      // ========== COMMANDES RAPIDES (réponse immédiate) ==========
      
      // Commande /couleurs
      if (commandName === 'couleurs') {
        let message = '**🎨 Couleurs disponibles :**\n\n';
        COLORS.forEach(c => {
          message += `${c.emoji} **${c.name}** - \`${c.hex}\`\n`;
        });
        
        return {
          statusCode: 200,
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            data: { content: message }
          })
        };
      }
      
      // ========== COMMANDES LOURDES (passage par SQS) ==========
      // Liste des commandes qui nécessitent un traitement asynchrone
      const heavyCommands = ['draw', 'canvas', 'snapshot', 'pixel', 'stats', 'new', 'session'];
      
      if (heavyCommands.includes(commandName)) {
        // LOGS DE DEBUG
        console.log("🔍 QUEUE_URL =", QUEUE_URL);
        console.log("🔍 AWS_REGION =", process.env.AWS_REGION);
        
        // Vérifier que la queue SQS est configurée
        if (!QUEUE_URL) {
          console.error("❌ QUEUE_URL non configurée");
          return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: { content: '❌ Erreur de configuration: SQS non disponible' }
            })
          };
        }
        
        try {
          // Préparer le message pour SQS
          const messageBody = JSON.stringify({
            interaction,
            timestamp: Date.now()
          });
          
          console.log("📤 Tentative d'envoi vers SQS...");
          console.log("📤 Message body:", messageBody);
          
          const command = new SendMessageCommand({
            QueueUrl: QUEUE_URL,
            MessageBody: messageBody
          });
          
          const result = await sqsClient.send(command);
          console.log("✅ Message envoyé avec succès à SQS");
          console.log("📤 MessageId:", result.MessageId);
          
          // Réponse différée à Discord (type 5)
          return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE
            })
          };
          
        } catch (sqsError) {
          console.error("💥 Erreur SQS détaillée:", sqsError);
          console.error("💥 Error name:", sqsError.name);
          console.error("💥 Error message:", sqsError.message);
          console.error("💥 Error stack:", sqsError.stack);
          
          return {
            statusCode: 200,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
              data: { content: '❌ Erreur lors du traitement de la commande' }
            })
          };
        }
      }
      
      // Commande inconnue (non listée)
      console.log(`⚠️ Commande inconnue: ${commandName}`);
      return {
        statusCode: 200,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
          data: { content: '❓ Commande inconnue' }
        })
      };
    }
    
    // Type d'interaction non géré
    console.log(`⚠️ Type d'interaction inconnu: ${interaction.type}`);
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: { content: '❓ Type d\'interaction inconnu' }
      })
    };
    
  } catch (error) {
    console.error('💥 ERREUR CATASTROPHIQUE:', error);
    console.error('Stack trace:', error.stack);
    
    return {
      statusCode: 200,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
        data: { content: '❌ Une erreur interne est survenue.' }
      })
    };
  }
};

// Fonction rapide pour /couleurs (réponse immédiate)
function handleColors(interaction) {
  let message = '**🎨 Couleurs disponibles :**\n\n';
  COLORS.forEach(c => {
    message += `${c.emoji} **${c.name}** - \`${c.hex}\`\n`;
  });
  
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      type: InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
      data: { content: message }
    })
  };
}