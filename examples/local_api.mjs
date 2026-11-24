// Query authorized CueFleet accounts. Requires Node.js 20+.
import http from 'node:http';

const key = process.env.CUEFLEET_API_KEY;
if (!key) throw Error('Set CUEFLEET_API_KEY to the key generated in CueFleet.');

const url = new URL(process.env.CUEFLEET_API_URL || 'http://127.0.0.1:17687');
if (url.protocol !== 'http:' || url.hostname !== '127.0.0.1'
    || url.username || url.password || url.pathname !== '/' || url.search || url.hash) {
  throw Error('Use the IPv4 loopback address shown in CueFleet.');
}

const body = await new Promise((resolve, reject) => {
  const request = http.get(new URL('/v1/accounts', url), {
    agent: new http.Agent(),
    headers: { Authorization: 'Bearer ' + key },
    signal: AbortSignal.timeout(35000),
  }, async response => {
    try {
      if (response.statusCode !== 200) {
        response.resume();
        reject(Error('CueFleet request failed with HTTP ' + response.statusCode));
        return;
      }
      const chunks = [];
      for await (const chunk of response) chunks.push(chunk);
      resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
    } catch (error) { reject(error); }
  });
  request.on('error', reject);
});
console.log(JSON.stringify(body, null, 2));
