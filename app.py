"""
Agente de Voz Bíblico
=====================
Flask + Twilio + Anthropic Claude
"""

from flask import Flask, request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
import anthropic
import os

app = Flask(__name__)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

SYSTEM_PROMPT = """Eres 'Heraldo', un narrador bíblico cálido y sabio.
Cuando te pidan una historia bíblica, nárrala en exactamente 70-80 palabras.
Usa lenguaje sencillo y emotivo. Termina con una enseñanza de máximo 10 palabras.
No uses listas, asteriscos ni formato. Solo narración fluida en español."""


def generar_historia(peticion: str) -> str:
    try:
        message = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": f"Narra la historia bíblica de: {peticion}"}
            ]
        )
        historia = message.content[0].text.strip()
        print(f"[Historia generada] {historia}")
        return historia

    except Exception as e:
        print(f"Error Claude API: {e}")
        return "Lo siento, en este momento no puedo narrar la historia. Por favor intenta más tarde."


@app.route("/voz/bienvenida", methods=["GET", "POST"])
def bienvenida():
    resp = VoiceResponse()
    gather = Gather(
        input="speech",
        action="/voz/narrar",
        method="POST",
        language="es-419",
        speech_timeout="auto",
        timeout=6
    )
    gather.say(
        "Bienvenido al narrador bíblico para mi Babucita. "
        "¿Qué historia de la Biblia deseas escuchar hoy?",
        voice="Polly.Miguel",
        language="es-US"
    )
    resp.append(gather)
    resp.redirect("/voz/bienvenida")
    return Response(str(resp), mimetype="text/xml")


@app.route("/voz/narrar", methods=["GET", "POST"])
def narrar():
    resp = VoiceResponse()
    texto = request.form.get("SpeechResult", "").strip()

    if not texto:
        resp.say(
            "No entendí bien. Por favor llama nuevamente.",
            voice="Polly.Miguel", language="es-US"
        )
        resp.hangup()
        return Response(str(resp), mimetype="text/xml")

    print(f"[Petición] {texto}")
    historia = generar_historia(texto)

    resp.say(historia, voice="Polly.Miguel", language="es-US")

    gather = Gather(
        input="speech",
        action="/voz/narrar",
        method="POST",
        language="es-419",
        speech_timeout="auto",
        timeout=5
    )
    gather.say(
        "¿Deseas escuchar otra historia? Dime cuál.",
        voice="Polly.Miguel", language="es-US"
    )
    resp.append(gather)

    resp.say(
        "Que Dios te bendiga. Hasta pronto.",
        voice="Polly.Miguel", language="es-US"
    )
    resp.hangup()
    return Response(str(resp), mimetype="text/xml")


@app.route("/health", methods=["GET"])
def health():
    return {"status": "ok", "agente": "Narrador Bíblico Maranatha"}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
