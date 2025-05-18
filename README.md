# 🦜🎤 Voice ReAct Agent

This is an implementation of a [ReAct](https://arxiv.org/abs/2210.03629)-style agent that uses OpenAI's new [Realtime API](https://platform.openai.com/docs/guides/realtime).It includes implementations in both Python and TypeScript, choose whichever best fits your stack.

Specifically, we enable this model to call tools by providing it a list of [LangChain tools](https://python.langchain.com/docs/how_to/custom_tools/#creating-tools-from-functions). It is easy to write custom tools, and you can easily pass these to the model.

![ReAct Diagram](static/react.png)

## Setup Instructions

### 1. Clone the repo

```bash
git clone https://github.com/your-org/voice-react-agent.git
cd voice-react-agent
```

---

### 2. Configure environment variables

#### Unix (bash/zsh)

```bash
export OPENAI_API_KEY=your_openai_api_key
export TAVILY_API_KEY=your_tavily_api_key
```

#### PowerShell

```powershell
$env:OPENAI_API_KEY="your_openai_api_key"
$env:TAVILY_API_KEY="your_tavily_api_key"
```

#### Windows CMD

```cmd
set OPENAI_API_KEY=your_openai_api_key
set TAVILY_API_KEY=your_tavily_api_key
```

Or create a `.env` file in each directory (`server/` and `js_server/`) with:

```
OPENAI_API_KEY=your_openai_api_key
TAVILY_API_KEY=your_tavily_api_key
```

Note: the Tavily API key is for the Tavily search engine, you can get an API key [here](https://app.tavily.com/). This is just an example tool, and if you do not want to use it you do not have to (see [Adding your own tools](#adding-your-own-tools))

---

## Running the Python Server

1. **Install dependencies** (ensure Python 3.10+):

   ```bash
   cd server
   pip install uv
   ```

2. **Start the server**:

   ```bash
   uv run src/server/app.py
   ```

3. **Open in browser**:
   Navigate to [http://localhost:3000](http://localhost:3000).

---

## Running the TypeScript Server

1. **Install dependencies**:

   ```bash
   cd js_server
   yarn        # or npm install
   ```

2. **Start the dev server**:

   ```bash
   yarn dev    # or npm run dev
   ```

3. **Open in browser**:
   Navigate to [http://localhost:3000](http://localhost:3000).

---

## Enable Microphone Access

Your browser will prompt you for microphone permissions. If it doesn’t:

* **Chrome:** visit `chrome://settings/content/microphone`
* **Firefox:** visit `about:preferences#privacy`
* **Edge:** visit `edge://settings/content/microphone`

---

## Adding Custom Tools

* **Python:** edit `server/src/server/tools.py`
* **TypeScript:** edit `js_server/src/tools.ts`

---

## Custom Instructions & Prompts

* **Python:** modify `server/src/server/prompt.py`
* **TypeScript:** modify `js_server/src/prompt.ts`

---

## Common Errors

* **WebSocket connection: HTTP 403**

  * Usually means your org/account lacks Realtime API access or has insufficient funds.
  * Check if you have Realtime API access in the playground [here](https://platform.openai.com/playground/realtime).

---

## Next steps

- [ ] Enable interrupting the AI
- [ ] Enable changing of instructions/tools based on state
