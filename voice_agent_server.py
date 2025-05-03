from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Say, Record, Play, Pause
import os
import requests
from dotenv import load_dotenv
from whisper import transcribe_audio
from openai import OpenAI

load_dotenv()
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

# The voice webhook interface accessed after dialing through twilio
# set to-city and from-city accorfing to url parameters
@app.route("/voice",methods=["GET","POST"])
def voice():
    print("📞 /voice 接口被访问")
    response = VoiceResponse()

    # access city parameters
    from_city = request.args.get("from","Boston")
    to_city = request.args.get("to","New York")

    # play the greeting message
    response.say("Connecting you to the next available moving company...")
    response.say("Hi, I'm calling to get a moving quote. Please connect me to a representative.", voice='alice', language='en-US')
    response.pause(length=3)

    #simulate customers' emergency pressing '0' to jump to a representative
    response.play(digits='0')
    response.say("Please connect me to a representative.")
    response.pause(length=4)
    response.play(digits='0')
    response.say("Please connect me to a representative.")
    response.pause(length=4)
    response.play(digits='0')

    # waiting for the representative to pick up
    response.pause(length=6)

    # dynamic voice content
    questions = [
        f"Hi, I'm planning to move from {from_city} to {to_city}. Could you give me a rough price estimate?",
        "Are packing and unpacking services included in the quote?",
        "Is insurance available for my belongings during the move?",
        "How many days would the move typically take from pickup to delivery?",
        "What is the type of the vehicle used for transportation?"
    ]

    for idx, question in enumerate(questions):
        response.say(question, voice='alice', language='en-US')
        response.pause(length=15)  # Allow 15 seconds to answer

        # Record after each question, with index tracking for file naming
        response.record(
            max_length=15,
            timeout=5,  # Stop recording after 5 seconds of silence
            action=f"/record?question_id={idx+1}",
            method="POST",
            transcribe=False,
            play_beep=True
        )

    print("✅ TwiML generated:\n", str(response))
    return Response(str(response), mimetype='text/xml')

# Handle the recording callback from Twilio
# Download and transcribe the audio
@app.route("/record", methods=["GET","POST"])
def record():
    recording_url = request.form.get("RecordingUrl")
    question_id = request.args.get("question_id", "unknown")
    filename = f"recording_q{question_id}.mp3"
    print(f"✅ Recording URL received for Q{question_id}: {recording_url}")
    
    if not recording_url:
        print("❌ No recording URL provided")
        return Response("No recording found", mimetype='text/plain')
    
    mp3_url = recording_url + ".mp3"

    try:
        # Download the MP3 audio
        res = requests.get(mp3_url, auth=(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN))
        with open(filename, "wb") as f:
            f.write(res.content)
        print(f"✅ Audio saved as {filename}")

        # Run transcription using whisper.py
        client = OpenAI(api_key=OPENAI_API_KEY)
        transcribe_audio(filename, client)

    except Exception as e:
        print("❌ Error downloading or transcribing:", e)

    return Response("Thanks!", mimetype='text/plain')

# run the flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
