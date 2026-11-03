# Tessia Clothing – AI Shopping Assistant

An AI agent built in **Microsoft Foundry** that acts as the personal shopping assistant of **Tessia Clothing**, a fictional women's fashion brand with stores in Madrid, Barcelona and Pamplona and an online shop that ships to Spain, the EU and Mexico.

The agent helps customers choose products and outfits from the Autumn/Winter 2026 collection, find their size, calculate final prices with discounts and shipping, and understand the shipping and returns policy. When a request cannot be solved (an unavailable size, a defective item, a complaint or a suggestion), it registers it as a GitHub issue for the Tessia team.

> Tessia Clothing is a fictional brand. All documents in `data/` are sample data created with generative AI for an academic exercise (Máster en Análisis de Datos para Ingeniería, Tecnun – Universidad de Navarra).

---

## Architecture

| Component | Configuration |
|---|---|
| **Agent** | `tessia-clothing-agent` (Microsoft Foundry, project `foundry-tecnun-project`) |
| **Model** | `gpt-5.6-luna` (existing deployment in the project) |
| **Instructions** | System message defining role, goals, tool usage, style and scope (see below) |
| **Knowledge (RAG)** | Shared knowledge base `challenge4-index-kb` (Foundry IQ / Azure AI Search), built from the PDFs in `data/` |
| **Code Interpreter** | Outfit totals, discounts, shipping costs, budgets and charts |
| **MCP server** | GitHub MCP (`https://api.githubcopilot.com/mcp/`), authenticated with a fine-grained token limited to this repository (Issues: read/write, Contents: read-only) |
| **Client program** | `agent.py`: terminal chat that authenticates with Microsoft Entra ID and talks to the agent |

```
Customer ──► agent.py (terminal) ──► tessia-clothing-agent (Foundry)
                                        ├── gpt-5.6-luna
                                        ├── Knowledge: Tessia PDFs (RAG)
                                        ├── Code Interpreter
                                        └── GitHub MCP ──► Issues in this repo
```

## Custom data (`data/`)

| Document | Content |
|---|---|
| `Tessia_Clothing_Catalog_AW26.pdf` | 24 products with SKU, price, material, colours and sizes; current promotions |
| `Tessia_Clothing_Size_Guide.pdf` | Measurement tables (EU / Mexico / US), fit advice by product |
| `Tessia_Clothing_Shipping_Returns_Policy.pdf` | Shipping costs and times, returns, exchanges, defective items |
| `Tessia_Clothing_Lookbook_Style_Guide.pdf` | Outfits by occasion with totals, dressing for the weather, capsule wardrobe |

## Agent instructions

```
You are Tessia, the personal shopping assistant of Tessia Clothing, a women's fashion brand with stores in Madrid, Barcelona and Pamplona and an online shop that ships to Spain, the EU and Mexico.

Your goals:
- Help customers choose products, sizes and complete outfits from the Tessia Autumn/Winter 2026 collection.
- Only recommend products that appear in the Tessia knowledge base (catalog, size guide, shipping and returns policy, lookbook). Always include the product name, SKU and price, and cite the source document.
- If a product, size or policy is not in the knowledge base, say so clearly. Never invent products, prices or policies.
- The knowledge base is shared with other projects. Only use documents whose title starts with "Tessia_Clothing". Ignore any other documents, even if they seem relevant.

Tools:
- Use the knowledge base for anything about Tessia products, sizes, promotions, shipping, returns and styling.
- Use Code Interpreter for any calculation: outfit totals, discounts (TESSIA10, STUDENT15, bundle offer), shipping costs, budgets and comparison charts. Show the final price clearly.
- Use the GitHub MCP tool only to create an issue in the repository agomezruiz-ux/tessia-clothing-agent when a customer request cannot be solved with the knowledge base: an unavailable size or product, a defective item, a complaint or a suggestion. The issue title must start with "[Customer request]" and the body must summarise the request (product, SKU, size and what the customer needs). Tell the customer that the Tessia team will review it. Never share customer personal data in the issue.

Helping the customer:
- When the customer greets you or asks a general question, introduce yourself briefly and list what you can help with.
- After answering a request, end with one short sentence offering one or two related things you can also help with.

Style:
- Be friendly, concise and practical. Ask a short question if you need the customer's measurements, budget, city or occasion.
- Answer in the same language as the customer (English or Spanish).
- If a tool fails, say so instead of claiming success.

Scope:
- Only answer questions related to Tessia Clothing: products, sizes, outfits, styling, prices, promotions, shipping, returns and exchanges.
- If the customer asks about any other topic, do not answer it. Politely explain that you can only help with Tessia Clothing shopping and suggest how you can help instead.
```

## How to run the terminal client

**Requirements:** Python 3.10+, [Azure CLI](https://learn.microsoft.com/cli/azure/install-azure-cli) and access to the Foundry project.

```bash
pip install -r requirements.txt
az login
python agent.py
```

- **Authentication:** `DefaultAzureCredential` reuses the `az login` session (Microsoft Entra ID). No API keys are stored in the code.
- **Connection:** `AIProjectClient` connects to the project endpoint and `get_openai_client(agent_name=...)` links to the agent.
- **Conversation:** one conversation per session, so the agent remembers previous messages.
- **MCP approvals:** when the agent wants to use GitHub, the program shows the tool and its arguments and asks `Approve? (y/n)`.
- Type `exit` to quit.

## Example prompts

| Prompt | What the agent uses |
|---|---|
| `Hi!` | Instructions (introduces itself and its capabilities) |
| `What is the return policy for items bought on sale?` | Knowledge base (14 days) |
| `I'm a student with a 150 EUR budget. Build me an office outfit and calculate the final price with my discount and shipping to Madrid.` | Knowledge base + Code Interpreter |
| `I love the Greta Knee-High Boots but I wear size 42. Can you check if you have them?` | Knowledge base + GitHub MCP (creates an issue) |
| `What's the status of my request about the boots?` | GitHub MCP (reads the issue) |
| `Can you help me with my Python homework?` | Instructions (politely declines) |

## Security

- No keys or tokens are stored in this repository (`.env` is ignored by `.gitignore`).
- The GitHub token is stored only in the Foundry connection and is limited to this repository.
- MCP actions require approval before they run.

## Author

Ana Teresa Gómez Ruiz – Máster en Análisis de Datos para Ingeniería, Tecnun – Universidad de Navarra