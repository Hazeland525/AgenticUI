# Google Cloud Speech-to-Text Setup

The app uses **Speech-to-Text V2 with the Chirp 2 model** when a project ID and credentials are available (best accuracy). Otherwise it falls back to V1 (API key or legacy client).

## Option 1: V2 with Chirp 2 (Recommended – best accuracy)

[Chirp 2](https://cloud.google.com/speech-to-text/v2/docs/chirp_2-model) is a high-accuracy model available only in the V2 API.

1. **Create a service account** in your [Google Cloud Console](https://console.cloud.google.com/):
   - IAM & Admin → Service Accounts → Create → Download JSON key.

2. **Enable the Speech-to-Text API** (and Cloud Speech-to-Text API if listed) for your project.

3. **Grant the service account** the “Cloud Speech-to-Text API User” role.

4. **Configure `backend/.env`:**
   ```env
   GOOGLE_CLOUD_PROJECT=your-gcp-project-id
   GOOGLE_APPLICATION_CREDENTIALS=./path/to/service-account-key.json
   ```
   The project ID can also be read from the service account JSON; setting `GOOGLE_CLOUD_PROJECT` explicitly is optional in that case.

5. **Optional – region:** Chirp 2 is available in `us-central1`, `europe-west4`, and `asia-southeast1`. Default is `us-central1`. Override with:
   ```env
   SPEECH_V2_LOCATION=us-central1
   ```

## Option 2: API key only (V1 REST fallback)

If you only set `GEMINI_API_KEY`, the app uses the **V1 REST** API (no Chirp 2). Accuracy is lower than V2 + Chirp 2.

```env
GEMINI_API_KEY=your_api_key_here
```

To get Chirp 2, use Option 1 (project + service account or ADC).

## Installation

```bash
cd backend
pip install -r requirements.txt
```

This installs `google-cloud-speech` (V1 and V2 clients).

## Testing

1. Start the backend: `cd backend && python main.py`
2. In the app, hold **S**, speak your question, then release **S**.

Audio is sent to Speech-to-Text (V2 Chirp 2 when configured, otherwise V1), then refined by Gemini and submitted as the question.

## Troubleshooting

- **"No credentials found"**: Set `GOOGLE_CLOUD_PROJECT` and `GOOGLE_APPLICATION_CREDENTIALS` for V2 Chirp 2, or `GEMINI_API_KEY` for V1 REST.
- **"Service account file not found"**: Fix the path in `GOOGLE_APPLICATION_CREDENTIALS` (relative paths are from `backend/`).
- **"V2 init failed"**: Ensure the Speech-to-Text API is enabled and the service account has the “Cloud Speech-to-Text API User” role. Chirp 2 is available in `us-central1`, `europe-west4`, and `asia-southeast1`—set `SPEECH_V2_LOCATION` if needed.
- **Using Chirp 2**: You must set `GOOGLE_CLOUD_PROJECT` (or use a service account JSON that includes `project_id`); API key alone uses V1 only.
