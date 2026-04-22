import React, { useState } from 'react';
import type { RecommendationRequest } from '../services/api';

interface SearchFormProps {
  onSearch: (request: RecommendationRequest) => void;
  isLoading: boolean;
}

const LOCALITIES = ["Sarjapur Road", "BTM", "Whitefield", "Koramangala 5th Block", "Indiranagar", "Malleshwaram", "Brigade Road", "Marathahalli", "JP Nagar", "Basavanagudi", "Rajajinagar", "Vasanth Nagar", "Kalyan Nagar", "Old Airport Road", "HSR", "Cunningham Road", "Residency Road", "New BEL Road", "Koramangala 1st Block", "Koramangala 7th Block", "Banashankari", "Electronic City", "Koramangala 4th Block", "Lavelle Road", "MG Road", "Church Street", "Richmond Road", "Bellandur", "St. Marks Road", "ITPL Main Road, Whitefield", "Jayanagar", "Seshadripuram", "Bannerghatta Road", "Race Course Road", "Nagawara", "Koramangala 6th Block", "Ulsoor", "Hennur", "Kammanahalli", "City Market", "Brookefield", "Varthur Main Road, Whitefield", "Frazer Town", "Sadashiv Nagar", "Basaveshwara Nagar", "Thippasandra", "Koramangala 3rd Block", "Banaswadi", "Koramangala", "Koramangala 8th Block", "Sahakara Nagar", "Domlur", "Infantry Road", "Shanti Nagar", "Sankey Road", "Vijay Nagar", "Jeevan Bhima Nagar", "Majestic", "HBR Layout", "Yeshwantpur", "Koramangala 2nd Block", "Commercial Street", "Hosur Road", "Shivajinagar", "Kumaraswamy Layout", "Old Madras Road", "Sanjay Nagar", "RT Nagar", "Kaggadasapura", "Ejipura", "CV Raman Nagar", "Wilson Garden", "Rajarajeshwari Nagar", "Hebbal", "Bommanahalli", "Langford Town", "Magadi Road", "Rammurthy Nagar", "Yelahanka", "Jalahalli", "KR Puram", "South Bangalore", "East Bangalore", "Kanakapura Road", "Mysore Road", "Kengeri", "Uttarahalli", "Central Bangalore", "North Bangalore", "West Bangalore", "Nagarbhavi", "Peenya"];

const CUISINES = ['Italian', 'Japanese', 'Mexican', 'Indian', 'Mediterranean', 'Chinese', 'North Indian', 'South Indian', 'Thai', 'Continental', 'Fast Food', 'Cafe'];

export const SearchForm: React.FC<SearchFormProps> = ({ onSearch, isLoading }) => {
  const [formData, setFormData] = useState<RecommendationRequest>({
    area: '',
    budget_inr: 1000,
    cuisine: 'Italian',
    min_rating: 4.0,
    notes: '',
    top_n: 20
  });

  const handleSubmit = () => {
    onSearch(formData);
  };

  return (
    <div className="context-bar">
      {/* Location */}
      <div className="context-bar-input-group location">
        <span className="group-icon">📍</span>
        <input
          id="location-input"
          type="text"
          placeholder="Where are we dining?"
          value={formData.area}
          onChange={e => setFormData(p => ({ ...p, area: e.target.value }))}
          list="area-options"
        />
        <datalist id="area-options">
          {LOCALITIES.map(loc => <option key={loc} value={loc} />)}
        </datalist>
      </div>

      {/* Cuisine */}
      <div className="context-bar-input-group">
        <span className="group-icon">🍽️</span>
        <select
          id="cuisine-select"
          value={formData.cuisine}
          onChange={e => setFormData(p => ({ ...p, cuisine: e.target.value }))}
        >
          {CUISINES.map(c => <option key={c} value={c}>{c}</option>)}
        </select>
      </div>

      {/* Budget */}
      <div className="context-bar-input-group">
        <span className="group-icon">💰</span>
        <select
          id="budget-select"
          value={formData.budget_inr}
          onChange={e => setFormData(p => ({ ...p, budget_inr: Number(e.target.value) }))}
        >
          <option value={500}>Under ₹500</option>
          <option value={1000}>₹500 – ₹1,000</option>
          <option value={2000}>₹1,000 – ₹2,000</option>
          <option value={4000}>₹2,000+</option>
        </select>
      </div>

      {/* Rating */}
      <div className="context-bar-input-group last-group">
        <span className="group-icon">⭐</span>
        <select
          id="rating-select"
          value={formData.min_rating}
          onChange={e => setFormData(p => ({ ...p, min_rating: Number(e.target.value) }))}
        >
          <option value={0}>Any Rating</option>
          <option value={3.5}>3.5+ Stars</option>
          <option value={4.0}>4.0+ Stars</option>
          <option value={4.5}>4.5+ Stars</option>
        </select>
      </div>

      {/* Generate Button */}
      <button
        id="generate-btn"
        className="btn btn-primary context-bar-btn"
        onClick={handleSubmit}
        disabled={isLoading || !formData.area}
      >
        {isLoading
          ? <div className="spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }}></div>
          : 'Find Restaurants'}
      </button>
    </div>
  );
};
