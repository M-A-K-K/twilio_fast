from fastapi import FastAPI, HTTPException, WebSocket, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from twilio.rest import Client

print("WebSocket URL:", os.getenv("WEB_SOCKET_URL"))

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER")
  # Your Twilio phone number

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

application = FastAPI()
application.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@application.get("/")
def home(request: Request):
    return {"request": "success app v1"}

@application.websocket("/ws")
async def voicebot_endpoint(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket connection accepted")
    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Received data: {data}")
            # Process audio data or commands here
    except Exception as e:
        logging.error(f"Error in WebSocket connection: {e}")
    finally:
        logging.info("WebSocket connection closed")
        await websocket.close()

@application.get("/make_call")
async def call():
    try:
        websocket_url = 'https://7f37-39-34-175-20.ngrok-free.app/ws'  # Ensure this is set in your environment

        if not websocket_url:
            raise HTTPException(status_code=500, detail="WebSocket URL is missing")

        client = create_twilio_client()

        call = client.calls.create(
            to='+923170700995',  # Hardcoded recipient number
            from_=TWILIO_NUMBER,
            twiml=f'''
                <Response>
                    <Say voice="alice" language="en-US">
                        Hello, this is your assistant. The call will now be connected.
                    </Say>
                    <Connect>
                        <Stream url="{websocket_url}" />
                    </Connect>
                </Response>
            '''
        )

        call_sid = call.sid
        logging.info(f"Call initiated with SID: {call_sid}")
        return {"call_sid": call_sid}

    except Exception as e:
        logging.error(f"Error in initiating call: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    configure_logging()
    uvicorn.run(application, host="0.0.0.0", port=8000)
