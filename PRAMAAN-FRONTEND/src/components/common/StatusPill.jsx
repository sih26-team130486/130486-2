export default function StatusPill({ status }) {
  const value = String(status ?? '');
  const lower = value.toLowerCase();
  const tone =
    lower.includes('tamper') || lower.includes('critical') || lower.includes('invalid')
      ? 'danger'
      : lower.includes('pending') || lower.includes('analysis')
        ? 'warn'
        : lower.includes('verified') || lower.includes('valid') || lower.includes('active')
          ? 'ok'
          : 'info';

  return <span className={`status ${tone}`}><i>●</i>{value}</span>;
}
