import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import Navbar from './components/Navbar';
import WaveBackground from './components/WaveBackground';
import Home from './pages/Home';
import Login from './pages/Login';
import Signup from './pages/Signup';
import ConnectWallet from './pages/ConnectWallet';
import Product from './pages/Product';
import Policies from './pages/Policies';
import Logs from './pages/Logs';
import Enterprise from './pages/Enterprise';
import { TradeSubmission } from './components/TradeSubmission';
import { ErrorBoundary } from './components/ErrorBoundary';
import './styles/trade.css';

export default function App() {
  return (
    <AppProvider>
      <Router>
        <div className="min-h-screen flex flex-col">
          <WaveBackground />
          <Navbar />
          
          <ErrorBoundary>
            <Routes>
              <Route path="/" element={<Home />} />
              <Route path="/login" element={<Login />} />
              <Route path="/signup" element={<Signup />} />
              <Route path="/wallet" element={<ConnectWallet />} />
              <Route path="/product" element={<Product />} />
              <Route path="/policies" element={<Policies />} />
              <Route path="/logs" element={<Logs />} />
              <Route path="/enterprise" element={<Enterprise />} />
              <Route path="/trade" element={<TradeSubmission />} />
            </Routes>
          </ErrorBoundary>
        </div>
      </Router>
    </AppProvider>
  );
}