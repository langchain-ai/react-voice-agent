import WebSocket from "ws";

/**
 * Merge multiple streams into one stream.
 */
export async function* mergeStreams<T>(
  streams: Record<string, AsyncGenerator<T>>
): AsyncGenerator<[string, T]> {
  // start the first iteration of each output iterator
  const tasks = new Map(
    Object.entries(streams).map(([key, stream], i) => {
      return [key, stream.next().then((result) => ({ key, stream, result }))];
    })
  );
  // yield chunks as they become available,
  // starting new iterations as needed,
  // until all iterators are done
  while (tasks.size) {
    const { key, result, stream } = await Promise.race(tasks.values());
    tasks.delete(key);
    if (!result.done) {
      yield [key, result.value];
      tasks.set(
        key,
        stream.next().then((result) => ({ key, stream, result }))
      );
    }
  }
}

export async function* createStreamFromWebsocket(ws: WebSocket) {
  const messageQueue: string[] = [];
  let resolveMessage: ((value: string | PromiseLike<string>) => void) | null =
    null;
  let rejectMessage: ((reason?: any) => void) | null = null;

  const onMessage = (data: WebSocket.Data) => {
    const message = data.toString();
    if (resolveMessage) {
      resolveMessage(message);
      resolveMessage = null;
      rejectMessage = null;
    } else {
      messageQueue.push(message);
    }
  };

  const onError = (error: Error) => {
    if (rejectMessage) {
      rejectMessage(error);
      resolveMessage = null;
      rejectMessage = null;
    }
  };

  ws.on("message", onMessage);
  ws.on("error", onError);

  try {
    while (ws.readyState === WebSocket.OPEN) {
      let message: string;
      if (messageQueue.length > 0) {
        message = messageQueue.shift()!;
      } else {
        message = await new Promise<string>((resolve, reject) => {
          resolveMessage = resolve;
          rejectMessage = reject;
        });
      }

      yield JSON.parse(message);
    }
  } finally {
    ws.off("message", onMessage);
    ws.off("error", onError);
  }
}
