from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Say, Record, Redirect, Pause
import os
import requests
from dotenv import load_dotenv
from whisper import transcribe_audio, OpenAI
import subprocess
import pandas as pd

load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# Ordered question list
QUESTION_LIST = [
    "Hi, I'm planning to move from {from_city} to {to_city}. Could you give me a rough price estimate?",
    "Are packing and unpacking services included in the quote?",
    "Is insurance available for my belongings during the move?",
    "How many days would the move typically take from pickup to delivery?",
    "What is the type of the vehicle used for transportation?"
]

@app.route("/voice", methods=["GET", "POST"])
def voice():
    step = int(request.args.get("step", 0))
    from_city = request.args.get("from", "Boston")
    to_city = request.args.get("to", "New York")

    response = VoiceResponse()

    if step == 0:
        # Initial greeting and representative jump
        response.say("Connecting you to the next available moving company...")
        response.say("Hi, I'm calling to get a moving quote. Please connect me to a representative.", voice='alice')
        response.play(digits='0')
        response.pause(length=5)
        response.play(digits='0')
        response.pause(length=5)
        response.play(digits='0')
        response.pause(length=5)
        response.redirect("/voice?step=1&from={}&to={}".format(from_city, to_city))
        return Response(str(response), mimetype='text/xml')

    if step <= len(QUESTION_LIST):
        question = QUESTION_LIST[step - 1].format(from_city=from_city, to_city=to_city)
        response.say(question, voice='alice')
        response.pause(length=10)
        response.record(
            max_length=10,
            timeout=3,
            play_beep=True,
            action=f"/record?step={step}&from={from_city}&to={to_city}",
            method="POST"
        )
    else:
        response.say("Thank you for your time. Goodbye!", voice='alice')

    return Response(str(response), mimetype='text/xml')

@app.route("/record", methods=["GET", "POST"])
def record():
    step = int(request.args.get("step", 0))
    from_city = request.args.get("from", "Boston")
    to_city = request.args.get("to", "New York")
    recording_url = request.form.get("RecordingUrl")
    filename = f"recording_q{step}.mp3"

    if not recording_url:
        return Response("No recording", mimetype='text/plain')

    mp3_url = recording_url + ".mp3"
    try:
        res = requests.get(mp3_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        with open(filename, "wb") as f:
            f.write(res.content)
        print(f"✅ Saved recording {filename}")

        client = OpenAI(api_key=OPENAI_API_KEY)
        transcribe_audio(filename, client)

        subprocess.run(["python", "extract_dataset.py"], check=True)

        df = pd.read_csv("moving_dataset.csv")
        print(df.tail())

    except Exception as e:
        print("❌ Recording error:", e)

    # Redirect to next step
    next_step = step + 1
    twiml = VoiceResponse()
    twiml.redirect(f"/voice?step={next_step}&from={from_city}&to={to_city}")
    return Response(str(twiml), mimetype='text/xml')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)