/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output keeps the Docker image to node_modules actually needed.
  output: "standalone",
};

export default nextConfig;
