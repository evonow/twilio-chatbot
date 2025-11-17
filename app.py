"""
Twilio Chatbot for Customer Service
Main Flask application handling Twilio SMS webhooks
"""

from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
import os
from dotenv import load_dotenv
from chatbot import ChatbotAgent

load_dotenv()

app = Flask(__name__)
chatbot = ChatbotAgent()

@app.route('/sms', methods=['POST'])
def sms_reply():
    """Handle incoming SMS messages from Twilio"""
    # Get the message body and sender number
    incoming_msg = request.values.get('Body', '').strip()
    sender_phone = request.values.get('From', '')
    
    # Log the incoming message
    print(f"Received message from {sender_phone}: {incoming_msg}")
    
    # Generate response using the chatbot
    try:
        response_text = chatbot.get_response(incoming_msg)
    except Exception as e:
        print(f"Error generating response: {e}")
        response_text = "I apologize, but I encountered an error processing your request. Please try again or contact support directly."
    
    # Create TwiML response
    resp = MessagingResponse()
    resp.message(response_text)
    
    return Response(str(resp), mimetype='text/xml')

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return {'status': 'healthy', 'service': 'twilio-chatbot'}, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)


