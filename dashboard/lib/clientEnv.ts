// Client-visible demo flag (inlined at build). Set NEXT_PUBLIC_FORGE_DEMO=1 on
// Vercel so ChatPanel and incident actions simulate the agent locally instead of
// calling a backend that isn't there. Unset in docker-compose → real proxy.
export const IS_DEMO = process.env.NEXT_PUBLIC_FORGE_DEMO === "1";
