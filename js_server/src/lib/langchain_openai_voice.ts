import WebSocket from "ws";
import { StructuredTool } from "@langchain/core/tools";
import { mergeStreams, createStreamFromWebsocket } from "./utils";
import { zodToJsonSchema } from "zod-to-json-schema";

const DEFAULT_MODEL = "gpt-4o-realtime-preview";
const DEFAULT_URL = "wss://api.openai.com/v1/realtime";

const EVENTS_TO_IGNORE = [
  "response.function_call_arguments.delta",
  "rate_limits.updated",
  "response.audio_transcript.delta",
  "response.created",
  "response.content_part.added",
  "response.content_part.done",
  "conversation.item.created",
  "response.audio.done",
  "session.created",
  "session.updated",
  "response.done",
  "response.output_item.done",
];

class OpenAIWebSocketConnection {
  ws?: WebSocket;

  url: string;

  apiKey?: string;

  model: string;

  constructor(params: { url?: string; apiKey?: string; model?: string }) {
    this.url = params.url ?? DEFAULT_URL;
    this.model = params.model ?? DEFAULT_MODEL;
    this.apiKey = params.apiKey ?? process.env.OPENAI_API_KEY;
  }

  async connect() {
    const headers = {
      Authorization: `Bearer ${this.apiKey}`,
      "OpenAI-Beta": "realtime=v1",
    };

    const finalUrl = `${this.url}?model=${this.model}`;
    this.ws = new WebSocket(finalUrl, { headers });
    await new Promise<void>((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Connection timed out after 10 seconds."));
      }, 10000);

      this.ws?.once("open", () => {
        clearTimeout(timeout);
        resolve();
      });

      this.ws?.once("error", (error) => {
        clearTimeout(timeout);
        reject(error);
      });
    });
  }

  sendEvent(event: Record<string, unknown>) {
    const formattedEvent = JSON.stringify(event);
    if (this.ws === undefined) {
      throw new Error("Socket connection is not active, call .connect() first");
    }
    this.ws?.send(formattedEvent);
  }

  async *eventStream() {
    if (!this.ws) {
      throw new Error("Socket connection is not active, call .connect() first");
    }
    yield* createStreamFromWebsocket(this.ws);
  }
}

/**
 * Can accept function calls and emits function call outputs to a stream.
 */
class VoiceToolExecutor {
  protected toolsByName: Record<string, StructuredTool>;
  protected triggerPromise: Promise<any> | null = null;
  protected triggerResolve: ((value: any) => void) | null = null;
  protected lock: Promise<void> | null = null;

  constructor(toolsByName: Record<string, StructuredTool>) {
    this.toolsByName = toolsByName;
  }

  protected async triggerFunc(): Promise<any> {
    if (!this.triggerPromise) {
      this.triggerPromise = new Promise((resolve) => {
        this.triggerResolve = resolve;
      });
    }
    return this.triggerPromise;
  }

  async addToolCall(toolCall: any): Promise<void> {
    while (this.lock) {
      await this.lock;
    }

    this.lock = (async () => {
      if (this.triggerResolve) {
        this.triggerResolve(toolCall);
        this.triggerPromise = null;
        this.triggerResolve = null;
      } else {
        throw new Error("Tool call adding already in progress");
      }
    })();

    await this.lock;
    this.lock = null;
  }

  protected async createToolCallTask(toolCall: any): Promise<any> {
    const tool = this.toolsByName[toolCall.name];
    if (!tool) {
      throw new Error(
        `Tool ${toolCall.name} not found. Must be one of ${Object.keys(
          this.toolsByName
        )}`
      );
    }

    let args;
    try {
      args = JSON.parse(toolCall.arguments);
    } catch (error) {
      throw new Error(
        `Failed to parse arguments '${toolCall.arguments}'. Must be valid JSON.`
      );
    }

    const result = await tool.call(args);
    const resultStr =
      typeof result === "string" ? result : JSON.stringify(result);

    return {
      type: "conversation.item.create",
      item: {
        id: toolCall.call_id,
        call_id: toolCall.call_id,
        type: "function_call_output",
        output: resultStr,
      },
    };
  }

