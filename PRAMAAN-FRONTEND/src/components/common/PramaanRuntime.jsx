import { useEffect, useState } from 'react';
import { bootPramaan } from '../../core/pramaanRuntime.js';

export default function PramaanRuntime() {
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;

    const startPramaan = async () => {
      try {
        // Make sure DOM mount exists before booting runtime
        const app = document.getElementById('app');

        if (!app) {
          throw new Error('PRAMAAN app mount was not found.');
        }

        await bootPramaan();

        // Runtime should expose doLogin globally because
        // PRAMAAN pages use inline onclick handlers.
        if (typeof window.doLogin !== 'function') {
          console.warn(
            'PRAMAAN: doLogin was not exposed by pramaanRuntime.js'
          );
        }
      } catch (err) {
        console.error('PRAMAAN boot failed:', err);

        if (active) {
          setError(
            err?.message || 'Unable to start PRAMAAN.'
          );
        }
      }
    };

    startPramaan();

    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <div
        className="runtime-error"
        role="alert"
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '24px',
        }}
      >
        <div className="runtime-error-card">
          <div className="runtime-error-mark">⚖</div>

          <h1>PRAMAAN</h1>

          <h2>Application could not start</h2>

          <p>{error}</p>

          <button
            type="button"
            className="btn btn-primary"
            onClick={() => window.location.reload()}
          >
            Reload Application
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div
        id="app"
        className="app"
        aria-live="polite"
      />

      <div
        id="toast-root"
        aria-live="polite"
        aria-atomic="true"
      />
    </>
  );
}