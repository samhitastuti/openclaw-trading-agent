import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Moon, Sun } from 'lucide-react';
import { motion } from 'motion/react';
import { useAppContext } from '../context/AppContext';

const Navbar = () => {
  const { theme, toggleTheme, user } = useAppContext();
  const location = useLocation();

  const navLinks = [
    { name: 'Product', path: '/product' },
    { name: 'Policies', path: '/policies' },
    { name: 'Logs', path: '/logs' },
    { name: 'Enterprise', path: '/enterprise' },
  ];

  const isActive = (path: string) => location.pathname === path;

  const MotionLink = motion.create(Link);

  return (
    <nav className="flex items-center justify-between px-8 py-6 border-b border-[var(--border)] glass sticky top-0 z-50">
      <div className="flex items-center gap-8">
        <Link to="/" className="flex items-center gap-2 font-bold text-xl tracking-tight">
          <div className="w-8 h-8 bg-black dark:bg-white rounded-lg flex items-center justify-center">
            <Shield className="w-5 h-5 text-white dark:text-black" />
          </div>
          <span>Veridict</span>
        </Link>
        <div className="hidden md:flex items-center gap-6 text-sm font-medium">
          {navLinks.map((link) => (
            <MotionLink
              key={link.path}
              to={link.path}
              whileHover={{ scale: 1.05, color: 'var(--foreground)' }}
              transition={{ type: 'spring', stiffness: 400, damping: 17 }}
              className={`relative py-1 transition-colors ${
                isActive(link.path)
                  ? 'text-[var(--foreground)]'
                  : 'text-[var(--muted)]'
              }`}
            >
              {link.name}
              {isActive(link.path) && (
                <motion.div
                  layoutId="nav-active"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
            </MotionLink>
          ))}
        </div>
      </div>
      <div className="flex items-center gap-4">
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full hover:bg-[var(--accent)] transition-colors"
        >
          {theme === 'light' ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
        </button>
        {user ? (
          <span className="text-sm font-medium text-[var(--muted)]">{user.email}</span>
        ) : (
          <MotionLink
            to="/login"
            whileHover={{ scale: 1.05, color: 'var(--foreground)' }}
            transition={{ type: 'spring', stiffness: 400, damping: 17 }}
            className={`relative py-1 text-sm font-medium transition-colors ${
              isActive('/login') ? 'text-[var(--foreground)]' : 'text-[var(--muted)]'
            }`}
          >
            Login
            {isActive('/login') && (
              <motion.div
                layoutId="nav-active"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-500 rounded-full"
                transition={{ type: 'spring', stiffness: 380, damping: 30 }}
              />
            )}
          </MotionLink>
        )}
        <Link to="/wallet">
          <button className="px-5 py-2.5 bg-[var(--primary)] text-[var(--primary-foreground)] rounded-full text-sm font-semibold hover:opacity-90 transition-all active:scale-95">
            Connect Wallet
          </button>
        </Link>
      </div>
    </nav>
  );
};

export default Navbar;
