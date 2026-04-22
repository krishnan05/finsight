import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';


export default function ScenarioExplorer({ data, currentPrice }) {
  const [active, setActive] = useState('📊 Base');

  if (!data) return <div className="loading">⏳ Running scenarios...</div>;

  const scenarios  = Object.keys(data);
  const scenario   = data[active];
  const projections= scenario?.projections || [];
  const target     = scenario?.target || {};

  const colors = { '🐻 Bear':'#ef4444', '📊 Base':'#f59e0b', '🐂 Bull':'#10b981' };
  const color  = colors[active] || '#f59e0b';

  const upside = target['Upside (%)'];

  return (
    <div>
      {/* Scenario tabs */}
      <div style={{ display:'flex', gap:8, marginBottom:16 }}>
        {scenarios.map(s => (
          <button key={s} onClick={() => setActive(s)}
            style={{
              padding:'8px 16px', borderRadius:8, border:'none',
              cursor:'pointer', fontSize:13, fontWeight:600,
              background: active===s ? '#1f2937' : 'transparent',
              color: active===s ? colors[s] : '#6b7280',
              borderBottom: active===s ? `2px solid ${colors[s]}` : '2px solid transparent',
            }}>
            {s}
          </button>
        ))}
      </div>

      <div style={{ fontSize:12, color:'#6b7280', marginBottom:16 }}>
        {scenario?.description}
      </div>

      <div className="grid-2">
        {/* Chart */}
        <div className="card">
          <div className="card-title">EBITDA Trajectory (₹ crore)</div>
          <ResponsiveContainer width="100%" height={180}>
            <AreaChart data={projections}
                       margin={{ top:10, right:10, bottom:0, left:10 }}>
              <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor={color} stopOpacity={0.3}/>
                  <stop offset="95%" stopColor={color} stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="Year" tick={{ fill:'#6b7280', fontSize:11 }} />
              <YAxis tick={{ fill:'#6b7280', fontSize:10 }}
                     tickFormatter={v => `₹${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ background:'#1f2937', border:'1px solid #374151',
                                borderRadius:8, fontSize:12 }}
                formatter={v => [`₹${v?.toLocaleString('en-IN')} cr`, 'EBITDA']} />
              <Area type="monotone" dataKey="EBITDA"
                    stroke={color} strokeWidth={2}
                    fill="url(#grad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Price target */}
        <div className="card" style={{ display:'flex', flexDirection:'column',
                                        justifyContent:'center', alignItems:'center',
                                        textAlign:'center' }}>
          <div style={{ fontSize:12, color:'#6b7280', marginBottom:8 }}>
            Price Target (FY2027E)
          </div>
          <div style={{ fontSize:36, fontWeight:800, color }}>
            ₹{target['Avg Target (₹)']?.toLocaleString('en-IN')}
          </div>
          <div style={{ fontSize:14, color, marginTop:8 }}>
            {upside > 0 ? '+' : ''}{upside}% vs CMP
          </div>
          <div style={{ display:'flex', gap:16, marginTop:16,
                        fontSize:12, color:'#6b7280' }}>
            <div>
              <div style={{ color:'#9ca3af' }}>EV/EBITDA</div>
              <div style={{ fontWeight:600 }}>
                ₹{target['EV/EBITDA Target (₹)']?.toLocaleString('en-IN')}
              </div>
            </div>
            <div>
              <div style={{ color:'#9ca3af' }}>P/E</div>
              <div style={{ fontWeight:600 }}>
                ₹{target['P/E Target (₹)']?.toLocaleString('en-IN')}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Projections table */}
      <div className="card" style={{ marginTop:16 }}>
        <div className="card-title">Detailed Projections (₹ crore)</div>
        <table>
          <thead>
            <tr>
              {['Year','Revenue','EBITDA','PAT','FCF','EPS (₹)','EBITDA %'].map(h => (
                <th key={h} style={{ textAlign: h==='Year'?'left':'right' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {projections.map((row, i) => (
              <tr key={i}>
                <td style={{ color:'#9ca3af' }}>{row.Year}</td>
                <td style={{ textAlign:'right' }}>{row.Revenue?.toLocaleString('en-IN')}</td>
                <td style={{ textAlign:'right' }}>{row.EBITDA?.toLocaleString('en-IN')}</td>
                <td style={{ textAlign:'right' }}>{row.PAT?.toLocaleString('en-IN')}</td>
                <td style={{ textAlign:'right',
                             color: row.FCF > 0 ? '#10b981' : '#ef4444' }}>
                  {row.FCF?.toLocaleString('en-IN')}
                </td>
                <td style={{ textAlign:'right', color:'#10b981', fontWeight:600 }}>
                  ₹{row['EPS (₹)']}
                </td>
                <td style={{ textAlign:'right' }}>{row['EBITDA %']}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}