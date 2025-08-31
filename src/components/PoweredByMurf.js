import React from 'react';

const PoweredByMurf = () => (
  <div style={{
    position: 'fixed',
    bottom: '16px',
    right: '16px',
    background: 'rgba(255,255,255,0.9)',
    padding: '8px 16px',
    borderRadius: '8px',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
    zIndex: 1000,
    fontSize: '15px'
  }}>
    <a
      href="https://murf.ai/api/docs/introduction/overview"
      target="_blank"
      rel="noopener noreferrer"
      style={{ textDecoration: 'none', color: '#3f51b5', fontWeight: 600 }}
    >
      Powered by Murf
    </a>
  </div>
);

export default PoweredByMurf;
