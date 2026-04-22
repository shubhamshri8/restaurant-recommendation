import React from 'react';
import type { RestaurantResult } from '../services/api';

interface RestaurantCardProps {
  restaurant: RestaurantResult;
}

export const RestaurantCard: React.FC<RestaurantCardProps> = ({ restaurant }) => {
  return (
    <div className="editorial-card" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem', height: '100%' }}>
      
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '1rem', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem' }}>
        <div style={{ minWidth: 0 }}>
          <h3 style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem', wordWrap: 'break-word', fontFamily: 'Playfair Display, serif' }}>
            {restaurant.name}
          </h3>
          <p style={{ fontSize: '0.875rem', fontWeight: 500 }}>
            <span style={{ color: 'var(--primary-color)' }}>★ {restaurant.rating.toFixed(1)}</span> • {restaurant.cuisines.join(', ')} • ₹{restaurant.estimated_cost}
          </p>
        </div>
      </div>

      {/* Match Section */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-start' }}>
        <div style={{ 
          width: '48px', 
          height: '48px', 
          borderRadius: '50%', 
          backgroundColor: 'var(--primary-color)', 
          color: 'white', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center', 
          fontWeight: '700',
          flexShrink: 0
        }}>
          95%
        </div>
        <div>
          <h4 style={{ fontSize: '1rem', fontWeight: 600, marginBottom: '0.5rem' }}>Why this is a perfect match</h4>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
            "{restaurant.reason}"
          </p>
        </div>
      </div>

      {/* Signals Grid */}
      {restaurant.match_signals && restaurant.match_signals.length > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: 'auto', paddingTop: '1rem', borderTop: '1px solid var(--border-color)' }}>
          {restaurant.match_signals.map((signal, idx) => (
            <div key={idx} style={{ background: '#F9FAFB', padding: '0.75rem', borderRadius: 'var(--radius-sm)' }}>
              <div style={{ color: 'var(--primary-color)', fontSize: '1.2rem', marginBottom: '0.25rem' }}>✦</div>
              <p style={{ fontSize: '0.8rem', fontWeight: 500, color: 'var(--text-primary)' }}>{signal}</p>
            </div>
          ))}
        </div>
      )}

    </div>
  );
};
