import React from 'react';
import { BrowserRouter as Router, Route, Routes, Link } from 'react-router-dom';
import ChildSafety from './ChildSafety';
import Navigation from './Navigation';
import childSafetyImg from './assets/child_safety.png';
import navigationImg from './assets/navigation.png';
import logoImg from './assets/logo.png';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app">
        <img src={logoImg} alt="VisionVoice Logo" className="logo" />
        <h1>VisionVoice</h1>
        <Routes>
          <Route path="/" element={
            <div className="container">
              <div className="half">
                <Link to="/child_safety">
                  <img src={childSafetyImg} alt="Child Safety" />
                </Link>
              </div>
              <div className="half">
                <Link to="/navigation">
                  <img src={navigationImg} alt="Navigation" />
                </Link>
              </div>
            </div>
          } />
          <Route path="/child_safety" element={<ChildSafety />} />
          <Route path="/navigation" element={<Navigation />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
