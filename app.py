# Tessia Clothing - web chat interface for the Foundry agent
# Run: streamlit run app.py   (requires: az login)

import streamlit as st
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

ENDPOINT = "https://foundry-tecnun-resource.services.ai.azure.com/api/projects/foundry-tecnun-project"
AGENT_NAME = "tessia-clothing-agent"

EXAMPLES = [
    "Hi! What can you help me with?",
    "I'm a student with 150 EUR. Build me an office outfit with the final price.",
    "My bust is 92 cm and my hips 104 cm. Which size for the Valentina Wrap Dress?",
    "Can I return boots I wore once outside?",
    "I love the Greta Knee-High Boots but I wear size 42. Do you have them?",
]

# Page setup and Tessia colours
st.set_page_config(page_title="Tessia Clothing", page_icon="🛍️", layout="centered")
st.markdown(
    """
    <style>
    .stApp {background-color: #FAF6F2;}
    h1 {color: #2B2422;}
    .tessia-sub {color: #8C5A4A; margin-top: -12px;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def get_client():
    """Connect once to the Foundry agent (Entra ID auth via az login, no API keys)."""
    credential = DefaultAzureCredential()
    project = AIProjectClient(endpoint=ENDPOINT, credential=credential, allow_preview=True)
    return project.get_openai_client(agent_name=AGENT_NAME)


client = get_client()

# Chat state for this browser session
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = client.conversations.create().id
    st.session_state.messages = []   # chat history shown on screen
    st.session_state.pending = []    # MCP approvals waiting for the user
    st.session_state.tokens = 0


def handle_response(response):
    """Save pending MCP approvals, or the agent's final answer."""
    st.session_state.tokens += response.usage.total_tokens
    pending = [
        {"id": item.id, "server": item.server_label, "tool": item.name, "args": item.arguments}
        for item in response.output
        if item.type == "mcp_approval_request"
    ]
    st.session_state.pending = pending
    if not pending:
        st.session_state.messages.append({"role": "assistant", "content": response.output_text})


def send(input_items):
    """Send a message (or approvals) to the agent."""
    with st.spinner("Tessia is thinking..."):
        try:
            response = client.responses.create(
                conversation=st.session_state.conversation_id,
                input=input_items,
            )
            handle_response(response)
        except Exception as error:
            st.session_state.pending = []
            st.session_state.messages.append({"role": "assistant", "content": f"⚠️ Error: {error}"})


def ask(text):
    """Add a user message and get the agent's reply."""
    st.session_state.messages.append({"role": "user", "content": text})
    send([{"role": "user", "content": text}])


def decide(approve):
    """Answer the pending MCP approval requests."""
    approvals = [
        {"type": "mcp_approval_response", "approve": approve, "approval_request_id": req["id"]}
        for req in st.session_state.pending
    ]
    send(approvals)


waiting = bool(st.session_state.pending)

# Header
st.title("🛍️ Tessia Clothing")
st.markdown('<p class="tessia-sub">Your personal shopping assistant · Autumn/Winter 2026</p>',
            unsafe_allow_html=True)

# Sidebar: example prompts, Instagram and session info
with st.sidebar:
    st.header("Try asking")
    for example in EXAMPLES:
        if st.button(example, use_container_width=True, disabled=waiting):
            ask(example)
            st.rerun()
    st.divider()
    st.markdown("**Follow Tessia** 📸")
    st.markdown("Instagram: [@tessia.clo](https://www.instagram.com/tessia.clo)")
    st.caption("Custom hoodies, t-shirts, jackets and tote bags ✨")
    st.divider()
    st.caption(f"Tokens used in this chat: {st.session_state.tokens}")
    if st.button("🔄 New conversation", use_container_width=True):
        for key in ["conversation_id", "messages", "pending", "tokens"]:
            del st.session_state[key]
        st.rerun()

# Chat history
for message in st.session_state.messages:
    avatar = "🛍️" if message["role"] == "assistant" else "🙋‍♀️"
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# MCP approval box
if waiting:
    with st.container(border=True):
        st.warning("Tessia wants to use an external tool (GitHub). Do you approve?")
        for req in st.session_state.pending:
            st.markdown(f"**{req['server']} → {req['tool']}**")
            st.code(req["args"], language="json")
        col1, col2 = st.columns(2)
        if col1.button("✅ Approve", type="primary", use_container_width=True):
            decide(True)
            st.rerun()
        if col2.button("❌ Deny", use_container_width=True):
            decide(False)
            st.rerun()

# Message box
prompt = st.chat_input("Ask Tessia about outfits, sizes, prices or returns...", disabled=waiting)
if prompt:
    ask(prompt)
    st.rerun()