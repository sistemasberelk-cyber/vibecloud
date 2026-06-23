'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiRequest } from '@/services/api';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [niche, setNiche] = useState('general');
  const [companyName, setCompanyName] = useState('');
  const [themeId, setThemeId] = useState('combo-4');
  
  const [texts, setTexts] = useState(null);
  const [loadingText, setLoadingText] = useState(true);
  const [loadingAction, setLoadingAction] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchTexts(step, niche);
  }, [step, niche]);

  const fetchTexts = async (currentStep, currentNiche) => {
    setLoadingText(true);
    setError(null);
    try {
      const res = await apiRequest(`/ai/onboarding/texts?step=${currentStep}&niche=${currentNiche}`);
      if (res && res.title) {
        setTexts(res);
      } else {
        throw new Error("Respuesta inválida de la IA");
      }
    } catch (err) {
      console.error(err);
      setError('Fallo de conexión espacial al generar textos. ' + err.message);
    } finally {
      setLoadingText(false);
    }
  };

  const handleNextStep1 = async () => {
    setStep(2);
  };

  const handleNextStep2 = async (selectedNiche) => {
    setNiche(selectedNiche);
    setStep(3);
  };

  const handleNextStep3 = async () => {
    if (!companyName.trim()) {
      setError('Debes darle un nombre a tu imperio.');
      return;
    }
    setLoadingAction(true);
    try {
      // Guardar nombre y tema
      await apiRequest('/store/theme', {
        method: 'PUT',
        body: { theme_id: themeId }
      });
      localStorage.setItem('vibecloud_theme', themeId);
      await apiRequest('/store/onboarding-progress', {
        method: 'PUT',
        body: { step: 3, company_name: companyName }
      });
      setStep(4);
    } catch (err) {
      setError('Error guardando configuración: ' + err.message);
    } finally {
      setLoadingAction(false);
    }
  };

  const handleFinish = async () => {
    setLoadingAction(true);
    try {
      // Finalizar onboarding seleccionando todos los productos por defecto para empezar
      const prodRes = await apiRequest('/products?limit=100');
      const allIds = prodRes && prodRes.items ? prodRes.items.map(p => p.id) : [];
      await apiRequest('/store/catalog', {
        method: 'POST',
        body: { product_ids: allIds }
      });
      await apiRequest('/store/onboarding-progress', {
        method: 'PUT',
        body: { step: 4 } // Listo
      });
      router.push('/');
    } catch (err) {
      setError('Error finalizando: ' + err.message);
    } finally {
      setLoadingAction(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh', 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center',
      background: 'radial-gradient(circle at center, #1e1b4b 0%, #020617 100%)',
      color: '#fff',
      padding: '2rem'
    }}>
      <div className="glass-card animate-fade-in" style={{
        maxWidth: '700px', 
        width: '100%', 
        padding: '3rem',
        borderRadius: '24px',
        border: '1px solid rgba(139, 92, 246, 0.3)',
        boxShadow: '0 0 40px rgba(139, 92, 246, 0.15)'
      }}>
        
        {loadingText ? (
          <div style={{ textAlign: 'center', padding: '3rem 0' }}>
            <div style={{
              width: '50px', height: '50px', 
              border: '3px solid rgba(255,255,255,0.1)', 
              borderTopColor: '#a855f7', 
              borderRadius: '50%', 
              animation: 'spin 1s linear infinite',
              margin: '0 auto 20px'
            }}></div>
            <h2 style={{ color: '#a855f7', fontWeight: '400', letterSpacing: '2px' }}>CONECTANDO AL MULTIVERSO...</h2>
            <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
          </div>
        ) : (
          <div className="animate-fade-in">
            {/* Cabecera generada por IA */}
            {texts && (
              <div style={{ marginBottom: '2.5rem', textAlign: 'center' }}>
                <h1 
                  dangerouslySetInnerHTML={{ __html: texts.title }} 
                  style={{ 
                    fontSize: '2.5rem', 
                    marginBottom: '1rem', 
                    background: 'linear-gradient(to right, #c084fc, #38bdf8)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent'
                  }} 
                />
                <h2 
                  dangerouslySetInnerHTML={{ __html: texts.subtitle }} 
                  style={{ fontSize: '1.2rem', fontWeight: '400', opacity: 0.8, marginBottom: '1.5rem' }} 
                />
                <div 
                  dangerouslySetInnerHTML={{ __html: texts.body }} 
                  style={{ fontSize: '1rem', lineHeight: '1.6', opacity: 0.7 }}
                />
              </div>
            )}

            {error && (
              <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#fca5a5', marginBottom: '1.5rem' }}>
                {error}
              </div>
            )}

            {/* Contenido interactivo según el paso */}
            {step === 1 && (
              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button 
                  onClick={handleNextStep1}
                  style={{
                    padding: '1rem 3rem', background: 'linear-gradient(135deg, #8b5cf6, #3b82f6)',
                    color: '#fff', border: 'none', borderRadius: '50px', fontSize: '1.2rem',
                    fontWeight: 'bold', cursor: 'pointer', boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
                  }}
                >
                  INICIAR SECUENCIA
                </button>
              </div>
            )}

            {step === 2 && (
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '2rem' }}>
                {['Moda y Ropa', 'Alimentos y Bebidas', 'Servicios Profesionales', 'Tecnología', 'Hogar y Decoración'].map(n => (
                  <button 
                    key={n}
                    onClick={() => handleNextStep2(n)}
                    style={{
                      padding: '1.5rem', background: 'rgba(255,255,255,0.05)',
                      border: '1px solid rgba(255,255,255,0.1)', borderRadius: '16px',
                      color: '#fff', cursor: 'pointer', transition: 'all 0.2s',
                      fontSize: '1.1rem', fontWeight: '500'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.borderColor = '#a855f7'}
                    onMouseOut={(e) => e.currentTarget.style.borderColor = 'rgba(255,255,255,0.1)'}
                  >
                    {n}
                  </button>
                ))}
              </div>
            )}

            {step === 3 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', marginTop: '2rem' }}>
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', opacity: 0.8 }}>Nombre del Imperio</label>
                  <input 
                    type="text" 
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Ej. NovaTech, AstroFashion..."
                    style={{
                      width: '100%', padding: '1rem', background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.2)', borderRadius: '12px',
                      color: '#fff', fontSize: '1.1rem'
                    }}
                  />
                </div>
                
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', opacity: 0.8 }}>Tema Holográfico</label>
                  <select 
                    value={themeId} 
                    onChange={e => setThemeId(e.target.value)}
                    style={{
                      width: '100%', padding: '1rem', background: 'rgba(0,0,0,0.3)',
                      border: '1px solid rgba(255,255,255,0.2)', borderRadius: '12px',
                      color: '#fff', fontSize: '1.1rem'
                    }}
                  >
                    <option value="combo-4">Cyberpunk Neon</option>
                    <option value="combo-2">Vibrant Glass</option>
                    <option value="combo-5">Luxury Gold</option>
                    <option value="combo-1">Minimal Light</option>
                  </select>
                </div>

                <button 
                  onClick={handleNextStep3}
                  disabled={loadingAction}
                  style={{
                    marginTop: '1rem', padding: '1rem', background: 'linear-gradient(135deg, #10b981, #059669)',
                    color: '#fff', border: 'none', borderRadius: '12px', fontSize: '1.1rem',
                    fontWeight: 'bold', cursor: loadingAction ? 'wait' : 'pointer', opacity: loadingAction ? 0.7 : 1
                  }}
                >
                  {loadingAction ? 'SINCRONIZANDO...' : 'SINTETIZAR MARCA'}
                </button>
              </div>
            )}

            {step === 4 && (
              <div style={{ textAlign: 'center', marginTop: '2rem' }}>
                <button 
                  onClick={handleFinish}
                  disabled={loadingAction}
                  style={{
                    padding: '1.2rem 3rem', background: 'linear-gradient(135deg, #f43f5e, #e11d48)',
                    color: '#fff', border: 'none', borderRadius: '50px', fontSize: '1.3rem',
                    fontWeight: 'bold', cursor: loadingAction ? 'wait' : 'pointer',
                    boxShadow: '0 0 30px rgba(225, 29, 72, 0.4)'
                  }}
                >
                  {loadingAction ? 'DESPEGANDO...' : 'ENTRAR AL ESPACIO-TIEMPO'}
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
