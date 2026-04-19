import React, { useState } from 'react';
import { AreaChart, Area, XAxis, YAxis, Tooltip,
         ResponsiveContainer } from 'recharts';


const YEARS = ['FY2025E', 'FY2026E', 'FY2027E'];
const SHARES = 703;
const CURRENT_PRICE = 1346.8;

function projectPAT(nim, loanGrowth, creditCost, costToIncome) {
  let advances = 1_261_491;
  let nonII    = 22_958;
  const results = [];

  for (let i = 0; i < 3; i++) {
    advances  = advances * (1 + loanGrowth);
    nonII     = nonII * 1.10;
    const nii  = advances * nim;
    const tot  = nii + nonII;
    const opex = tot * costToIncome;
    const prov = advances * creditCost;
    const pat  = (tot - opex - prov) * 0.75;
    const eps  = pat / SHARES;
    results.push({
      year: YEARS[i],
      PAT:  Math.round(pat),
      EPS:  Math.round(eps * 10) / 10,
    });
  }
  return results;
}

const Slider = ({ label, value, min, max, step, onChange, format }) => (
  <div style={{ marginBottom: 16 }}>
    <div style={{ display:'flex', justifyContent:'space-between',
                  marginBottom:6 }}>
      <span style={{ fontSize:12, color:'#9ca3af' }}>{label}</span>
      <span style={{ fontSize:12, fontWeight:700,
                     color:'#3b82f6' }}>{format(value)}</span>
    </div>
    <input type="range" min={min} max={max} step={step}
           value={value}
           onChange={e => onChange(parseFloat(e.target.value))}
           style={{ width:'100%', accentColor:'#3b82f6' }} />
    <div style={{ display:'flex', justifyContent:'space-between',
                  fontSize:10, color:'#4b5563', marginTop:2 }}>
      <span>{format(min)}</span>
      <span>{format(max)}</span>
    </div>
  </div>
);

export default function ScenarioExplorer() {
  const [nim,         setNim]         = useState(0.046);
  const [loanGrowth,  setLoanGrowth]  = useState(0.15);
  const [creditCost,  setCreditCost]  = useState(0.007);
  const [costToIncome,setCostToIncome]= useState(0.375);
  const [peMultiple,  setPeMultiple]  = useState(18);

  const results  = projectPAT(nim, loanGrowth, creditCost, costToIncome);
  const eps27    = results[2]?.EPS || 0;
  const target   = Math.round(eps27 * peMultiple);
  const upside   = (((target - CURRENT_PRICE) / CURRENT_PRICE) * 100).toFixed(1);
  const isUpside = target > CURRENT_PRICE;

  return (
    <div>
      <div style={{ display:'flex', alignItems:'center',
                    gap:12, marginBottom:20 }}>
        ⚙️
        <h2 style={{ fontSize:16, fontWeight:700 }}>
          Interactive Scenario Explorer
        </h2>
      </div>

      <div style={{ display:'grid',
                    gridTemplateColumns:'1fr 1.5fr', gap:16 }}>
        {/* Controls */}
        <div className="card">
          <div className="card-title">Adjust Assumptions</div>
          <Slider label="Net Interest Margin (NIM)"
                  value={nim} min={0.030} max={0.060} step={0.001}
                  onChange={setNim}
                  format={v => `${(v*100).toFixed(1)}%`} />
          <Slider label="Loan Book Growth"
                  value={loanGrowth} min={0.05} max={0.30} step={0.01}
                  onChange={setLoanGrowth}
                  format={v => `${(v*100).toFixed(0)}%`} />
          <Slider label="Credit Cost"
                  value={creditCost} min={0.003} max={0.025} step={0.001}
                  onChange={setCreditCost}
                  format={v => `${(v*100).toFixed(1)}%`} />
          <Slider label="Cost-to-Income"
                  value={costToIncome} min={0.30} max={0.55} step={0.005}
                  onChange={setCostToIncome}
                  format={v => `${(v*100).toFixed(1)}%`} />
          <Slider label="P/E Multiple"
                  value={peMultiple} min={10} max={30} step={0.5}
                  onChange={setPeMultiple}
                  format={v => `${v}x`} />

          {/* Live price target */}
          <div style={{ marginTop:20, padding:'16px',
               borderRadius:8, textAlign:'center',
               background: isUpside ? '#064e3b' : '#450a0a',
               border:`1px solid ${isUpside ? '#10b981' : '#ef4444'}` }}>
            <div style={{ fontSize:11, color:'#6b7280',
                          marginBottom:4 }}>
              Implied Price Target (FY2027E)
            </div>
            <div style={{ fontSize:32, fontWeight:800,
              color: isUpside ? '#10b981' : '#ef4444' }}>
              ₹{target.toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize:13, marginTop:4,
              color: isUpside ? '#10b981' : '#ef4444' }}>
              {isUpside ? '+' : ''}{upside}% vs CMP ₹{CURRENT_PRICE}
            </div>
          </div>
        </div>

        {/* Chart */}
        <div className="card">
          <div className="card-title">Projected PAT (₹ crore)</div>
          <ResponsiveContainer width="100%" height={200}>
            <AreaChart data={results}
                       margin={{ top:10, right:10, bottom:0, left:10 }}>
              <defs>
                <linearGradient id="patGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%"  stopColor="#10b981" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <XAxis dataKey="year"
                     tick={{ fill:'#6b7280', fontSize:11 }} />
              <YAxis tick={{ fill:'#6b7280', fontSize:10 }}
                     tickFormatter={v =>
                       `₹${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ background:'#1f2937',
                  border:'1px solid #374151',
                  borderRadius:8, fontSize:12 }}
                formatter={v =>
                  [`₹${v.toLocaleString('en-IN')} cr`, 'PAT']} />
              <Area type="monotone" dataKey="PAT"
                    stroke="#10b981" strokeWidth={2}
                    fill="url(#patGrad)" />
            </AreaChart>
          </ResponsiveContainer>

          {/* EPS table */}
          <div style={{ marginTop:16 }}>
            <table style={{ width:'100%', fontSize:12,
                            borderCollapse:'collapse' }}>
              <thead>
                <tr style={{ borderBottom:'1px solid #1f2937' }}>
                  {['Year','PAT (₹ cr)','EPS (₹)'].map(h => (
                    <th key={h} style={{ padding:'6px 8px',
                      textAlign: h==='Year'?'left':'right',
                      color:'#6b7280', fontWeight:600 }}>{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {results.map((r, i) => (
                  <tr key={i}
                      style={{ borderBottom:'1px solid #0f172a' }}>
                    <td style={{ padding:'6px 8px',
                                 color:'#9ca3af' }}>{r.year}</td>
                    <td style={{ padding:'6px 8px', textAlign:'right' }}>
                      {r.PAT?.toLocaleString('en-IN')}
                    </td>
                    <td style={{ padding:'6px 8px', textAlign:'right',
                                 color:'#10b981', fontWeight:600 }}>
                      ₹{r.EPS}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div style={{ marginTop:12, padding:'10px 12px',
               borderRadius:6, background:'#0f172a',
               fontSize:11, color:'#6b7280' }}>
            💡 Move the sliders to explore how NIM compression,
            loan growth, or rising NPAs affect the price target in real time.
          </div>
        </div>
      </div>
    </div>
  );
}