// ============================================================
// Charts Utility — Professional Data Visualization Engine
// Uses Chart.js with Agri-Connect's dark green theme
// ============================================================

const CHART_COLORS = {
  primary: '#22c55e',
  primaryDark: '#16a34a',
  primaryLight: '#4ade80',
  accent: '#f59e0b',
  accentDark: '#d97706',
  info: '#3b82f6',
  danger: '#ef4444',
  success: '#22c55e',
  text: '#f0fdf4',
  textMuted: '#6b7280',
  surface: '#1e2a20',
  border: 'rgba(34, 197, 94, 0.12)',
  gradientGreen1: 'rgba(22, 163, 74, 0.8)',
  gradientGreen2: 'rgba(34, 197, 94, 0.4)',
  gradientAmber1: 'rgba(245, 158, 11, 0.8)',
  gradientAmber2: 'rgba(245, 158, 11, 0.3)',
  gradientBlue1: 'rgba(59, 130, 246, 0.8)',
  gradientBlue2: 'rgba(59, 130, 246, 0.3)',
};

const PALETTE = [
  '#22c55e', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6',
  '#06b6d4', '#ec4899', '#14b8a6', '#f97316', '#6366f1',
];

// Active chart instances to destroy before re-creating
const chartInstances = {};

function destroyChart(id) {
  if (chartInstances[id]) {
    chartInstances[id].destroy();
    delete chartInstances[id];
  }
}

function getCtx(canvasId) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return null;
  return canvas.getContext('2d');
}

function makeGradient(ctx, color1, color2, vertical = true) {
  const gradient = vertical
    ? ctx.createLinearGradient(0, 0, 0, ctx.canvas.height)
    : ctx.createLinearGradient(0, 0, ctx.canvas.width, 0);
  gradient.addColorStop(0, color1);
  gradient.addColorStop(1, color2);
  return gradient;
}

// ============================================================
// 1. SOIL NUTRIENT RADAR CHART
// ============================================================
export function createSoilRadarChart(canvasId, soilData) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const labels = ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)', 'pH Level', 'Moisture %', 'Organic Carbon'];
  
  // Normalize values to 0-100 scale for radar
  const maxValues = { N: 140, P: 145, K: 205, ph: 9, moisture: 100, oc: 500 };
  const values = [
    ((soilData.N || 0) / maxValues.N) * 100,
    ((soilData.P || 0) / maxValues.P) * 100,
    ((soilData.K || 0) / maxValues.K) * 100,
    ((soilData.ph || 0) / maxValues.ph) * 100,
    ((soilData.moisture_pct || soilData.soil_moisture || 0) / maxValues.moisture) * 100,
    ((soilData.organic_carbon || soilData.oc || 0) / maxValues.oc) * 100,
  ];

  // Ideal range values
  const idealValues = [
    (80 / maxValues.N) * 100,
    (60 / maxValues.P) * 100,
    (80 / maxValues.K) * 100,
    (6.5 / maxValues.ph) * 100,
    (50 / maxValues.moisture) * 100,
    (150 / maxValues.oc) * 100,
  ];

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'radar',
    data: {
      labels,
      datasets: [
        {
          label: 'Your Soil',
          data: values,
          backgroundColor: 'rgba(22, 163, 74, 0.2)',
          borderColor: CHART_COLORS.primary,
          borderWidth: 2.5,
          pointBackgroundColor: CHART_COLORS.primary,
          pointBorderColor: '#fff',
          pointBorderWidth: 1,
          pointRadius: 5,
          pointHoverRadius: 8,
        },
        {
          label: 'Ideal Range',
          data: idealValues,
          backgroundColor: 'rgba(245, 158, 11, 0.08)',
          borderColor: CHART_COLORS.accent,
          borderWidth: 1.5,
          borderDash: [6, 4],
          pointBackgroundColor: CHART_COLORS.accent,
          pointRadius: 3,
          pointHoverRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            padding: 20,
            usePointStyle: true,
            pointStyleWidth: 12,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          titleFont: { family: 'Inter', weight: '700' },
          bodyFont: { family: 'Inter' },
          callbacks: {
            label: (context) => {
              const rawVals = [soilData.N, soilData.P, soilData.K, soilData.ph, soilData.moisture_pct || soilData.soil_moisture, soilData.organic_carbon || soilData.oc];
              const units = ['kg/ha', 'kg/ha', 'kg/ha', '', '%', 'dg/kg'];
              const idx = context.dataIndex;
              return `${context.dataset.label}: ${rawVals[idx] || 0} ${units[idx]} (${context.raw.toFixed(0)}% of max)`;
            }
          }
        }
      },
      scales: {
        r: {
          beginAtZero: true,
          max: 100,
          ticks: {
            stepSize: 20,
            color: CHART_COLORS.textMuted,
            font: { size: 10 },
            backdropColor: 'transparent',
          },
          grid: {
            color: 'rgba(34, 197, 94, 0.1)',
            lineWidth: 1,
          },
          angleLines: {
            color: 'rgba(34, 197, 94, 0.08)',
          },
          pointLabels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '600' },
          }
        }
      },
      animation: {
        duration: 1200,
        easing: 'easeOutQuart',
      }
    }
  });
}

