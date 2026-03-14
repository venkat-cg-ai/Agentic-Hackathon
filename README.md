# Agentic-Hackathon

**Step 1:  Install Dependencies**

python -m venv venv
venv\Scripts\activate   # On Windows
source venv/bin/activate  # On Mac/Linux
pip install -r requirements.txt

**Step 2: Configure AWS Access**

Edit the `.env` file in the root folder:

AWS_ACCESS_KEY_ID=your-access-key-id

AWS_SECRET_ACCESS_KEY=your-secret-access-key

AWS_REGION=us-east-1

BEDROCK_MODEL_ID=amazon.titan-text-premier-v1:0 // You can use other models as well 

**Step 3: Run the agent and type your prompt:**
python dinein_reservation_agent.py

Example input:

book a table for 4 near the bar at 7:30 PM

---

## Using GitHub Copilot Agent Mode in VS Code

**Step 1: Install Required Extensions**

Open VS Code and install the following extensions (the repo includes recommendations in `.vscode/extensions.json`):

- [GitHub Copilot](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot)
- [GitHub Copilot Chat](https://marketplace.visualstudio.com/items?itemName=GitHub.copilot-chat)

When you open this project in VS Code, you will be prompted to install the recommended extensions automatically.

**Step 2: Enable Agent Mode**

Agent mode is enabled by default via `.vscode/settings.json` in this repo. If you do not see it, verify the following settings are present in your VS Code settings (File → Preferences → Settings, search for the keys below or open `.vscode/settings.json`):

```json
{
  "chat.agent.enabled": true,
  "github.copilot.chat.edits.enabled": true
}
```

You can also enable it manually:
1. Open VS Code Settings (`Ctrl+,` / `Cmd+,`)
2. Search for `chat.agent.enabled` and set it to `true`
3. Search for `github.copilot.chat.edits.enabled` and set it to `true`

**Step 3: Open Copilot Chat in Agent Mode**

1. Open the GitHub Copilot Chat panel (`Ctrl+Alt+I` / `Cmd+Alt+I`) or click the Copilot icon in the Activity Bar.
2. At the top of the Chat panel, click the mode dropdown and select **Agent** (you may see options like *Ask*, *Edit*, or *Agent*).
3. You can now interact with the agent using natural language — for example:
   - *"Explain how the table_optimization_agent works"*
   - *"Add a cancellation function to dinein_reservation_agent.py"*
   - *"Run the agent and show me the output"*

**Step 4: Use `@workspace` for Codebase-Aware Queries**

In the Chat panel, prefix your message with `@workspace` to give Copilot full context of this project:

```
@workspace How does the reservation confirmation flow work?
```

> **Note:** Agent mode requires an active GitHub Copilot subscription and VS Code version 1.93 or later.
