import React from 'react';
import logoImg from './assets/logo.png';

const ChildSafety = () => {
  return (
    <div style={{ width: '100vw', height: '100vh', margin: '0', padding: '0' }}>
      <img src={logoImg} alt="VisionVoice Logo" className="logo" />
      <img src="http://localhost:5000/video/child_safety" alt="Child Safety Feed" style={{ width: '100vw', height: '100vh', objectFit: 'contain', borderRadius:'12px' }} />
      <div style={{ width: '100vw', height: '100vh', margin: '0', padding: '0' }}>hi</div>
    </div>
  );
};

export default ChildSafety;
