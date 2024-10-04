import "dotenv/config";

import { serve } from "@hono/node-server";
import { Hono } from "hono";
import { createNodeWebSocket } from "@hono/node-ws";
import { serveStatic } from "@hono/node-server/serve-static";
import { WebSocket } from "ws";

import { OpenAIVoiceReactAgent } from "./lib/langchain_openai_voice";
import { INSTRUCTIONS } from "./prompt";
import { TOOLS } from "./tools";
import { createStreamFromWebsocket } from "./lib/utils";

const app = new Hono();

const { injectWebSocket, upgradeWebSocket } = createNodeWebSocket({ app });

app.use("/", serveStatic({ path: "./static/index.html" }));
app.use("/static/*", serveStatic({ root: "./" }));

app.get(
  "/ws",
  upgradeWebSocket((c) => ({
    onOpen: async (c, ws) => {
      if (!process.env.OPENAI_API_KEY) {
        return ws.close();
      }
      const agent = new OpenAIVoiceReactAgent({
        instructions: INSTRUCTIONS,
        tools: TOOLS,
        model: "gpt-4o-realtime-preview",
      });
      await agent.connect(
        createStreamFromWebsocket(ws.raw as WebSocket),
        ws.send.bind(ws)
      );
    },
    onClose: () => {
      console.log("CLOSING");
    },
  }))
);

const port = 3000;

const server = serve({
  fetch: app.fetch,
  port,
});

injectWebSocket(server);

console.log(`Server is running on port ${port}`);
