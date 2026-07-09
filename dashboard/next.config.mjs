/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output keeps the Docker image to node_modules actually needed.
  // Skip it on Vercel (VERCEL=1 is set automatically during Vercel builds) —
  // Vercel's builder handles this itself, and standalone output breaks its
  // build-output detection (see https://vercel.com/guides/nextjs-standalone-output-directory).
  output: process.env.VERCEL ? undefined : "standalone",
};

export default nextConfig;