// ============================================================
// 2. CROP SUITABILITY HORIZONTAL BAR CHART
// ============================================================
export function createCropSuitabilityChart(canvasId, crops) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const labels = crops.map(c => c.crop.charAt(0).toUpperCase() + c.crop.slice(1));
  const scores = crops.map(c => c.suitability_score);

  const barColors = scores.map((s, i) => {
    if (i === 0) return CHART_COLORS.primary;
    if (s >= 75) return 'rgba(22, 163, 74, 0.7)';
    if (s >= 50) return 'rgba(245, 158, 11, 0.7)';
    return 'rgba(239, 68, 68, 0.5)';
  });

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: 'Suitability Score',
        data: scores,
        backgroundColor: barColors,
        borderColor: barColors.map(c => c.replace(/[\d.]+\)$/, '1)')),
        borderWidth: 1.5,
        borderRadius: 8,
        borderSkipped: false,
        barPercentage: 0.7,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => `Suitability: ${ctx.raw}%`
          }
        },
        datalabels: {
          anchor: 'end',
          align: 'end',
          color: CHART_COLORS.text,
          font: { family: 'Inter', size: 12, weight: '700' },
          formatter: (value) => `${value}%`,
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          max: 100,
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 11 },
            callback: v => v + '%',
          },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { color: 'rgba(34, 197, 94, 0.12)' },
        },
        y: {
          ticks: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '600' },
          },
          grid: { display: false },
          border: { display: false },
        }
      },
      animation: {
        duration: 1000,
        easing: 'easeOutCubic',
      }
    },
    plugins: [ChartDataLabels],
  });
}

