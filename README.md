# Demo Voice React Agent

## Installation

Make sure you're running Python 3.10 or later, then install `uv` to be able to run the project:

```bash
pip install uv
```

And make sure you have both `OPENAI_API_KEY` and `TAVILY_API_KEY` environment variables set up.

```bash
export OPENAI_API_KEY=your_openai_api_key
export TAVILY_API_KEY=your_tavily_api_key
```

## Running the project

To run the project, execute the following command:

```bash
cd server
uv run src/server/app.py
```

## Open the browser

Now you can open the browser and navigate to `http://localhost:3000` to see the project running.

## Adding your own tools

You can add your own tools by adding them to the `server/src/server/app.py` file
in the webhook handler.
