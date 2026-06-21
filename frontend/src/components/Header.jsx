'use client';
import React from 'react';

export default function Header({ user, onLogout }) {
  return (
    <header className="sdui-header" style={{
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center',
      padding: '1rem 1.5rem',
      background: 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(10px)',
      borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: 'var(--border-radius)',
      marginBottom: '1rem',
      color: '#fff'
    }}>
      <div>
        <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: '700', fontFamily: 'var(--font-family)' }}>
          NexPos <span style={{ color: 'var(--primary-color)' }}>Enterprise</span>
        </h1>
        <p style={{ margin: 0, fontSize: '0.8rem', opacity: 0.7 }}>
          Terminal de Ventas Mayorista
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
        <div style={{ textAlign: 'right' }}>
          <div style={{ fontWeight: '600', fontSize: '0.9rem' }}>{user?.full_name || user?.username}</div>
          <div style={{ fontSize: '0.75rem', opacity: 0.6, textTransform: 'capitalize' }}>
            Rol: {user?.role} | Tenant ID: {user?.tenant_id}
          </div>
        </div>

        <button
          onClick={onLogout}
          style={{
            background: 'rgba(239, 68, 68, 0.2)',
            color: '#ef4444',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            padding: '0.5rem 1rem',
            borderRadius: 'calc(var(--border-radius) / 2)',
            cursor: 'pointer',
            fontWeight: '600',
            fontSize: '0.85rem',
            transition: 'all 0.2s'
          }}
          onMouseEnter={(e) => e.target.style.background = 'rgba(239, 68, 68, 0.3)'}
          onMouseLeave={(e) => e.target.style.background = 'rgba(239, 68, 68, 0.2)'}
        >
          Cerrar Sesión
        </button>
      </div>
    </header>
  );
}
