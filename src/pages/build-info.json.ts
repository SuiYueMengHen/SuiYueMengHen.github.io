export const prerender = true;

export function GET() {
  return new Response(JSON.stringify({
    commit: process.env.GITHUB_SHA || 'local',
    builtAt: new Date().toISOString(),
  }), {
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      'Cache-Control': 'no-store, max-age=0',
    },
  });
}