  async *outputIterator(): AsyncGenerator<any, void, unknown> {
    while (true) {
      const toolCall = await this.triggerFunc();
      try {
        const result = await this.createToolCallTask(toolCall);
        yield result;
      } catch (error: any) {
        yield {
          type: "conversation.item.create",
          item: {
            id: toolCall.call_id,
            call_id: toolCall.call_id,
            type: "function_call_output",
            output: `Error: ${error.message}`,
          },
        };
      }
    }
  }
}

export class OpenAIVoiceReactAgent {
  protected connection: OpenAIWebSocketConnection;

  protected instructions?: string;

  protected tools: StructuredTool[];

  constructor(params: {
    instructions?: string;
    tools?: StructuredTool[];
    url?: string;
    apiKey?: string;
    model?: string;
  }) {
    this.connection = new OpenAIWebSocketConnection({
      url: params.url,
      apiKey: params.apiKey,
      model: params.model,
    });
    this.instructions = params.instructions;
    this.tools = params.tools ?? [];
  }

  /**
   * Connect to the OpenAI API and send and receive messages.
   * @param inputStream
   * @param sendOutputChunk
   */
  async connect(
    inputStream: AsyncGenerator<string>,
    sendOutputChunk: (chunk: string) => void | Promise<void>
  ) {
    const toolsByName = this.tools.reduce(
      (toolsByName: Record<string, StructuredTool>, tool) => {
        toolsByName[tool.name] = tool;
        return toolsByName;
      },
      {}
    );
    const toolExecutor = new VoiceToolExecutor(toolsByName);
    await this.connection.connect();
    const modelReceiveStream = this.connection.eventStream();
    // Send tools and instructions with initial chunk
    const toolDefs = Object.values(toolsByName).map((tool) => ({
      type: "function",
      name: tool.name,
      description: tool.description,
      parameters: zodToJsonSchema(tool.schema),
    }));

    this.connection.sendEvent({
      type: "session.update",
      session: {
        instructions: this.instructions,
        input_audio_transcription: {
          model: "whisper-1",
        },
        tools: toolDefs,
      },
    });
    for await (const [streamKey, dataRaw] of mergeStreams({
      input_mic: inputStream,
      output_speaker: modelReceiveStream,
      tool_outputs: toolExecutor.outputIterator(),
    })) {
      let data: any;
      try {
        data = typeof dataRaw === "string" ? JSON.parse(dataRaw) : dataRaw;
      } catch (error) {
        console.error("Error decoding data:", dataRaw);
        continue;
      }

      if (streamKey === "input_mic") {
        this.connection.sendEvent(data);
      } else if (streamKey === "tool_outputs") {
        console.log("tool output", data);
        this.connection.sendEvent(data);
        this.connection.sendEvent({ type: "response.create", response: {} });
      } else if (streamKey === "output_speaker") {
        const { type } = data;
        if (type === "response.audio.delta") {
          sendOutputChunk(JSON.stringify(data));
        } else if (type === "response.audio_buffer.speech_started") {
          console.log("interrupt");
          sendOutputChunk(JSON.stringify(data));
        } else if (type === "error") {
          console.error("error:", data);
        } else if (type === "response.function_call_arguments.done") {
          console.log("tool call", data);
          toolExecutor.addToolCall(data);
        } else if (type === "response.audio_transcript.done") {
          console.log("model:", data.transcript);
        } else if (
          type === "conversation.item.input_audio_transcription.completed"
        ) {
          console.log("user:", data.transcript);
        } else if (!EVENTS_TO_IGNORE.includes(type)) {
          console.log(type);
        }
      }
    }
  }
}
