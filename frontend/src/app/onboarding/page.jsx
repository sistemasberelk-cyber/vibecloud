'use client';
import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { apiRequest } from '@/services/api';
import { predefinedCombinations, composeTheme, applyThemeToDOM } from '@/lib/themes';

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [companyName, setCompanyName] = useState('');
  const [themeId, setThemeId] = useState('combo-1');
  const [products, setProducts] = useState([]);
  const [selectedProductIds, setSelectedProductIds] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Basic setup on load
    const savedTheme = localStorage.getItem('vibecloud_theme') || 'combo-1';
    setThemeId(savedTheme);
    applyThemePreview(savedTheme);
    
    // Check if we have an existing step saved in backend
    fetchInitialProgress();
  }, []);

  const fetchInitialProgress = async () => {
    try {
      // In a real scenario we'd fetch the tenant settings here 
      // to resume the exact step. For simplicity we'll assume step 1 unless implemented.
    } catch (e) {
      console.error(e);
    }
  };

  const applyThemePreview = (comboId) => {
    const combo = predefinedCombinations.find(c => c.id === comboId);
    if (combo) {
      const composed = composeTheme(combo.palette, combo.header, combo.hero, combo.footer, combo.card);
      applyThemeToDOM(composed);
    }
  };

  const handleNextStep1 = async () => {
    if (!companyName.trim()) {
      setError('Por favor, ingresa el nombre de tu tienda.');
      return;
    }
    setError(null);
    setLoading(true);
    try {
      await apiRequest('/store/onboarding-progress', {
        method: 'PUT',
        body: { step: 2, company_name: companyName }
      });
      setStep(2);
    } catch (err) {
      setError('Error guardando progreso: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleNextStep2 = async () => {
    setLoading(true);
    try {
      await apiRequest('/store/theme', {
        method: 'PUT',
        body: { theme_id: themeId }
      });
      localStorage.setItem('vibecloud_theme', themeId);
      await apiRequest('/store/onboarding-progress', {
        method: 'PUT',
        body: { step: 3 }
      });
      
      // Load products for step 3
      const prodRes = await apiRequest('/products?limit=1000'); // Fetch all for simplified onboarding
      if (prodRes && prodRes.items) {
        setProducts(prodRes.items);
        // Hybrid: Pre-select all by default
        const allIds = prodRes.items.map(p => p.id);
        setSelectedProductIds(new Set(allIds));
      }
      setStep(3);
    } catch (err) {
      setError('Error guardando diseño: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleFinish = async () => {
    setLoading(true);
    try {
      await apiRequest('/store/catalog', {
        method: 'POST',
        body: { product_ids: Array.from(selectedProductIds) }
      });
      
      // Set local cookie for middleware
      document.cookie = `is_onboarded=true; path=/; max-age=604800`;
      
      router.push('/');
    } catch (err) {
      setError('Error guardando catálogo: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  const toggleProduct = (id) => {
    const newSet = new Set(selectedProductIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedProductIds(newSet);
  };

  return (
    <div style={{ minHeight: '100vh', background: 'var(--background-gradient)', color: 'var(--text-color)', padding: '2rem' }}>
      <div style={{ maxWidth: '800px', margin: '0 auto', background: 'var(--card-bg)', borderRadius: '12px', padding: '2rem', border: '1px solid var(--border-color)' }}>
        
        {/* Progress Indicator */}
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '2rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
          <div style={{ fontWeight: step >= 1 ? '700' : '400', color: step >= 1 ? 'var(--primary-color)' : 'inherit' }}>1. Negocio</div>
          <div style={{ fontWeight: step >= 2 ? '700' : '400', color: step >= 2 ? 'var(--primary-color)' : 'inherit' }}>2. Diseño</div>
          <div style={{ fontWeight: step >= 3 ? '700' : '400', color: step >= 3 ? 'var(--primary-color)' : 'inherit' }}>3. Catálogo</div>
        </div>

        {error && <div style={{ background: 'var(--danger-color)', color: '#fff', padding: '1rem', borderRadius: '8px', marginBottom: '1rem' }}>{error}</div>}

        {/* STEP 1 */}
        {step === 1 && (
          <div>
            <h2>Bienvenido a VibeCloud</h2>
            <p style={{ opacity: 0.8, marginBottom: '2rem' }}>Vamos a configurar tu nueva tienda minorista en 3 simples pasos.</p>
            
            <div style={{ marginBottom: '1.5rem' }}>
              <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '600' }}>Nombre de tu tienda</label>
              <input 
                type="text" 
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                placeholder="Ej. Mi Tienda Increíble"
                style={{ width: '100%', padding: '0.75rem', borderRadius: '6px', border: '1px solid var(--border-color)', background: 'rgba(0,0,0,0.1)', color: 'inherit', outline: 'none' }}
              />
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button onClick={handleNextStep1} disabled={loading} style={{ background: 'var(--primary-color)', color: '#fff', border: 'none', padding: '0.75rem 1.5rem', borderRadius: '6px', fontWeight: '600', cursor: 'pointer' }}>
                {loading ? 'Guardando...' : 'Siguiente Paso'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <div>
            <h2>Selecciona un Diseño Base</h2>
            <p style={{ opacity: 0.8, marginBottom: '2rem' }}>Elige una plantilla inicial. Podrás generar una con IA o modificarla más tarde.</p>
            
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
              {predefinedCombinations.slice(0, 4).map(combo => (
                <div 
                  key={combo.id}
                  onClick={() => { setThemeId(combo.id); applyThemePreview(combo.id); }}
                  style={{
                    border: themeId === combo.id ? '2px solid var(--primary-color)' : '1px solid var(--border-color)',
                    padding: '1rem',
                    borderRadius: '8px',
                    cursor: 'pointer',
                    opacity: themeId === combo.id ? 1 : 0.6
                  }}
                >
                  <strong>{combo.name}</strong>
                  <div style={{ fontSize: '0.8rem', marginTop: '0.5rem' }}>{combo.palette}</div>
                </div>
              ))}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button onClick={() => setStep(1)} style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-color)', padding: '0.75rem 1.5rem', borderRadius: '6px', cursor: 'pointer' }}>
                Atrás
              </button>
              <button onClick={handleNextStep2} disabled={loading} style={{ background: 'var(--primary-color)', color: '#fff', border: 'none', padding: '0.75rem 1.5rem', borderRadius: '6px', fontWeight: '600', cursor: 'pointer' }}>
                {loading ? 'Aplicando...' : 'Confirmar Diseño'}
              </button>
            </div>
          </div>
        )}

        {/* STEP 3 */}
        {step === 3 && (
          <div>
            <h2>Catálogo de Productos</h2>
            <p style={{ opacity: 0.8, marginBottom: '2rem' }}>Selecciona qué productos mayoristas deseas revender. Hemos pre-seleccionado todos por defecto.</p>
            
            <div style={{ maxHeight: '400px', overflowY: 'auto', border: '1px solid var(--border-color)', borderRadius: '8px', padding: '1rem', marginBottom: '2rem' }}>
              {products.map(p => (
                <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: '1rem', padding: '0.5rem 0', borderBottom: '1px solid var(--border-color)' }}>
                  <input 
                    type="checkbox" 
                    checked={selectedProductIds.has(p.id)} 
                    onChange={() => toggleProduct(p.id)}
                    style={{ width: '18px', height: '18px' }}
                  />
                  <div>
                    <div style={{ fontWeight: '600' }}>{p.name}</div>
                    <div style={{ fontSize: '0.85rem', opacity: 0.7 }}>Stock: {p.stock_quantity} | Precio Minorista: ${p.price_retail}</div>
                  </div>
                </div>
              ))}
              {products.length === 0 && <div style={{ textAlign: 'center', opacity: 0.5, padding: '2rem' }}>No hay productos en tu inventario mayorista.</div>}
            </div>
            
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <button onClick={() => setStep(2)} style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-color)', padding: '0.75rem 1.5rem', borderRadius: '6px', cursor: 'pointer' }}>
                Atrás
              </button>
              <button onClick={handleFinish} disabled={loading} style={{ background: 'var(--success-color, #10B981)', color: '#fff', border: 'none', padding: '0.75rem 1.5rem', borderRadius: '6px', fontWeight: '600', cursor: 'pointer' }}>
                {loading ? 'Finalizando...' : `¡Lanzar Tienda! (${selectedProductIds.size} productos)`}
              </button>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
