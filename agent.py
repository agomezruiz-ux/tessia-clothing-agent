# Tessia Clothing - terminal chat with the Foundry agent
# Requirements: pip install -r requirements.txt  +  az login

from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient

ENDPOINT = "https://foundry-tecnun-resource.services.ai.azure.com/api/projects/foundry-tecnun-project"
AGENT_NAME = "tessia-clothing-agent"


def ask_approvals(response):
    """Ask the user to approve each MCP tool call the agent wants to make."""
    approvals = []
    for item in response.output:
        if item.type == "mcp_approval_request":
            print(f"\n[Tool request] {item.server_label} -> {item.name}")
            print(f"  Arguments: {item.arguments}")
            answer = input("  Approve? (y/n): ").strip().lower()
            approvals.append({
                "type": "mcp_approval_response",
                "approve": answer == "y",
                "approval_request_id": item.id,
            })
    return approvals


def main():
    # Authentication with Microsoft Entra ID (uses the az login session, no API keys)
    with (
        DefaultAzureCredential() as credential,
        AIProjectClient(endpoint=ENDPOINT, credential=credential, allow_preview=True) as project,
    ):
        client = project.get_openai_client(agent_name=AGENT_NAME)
        conversation = client.conversations.create()  # keeps the chat history

        print("Tessia Clothing - personal shopping assistant")
        print("Type your message, or 'exit' to quit.\n")

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ("exit", "quit", "salir"):
                print("Goodbye!")
                break
            if not user_input:
                continue

            try:
                response = client.responses.create(
                    conversation=conversation.id,
                    input=[{"role": "user", "content": user_input}],
                )
                # The agent may ask for several MCP approvals in a row
                for _ in range(10):
                    approvals = ask_approvals(response)
                    if not approvals:
                        break
                    response = client.responses.create(
                        conversation=conversation.id,
                        input=approvals,
                    )

                print(f"\nTessia: {response.output_text}")
                print(f"(tokens: {response.usage.total_tokens})\n")

            except Exception as error:
                print(f"\n[Error] {error}\n")


if __name__ == "__main__":
    main()
