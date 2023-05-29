from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
import firebase_admin
import time

from firebase_admin import credentials, firestore

cred = credentials.Certificate('./crypto4you-bot-firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("/encrypt", callback_data='encrypt'),
         InlineKeyboardButton("/decrypt", callback_data='decrypt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose operation:', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['operation'] = query.data
    query.edit_message_text(text=f"Selected operation: {query.data}")

    keyboard = [
        [InlineKeyboardButton("AES", callback_data='AES'),
         InlineKeyboardButton("RSA", callback_data='RSA')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text('Please choose encryption algorithm:', reply_markup=reply_markup)

def encrypt_command(update: Update, context: CallbackContext) -> None:
    context.user_data['operation'] = 'encrypt'
    keyboard = [
        [InlineKeyboardButton("AES", callback_data='AES'),
         InlineKeyboardButton("RSA", callback_data='RSA')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose encryption algorithm:', reply_markup=reply_markup)


def decrypt_command(update: Update, context: CallbackContext) -> None:
    context.user_data['operation'] = 'decrypt'
    keyboard = [
        [InlineKeyboardButton("AES", callback_data='AES'),
         InlineKeyboardButton("RSA", callback_data='RSA')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose encryption algorithm:', reply_markup=reply_markup)

def algorithm(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['algorithm'] = query.data
    query.edit_message_text(text=f"Selected algorithm: {query.data}")
    
    if context.user_data['operation'] == 'encrypt':
        query.message.reply_text('Please send me a message to encrypt.')
    else:
        query.message.reply_text('Please send me an ID to decrypt.')

def save(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    text = update.message.text  # leave text as string initially

    if 'operation' not in context.user_data or 'algorithm' not in context.user_data:
        update.message.reply_text('Please select operation and algorithm first')
        return

    if context.user_data['operation'] == 'encrypt':
        text = text.encode('utf-8')  # convert text to bytes only when encrypting
        if context.user_data['algorithm'] == 'AES':
            cipher = AES.new('This is a key123'.encode(), AES.MODE_CBC, 'This is an IV456'.encode())
            encrypted_text = cipher.encrypt(pad(text, AES.block_size))  # pad text to be multiple of AES block size
        else:
            key = RSA.generate(2048)
            private_key = key.export_key()
            public_key = key.publickey().export_key()
            cipher_rsa = PKCS1_OAEP.new(RSA.import_key(public_key))
            encrypted_text = cipher_rsa.encrypt(text)
            context.user_data['private_key'] = private_key
        doc = db.collection(u'plaintext').document()
        doc.set({u'text': encrypted_text})
        doc_id = doc.id  # get the ID of the document
        update.message.reply_text(f'Text encrypted and saved. Your ID is: {doc_id}')
    elif context.user_data['operation'] == 'decrypt':
        doc_id = text  # treat text as doc_id when decrypting
        doc_ref = db.collection(u'plaintext').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            encrypted_text = doc.to_dict().get('text')
            if context.user_data['algorithm'] == 'AES':
                cipher = AES.new('This is a key123'.encode(), AES.MODE_CBC, 'This is an IV456'.encode())
                decrypted_text = unpad(cipher.decrypt(encrypted_text), AES.block_size).decode('utf-8')  # unpad decrypted text and convert it to string
            else:
                private_key = context.user_data.get('private_key')
                if private_key:
                    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(private_key))
                    decrypted_text = cipher_rsa.decrypt(encrypted_text)
                else:
                    update.message.reply_text('No private key found for RSA decryption')
                    return
            update.message.reply_text(f'Decrypted text: {decrypted_text}')
        else:
            update.message.reply_text('No encrypted text found for the provided ID.')

def main() -> None:
    updater = Updater("TOKEN LU SENDIRI", use_context=True)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("encrypt", encrypt_command))
    dispatcher.add_handler(CommandHandler("decrypt", decrypt_command))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save))
    dispatcher.add_handler(CallbackQueryHandler(button, pattern='^(encrypt|decrypt)$'))
    dispatcher.add_handler(CallbackQueryHandler(algorithm, pattern='^(AES|RSA)$'))

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()


WAHYOOOOOOOOO