# QuickChart URL Patterns

All charts use [QuickChart.io](https://quickchart.io) — free, open-source, self-hostable.

## Common Parameters
- `bg=transparent` — Always use for dark mode compatibility
- `w=<width>` — Width in pixels (match email layout)
- `h=<height>` — Height in pixels
- `f=png` — Format (default)

## Bar Chart — Query Scores
```
https://quickchart.io/chart?c={type:'bar',data:{labels:['Q1','Q2','Q3'],datasets:[{data:[92,85,67],backgroundColor:['#D4A853','#B8943F','#8B7330']}]},options:{plugins:{legend:{display:false}},scales:{y:{beginAtZero:true,max:100}}}}&w=400&h=200&bg=transparent
```

## Line Chart — Trend
```
https://quickchart.io/chart?c={type:'line',data:{labels:['W1','W2','W3','W4'],datasets:[{label:'Score',data:[70,74,78,81],borderColor:'#D4A853',backgroundColor:'rgba(212,168,83,0.1)',fill:true,tension:0.4}]},options:{scales:{y:{beginAtZero:false,min:50,max:100}}}}&w=500&h=250&bg=transparent
```

## Doughnut/Gauge — Score 0-100
```
https://quickchart.io/chart?c={type:'doughnut',data:{labels:['Score','Reste'],datasets:[{data:[78,22],backgroundColor:['#D4A853','#2A2A2A'],borderWidth:0}]},options:{cutout:'75%',plugins:{legend:{display:false}}}}&w=150&h=150&bg=transparent
```

## Sparkline — Mini Trend (80x30)
```
https://quickchart.io/chart?c={type:'line',data:{labels:['','','','',''],datasets:[{data:[65,70,68,74,78],borderColor:'#D4A853',borderWidth:2,pointRadius:0,fill:false}]},options:{plugins:{legend:{display:false}},scales:{x:{display:false},y:{display:false}}}}&w=80&h=30&bg=transparent
```

## Radar — Competitor Comparison
```
https://quickchart.io/chart?c={type:'radar',data:{labels:['Visibilité','Contenu','Technique','Autorité','UX'],datasets:[{label:'Vous',data:[85,72,90,68,78],borderColor:'#D4A853',backgroundColor:'rgba(212,168,83,0.2)'},{label:'Concurrent',data:[70,80,75,85,70],borderColor:'#666',backgroundColor:'rgba(100,100,100,0.1)'}]},options:{scales:{r:{beginAtZero:true,max:100}}}}&w=400&h=300&bg=transparent
```

## Grouped Bar — Multi-Model Comparison
```
https://quickchart.io/chart?c={type:'bar',data:{labels:['Q1','Q2','Q3'],datasets:[{label:'GPT-4',data:[92,88,85],backgroundColor:'#D4A853'},{label:'Claude',data:[89,91,87],backgroundColor:'#8B7330'},{label:'Gemini',data:[85,83,82],backgroundColor:'#5A4F3A'}]},options:{scales:{y:{beginAtZero:true,max:100}}}}&w=500&h=280&bg=transparent
```

## Color Palette (Geo Presence Dark/Gold)
| Token | Color |
|-------|-------|
| Primary | `#D4A853` |
| Secondary | `#8B7330` |
| Tertiary | `#5A4F3A` |
| Background | `transparent` (use bg param) |
| Grid lines | `rgba(255,255,255,0.1)` |
| Up (positive) | `#4CAF50` |
| Down (negative) | `#E53935` |
