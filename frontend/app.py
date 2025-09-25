import os
import streamlit as st
import requests
import pandas as pd
import speech_recognition as sr
from gtts import gTTS
from deep_translator import GoogleTranslator

st.set_page_config(page_title="Crop Recommendation System", layout="centered")
st.title("🌾 AI-based Crop Recommendation System (Final Prototype)")

API = "http://127.0.0.1:8000"

SUPPORTED_TTS_LANGS = {
    "en": "en", "hi": "hi", "ta": "ta", "te": "te", "bn": "bn", "gu": "gu", "kn": "kn",
    "ml": "ml", "mr": "mr", "pa": "pa", "ur": "ur", "fr": "fr", "es": "es", "ar": "ar",
    "ru": "ru", "ja": "ja", "or": "or"
}

SPEECH_LANG_MAP = {
    "en": "en-US", "hi": "hi-IN", "ta": "ta-IN", "te": "te-IN", "bn": "bn-IN", "gu": "gu-IN",
    "kn": "kn-IN", "ml": "ml-IN", "mr": "mr-IN", "pa": "pa-IN", "ur": "ur-PK",
    "fr": "fr-FR", "es": "es-ES", "ar": "ar-EG", "ru": "ru-RU", "ja": "ja-JP", "or": "or-IN"
}

mode = st.radio("Select Access Mode:", ["Smartphone", "Button Phone"])

if mode == "Smartphone":
    st.write("Smartphone Mode — full app (voice + text + TTS)")
    lang = st.text_input("Enter language code (e.g., en, hi, or, fr, es):", "en")
    district = st.selectbox("Select your district", ["Ranchi", "Ranchi2"])

    def voice_input(selected_lang: str) -> str:
        recognizer = sr.Recognizer()
        try:
            with sr.Microphone() as source:
                st.info("🎤 Speak now... (listening for up to 8 seconds)")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            speech_lang = SPEECH_LANG_MAP.get(selected_lang, "en-US")
            try:
                text = recognizer.recognize_google(audio, language=speech_lang)
                return text
            except Exception:
                st.warning("Could not recognise speech or network issue with Google Speech API.")
                return ""
        except Exception:
            st.warning("Microphone unavailable or not configured on this machine.")
            return ""

    st.subheader("🧑‍🌾 Farmer Input Data")
    soil_ph = st.number_input("Soil pH", min_value=0.0, max_value=14.0, value=6.5, step=0.1)
    moisture = st.number_input("Soil Moisture (%)", min_value=0.0, max_value=100.0, value=25.0, step=0.1)
    n = st.number_input("Nitrogen (N)", min_value=0.0, value=50.0, step=1.0)
    p = st.number_input("Phosphorus (P)", min_value=0.0, value=30.0, step=1.0)
    k = st.number_input("Potassium (K)", min_value=0.0, value=40.0, step=1.0)
    last_crop = st.text_input("Last season's crop (optional)", "")

    if st.button("🎤 Use Voice Input"):
        spoken = voice_input(lang)
        if spoken:
            last_crop = spoken
            st.success(f"Detected voice input: {spoken}")

    if st.button("Get Recommendations"):
        payload = {
            "district": district,
            "soil_ph": float(soil_ph),
            "soil_moisture": float(moisture),
            "nutrient_n": float(n),
            "nutrient_p": float(p),
            "nutrient_k": float(k),
            "last_crop": last_crop,
            "top_k": 3
        }

        try:
            res = requests.post(f"{API}/recommendations", json=payload, timeout=10)
        except Exception:
            st.error("Could not connect to backend. Is uvicorn running on http://127.0.0.1:8000 ?")
            res = None

        if res and res.status_code == 200:
            response = res.json()
            weather = response.get("weather", {})
            data = response.get("recommendations", [])

            if len(data) > 0 and isinstance(data[0], dict) and data[0].get("error"):
                st.error("❌ Input Validation Failed")
                for err in data[0].get("details", []):
                    st.warning(err)
            else:
                df = pd.DataFrame(data)

                st.subheader("🌦 Weather Data (from Agro API)")
                st.write(f"Rainfall: {weather.get('rainfall', 'N/A')} mm")
                st.write(f"Temperature: {round(weather.get('temperature', 0), 2)} °C")

                st.subheader("🌾 Crop Recommendations")
                cols = [c for c in ['crop', 'score', 'yield', 'profit', 'sustainability', 'rainfall', 'temperature'] if c in df.columns]
                st.dataframe(df[cols])

                st.success(f"✅ Suggested crop: {data[0].get('crop', 'N/A')}")

                st.download_button("Download CSV", df.to_csv(index=False), "recommendations.csv")

                final_text = f"Suggested crop is {data[0].get('crop', 'N/A')} with expected yield {data[0].get('yield', 'N/A')} tons per acre."
                try:
                    translated = GoogleTranslator(source="auto", target=lang).translate(final_text)
                except Exception:
                    translated = final_text

                st.info(f"🗣️ {translated}")

                tts_lang = SUPPORTED_TTS_LANGS.get(lang, "en")
                try:
                    tts = gTTS(text=translated, lang=tts_lang)
                    tts.save("output.mp3")
                    st.audio("output.mp3")
                except Exception:
                    st.warning("Voice not available for this language; showing text only.")
        else:
            st.error("Failed to fetch recommendations. Ensure backend is running.")
else:
    mode = 'button'
    # Button phone mode content intentionally simplified for zipped prototype.
    # Full version available in the README and earlier messages.
    print('Button phone mode not expanded in this zipped prototype.')