// ============================================================
// 3. PROFIT COMPARISON CHART (Bar + Line combo)
// ============================================================
export function createProfitChart(canvasId, crops) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const labels = crops.map(c => c.crop.charAt(0).toUpperCase() + c.crop.slice(1));
  const profits = crops.map(c => c.net_profit_estimated || 0);
  const costs = crops.map(c => {
    // Estimate cost from price_per_kg and yield
    const yieldKg = c.yield_per_acre || c.avg_yield_kg_per_acre || 2000;
    const revenue = (c.price_per_kg || 20) * yieldKg;
    return revenue - (c.net_profit_estimated || 0);
  });
  const revenues = crops.map((c, i) => profits[i] + costs[i]);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Revenue (₹)',
          data: revenues,
          backgroundColor: 'rgba(59, 130, 246, 0.6)',
          borderColor: CHART_COLORS.info,
          borderWidth: 1.5,
          borderRadius: 6,
          order: 2,
        },
        {
          label: 'Cost (₹)',
          data: costs,
          backgroundColor: 'rgba(239, 68, 68, 0.4)',
          borderColor: CHART_COLORS.danger,
          borderWidth: 1.5,
          borderRadius: 6,
          order: 3,
        },
        {
          label: 'Net Profit (₹)',
          data: profits,
          type: 'line',
          borderColor: CHART_COLORS.primary,
          backgroundColor: 'rgba(22, 163, 74, 0.1)',
          borderWidth: 3,
          pointBackgroundColor: CHART_COLORS.primary,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 9,
          fill: true,
          tension: 0.3,
          order: 1,
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            padding: 16,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 14,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ₹${ctx.raw.toLocaleString()}`
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '600' },
          },
          grid: { display: false },
          border: { color: CHART_COLORS.border },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 11 },
            callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v),
          },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        }
      },
      animation: { duration: 1200, easing: 'easeOutQuart' },
    }
  });
}

// ============================================================
// 4. FERTILIZER NPK DONUT CHART
// ============================================================
export function createNPKDonutChart(canvasId, fertData) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  // Parse NPK ratio like "20:20:0" or use individual values
  let nVal = 0, pVal = 0, kVal = 0;
  if (fertData.details?.npk) {
    const parts = fertData.details.npk.split(':').map(Number);
    nVal = parts[0] || 0;
    pVal = parts[1] || 0;
    kVal = parts[2] || 0;
  } else {
    nVal = fertData.n_pct || 30;
    pVal = fertData.p_pct || 20;
    kVal = fertData.k_pct || 10;
  }

  const total = nVal + pVal + kVal || 1;
  
  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: ['Nitrogen (N)', 'Phosphorus (P)', 'Potassium (K)'],
      datasets: [{
        data: [nVal, pVal, kVal],
        backgroundColor: [
          'rgba(22, 163, 74, 0.85)',
          'rgba(59, 130, 246, 0.85)',
          'rgba(245, 158, 11, 0.85)',
        ],
        borderColor: [
          CHART_COLORS.primary,
          CHART_COLORS.info,
          CHART_COLORS.accent,
        ],
        borderWidth: 2,
        hoverOffset: 12,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '62%',
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            padding: 16,
            usePointStyle: true,
            generateLabels: (chart) => {
              const data = chart.data;
              return data.labels.map((label, i) => ({
                text: `${label}: ${data.datasets[0].data[i]}`,
                fillStyle: data.datasets[0].backgroundColor[i],
                strokeStyle: data.datasets[0].borderColor[i],
                lineWidth: 2,
                pointStyle: 'circle',
                index: i,
              }));
            }
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              const pct = ((ctx.raw / total) * 100).toFixed(1);
              return `${ctx.label}: ${ctx.raw} (${pct}%)`;
            }
          }
        }
      },
      animation: {
        animateRotate: true,
        duration: 1500,
        easing: 'easeOutQuart',
      }
    },
    plugins: [{
      // Center text plugin
      id: 'centerText',
      afterDraw(chart) {
        const { ctx, width, height } = chart;
        ctx.save();
        const centerX = width / 2;
        const centerY = height / 2 - 10;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        ctx.fillStyle = CHART_COLORS.text;
        ctx.font = '800 20px "Outfit", sans-serif';
        ctx.fillText(`${nVal}:${pVal}:${kVal}`, centerX, centerY);
        
        ctx.fillStyle = CHART_COLORS.textMuted;
        ctx.font = '500 11px "Inter", sans-serif';
        ctx.fillText('NPK Ratio', centerX, centerY + 22);
        ctx.restore();
      }
    }]
  });
}

// ============================================================
// 5. CROP DURATION & WATER NEED BUBBLE CHART
// ============================================================
export function createCropBubbleChart(canvasId, crops) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const waterMap = { Low: 20, 'Low-Medium': 30, Medium: 45, 'Medium-High': 60, High: 75 };

  const data = crops.map((c, i) => ({
    x: c.duration_days || 90,
    y: c.suitability_score || 50,
    r: Math.max(8, (c.net_profit_estimated || 10000) / 3000),
    label: c.crop,
  }));

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bubble',
    data: {
      datasets: crops.map((c, i) => ({
        label: c.crop.charAt(0).toUpperCase() + c.crop.slice(1),
        data: [{
          x: c.duration_days || 90,
          y: c.suitability_score || 50,
          r: Math.min(25, Math.max(8, (c.net_profit_estimated || 10000) / 3000)),
        }],
        backgroundColor: PALETTE[i % PALETTE.length] + '66',
        borderColor: PALETTE[i % PALETTE.length],
        borderWidth: 2,
      }))
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '500' },
            padding: 12,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            title: (items) => items[0]?.dataset.label || '',
            label: (ctx) => [
              `Duration: ${ctx.raw.x} days`,
              `Suitability: ${ctx.raw.y}%`,
              `Bubble = Profit potential`,
            ]
          }
        }
      },
      scales: {
        x: {
          title: {
            display: true,
            text: 'Crop Duration (days)',
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '600' },
          },
          ticks: { color: CHART_COLORS.textMuted, font: { size: 11 } },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { color: CHART_COLORS.border },
        },
        y: {
          title: {
            display: true,
            text: 'Suitability Score (%)',
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '600' },
          },
          beginAtZero: true,
          max: 100,
          ticks: { color: CHART_COLORS.textMuted, font: { size: 11 } },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        }
      },
      animation: { duration: 1400, easing: 'easeOutQuart' },
    }
  });
}

// ============================================================
// 6. WEATHER CONDITIONS GAUGE (Polar Area)
// ============================================================
export function createWeatherGaugeChart(canvasId, weather) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'polarArea',
    data: {
      labels: ['Temperature °C', 'Humidity %', 'Wind Speed m/s', 'Cloud Cover %'],
      datasets: [{
        data: [
          weather.temperature || 0,
          weather.humidity || 0,
          (weather.wind_speed || 0) * 5, // Scale up for visibility
          weather.clouds || 50,
        ],
        backgroundColor: [
          'rgba(239, 68, 68, 0.6)',
          'rgba(59, 130, 246, 0.6)',
          'rgba(22, 163, 74, 0.6)',
          'rgba(107, 114, 128, 0.6)',
        ],
        borderColor: [
          CHART_COLORS.danger,
          CHART_COLORS.info,
          CHART_COLORS.primary,
          CHART_COLORS.textMuted,
        ],
        borderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '500' },
            padding: 14,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              const actual = [
                weather.temperature || 0,
                weather.humidity || 0,
                weather.wind_speed || 0,
                weather.clouds || 0,
              ];
              const units = ['°C', '%', 'm/s', '%'];
              return `${ctx.label}: ${actual[ctx.dataIndex]}${units[ctx.dataIndex]}`;
            }
          }
        }
      },
      scales: {
        r: {
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 10 },
            backdropColor: 'transparent',
          },
          grid: { color: 'rgba(34, 197, 94, 0.08)' },
        }
      },
      animation: { duration: 1200, easing: 'easeOutQuart' },
    }
  });
}

// ============================================================
// 7. FERTILIZER STAGE APPLICATION CHART
// ============================================================
export function createFertilizerStageChart(canvasId, stages) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const labels = stages.map(s => s.stage);
  
  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Nitrogen %',
          data: stages.map(s => s.n_pct),
          backgroundColor: 'rgba(22, 163, 74, 0.7)',
          borderColor: CHART_COLORS.primary,
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: 'Phosphorus %',
          data: stages.map(s => s.p_pct),
          backgroundColor: 'rgba(59, 130, 246, 0.7)',
          borderColor: CHART_COLORS.info,
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: 'Potassium %',
          data: stages.map(s => s.k_pct),
          backgroundColor: 'rgba(245, 158, 11, 0.7)',
          borderColor: CHART_COLORS.accent,
          borderWidth: 1,
          borderRadius: 4,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            padding: 14,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
        }
      },
      scales: {
        x: {
          ticks: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '600' },
          },
          grid: { display: false },
          border: { color: CHART_COLORS.border },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 11 },
            callback: v => v + '%',
          },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        }
      },
      animation: { duration: 1000, easing: 'easeOutCubic' },
    }
  });
}


// ============================================================
// 8. MARKET PRICE COMPARISON BAR CHART
// ============================================================
export function createMarketPriceChart(canvasId, markets, cropName) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  // Take top 15 markets sorted by modal price
  const topMarkets = markets
    .filter(m => m.price_per_kg > 0)
    .sort((a, b) => b.price_per_kg - a.price_per_kg)
    .slice(0, 15);

  const labels = topMarkets.map(m => m.name || m.market);
  const prices = topMarkets.map(m => parseFloat(m.price_per_kg));
  const avgPrice = prices.reduce((a, b) => a + b, 0) / prices.length;

  const barColors = prices.map(p => {
    if (p >= avgPrice * 1.15) return 'rgba(22, 163, 74, 0.75)';
    if (p >= avgPrice * 0.85) return 'rgba(59, 130, 246, 0.65)';
    return 'rgba(239, 68, 68, 0.55)';
  });

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: `${cropName} Price (₹/kg)`,
          data: prices,
          backgroundColor: barColors,
          borderColor: barColors.map(c => c.replace(/[\d.]+\)$/, '1)')),
          borderWidth: 1.5,
          borderRadius: 6,
          barPercentage: 0.75,
        },
        {
          label: 'Avg Price',
          data: new Array(labels.length).fill(avgPrice),
          type: 'line',
          borderColor: CHART_COLORS.accent,
          borderWidth: 2,
          borderDash: [8, 4],
          pointRadius: 0,
          fill: false,
          order: 0,
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            padding: 14,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => {
              if (ctx.dataset.label === 'Avg Price') return `Average: ₹${avgPrice.toFixed(2)}/kg`;
              return `Price: ₹${ctx.raw}/kg`;
            }
          }
        },
        datalabels: {
          anchor: 'end',
          align: 'end',
          color: CHART_COLORS.text,
          font: { family: 'Inter', size: 10, weight: '700' },
          formatter: (value, ctx) => {
            if (ctx.dataset.label === 'Avg Price') return '';
            return `₹${value}`;
          },
        }
      },
      scales: {
        x: {
          beginAtZero: true,
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 11 },
            callback: v => '₹' + v,
          },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { color: CHART_COLORS.border },
        },
        y: {
          ticks: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '500' },
          },
          grid: { display: false },
          border: { display: false },
        }
      },
      animation: { duration: 1200, easing: 'easeOutCubic' },
    },
    plugins: [ChartDataLabels],
  });
}

// ============================================================
// 9. MARKET PRICE DISTRIBUTION (Min/Modal/Max)
// ============================================================
export function createPriceDistributionChart(canvasId, markets, cropName) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  // Group by district
  const districtMap = {};
  markets.forEach(m => {
    const dist = m.district || 'Other';
    if (!districtMap[dist]) districtMap[dist] = { min: [], max: [], modal: [] };
    districtMap[dist].min.push(parseFloat(m.min_price_per_quintal || m.price_per_quintal));
    districtMap[dist].max.push(parseFloat(m.max_price_per_quintal || m.price_per_quintal));
    districtMap[dist].modal.push(parseFloat(m.price_per_quintal));
  });

  const districts = Object.keys(districtMap).slice(0, 12);
  const minPrices = districts.map(d => {
    const vals = districtMap[d].min;
    return Math.min(...vals);
  });
  const maxPrices = districts.map(d => {
    const vals = districtMap[d].max;
    return Math.max(...vals);
  });
  const modalPrices = districts.map(d => {
    const vals = districtMap[d].modal;
    return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
  });

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: districts,
      datasets: [
        {
          label: 'Min Price (₹/Qtl)',
          data: minPrices,
          backgroundColor: 'rgba(239, 68, 68, 0.5)',
          borderColor: CHART_COLORS.danger,
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: 'Modal Price (₹/Qtl)',
          data: modalPrices,
          backgroundColor: 'rgba(22, 163, 74, 0.6)',
          borderColor: CHART_COLORS.primary,
          borderWidth: 1,
          borderRadius: 4,
        },
        {
          label: 'Max Price (₹/Qtl)',
          data: maxPrices,
          backgroundColor: 'rgba(59, 130, 246, 0.5)',
          borderColor: CHART_COLORS.info,
          borderWidth: 1,
          borderRadius: 4,
        },
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index' },
      plugins: {
        legend: {
          position: 'bottom',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '500' },
            padding: 14,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => `${ctx.dataset.label}: ₹${ctx.raw.toLocaleString()}`
          }
        }
      },
      scales: {
        x: {
          ticks: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '500' },
            maxRotation: 45,
          },
          grid: { display: false },
          border: { color: CHART_COLORS.border },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 11 },
            callback: v => '₹' + (v >= 1000 ? (v / 1000).toFixed(0) + 'K' : v),
          },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        }
      },
      animation: { duration: 1100, easing: 'easeOutQuart' },
    }
  });
}

// ============================================================
// 10. MARKET PRICE PIE (District share of markets)
// ============================================================
export function createMarketSharePieChart(canvasId, markets) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const districtCounts = {};
  markets.forEach(m => {
    const d = m.district || 'Other';
    districtCounts[d] = (districtCounts[d] || 0) + 1;
  });

  const sortedDistricts = Object.entries(districtCounts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: sortedDistricts.map(([d]) => d),
      datasets: [{
        data: sortedDistricts.map(([, c]) => c),
        backgroundColor: PALETTE.slice(0, sortedDistricts.length).map(c => c + 'AA'),
        borderColor: PALETTE.slice(0, sortedDistricts.length),
        borderWidth: 2,
        hoverOffset: 10,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      cutout: '55%',
      plugins: {
        legend: {
          position: 'right',
          labels: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 11, weight: '500' },
            padding: 10,
            usePointStyle: true,
          }
        },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.raw} mandis`
          }
        }
      },
      animation: { animateRotate: true, duration: 1400, easing: 'easeOutQuart' },
    },
    plugins: [{
      id: 'centerText',
      afterDraw(chart) {
        const { ctx, width, height } = chart;
        ctx.save();
        const centerX = width / 2 - 40;
        const centerY = height / 2;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillStyle = CHART_COLORS.text;
        ctx.font = '800 22px "Outfit", sans-serif';
        ctx.fillText(markets.length, centerX, centerY - 8);
        ctx.fillStyle = CHART_COLORS.textMuted;
        ctx.font = '500 10px "Inter", sans-serif';
        ctx.fillText('Total Mandis', centerX, centerY + 12);
        ctx.restore();
      }
    }]
  });
}

