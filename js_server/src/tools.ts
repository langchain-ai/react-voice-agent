import { z } from "zod";

import { tool } from "@langchain/core/tools";
import { TavilySearchResults } from "@langchain/community/tools/tavily_search";

const add = tool(
  async ({ a, b }) => {
    return a + b;
  },
  {
    name: "add",
    description:
      "Add two numbers. Please let the user know that you're adding the numbers BEFORE you call the tool",
    schema: z.object({
      a: z.number(),
      b: z.number(),
    }),
  }
);

const tavilyTool = new TavilySearchResults({
  maxResults: 5,
  kwargs: {
    includeAnswer: true,
  },
});

tavilyTool.description = `This is a search tool for accessing the internet.\n\nLet the user know you're asking your friend Tavily for help before you call the tool.`;

export const TOOLS = [add, tavilyTool];
