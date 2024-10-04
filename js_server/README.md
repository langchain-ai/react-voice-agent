# 🦜🎤 Voice ReAct Agent (TypeScript)

This is an implementation of a [ReAct](https://arxiv.org/abs/2210.03629)-style agent that uses OpenAI's new [Realtime API](https://platform.openai.com/docs/guides/realtime). It is a light [Hono](https://hono.dev/) app that statically serves a simple frontend from `/src/static` as well as a websocket endpoint for handling streaming audio input and output.

Specifically, we enable this model to call tools by providing it a list of [LangChain tools](https://js.langchain.com/docs/how_to/custom_tools/). It is easy to write these custom tools, and you can easily pass these to the model.

![](../static/react.png)

## Installation

Install required dependencies with `yarn`:

```bash
yarn
```

You will also need to copy the provided `.env.example` file to `.env` and fill in your OpenAI and Tavily keys.

## Running the project

```bash
yarn dev
```

## Open the browser

Now you can open the browser and navigate to `http://localhost:3000` to see the project running.

### Enable microphone

You may need to make sure that your browser can access your microphone.

- [Chrome](http://0.0.0.0:3000/)

## Adding your own tools

You can add your own tools by adding them to the `/src/tools.ts` folder for TypeScript.

## Adding your own custom instructions

You can add your own custom instructions by adding them to the `/src/prompt.ts` folder for TypeScript.

## Next steps

- [ ] Enable interrupting the AI
- [ ] Enable changing of instructions/tools based on state
- [ ] Add auth middleware
