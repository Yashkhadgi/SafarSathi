# Monkey-patch gradio_client for compatibility with modern Pydantic boolean schemas
try:
    import gradio_client.utils as _gc_utils
    _orig_get_type = _gc_utils.get_type
    _orig_json_schema = _gc_utils._json_schema_to_python_type

    def _safe_get_type(schema):
        if not isinstance(schema, dict):
            return {}
        return _orig_get_type(schema)

    def _safe_json_schema(schema, defs):
        if not isinstance(schema, dict) or schema == {}:
            return "Any"
        return _orig_json_schema(schema, defs)

    _gc_utils.get_type = _safe_get_type
    _gc_utils._json_schema_to_python_type = _safe_json_schema
except Exception:
    pass

import gradio as gr
import sys
import os
import tempfile

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.orchestrator_graph import run_agent
from config.settings import validate_config
from tools.currency_tool import convert_currency
from tools.voice_tool import speech_to_text, text_to_speech

validate_config()

# ── Shared session IDs ────────────────────────────────────────────────────────
CHAT_SESSION = "gradio-chat-session"
VOICE_SESSION = "gradio-voice-session"


# ── Chat handler ──────────────────────────────────────────────────────────────
def chat_with_agent(message, history):
    agent_name, response = run_agent(CHAT_SESSION, message)
    return f"**[Routed to: {agent_name}]**\n\n{response}"


# ── Currency handler ──────────────────────────────────────────────────────────
def do_convert(amount, from_cur, to_cur):
    result = convert_currency(float(amount), from_cur, to_cur)
    if "error" in result:
        return f"Error: {result['error']}"
    return f"{amount} {from_cur} = {result['converted_amount']} {to_cur}  (rate: {result['rate']})"


# ── Voice handler ─────────────────────────────────────────────────────────────
def handle_voice(audio_path, voice_lang):
    """
    audio_path: file path Gradio gives us from gr.Audio(type='filepath')
    voice_lang: language code selected by user (hi-IN, en-IN, etc.)
    Returns: (transcript_text, agent_reply_text, audio_reply_path)
    """
    if audio_path is None:
        return "❌ No audio recorded.", "", None

    # Step 1: Read audio file
    try:
        with open(audio_path, "rb") as f:
            audio_bytes = f.read()
        file_ext = os.path.splitext(audio_path)[-1].lstrip(".") or "wav"
    except Exception as e:
        return f"❌ Could not read audio: {e}", "", None

    # Step 2: STT — audio → text
    transcript = speech_to_text(audio_bytes, file_format=file_ext, lang_code=voice_lang)
    if not transcript:
        return "❌ Could not understand audio. Please speak clearly and try again.", "", None

    # Step 3: Route through agent
    agent_name, reply_text = run_agent(VOICE_SESSION, transcript)
    display_reply = f"**[Routed to: {agent_name}]**\n\n{reply_text}"

    # Step 4: TTS — agent reply → audio
    # Detect if reply has Hindi characters → use hi-IN; else use selected lang
    has_hindi = any('\u0900' <= ch <= '\u097f' for ch in reply_text)
    tts_lang = "hi-IN" if has_hindi else voice_lang
    speaker = "advait"

    audio_bytes_out = text_to_speech(reply_text, lang_code=tts_lang, speaker=speaker)

    audio_output_path = None
    if audio_bytes_out:
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.write(audio_bytes_out)
        tmp.close()
        audio_output_path = tmp.name

    return transcript, display_reply, audio_output_path


