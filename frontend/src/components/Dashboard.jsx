import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import ChatPanel from './ChatPanel'

export default function Dashboard({ token, onLogout }) {
  const [stats, setStats] = useState(null)
  const [empresas, setEmpresas] = useState([])
  const [selectedEmpresa, setSelectedEmpresa] = useState(null)
  const [resumen, setResumen] = useState(null)
  const [transacciones, setTransacciones] = useState([])
  const [tesoreria, setTesoreria] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('dashboard')
  const [chatOpen, setChatOpen] = useState(false)

  const headers = { 'Authorization': `Bearer ${token}` }

  useEffect(() => {
    loadInitialData()
  }, [])

  useEffect(() => {
    if (selectedEmpresa) {
      loadEmpresaData(selectedEmpresa)
    }
  }, [selectedEmpresa])

  const loadInitialData = async () => {
    try {
      const [statsRes, empresasRes] = await Promise.all([
        fetch('/api/v1/debug/stats', { headers }),
        fetch('/api/v1/empresas/', { headers }),
      ])
      
      setStats(await statsRes.json())
      const empresasData = await empresasRes.json()
      setEmpresas(empresasData)
      
      if (empresasData.length > 0) {
        setSelectedEmpresa(empresasData[0].id)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadEmpresaData = async (empresaId) => {
    try {
      const [resumenRes, txRes] = await Promise.all([
        fetch(`/api/v1/debug/transacciones/resumen?empresa_id=${empresaId}`, { headers }),
        fetch(`/api/v1/debug/transacciones?empresa_id=${empresaId}&limit=20`, { headers }),
      ])
      
      setResumen(await resumenRes.json())
      setTransacciones((await txRes.json()).data)
    } catch (err) {
      console.error(err)
    }
  }

  const runTesoreriaAnalysis = async () => {
    if (!selectedEmpresa) return
    setLoading(true)
    try {
      const res = await fetch('/api/v1/tesoreria/analisis', {
        method: 'POST',
        headers: { ...headers, 'Content-Type': 'application/json' },
        body: JSON.stringify({ empresa_id: selectedEmpresa, periodo_dias: 90 }),
      })
      setTesoreria(await res.json())
      setActiveTab('tesoreria')
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  if (loading && !stats) {
    return <div className="min-h-screen bg-gray-100 flex items-center justify-center">Cargando...</div>
  }

  const chartData = resumen?.por_mes 
    ? Object.entries(resumen.por_mes).map(([mes, data]) => ({
        mes: mes.slice(5),
        ingresos: Math.round(data.ingresos),
        gastos: Math.round(data.gastos),
      }))
    : []

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Main Content */}
      <div className={`flex-1 flex flex-col ${chatOpen ? 'mr-96' : ''} transition-all duration-300`}>
        {/* Header */}
        <header className="bg-white shadow">
          <div className="px-4 py-4 flex justify-between items-center">
            <h1 className="text-xl font-bold">🤖 Agente Financiero IA</h1>
            <div className="flex items-center gap-4">
              <select
                value={selectedEmpresa || ''}
                onChange={(e) => setSelectedEmpresa(e.target.value)}
                className="border rounded px-3 py-1"
              >
                {empresas.map(e => (
                  <option key={e.id} value={e.id}>{e.nombre}</option>
                ))}
              </select>
              <button 
                onClick={() => setChatOpen(!chatOpen)}
                className={`px-4 py-2 rounded-lg transition ${
                  chatOpen 
                    ? 'bg-blue-100 text-blue-700' 
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                💬 {chatOpen ? 'Cerrar Chat' : 'Abrir Chat IA'}
              </button>
              <button onClick={onLogout} className="text-gray-600 hover:text-gray-800">
                Salir
              </button>
            </div>
          </div>
        </header>

        {/* Tabs */}
        <div className="px-4 mt-4">
          <div className="flex gap-2">
            {['dashboard', 'transacciones', 'tesoreria'].map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-t ${activeTab === tab ? 'bg-white font-medium' : 'bg-gray-200'}`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <main className="flex-1 overflow-auto px-4 py-6">
          {activeTab === 'dashboard' && (
            <div className="space-y-6">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard title="Empresas" value={stats?.empresas || 0} icon="🏢" />
                <StatCard title="Transacciones" value={stats?.transacciones || 0} icon="💳" />
                <StatCard title="Reglas" value={stats?.reglas_clasificacion || 0} icon="📋" />
                <StatCard 
                  title="Balance" 
                  value={`€${resumen?.balance?.toLocaleString() || 0}`} 
                  icon="💰"
                  color={resumen?.balance >= 0 ? 'text-green-600' : 'text-red-600'}
                />
              </div>

              {/* Chart */}
              {chartData.length > 0 && (
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-lg font-medium mb-4">Ingresos vs Gastos por Mes</h2>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="mes" />
                      <YAxis />
                      <Tooltip formatter={(v) => `€${v.toLocaleString()}`} />
                      <Bar dataKey="ingresos" fill="#22c55e" name="Ingresos" />
                      <Bar dataKey="gastos" fill="#ef4444" name="Gastos" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}

              {/* Quick Actions */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h2 className="text-lg font-medium mb-4">Acciones Rápidas</h2>
                <div className="flex gap-4">
                  <button
                    onClick={runTesoreriaAnalysis}
                    disabled={loading}
                    className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    📊 Analizar Tesorería
                  </button>
                  <button
                    onClick={() => setChatOpen(true)}
                    className="bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700"
                  >
                    💬 Preguntar al Asistente
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'transacciones' && (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fecha</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Concepto</th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">Importe</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Tipo</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {transacciones.map(tx => (
                    <tr key={tx.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">{tx.fecha}</td>
                      <td className="px-6 py-4 text-sm">{tx.concepto?.slice(0, 50)}</td>
                      <td className={`px-6 py-4 whitespace-nowrap text-sm text-right font-medium ${tx.importe >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        €{tx.importe.toLocaleString()}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded ${tx.tipo === 'ingreso' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}`}>
                          {tx.tipo}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {activeTab === 'tesoreria' && tesoreria && (
            <div className="space-y-6">
              {/* Métricas */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <StatCard title="Saldo Total" value={`€${tesoreria.metricas?.saldo_total?.toLocaleString() || 0}`} icon="💰" />
                <StatCard title="Burn Rate/Mes" value={`€${tesoreria.metricas?.burn_rate_mensual?.toLocaleString() || 0}`} icon="🔥" />
                <StatCard title="Runway" value={`${tesoreria.metricas?.runway_meses || '∞'} meses`} icon="🛤️" />
                <StatCard title="Ratio I/G" value={tesoreria.metricas?.ratio_ingresos_gastos?.toFixed(2) || 'N/A'} icon="📈" />
              </div>

              {/* Alertas */}
              {tesoreria.alertas?.length > 0 && (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                  <h3 className="font-medium text-yellow-800 mb-2">⚠️ Alertas</h3>
                  <ul className="space-y-1">
                    {tesoreria.alertas.map((a, i) => (
                      <li key={i} className="text-yellow-700">{a}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Recomendaciones */}
              {tesoreria.recomendaciones?.length > 0 && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h3 className="font-medium text-blue-800 mb-2">💡 Recomendaciones</h3>
                  <ul className="space-y-1">
                    {tesoreria.recomendaciones.map((r, i) => (
                      <li key={i} className="text-blue-700">{r}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Proyección */}
              {tesoreria.proyeccion && (
                <div className="bg-white p-6 rounded-lg shadow">
                  <h2 className="text-lg font-medium mb-4">Proyección de Cash Flow</h2>
                  <div className="grid grid-cols-3 gap-4">
                    {Object.entries(tesoreria.proyeccion).map(([periodo, data]) => (
                      <div key={periodo} className="border rounded p-4">
                        <h3 className="font-medium mb-2">{periodo}</h3>
                        <div className="space-y-1 text-sm">
                          <div className="flex justify-between">
                            <span>Optimista:</span>
                            <span className="text-green-600">€{data.optimista?.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Base:</span>
                            <span>€{data.base?.toLocaleString()}</span>
                          </div>
                          <div className="flex justify-between">
                            <span>Pesimista:</span>
                            <span className="text-red-600">€{data.pesimista?.toLocaleString()}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </main>
      </div>

      {/* Chat Sidebar */}
      {chatOpen && (
        <div className="fixed right-0 top-0 h-full w-96 shadow-xl z-50">
          <ChatPanel 
            token={token} 
            empresaId={selectedEmpresa}
            onClose={() => setChatOpen(false)} 
          />
        </div>
      )}
    </div>
  )
}

function StatCard({ title, value, icon, color = '' }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-500">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
        </div>
        <span className="text-3xl">{icon}</span>
      </div>
    </div>
  )
}
