from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Say, Record, Play, Pause
import os

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
    
    #simulate customers' emergency pressing '0' to jump to a representative
    response.play(digits='0')
    response.say("Please connect me to a representative.")
    response.pause(length=2)
    response.play(digits='0')
    response.say("Please connect me to a representative.")
    response.pause(length=1)
    response.play(digits='0')

    # waiting for the representative to pick up
    response.pause(length=5)

    # dynamic voice content
    question_text = (
        f"Hi, I'm looking to move from {from_city} to {to_city}. "
        "Could you please tell me the estimated price, whether packing services are included, "
        "whether insurance is available, and how long it would take? Thank you."
    )
    response.say(question_text, voice='alice', language='en-US')

    # record the response
    response.record(
        max_length=120,
        timeout=10,
        action="/record",
        method="POST",
        transcribe=False,
        play_beep=True
    )

    return Response(str(response), mimetype='text/xml')

# handle the callback of record and print the link of the recording file
@app.route("/record", methods=["GET","POST"])
def record():
    recording_url = request.form.get("RecordingUrl")
    print(f"Recording url received: {recording_url}")
    return Response("Thanks!", mimetype='text/plain')
    
# run the flask app
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
