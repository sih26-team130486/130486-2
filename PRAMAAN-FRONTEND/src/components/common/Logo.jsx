export default function Logo({ wordmark = false }) {
  return wordmark
    ? <img src="/assets/pramaan-wordmark.svg" alt="PRAMAAN" className="pramaan-wordmark" />
    : <img src="/assets/pramaan-mark.svg" alt="PRAMAAN" className="pramaan-mark" />;
}
