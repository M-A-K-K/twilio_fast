# from fastapi import FastAPI, HTTPException, WebSocket, Request
# from fastapi.middleware.cors import CORSMiddleware
# import logging
# import os
# from twilio.rest import Client

# print("WebSocket URL:", os.getenv("WEB_SOCKET_URL"))

# TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
# TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
#   # Your Twilio phone number

# def create_twilio_client():
#     return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# def configure_logging():
#     logger = logging.getLogger()
#     logger.setLevel(logging.INFO)

#     # Console handler
#     console_handler = logging.StreamHandler()
#     console_handler.setLevel(logging.INFO)
#     console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

#     # Add the console handler to the logger
#     logger.addHandler(console_handler)

# application = FastAPI()
# application.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# @application.get("/")
# def home(request: Request):
#     return {"request": "success app v1"}

# @application.websocket("/ws")
# async def voicebot_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     logging.info("WebSocket connection accepted")
#     try:
#         while True:
#             data = await websocket.receive_text()
#             logging.info(f"Received data: {data}")
#             # Process audio data or commands here
#     except Exception as e:
#         logging.error(f"Error in WebSocket connection: {e}")
#     finally:
#         logging.info("WebSocket connection closed")
#         await websocket.close()

# @application.get("/make_call")
# async def call():
#     try:
#         websocket_url = 'https://7f37-39-34-175-20.ngrok-free.app/ws'  # Ensure this is set in your environment

#         if not websocket_url:
#             raise HTTPException(status_code=500, detail="WebSocket URL is missing")

#         client = create_twilio_client()

#         call = client.calls.create(
#             to='+923170700995',  # Hardcoded recipient number
#             from_=TWILIO_NUMBER,
#             twiml=f'''
#                 <Response>
#                     <Say voice="alice" language="en-US">
#                         Hello, this is your assistant. The call will now be connected.
#                     </Say>
#                     <Connect>
#                         <Stream url="{websocket_url}" />
#                     </Connect>
#                 </Response>
#             '''
#         )

#         call_sid = call.sid
#         logging.info(f"Call initiated with SID: {call_sid}")
#         return {"call_sid": call_sid}

#     except Exception as e:
#         logging.error(f"Error in initiating call: {e}")
#         raise HTTPException(status_code=500, detail=str(e))

# if __name__ == "__main__":
#     import uvicorn
#     configure_logging()
#     uvicorn.run(application, host="0.0.0.0", port=8000)



from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
from twilio.rest import Client
from twilio.twiml.voice_response import VoiceResponse, Gather
import logging
import os
import uuid
import openai  # Assuming OpenAI is used for LLM

# Load environment variables
print("WebSocket URL:", os.getenv("WEB_SOCKET_URL"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")  # Your Twilio phone number
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CUSTOM_PROMPT = os.getenv("CUSTOM_PROMPT", "You are a helpful assistant.")

def create_twilio_client():
    return Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

def configure_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))

    # Add the console handler to the logger
    logger.addHandler(console_handler)

# Initialize OpenAI API client
openai.api_key = OPENAI_API_KEY

application = FastAPI()
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# For maintaining session data
sessions = {}

@application.get("/")
def home(request: Request):
    return {"request": "success app v1"}

@application.websocket("/ws")
async def voicebot_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection accepted")

    session_id = str(uuid.uuid4())
    sessions[session_id] = {"conversation": []}

    try:
        while True:
            data = await websocket.receive_bytes()  # Expect audio data
            logging.info(f"Received audio data of size: {len(data)} bytes")

            # Process audio data and respond
            response_text = "Audio received and processed"
            await websocket.send_text(response_text)

    except Exception as e:
        logging.error(f"Error in WebSocket connection: {e}")
    finally:
        logging.info("WebSocket connection closed")
        await websocket.close()
        del sessions[session_id]

@application.post("/make_call")
async def make_call():
    try:
        websocket_url = os.getenv("WEB_SOCKET_URL")  # Ensure this is set in your environment

        if not websocket_url:
            raise HTTPException(status_code=500, detail="WebSocket URL is missing")

        client = create_twilio_client()

        call = client.calls.create(
            to='+923170700995',  # Replace with the destination phone number
            from_=TWILIO_NUMBER,
            url=f"https://yourdomain.com/voice"  # Replace with your publicly accessible URL
        )

        call_sid = call.sid
        logging.info(f"Call initiated with SID: {call_sid}")
        return {"call_sid": call_sid}

    except Exception as e:
        logging.error(f"Error creating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@application.post("/voice")
async def voice(request: Request):
    form_data = await request.form()
    response = VoiceResponse()

    session_id = form_data.get('session_id')
    if not session_id:
        session_id = str(uuid.uuid4())
        sessions[session_id] = {"conversation": []}
        
        # Initial greeting message
        initial_message = "Hi, how can I help you today?"
        response.say(initial_message, language='en-IN')

        # Store the initial greeting message in conversation history
        sessions[session_id]['conversation'].append({'assistant': initial_message})

        # Gather user input
        gather = Gather(
            input='speech',
            timeout=10,
            speechTimeout='auto',
            action='/voice',
            method='POST',
            language='en-IN'
        )
        response.append(gather)
        response.say("Please say something after the beep.", language='en-IN')

    else:
        user_speech = form_data.get('SpeechResult', 'No speech detected')

        # Print the user's speech to the console
        print(f"User speech: {user_speech}")

        # Normalize the user speech for better matching
        user_speech_normalized = user_speech.strip().lower()

        # Store user speech in conversation history
        sessions[session_id]['conversation'].append({'user': user_speech})

        # Check if the user said "Goodbye" exactly or as part of their speech
        if "goodbye" in user_speech_normalized:
            print("Ending the call.")
            response.say("Goodbye! Ending the call.")
            sessions[session_id]['conversation'].append({'assistant': "Goodbye! Ending the call."})
            response.hangup()
        else:
            # Combine the custom prompt with the user's speech
            prompt = f"{CUSTOM_PROMPT}\nUser said: {user_speech}\nResponse:"

            try:
                # Call the LLM API
                completion = openai.Completion.create(
                    engine="text-davinci-003",  # Use the appropriate model engine
                    prompt=prompt,
                    max_tokens=150  # Adjust the number of tokens as needed
                )
                response_text = completion.choices[0].text.strip()
                print(f"Model response: {response_text}")

                # Ensure the response is within a reasonable length
                if not response_text:
                    response_text = "Sorry, I didn't catch that."

                answer = ' '.join(response_text.split()[:200])  # Ensure the response is within 200 characters

                # Store assistant's response in conversation history
                sessions[session_id]['conversation'].append({'assistant': answer})

                # Respond with the assistant's answer and continue the conversation
                response.say(answer, language='en-IN')

                # Gather user input again
                gather = Gather(
                    input='speech',
                    timeout=10,
                    speechTimeout='auto',
                    action='/voice',
                    method='POST',
                    language='en-IN'
                )
                response.append(gather)
                response.say("Please say something after the beep.", language='en-IN')

            except Exception as e:
                print(f"Error: {e}")
                response.say("Sorry, there was an error processing your request. Please try again.", language='en-IN')

                # Gather user input again
                gather = Gather(
                    input='speech',
                    timeout=10,
                    speechTimeout='auto',
                    action='/voice',
                    method='POST',
                    language='en-IN'
                )
                response.append(gather)
                response.say("Please say something after the beep.", language='en-IN')

    return Response(content=str(response), media_type='text/xml')

if __name__ == "__main__":
    import uvicorn
    configure_logging()
    uvicorn.run(application, host="0.0.0.0", port=8000)
