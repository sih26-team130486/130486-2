export default function Brand({ compact = false }) {
  return (
    <div className={`brand ${compact ? 'brand-compact' : ''}`}>
      <div className="brand-mark" aria-hidden="true">⚖</div>
      <div>
        <div className="brand-title">Pramaan</div>
        <div className="brand-sub">Secure digital evidence lifecycle</div>
      </div>
    </div>
  );
}
