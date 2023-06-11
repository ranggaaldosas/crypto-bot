## Installation

- Install

```python
  pip install python-telegram-bot firebase-admin pycryptodomex python-dotenv
```

- Setup .env file

```python
API_TOKEN=<your_api_token>
FIREBASE_CREDENTIALS=<firebase_credentials_path>
AES_KEY=<aes_key>
AES_IV=<aes_iv>
PRIVATE_KEY=<private_key_content>
```

- Add your firebase.json

```python
{
  "type": "service_account",
  "project_id": "crypto4you-bot",
  "private_key_id": "YOUR_PRIVATE_KEY_ID",
  "private_key": "YOUR_PRIVATE_KEY"
}

```

- Run Script

```python
  python cryptobot.py
```

## Documentation

![ScreenShot](https://i.ibb.co/p1sQTMs/Screenshot-42.png)
![ScreenShot](https://i.ibb.co/jzsSXFW/Screenshot-43.png)
