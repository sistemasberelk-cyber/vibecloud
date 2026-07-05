'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiRequest } from '@/services/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Clear any old session details when visiting login page
  useEffect(() => {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('username');
  }, []);

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username || !password) {
      setError('Por favor complete todos los campos.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const response = await apiRequest('/auth/login', {
        method: 'POST',
        body: { username, password }
      });

      if (response && response.access_token) {
        localStorage.setItem('accessToken', response.access_token);
        localStorage.setItem('refreshToken', response.refresh_token);
        localStorage.setItem('username', username);
        // Set cookie for middleware
        document.cookie = `is_onboarded=${response.is_onboarded}; path=/; max-age=604800`; // 7 days
        router.push('/');
      } else {
        setError('Error al recibir tokens de sesión.');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Error al iniciar sesión. Verifique sus credenciales.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      width: '100%',
      // Premium mesh gradient background
      background: 'radial-gradient(circle at 15% 50%, rgba(79, 70, 229, 0.15), transparent 25%), radial-gradient(circle at 85% 30%, rgba(16, 185, 129, 0.15), transparent 25%), linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%)',
      padding: '1.5rem',
      fontFamily: 'Inter, system-ui, sans-serif'
    }}>
      <div style={{
        background: 'rgba(30, 41, 59, 0.4)',
        backdropFilter: 'blur(20px) saturate(180%)',
        WebkitBackdropFilter: 'blur(20px) saturate(180%)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '24px',
        padding: '3rem',
        width: '100%',
        maxWidth: '440px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.05)',
        color: '#f8fafc',
        display: 'flex',
        flexDirection: 'column',
        gap: '2rem',
        position: 'relative',
        overflow: 'hidden'
      }}>
        {/* Subtle glow effect inside the card */}
        <div style={{
          position: 'absolute',
          top: '-50%',
          left: '-50%',
          width: '200%',
          height: '200%',
          background: 'radial-gradient(circle, rgba(255,255,255,0.03) 0%, transparent 60%)',
          pointerEvents: 'none'
        }} />

        {/* Header Branding */}
        <div style={{ textAlign: 'center', position: 'relative', zIndex: 1 }}>
          <h1 style={{
            fontSize: '2.5rem',
            fontWeight: '800',
            margin: '0 0 0.5rem 0',
            letterSpacing: '-0.03em',
            background: 'linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            filter: 'drop-shadow(0px 2px 4px rgba(0,0,0,0.5))'
          }}>
            VibeCloud
          </h1>
          <p style={{
            fontSize: '0.9rem',
            color: '#94a3b8',
            fontWeight: '500',
            letterSpacing: '0.01em',
            margin: 0
          }}>
            Portal de Acceso Mayorista
          </p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', position: 'relative', zIndex: 1 }}>
          
          {/* User Input */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: '600', color: '#cbd5e1' }}>Usuario</label>
            <div style={{ position: 'relative' }}>
              <input
                type="text"
                placeholder="Ingresa tu usuario"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                style={{
                  width: '100%',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '1rem 1.2rem',
                  borderRadius: '12px',
                  color: '#ffffff',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.3s ease',
                  boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.2)'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#818cf8';
                  e.target.style.boxShadow = '0 0 0 3px rgba(129, 140, 248, 0.2), inset 0 2px 4px rgba(0,0,0,0.2)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  e.target.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.2)';
                }}
              />
            </div>
          </div>

          {/* Password Input */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ fontSize: '0.85rem', fontWeight: '600', color: '#cbd5e1' }}>Contraseña</label>
            <div style={{ position: 'relative' }}>
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                style={{
                  width: '100%',
                  background: 'rgba(15, 23, 42, 0.6)',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  padding: '1rem 1.2rem',
                  borderRadius: '12px',
                  color: '#ffffff',
                  fontSize: '1rem',
                  outline: 'none',
                  transition: 'all 0.3s ease',
                  boxShadow: 'inset 0 2px 4px rgba(0,0,0,0.2)'
                }}
                onFocus={(e) => {
                  e.target.style.borderColor = '#818cf8';
                  e.target.style.boxShadow = '0 0 0 3px rgba(129, 140, 248, 0.2), inset 0 2px 4px rgba(0,0,0,0.2)';
                }}
                onBlur={(e) => {
                  e.target.style.borderColor = 'rgba(255, 255, 255, 0.1)';
                  e.target.style.boxShadow = 'inset 0 2px 4px rgba(0,0,0,0.2)';
                }}
              />
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              color: '#fca5a5',
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.3)',
              borderRadius: '10px',
              padding: '0.8rem 1rem',
              fontSize: '0.85rem',
              fontWeight: '500',
              animation: 'fadeIn 0.3s ease'
            }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10"></circle>
                <line x1="12" y1="8" x2="12" y2="12"></line>
                <line x1="12" y1="16" x2="12.01" y2="16"></line>
              </svg>
              {error}
            </div>
          )}

          {/* Submit Button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              background: 'linear-gradient(135deg, #6366f1 0%, #4f46e5 100%)',
              color: '#ffffff',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              padding: '1rem',
              borderRadius: '12px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: '700',
              fontSize: '1rem',
              marginTop: '0.5rem',
              transition: 'all 0.3s ease',
              boxShadow: '0 10px 20px -10px rgba(99, 102, 241, 0.5)',
              opacity: loading ? 0.7 : 1,
              transform: loading ? 'scale(0.98)' : 'scale(1)'
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 15px 25px -10px rgba(99, 102, 241, 0.6)';
              }
            }}
            onMouseLeave={(e) => {
              if (!loading) {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 10px 20px -10px rgba(99, 102, 241, 0.5)';
              }
            }}
          >
            {loading ? (
              <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                <svg className="animate-spin" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ animation: 'spin 1s linear infinite' }}>
                  <path d="M21 12a9 9 0 11-6.219-8.56"></path>
                </svg>
                Iniciando Sesión...
              </span>
            ) : 'Ingresar'}
          </button>
        </form>

        {/* Footer */}
        <div style={{
          textAlign: 'center',
          fontSize: '0.75rem',
          color: '#64748b',
          marginTop: '1rem',
          position: 'relative',
          zIndex: 1
        }}>
          VibeCloud SaaS &copy; 2026. <br/> Todos los derechos reservados.
        </div>
      </div>

      {/* Global styles for animations since we use inline styles mostly */}
      <style dangerouslySetInnerHTML={{__html: `
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-5px); }
          to { opacity: 1; transform: translateY(0); }
        }
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        * { box-sizing: border-box; }
      `}} />
    </div>
  );
}