# ── Styling ───────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
:root, .dark {
    --body-background-fill: #1a1a17;
    --background-fill-primary: #1a1a17;
    --background-fill-secondary: #24241f;
    --block-background-fill: #24241f;
    --border-color-primary: #4b4b3a;
    --body-text-color: #e8e6dc;
    --block-title-text-color: #e8e6dc;
    --button-primary-background-fill: #556b2f;
    --button-primary-background-fill-hover: #6b8536;
    --button-primary-text-color: #f5f5ef;
}
body, .gradio-container {
    background-color: #1a1a17 !important;
}
.message.user {
    background-color: #556b2f !important;
    color: #f5f5ef !important;
}
.message.bot {
    background-color: #24241f !important;
    color: #e8e6dc !important;
    border: 1px solid #4b4b3a !important;
}
.voice-hint {
    font-size: 0.85rem;
    color: #a0a08a;
    margin-top: 4px;
}
"""

theme = gr.themes.Base(
    primary_hue=gr.themes.colors.green,
    neutral_hue=gr.themes.colors.stone,
).set(
    body_background_fill="#1a1a17",
    block_background_fill="#24241f",
    border_color_primary="#4b4b3a",
)

CURRENCY_CHOICES = ["INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD", "AED", "SGD"]

LANG_CHOICES = [
    ("Hindi (हिन्दी)", "hi-IN"),
    ("English", "en-IN"),
    ("Bengali (বাংলা)", "bn-IN"),
    ("Tamil (தமிழ்)", "ta-IN"),
    ("Telugu (తెలుగు)", "te-IN"),
    ("Marathi (मराठी)", "mr-IN"),
    ("Gujarati (ગુજરાતી)", "gu-IN"),
    ("Kannada (ಕನ್ನಡ)", "kn-IN"),
]


# ── Build UI ──────────────────────────────────────────────────────────────────
with gr.Blocks(theme=theme, css=CUSTOM_CSS, title="🧳 Multilingual Tourist Assistant") as demo:

    gr.Markdown(
        "# 🧳 Multilingual Tourist Assistant\n"
        "Plan trips · Get local info · Emergency help · Cultural tips · Voice support"
    )

    # ── Tab 1: Chat ────────────────────────────────────────────────────────
    with gr.Tab("💬 Chat"):
        gr.ChatInterface(
            fn=chat_with_agent,
            description="Type your query — routes to Planner, Info, Safety, or Etiquette agent automatically.",
            chatbot=gr.Chatbot(likeable=True, height=500),
        )

        with gr.Accordion("💱 Currency Converter", open=False):
            with gr.Row():
                amount_input = gr.Number(value=100, label="Amount")
                from_cur = gr.Dropdown(choices=CURRENCY_CHOICES, value="INR", label="From")
                to_cur = gr.Dropdown(choices=CURRENCY_CHOICES, value="USD", label="To")
            convert_btn = gr.Button("Convert", variant="primary")
            result_box = gr.Textbox(label="Result", interactive=False)
            convert_btn.click(fn=do_convert, inputs=[amount_input, from_cur, to_cur], outputs=result_box)

    # ── Tab 2: Voice ───────────────────────────────────────────────────────
    with gr.Tab("🎤 Voice Assistant"):
        gr.Markdown(
            "### 🎤 Speak your question — get a voice reply!\n"
            "Supports Hindi, English, Bengali, Tamil, Telugu, Marathi, Gujarati, Kannada."
        )

        with gr.Row():
            with gr.Column(scale=1):
                voice_lang = gr.Dropdown(
                    choices=LANG_CHOICES,
                    value="hi-IN",
                    label="🌐 Your Language (for speech recognition)",
                )
                mic_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎙️ Record your question",
                )
                voice_btn = gr.Button("🚀 Send Voice Message", variant="primary", size="lg")
                gr.HTML('<p class="voice-hint">Tip: Click the mic, speak clearly, click stop, then press Send.</p>')

            with gr.Column(scale=1):
                transcript_box = gr.Textbox(
                    label="📝 What we heard (transcript)",
                    interactive=False,
                    lines=2,
                )
                reply_box = gr.Markdown(label="🤖 Agent Reply")
                audio_output = gr.Audio(
                    label="🔊 Voice Reply — press play",
                    type="filepath",
                    autoplay=True,
                )

        voice_btn.click(
            fn=handle_voice,
            inputs=[mic_input, voice_lang],
            outputs=[transcript_box, reply_box, audio_output],
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
