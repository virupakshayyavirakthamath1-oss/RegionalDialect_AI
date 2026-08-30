# RegionalDialect AI - Complete BCA Project

## Features
- Landing page with feature showcase and footer
- Registration and login
- Secure password hashing, CSRF protection and secure session settings
- Dashboard and private history
- Grammar/style correction
- Kanglish, Hinglish and Tanglish detection
- Regional slang detection and explanations
- Personal dictionary
- Practice mode
- Voice input and text-to-speech
- PDF and CSV reports
- Dark mode and mobile responsive UI
- Security headers and basic rate limiting

## Run on Windows
```cmd
cd /d "C:\Users\Vikas Viraktamath\Desktop\Pooja"
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Mobile on same Wi-Fi
The app uses host 0.0.0.0. Find the PC IPv4 address with `ipconfig` and open `http://YOUR_IP:5000` on the phone.

## Production
Do not use Flask's development server for production. Use Gunicorn/waitress behind a reverse proxy with a real HTTPS certificate. Set a strong `SECRET_KEY` and `HTTPS_ONLY=1` in the production environment.

## NLP note
The included engine is a lightweight hybrid baseline: marker-based dialect detection + rules + slang dictionary. For the research component, train a Transformer on a custom labelled corpus and replace/augment `nlp/checker.py`.
