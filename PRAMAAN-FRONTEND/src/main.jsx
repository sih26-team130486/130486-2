import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App.jsx';

const root = document.getElementById('root');

if (!root) {
  throw new Error('PRAMAAN root element was not found.');
}

ReactDOM.createRoot(root).render(<App />);
