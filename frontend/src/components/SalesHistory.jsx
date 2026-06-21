'use client';
import React from 'react';

export default function SalesHistory({ sales, totalCount }) {
  const formatDate = (isoStr) => {
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="sdui-saleshistory" style={{
      background: 'rgba(255, 255, 255, 0.02)',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: 'var(--border-radius)',
      padding: '1.2rem',
      color: '#fff',
      fontFamily: 'var(--font-family)',
      overflowX: 'auto'
    }}>
      <h2 style={{ margin: '0 0 1rem 0', fontSize: '1.2rem', fontWeight: '600', borderBottom: '1px solid rgba(255, 255, 255, 0.1)', paddingBottom: '0.5rem' }}>
        Ventas Recientes
      </h2>

      {sales.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '2rem 1rem', color: 'rgba(255, 255, 255, 0.3)', fontSize: '0.9rem' }}>
          No se registraron ventas en esta sesión.
        </div>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem', minWidth: '400px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.1)', textAlign: 'left', opacity: 0.7 }}>
              <th style={{ padding: '0.5rem' }}>ID</th>
              <th style={{ padding: '0.5rem' }}>Fecha/Hora</th>
              <th style={{ padding: '0.5rem' }}>Mtodo</th>
              <th style={{ padding: '0.5rem' }}>Estado</th>
              <th style={{ padding: '0.5rem', textAlign: 'right' }}>Total</th>
            </tr>
          </thead>
          <tbody>
            {sales.map((sale) => (
              <tr key={sale.id} style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.03)' }}>
                <td style={{ padding: '0.5rem', fontWeight: '600' }}>#{sale.id}</td>
                <td style={{ padding: '0.5rem', opacity: 0.8 }}>{formatDate(sale.timestamp)}</td>
                <td style={{ padding: '0.5rem', textTransform: 'capitalize', opacity: 0.8 }}>{sale.payment_method}</td>
                <td style={{ padding: '0.5rem' }}>
                  <span style={{
                    background: sale.payment_status === 'paid' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                    color: sale.payment_status === 'paid' ? '#10b981' : '#f59e0b',
                    padding: '0.15rem 0.4rem',
                    borderRadius: '4px',
                    fontSize: '0.75rem',
                    fontWeight: '600'
                  }}>
                    {sale.payment_status === 'paid' ? 'Pagado' : 'Impago'}
                  </span>
                </td>
                <td style={{ padding: '0.5rem', textAlign: 'right', fontWeight: '700', color: 'var(--secondary-color)' }}>
                  ${sale.total_amount.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
