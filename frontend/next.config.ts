import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Enable standalone output for Docker deployment
  output: "standalone",
  // Allow ngrok domains for development (just hostnames, no protocol)
  allowedDevOrigins: [
    "intent-advisor.ngrok.app",
    "aigc-api.ngrok.app",
    "*.ngrok.app",
  ],
};

export default nextConfig;
