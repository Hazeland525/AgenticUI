# Google Cloud Speech-to-Text Setup

## Where to Put Your API Key

You have two options for authenticating with Google Cloud Speech-to-Text:

### Option 1: Service Account JSON File (Recommended)

1. Create a service account in your Google Cloud project:
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Navigate to "IAM & Admin" > "Service Accounts"
   - Create a new service account or use an existing one
   - Download the JSON key file

2. Place the JSON file in your `backend/` directory (or any secure location)

3. Add to your `.env` file in the `backend/` directory:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
   ```
   
   Example (if the file is in the backend directory):
   ```
   GOOGLE_APPLICATION_CREDENTIALS=./service-account-key.json
   ```

### Option 2: API Key (Less Common)

If you have a Google Cloud API key specifically for Speech-to-Text:

1. Add to your `.env` file in the `backend/` directory:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

**Note:** The API key approach may have limitations. Service account JSON is the recommended method.

## Environment Variables

Your `backend/.env` file should now include:

```env
# Existing
GEMINI_API_KEY=your_gemini_api_key_here

# New - Choose ONE of these:
GOOGLE_APPLICATION_CREDENTIALS=./path/to/service-account-key.json
# OR
GOOGLE_CLOUD_SPEECH_API_KEY=your_speech_api_key_here
```

## Installation

After adding the credentials, install the new dependency:

```bash
cd backend
pip install -r requirements.txt
```

This will install `google-cloud-speech>=2.21.0`.

## Testing

1. Start the backend server:
   ```bash
   cd backend
   python main.py
   ```

2. The frontend will automatically use Google Cloud Speech-to-Text when you:
   - Press and hold "S" key
   - Speak your question
   - Release "S" key

The audio will be captured, sent to Google Cloud Speech-to-Text, transcribed, refined by Gemini, and then submitted as a question.

## Troubleshooting

- **"No credentials found"**: Make sure you've set either `GOOGLE_APPLICATION_CREDENTIALS` or `GEMINI_API_KEY` in your `.env` file
- **"Service account file not found"**: Check that the path in `GOOGLE_APPLICATION_CREDENTIALS` is correct
- **"Permission denied"**: Make sure your service account has the "Cloud Speech-to-Text API User" role enabled
- **Enable the API**: Make sure the Cloud Speech-to-Text API is enabled in your Google Cloud project
