from dotenv import load_dotenv
import os
import gradio as gr

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_google_genai import ChatGoogleGenerativeAI

# ===============================
# ENV
# ===============================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# ===============================
# PERSONAS
# ===============================
PERSONAS = {
    "Scientist": """
You are an intelligent Scientist with rigorous training in the scientific method, statistics, and critical reasoning.
You approach problems by forming clear hypotheses, testing assumptions, and validating conclusions with evidence.
You prioritize accuracy over speed, clarity over complexity, and reproducibility over intuition.
Answer in 5-15 sentences
""",
    "Analyst": """
You are a senior data analyst.
Be precise, structured, and business-focused.
Use bullet points, clear logic, and actionable insights.
Focuses on metrics, trends, segments, and actionable business insights.
Answer in 5-15 sentences.
""",
    "Teacher": """
You are a patient and clear teacher.
Explain concepts step by step using simple language and examples.
Explains the concept simply, step by step, for non-technical stakeholders
Encourage understanding and curiosity.
Answer in 5-15 sentences.
"""
}

# ===============================
# LLM FACTORY
# ===============================
def get_llm(temperature: float):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=temperature
    )

# ===============================
# CLEANERS
# ===============================
def clean_llm_text(text: str) -> str:
    """Strip any accidental extra characters from model output."""
    if not text:
        return ""
    return text.strip()

# ===============================
# CHAT FUNCTION
# ===============================
def chat(user_input, history, temperature, persona):

    system_prompt = PERSONAS[persona]

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("user", "{input}")
    ])

    llm = get_llm(temperature)
    chain = prompt | llm

    # Convert Gradio history → LangChain history (RAW TEXT ONLY)
    lc_history = []
    for msg in history:
        if msg["role"] == "user":
            lc_history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            lc_history.append(AIMessage(content=msg["content"]))

    # Invoke model
    raw_response = chain.invoke({
        "input": user_input,
        "history": lc_history
    })

    # Extract & clean text
    response_text = (
        raw_response.content
        if isinstance(raw_response, AIMessage)
        else str(raw_response)
    )
    response_text = clean_llm_text(response_text)

    # Append messages to history (dict with role & content)
    history.append({
        "role": "user",
        "content": user_input
    })
    history.append({
        "role": "assistant",
        "content": response_text
    })

    return "", history  # history is a list of dicts now

# ===============================
# UI
# ===============================
with gr.Blocks(title="AI Assistant", theme=gr.themes.Soft()) as page:

    gr.Markdown("""
    <div style="text-align:center">
        <h2>AI Assistant</h2>
        <p>Multi-persona conversational assistant powered by Gemini & LangChain</p>
    </div>
    """)

    with gr.Row():
        with gr.Column(scale=4):
            chatbot = gr.Chatbot(height=340)
            msg = gr.Textbox(label="Your message", placeholder="Ask a question…")

            with gr.Row():
                send = gr.Button("Send")
                clear = gr.Button("Clear")

        with gr.Column(scale=1):
            persona = gr.Dropdown(
                choices=list(PERSONAS.keys()),
                value="Scientist",
                label="AI Persona"
            )

            temperature = gr.Slider(0, 1, 0.5, step=0.1, label="Creativity")

    send.click(chat, [msg, chatbot, temperature, persona], [msg, chatbot])
    msg.submit(chat, [msg, chatbot, temperature, persona], [msg, chatbot])
    clear.click(lambda: [], None, chatbot)

page.launch(share=True)
