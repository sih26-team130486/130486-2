export async function sha256(value) {
  const data = value instanceof ArrayBuffer
    ? new Uint8Array(value)
    : new TextEncoder().encode(String(value ?? ''));
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, '0')).join('').toUpperCase();
}
