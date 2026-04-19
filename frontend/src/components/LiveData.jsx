import React, { useEffect, useState } from 'react';
import axios from 'axios';


const API = 'http://localhost:8000/api';

const Metric = ({ label, value, sub, positive }) => (
  <div className="card" style={{ padding: '16px' }}>
    <div className="card-title" style={{ marginBottom: 8 }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 700,
      color: positive === true  ? '#10b981' :
             positive === false ? '#ef4444' : '#f1f5f9' }}>
      {value}
    </div>
    {sub && <div style={{ fontSize: 11, color: '#6b7280', marginTop: 4 }}>{sub}</div>}
  </div>
);

export default function LiveData() {
  const [data, setData]     = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/financials`)
      .then(r => { setData(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Fetching live data...</div>;
  if (!data)   return <div className="loading">Failed to load data.</div>;

  const live = data.live;
  const price = live.current_price;
  const high  = live['52w_high'];
  const low   = live['52w_low'];
  const pctFromHigh = (((price - high) / high) * 100).toFixed(1);

  return (
    <div>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center',
                    gap:12, marginBottom:20 }}>
        📊
        <h2 style={{ fontSize:16, fontWeight:700 }}>Live Market Data</h2>
        <span style={{ marginLeft:'auto', fontSize:11,
                       color:'#4b5563' }}>
          NSE: ICICIBANK
        </span>
      </div>

      {/* Price hero */}
      <div className="card" style={{ marginBottom:16, padding:'20px 24px',
           background:'linear-gradient(135deg,#1e3a5f,#111827)',
           borderColor:'#2563eb' }}>
        <div style={{ display:'flex', justifyContent:'space-between',
                      alignItems:'center' }}>
          <div>
            <div style={{ fontSize:36, fontWeight:800, color:'#f1f5f9' }}>
              ₹{price?.toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize:12, color:'#6b7280', marginTop:4 }}>
              Current Market Price
            </div>
          </div>
          <div style={{ textAlign:'right' }}>
            <div style={{ fontSize:13, color:'#6b7280' }}>52-Week Range</div>
            <div style={{ fontSize:13, marginTop:4 }}>
              <span className="negative">₹{low?.toLocaleString('en-IN')}</span>
              <span style={{ color:'#4b5563', margin:'0 6px' }}>—</span>
              <span className="positive">₹{high?.toLocaleString('en-IN')}</span>
            </div>
            <div style={{ fontSize:11, color:'#6b7280', marginTop:4 }}>
              {pctFromHigh}% from 52w high
            </div>
          </div>
        </div>
      </div>

      {/* Key metrics grid */}
      <div className="grid-4">
        <Metric label="P/E Ratio"
                value={`${live.pe_ratio?.toFixed(1)}x`}
                sub="Trailing twelve months" />
        <Metric label="P/BV Ratio"
                value={`${live.pb_ratio?.toFixed(2)}x`}
                sub="Price to Book" />
        <Metric label="EPS (TTM)"
                value={`₹${live.eps_ttm?.toFixed(1)}`}
                sub="Trailing twelve months"
                positive={true} />
        <Metric label="ROE"
                value={`${(live.roe * 100)?.toFixed(1)}%`}
                sub="Return on Equity"
                positive={live.roe > 0.15} />
        <Metric label="Book Value"
                value={`₹${live.book_value?.toFixed(0)}`}
                sub="Per share" />
        <Metric label="Market Cap"
                value={`₹${(live.market_cap_cr/100000)?.toFixed(1)}L cr`}
                sub="Lakh crore" />
        <Metric label="Dividend Yield"
                value={`${live.dividend_yield?.toFixed(2)}%`}
                sub="Annual yield" />
        <Metric label="52W Position"
                value={`${pctFromHigh}%`}
                sub="From 52-week high"
                positive={false} />
      </div>

      {/* Projection table */}
      <div className="card" style={{ marginTop:16 }}>
        <div className="card-title">3-Year Projections (₹ crore)</div>
        <table style={{ width:'100%', borderCollapse:'collapse',
                        fontSize:13 }}>
          <thead>
            <tr style={{ borderBottom:'1px solid #1f2937' }}>
              {['Metric','FY2025E','FY2026E','FY2027E'].map(h => (
                <th key={h} style={{ padding:'8px 12px', textAlign: h==='Metric'?'left':'right',
                                     color:'#6b7280', fontWeight:600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.projections?.map((row, i) => (
              <tr key={i} style={{ borderBottom:'1px solid #111827' }}>
                <td style={{ padding:'8px 12px', color:'#9ca3af' }}>{row.Year}</td>
                <td style={{ padding:'8px 12px', textAlign:'right' }}>
                  {row.NII?.toLocaleString('en-IN')}
                </td>
                <td style={{ padding:'8px 12px', textAlign:'right' }}>
                  {row.PAT?.toLocaleString('en-IN')}
                </td>
                <td style={{ padding:'8px 12px', textAlign:'right',
                             color:'#10b981' }}>
                  ₹{row['EPS (₹)']?.toFixed(1)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}