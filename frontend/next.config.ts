import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow ngrok domains for development (just hostnames, no protocol)
  allowedDevOrigins: [
    "intent-advisor.ngrok.app",
    "aigc-api.ngrok.app",
    "*.ngrok.app",
  ],
};

export default nextConfig;
