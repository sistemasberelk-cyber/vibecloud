'use client';
import React, { useEffect, useState } from 'react';
import { predefinedCombinations, composeTheme, applyThemeToDOM } from '../lib/themes';

export default function Header({ user, onLogout }) {
  const [activeTheme, setActiveTheme] = useState('combo-1');

  useEffect(() => {
    // Load theme from localStorage or user settings on mount
    const savedTheme = localStorage.getItem('vibecloud_theme') || 'combo-1';
    setActiveTheme(savedTheme);
    handleThemeChange(savedTheme, false);
  }, []);

  const handleThemeChange = async (comboId, saveToBackend = true) => {
    setActiveTheme(comboId);
    
    // Apply theme
    const combo = predefinedCombinations.find(c => c.id === comboId) || predefinedCombinations[0];
    const composed = composeTheme(combo.palette, combo.header, combo.hero, combo.footer, combo.card);
    applyThemeToDOM(composed);
    
    // Save locally
    localStorage.setItem('vibecloud_theme', comboId);

    // Save to backend
    if (saveToBackend && user?.tenant_id) {
      try {
        await fetch('/api/store/theme', {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ theme_id: comboId })
        });
      } catch (err) {
        console.error('Failed to save theme to backend', err);
      }
    }
  };

  return (
    <header className="sdui-header" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '0 1.5rem',
      height: 'var(--header-height, 60px)',
      background: 'var(--card-bg, rgba(255, 255, 255, 0.05))',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid var(--border-color, rgba(255, 255, 255, 0.1))',
      color: 'var(--text-color, #fff)',
      transition: 'all 0.3s ease'
    }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '700', fontFamily: 'var(--font-family)' }}>
          VibeCloud <span style={{ color: 'var(--primary-color)' }}>Minorista</span>
        </h1>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        
        {/* Theme Selector Dropdown */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <span style={{ fontSize: '0.8rem', opacity: 0.8 }}>Tema:</span>
          <select 
            value={activeTheme}
            onChange={(e) => handleThemeChange(e.target.value)}
            style={{
              background: 'var(--card-bg, rgba(0,0,0,0.2))',
              color: 'var(--text-color, #fff)',
              border: '1px solid var(--border-color, rgba(255,255,255,0.2))',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              fontSize: '0.85rem',
              outline: 'none',
              cursor: 'pointer'
            }}
          >
            {predefinedCombinations.map(combo => (
              <option key={combo.id} value={combo.id} style={{ color: '#000' }}>
                {combo.name}
              </option>
            ))}
          </select>
        </div>

        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{user?.full_name || user?.username}</div>
        </div>

        <button
          onClick={onLogout}
          style={{
            background: 'var(--card-bg)',
            color: 'var(--text-color)',
            border: '1px solid var(--border-color)',
            padding: '0.4rem 0.8rem',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '0.8rem',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.borderColor = 'var(--primary-color)'}
          onMouseLeave={(e) => e.target.style.borderColor = 'var(--border-color)'}
        >
          Cerrar
        </button>
      </div>
    </header>
  );
}
