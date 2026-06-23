/**
 * Minimal billable MCP server example (x402)
 * Base Sepolia testnet + Coinbase facilitator
 *
 * Run: node examples/mcp-server-billable.js
 * No secrets required for testnet.
 *
 * This is the generic skeleton. See examples/lemoncake-mcp-server/ for the full
 * LemonCake MVP with 5 priced tools, free tier stub, and verification script.
 */

import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { paymentMiddleware, x402ResourceServer } from "@x402/express";
import { ExactEvmScheme } from "@x402/evm/exact/server";
import { HTTPFacilitatorClient } from "@x402/core/server";
import { z } from "zod";

const app = express();
app.use(express.json());

const server = new McpServer({
  name: "billable-example",
  version: "1.0.0",
});

// Example tool with price
server.tool(
  "example_tool",
  "A simple billable tool that returns a greeting. Price example: $0.001",
  { name: z.string().min(1) },
  async ({ name }) => ({
    content: [{ type: "text", text: `Hello, ${name}! This call was billed via x402 on Base Sepolia.` }],
  })
);

const NETWORK = "eip155:84532";
const PAY_TO = process.env.PAY_TO || "0xYourTestnetAddressHere";
const FACILITATOR_URL = "https://api.cdp.coinbase.com/platform/v2/x402";

const facilitatorClient = new HTTPFacilitatorClient({ url: FACILITATOR_URL });
const resourceServer = new x402ResourceServer(facilitatorClient)
  .register(NETWORK, new ExactEvmScheme());

app.use(
  paymentMiddleware(
    {
      "POST /mcp": {
        accepts: [
          {
            scheme: "exact",
            price: "$0.001",
            network: NETWORK,
            payTo: PAY_TO,
          },
        ],
        description: "Billable MCP server example (generic skeleton)",
        mimeType: "application/json",
      },
    },
    resourceServer
  )
);

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => `sess_${Date.now()}`,
  enableJsonResponse: true,
});

await server.connect(transport);

app.post("/mcp", async (req, res) => {
  await transport.handleRequest(req, res, req.body);
});

app.get("/mcp", async (req, res) => {
  await transport.handleRequest(req, res);
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Billable MCP server (generic) running on http://localhost:${PORT}/mcp`);
  console.log("Testnet mode — Base Sepolia + Coinbase CDP facilitator");
  console.log("Free tier: 50–100 calls/day recommended for discovery");
  console.log("For full LemonCake MVP with 5 tools see ../examples/lemoncake-mcp-server/");
});