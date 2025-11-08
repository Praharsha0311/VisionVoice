import React from 'react';
import logoImg from './assets/logo.png';

const Navigation = () => {
  return (
    <div style={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '20px' }}>
      <img src={logoImg} alt="VisionVoice Logo" className="logo" />
      <img src="http://localhost:5000/video/navigation" alt="Navigation Feed" style={{ width: '90vw', height: '80vh', objectFit: 'contain' }} />
    </div>
  );
};

export default Navigation;
