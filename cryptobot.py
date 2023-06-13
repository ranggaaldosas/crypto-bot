from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad, unpad
import firebase_admin, time, telegram, os, codecs
from dotenv import load_dotenv
from firebase_admin import credentials, firestore

load_dotenv()  # Load environment variables from .env file

# Retrieve environment variables
api_token = os.getenv('API_TOKEN')
firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')
aes_key = os.getenv('AES_KEY')
aes_iv = os.getenv('AES_IV')


cred = credentials.Certificate(firebase_credentials)
firebase_admin.initialize_app(cred)
db = firestore.client()

def start(update: Update, context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Agree", callback_data='agree')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_message = """Selamat datang di Crypto4You Bot!
    
    Crypto4You Bot memungkinkan Anda melakukan enkripsi dan dekripsi pesan menggunakan algoritma AES dan RSA.
    
    Panduan Penggunaan:
    1. Klik tombol "Agree" untuk menerima Terms and Conditions.
    2. Pilih jenis operasi, yaitu /encrypt untuk enkripsi dan /decrypt untuk dekripsi.
    3. Pilih algoritma enkripsi/dekripsi, yaitu AES atau RSA.
    4. Ikuti petunjuk selanjutnya sesuai dengan operasi dan algoritma yang Anda pilih.
    
    Silakan ikuti instruksi dan nikmati pengalaman menggunakan Crypto4You Bot!
    """
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def agree(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    query.message.reply_text('Terimakasih telah telah menyepakati Terms and Conditions!')

    keyboard = [
        [InlineKeyboardButton("/encrypt", callback_data='encrypt'),
         InlineKeyboardButton("/decrypt", callback_data='decrypt')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text('Silahkan pilih jenis Operasi:', reply_markup=reply_markup)

def operation(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['operation'] = query.data
    query.edit_message_text(text=f"Operasi yang terpilih adalah {query.data}")

   
    keyboard = [
        [InlineKeyboardButton("AES", callback_data='AES'),
         InlineKeyboardButton("RSA", callback_data='RSA'),
         InlineKeyboardButton("ROT13", callback_data='ROT13')] 
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text('Silahkan pilih jenis Operasi algorithma', reply_markup=reply_markup)

def encrypt_command(update: Update, context: CallbackContext) -> None:
    context.user_data['operation'] = 'encrypt'
   
    keyboard = [
        [InlineKeyboardButton("AES", callback_data='AES'),
         InlineKeyboardButton("RSA", callback_data='RSA'),
         InlineKeyboardButton("ROT13", callback_data='ROT13')] 
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose encryption algorithm:', reply_markup=reply_markup)

def decrypt_command(update: Update, context: CallbackContext) -> None:
    context.user_data['operation'] = 'decrypt'
    keyboard = [
        [InlineKeyboardButton("AES", callback_data='AES'),
         InlineKeyboardButton("RSA", callback_data='RSA'),
         InlineKeyboardButton("ROT13", callback_data='ROT13')] 
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Please choose decryption algorithm:', reply_markup=reply_markup)

def algorithm(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    context.user_data['algorithm'] = query.data
    query.edit_message_text(text=f"Selected algorithm: {query.data}")

    if context.user_data['algorithm'] == 'AES':
        query.message.reply_text('Silahkan kirim pesan')
    else:
        query.message.reply_text('Silahkan kirim pesan')

def save(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    text = update.message.text 

    if 'operation' not in context.user_data or 'algorithm' not in context.user_data:
        update.message.reply_text('Please select operation and algorithm first')
        return

    if context.user_data['operation'] == 'encrypt':
        if context.user_data['algorithm'] == 'AES':
            text = text.encode('utf-8')  # convert text to bytes only for AES
            cipher = AES.new(aes_key.encode(), AES.MODE_CBC, aes_iv.encode())
            encrypted_text = cipher.encrypt(pad(text, AES.block_size))  # pad text to be multiple of AES block size
        elif context.user_data['algorithm'] == 'RSA':
            text = text.encode('utf-8')  # convert text to bytes only for RSA
            key = RSA.generate(2048)
            private_key = key.export_key()
            public_key = key.publickey().export_key()
            cipher_rsa = PKCS1_OAEP.new(RSA.import_key(public_key))
            encrypted_text = cipher_rsa.encrypt(text)
            context.user_data['private_key'] = private_key
        elif context.user_data['algorithm'] == 'ROT13':  
            encrypted_text = codecs.encode(text, 'rot_13') 

        doc = db.collection(u'plaintext').document()
        doc.set({u'text': encrypted_text})
        doc_id = doc.id  # get the ID of the document
        update.message.reply_text(f'Text encrypted and saved. Your ID is: {doc_id}')

    elif context.user_data['operation'] == 'decrypt':
        doc_id = text
        doc_ref = db.collection(u'plaintext').document(doc_id)
        doc = doc_ref.get()
        if doc.exists:
            encrypted_text = doc.to_dict().get('text')
            if context.user_data['algorithm'] == 'AES':
                cipher = AES.new(aes_key.encode(), AES.MODE_CBC, aes_iv.encode())
                decrypted_text = unpad(cipher.decrypt(encrypted_text), AES.block_size).decode('utf-8')
            elif context.user_data['algorithm'] == 'RSA':
                private_key = context.user_data.get('private_key')
                if private_key:
                    cipher_rsa = PKCS1_OAEP.new(RSA.import_key(private_key))
                    decrypted_text = cipher_rsa.decrypt(encrypted_text)
                else:
                    update.message.reply_text('No private key found for RSA decryption')
                    return
            elif context.user_data['algorithm'] == 'ROT13': 
                decrypted_text = codecs.decode(encrypted_text, 'rot_13')
            update.message.reply_text(f'Decrypted text: {decrypted_text}')
        else:
            update.message.reply_text('No encrypted text found for the provided ID.')

def main() -> None:
    try:
        updater = Updater(api_token, use_context=True)
        dispatcher = updater.dispatcher

        dispatcher.add_handler(CommandHandler("start", start))
        dispatcher.add_handler(CommandHandler("encrypt", encrypt_command))
        dispatcher.add_handler(CommandHandler("decrypt", decrypt_command))
        dispatcher.add_handler(CallbackQueryHandler(agree, pattern='^agree$'))
        dispatcher.add_handler(CallbackQueryHandler(operation, pattern='^(encrypt|decrypt)$'))
        dispatcher.add_handler(CallbackQueryHandler(algorithm, pattern='^(AES|RSA|ROT13)$')) 
        dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, save))

        updater.start_polling()
        updater.idle()
    except telegram.error.Conflict as e:
        print("Conflict terjadi. Pastikan hanya 1 instance yang berjalan.")
        print(f"Error details: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