// ============================================================
// 11. MSP COMPARISON LINE CHART
// ============================================================
export function createMSPComparisonChart(canvasId, avgPrice, mspPrice, cropName) {
  const ctx = getCtx(canvasId);
  if (!ctx) return;
  destroyChart(canvasId);

  const diff = avgPrice - mspPrice;
  const pct = ((diff / mspPrice) * 100).toFixed(1);

  chartInstances[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['MSP (Govt.)', 'Market Avg', 'Difference'],
      datasets: [{
        label: `${cropName} (₹/Qtl)`,
        data: [mspPrice, avgPrice, Math.abs(diff)],
        backgroundColor: [
          'rgba(245, 158, 11, 0.7)',
          'rgba(22, 163, 74, 0.7)',
          diff >= 0 ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)',
        ],
        borderColor: [
          CHART_COLORS.accent,
          CHART_COLORS.primary,
          diff >= 0 ? CHART_COLORS.success : CHART_COLORS.danger,
        ],
        borderWidth: 2,
        borderRadius: 8,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(17, 24, 20, 0.95)',
          titleColor: CHART_COLORS.text,
          bodyColor: CHART_COLORS.text,
          borderColor: CHART_COLORS.border,
          borderWidth: 1,
          padding: 12,
          callbacks: {
            label: (ctx) => `₹${ctx.raw.toLocaleString()}/quintal`
          }
        },
        datalabels: {
          anchor: 'end',
          align: 'end',
          color: CHART_COLORS.text,
          font: { family: 'Inter', size: 13, weight: '700' },
          formatter: (value) => `₹${value.toLocaleString()}`,
        }
      },
      scales: {
        x: {
          ticks: {
            color: CHART_COLORS.text,
            font: { family: 'Inter', size: 12, weight: '600' },
          },
          grid: { display: false },
          border: { color: CHART_COLORS.border },
        },
        y: {
          beginAtZero: true,
          ticks: {
            color: CHART_COLORS.textMuted,
            font: { size: 11 },
            callback: v => '₹' + v,
          },
          grid: { color: 'rgba(34, 197, 94, 0.06)' },
          border: { display: false },
        }
      },
      animation: { duration: 1000, easing: 'easeOutCubic' },
    },
    plugins: [ChartDataLabels],
  });
}
