export default function ResponsiveOverlay({ open, onClose, children }) {
  if (!open) return null;
  return (
    <div className="responsive-overlay" role="presentation" onClick={onClose}>
      <div onClick={(event) => event.stopPropagation()}>{children}</div>
    </div>
  );
}
