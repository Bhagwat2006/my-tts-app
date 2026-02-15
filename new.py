import React, { useState, useEffect, useMemo } from 'react';
import { 
  Mic, 
  BarChart3, 
  Users, 
  CreditCard, 
  ShieldCheck, 
  Settings, 
  LogOut, 
  Play, 
  Upload, 
  CheckCircle2, 
  AlertCircle,
  Menu,
  X,
  Plus,
  Zap,
  History
} from 'lucide-react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  BarChart, 
  Bar 
} from 'recharts';

// --- Mock Data & Config ---
const CONFIG = {
  freeDailyLimit: 5,
  maxAudioChars: 5000,
  upiId: "8452095418@ybl"
};

const INITIAL_USERS = [
  { id: '1', username: 'admin', role: 'admin', plan: 'Enterprise', usage: 145 },
  { id: '2', username: 'guest_user', role: 'user', plan: 'Basic', usage: 12 }
];

const INITIAL_GENS = [
  { id: 'g1', date: '2023-10-01', count: 45 },
  { id: 'g2', date: '2023-10-02', count: 52 },
  { id: 'g3', date: '2023-10-03', count: 38 },
  { id: 'g4', date: '2023-10-04', count: 65 },
  { id: 'g5', date: '2023-10-05', count: 48 },
  { id: 'g6', date: '2023-10-06', count: 70 },
  { id: 'g7', date: '2023-10-07', count: 55 },
];

export default function App() {
  const [user, setUser] = useState(null);
  const [page, setPage] = useState('studio');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [users, setUsers] = useState(INITIAL_USERS);
  const [generations, setGenerations] = useState(INITIAL_GENS);
  
  // Login State
  const [authMode, setAuthMode] = useState('login');
  const [formData, setFormData] = useState({ username: '', password: '', email: '' });
  const [error, setError] = useState('');

  // Studio State
  const [script, setScript] = useState('');
  const [engine, setEngine] = useState('edge');
  const [voiceId, setVoiceId] = useState('hi-IN-MadhurNeural');
  const [isRendering, setIsRendering] = useState(false);
  const [history, setHistory] = useState([]);

  // --- Auth Logic ---
  const handleLogin = (e) => {
    e.preventDefault();
    const found = users.find(u => u.username === formData.username);
    if (found) {
      setUser(found);
      setError('');
    } else {
      setError('Invalid credentials or user not found');
    }
  };

  const handleRegister = (e) => {
    e.preventDefault();
    const newUser = {
      id: Math.random().toString(36).substr(2, 9),
      username: formData.username,
      role: 'user',
      plan: 'Basic',
      usage: 0
    };
    setUsers([...users, newUser]);
    setUser(newUser);
  };

  const logout = () => {
    setUser(null);
    setPage('studio');
  };

  // --- Render Logic ---
  const handleRender = () => {
    if (!script.trim()) return;
    setIsRendering(true);
    
    // Simulate API Pipeline
    setTimeout(() => {
      const newGen = {
        id: Date.now(),
        text: script.substring(0, 30) + '...',
        engine,
        voice: voiceId,
        timestamp: new Date().toLocaleTimeString()
      };
      setHistory([newGen, ...history]);
      setIsRendering(false);
      
      // Update usage
      setUsers(prev => prev.map(u => u.id === user.id ? {...u, usage: u.usage + 1} : u));
    }, 2000);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
          <div className="flex flex-col items-center mb-8">
            <div className="bg-indigo-600 p-3 rounded-xl mb-4">
              <Mic className="text-white w-8 h-8" />
            </div>
            <h1 className="text-2xl font-bold text-white">Voice Studio AI</h1>
            <p className="text-slate-400 text-sm">Enterprise Edition v3.0</p>
          </div>

          <div className="flex gap-2 mb-6 bg-slate-800 p-1 rounded-lg">
            <button 
              onClick={() => setAuthMode('login')}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${authMode === 'login' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Login
            </button>
            <button 
              onClick={() => setAuthMode('register')}
              className={`flex-1 py-2 rounded-md text-sm font-medium transition-all ${authMode === 'register' ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-400 hover:text-slate-200'}`}
            >
              Register
            </button>
          </div>

          <form onSubmit={authMode === 'login' ? handleLogin : handleRegister} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Username</label>
              <input 
                type="text" 
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={formData.username}
                onChange={(e) => setFormData({...formData, username: e.target.value})}
              />
            </div>
            {authMode === 'register' && (
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Email</label>
                <input 
                  type="email" 
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                />
              </div>
            )}
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase mb-1">Password</label>
              <input 
                type="password" 
                required
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-4 py-2 text-white focus:outline-none focus:ring-2 focus:ring-indigo-500"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
              />
            </div>
            
            {error && <p className="text-red-400 text-sm flex items-center gap-1"><AlertCircle size={14}/> {error}</p>}

            <button className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-lg transition-colors shadow-lg shadow-indigo-500/20 mt-4">
              {authMode === 'login' ? 'Enter Studio' : 'Create Enterprise Account'}
            </button>
          </form>
          
          <div className="mt-6 text-center">
            <button className="text-slate-500 text-xs hover:text-indigo-400 transition-colors">Forgot Password?</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex">
      {/* Sidebar */}
      <aside className={`fixed inset-y-0 left-0 z-50 w-64 bg-slate-900 border-r border-slate-800 transition-transform lg:translate-x-0 lg:static ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="h-full flex flex-col">
          <div className="p-6 border-b border-slate-800 flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Mic className="text-white w-5 h-5" />
            </div>
            <span className="font-bold text-lg tracking-tight">Voice Studio</span>
          </div>
          
          <nav className="flex-1 p-4 space-y-1">
            <SidebarLink active={page === 'studio'} icon={<Mic size={18}/>} label="Studio" onClick={() => setPage('studio')} />
            <SidebarLink active={page === 'analytics'} icon={<BarChart3 size={18}/>} label="Analytics" onClick={() => setPage('analytics')} />
            <SidebarLink active={page === 'clone'} icon={<Zap size={18}/>} label="Voice Cloning" onClick={() => setPage('clone')} />
            <SidebarLink active={page === 'billing'} icon={<CreditCard size={18}/>} label="Billing" onClick={() => setPage('billing')} />
            {user.role === 'admin' && (
              <SidebarLink active={page === 'admin'} icon={<ShieldCheck size={18}/>} label="Admin Control" onClick={() => setPage('admin')} />
            )}
          </nav>

          <div className="p-4 border-t border-slate-800">
            <div className="flex items-center gap-3 mb-4 px-2">
              <div className="w-10 h-10 rounded-full bg-indigo-500/20 border border-indigo-500/50 flex items-center justify-center text-indigo-400 font-bold">
                {user.username.charAt(0).toUpperCase()}
              </div>
              <div className="overflow-hidden">
                <p className="text-sm font-bold truncate">{user.username}</p>
                <p className="text-xs text-slate-500 truncate">{user.plan} Plan</p>
              </div>
            </div>
            <button 
              onClick={logout}
              className="w-full flex items-center gap-3 px-3 py-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-all"
            >
              <LogOut size={18} />
              <span className="text-sm">Sign Out</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-slate-900/50 backdrop-blur-md border-b border-slate-800 px-6 flex items-center justify-between">
          <button className="lg:hidden p-2 text-slate-400" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            {isSidebarOpen ? <X /> : <Menu />}
          </button>
          <div className="flex items-center gap-2">
            <span className="text-slate-500">/</span>
            <span className="text-sm font-medium capitalize">{page}</span>
          </div>
          <div className="flex items-center gap-4">
             <div className="hidden md:flex flex-col items-end">
                <span className="text-xs text-slate-500">Credits Used</span>
                <span className="text-sm font-bold text-indigo-400">{user.usage} / ∞</span>
             </div>
             <div className="w-px h-6 bg-slate-800 mx-2"></div>
             <Settings className="text-slate-400 cursor-pointer hover:text-white transition-colors" size={20} />
          </div>
        </header>

        {/* Scrollable Area */}
        <div className="flex-1 overflow-y-auto p-6 bg-slate-950/50">
          <div className="max-w-6xl mx-auto space-y-8">
            {page === 'studio' && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Editor Section */}
                <div className="lg:col-span-2 space-y-6">
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                    <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                      <Play className="text-indigo-500" size={20}/>
                      Audio Production
                    </h2>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <div className="space-y-2">
                        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Synthesis Engine</label>
                        <select 
                          value={engine}
                          onChange={(e) => setEngine(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                        >
                          <option value="edge">Microsoft Edge (Standard)</option>
                          <option value="eleven">ElevenLabs (Neural High-Def)</option>
                          <option value="gtts">Google TTS (Fastest)</option>
                        </select>
                      </div>
                      <div className="space-y-2">
                        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Voice Profile</label>
                        <input 
                          type="text"
                          value={voiceId}
                          onChange={(e) => setVoiceId(e.target.value)}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl px-4 py-3 text-sm focus:ring-2 focus:ring-indigo-500 outline-none"
                          placeholder="Voice ID (e.g. MadhurNeural)"
                        />
                      </div>
                    </div>

                    <div className="space-y-2 mb-6">
                      <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider flex justify-between">
                        Script Output
                        <span className={script.length > CONFIG.maxAudioChars ? 'text-red-400' : 'text-slate-400'}>
                          {script.length} / {CONFIG.maxAudioChars} chars
                        </span>
                      </label>
                      <textarea 
                        rows={10}
                        value={script}
                        onChange={(e) => setScript(e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-5 py-4 text-sm focus:ring-2 focus:ring-indigo-500 outline-none resize-none leading-relaxed"
                        placeholder="Type or paste your script here..."
                      />
                    </div>

                    <button 
                      onClick={handleRender}
                      disabled={isRendering || script.length === 0}
                      className={`w-full py-4 rounded-xl font-bold flex items-center justify-center gap-2 transition-all shadow-lg ${
                        isRendering ? 'bg-indigo-600/50 cursor-not-allowed' : 'bg-indigo-600 hover:bg-indigo-500 shadow-indigo-500/20 active:scale-[0.98]'
                      }`}
                    >
                      {isRendering ? (
                        <>
                          <div className="animate-spin h-5 w-5 border-2 border-white/20 border-t-white rounded-full"></div>
                          Rendering Neural Audio...
                        </>
                      ) : (
                        <>
                          <Zap size={20}/>
                          Render Production Audio
                        </>
                      )}
                    </button>
                  </div>
                </div>

                {/* Sidebar Info Section */}
                <div className="space-y-6">
                  <div className="bg-indigo-600/10 border border-indigo-500/20 rounded-2xl p-6 relative overflow-hidden">
                    <div className="relative z-10">
                      <h3 className="text-indigo-400 font-bold mb-2 flex items-center gap-2">
                         <CreditCard size={18}/>
                         Enterprise Quota
                      </h3>
                      <p className="text-slate-400 text-sm mb-4">You are using a persistent server session. All generations are saved to history.</p>
                      <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                        <div className="bg-indigo-500 h-full transition-all duration-1000" style={{width: `${(user.usage / 200) * 100}%`}}></div>
                      </div>
                      <p className="text-[10px] text-slate-500 mt-2 uppercase tracking-tighter">Usage Reset in 14 Days</p>
                    </div>
                  </div>

                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                    <h3 className="text-white font-bold mb-4 flex items-center gap-2">
                      <History size={18} className="text-slate-500"/>
                      Recent Jobs
                    </h3>
                    <div className="space-y-4 max-h-[400px] overflow-y-auto pr-2 custom-scrollbar">
                      {history.length === 0 ? (
                        <div className="text-center py-8">
                          <p className="text-slate-600 text-sm italic">No recent activity</p>
                        </div>
                      ) : (
                        history.map(item => (
                          <div key={item.id} className="group p-3 bg-slate-950/50 border border-slate-800 rounded-xl hover:border-indigo-500/50 transition-colors">
                            <div className="flex justify-between items-start mb-2">
                              <span className="text-[10px] font-bold text-indigo-400 uppercase">{item.engine}</span>
                              <span className="text-[10px] text-slate-500">{item.timestamp}</span>
                            </div>
                            <p className="text-xs text-slate-300 truncate mb-2">{item.text}</p>
                            <div className="flex items-center gap-2">
                              <button className="text-indigo-400 hover:text-indigo-300">
                                <Play size={14} fill="currentColor"/>
                              </button>
                              <div className="h-1 flex-1 bg-slate-800 rounded-full"></div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {page === 'analytics' && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <StatCard label="Total Generations" value="1,284" sub="+12% from last week" />
                  <StatCard label="Characters Processed" value="4.2M" sub="Average 3k per job" />
                  <StatCard label="Active Licenses" value="14" sub="Managed by your team" />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                    <h3 className="text-lg font-bold mb-6 text-slate-300">Generation Volume (30D)</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={generations}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="date" stroke="#64748b" fontSize={12} />
                          <YAxis stroke="#64748b" fontSize={12} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                          />
                          <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={3} dot={{ fill: '#6366f1' }} />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
                    <h3 className="text-lg font-bold mb-6 text-slate-300">Usage by Engine</h3>
                    <div className="h-64">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={[
                          { name: 'Edge', value: 450 },
                          { name: 'Eleven', value: 380 },
                          { name: 'gTTS', value: 120 },
                        ]}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                          <XAxis dataKey="name" stroke="#64748b" fontSize={12} />
                          <YAxis stroke="#64748b" fontSize={12} />
                          <Tooltip 
                            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid #1e293b', borderRadius: '8px' }}
                          />
                          <Bar dataKey="value" fill="#6366f1" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {page === 'clone' && (
              <div className="max-w-2xl mx-auto space-y-8 animate-in zoom-in-95 duration-300">
                <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center">
                  <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Zap className="text-indigo-500 w-10 h-10" />
                  </div>
                  <h2 className="text-2xl font-bold mb-2">Neural Voice Cloning Lab</h2>
                  <p className="text-slate-400 mb-8 leading-relaxed">Create a high-fidelity digital replica of any voice with just 60 seconds of clean audio samples.</p>
                  
                  <div className="border-2 border-dashed border-slate-800 rounded-2xl p-12 mb-8 hover:border-indigo-500/50 hover:bg-slate-950/50 transition-all group cursor-pointer">
                    <Upload className="mx-auto text-slate-600 group-hover:text-indigo-500 mb-4 transition-colors" size={40}/>
                    <p className="text-sm font-medium text-slate-400">Drag and drop audio files or <span className="text-indigo-500">browse</span></p>
                    <p className="text-xs text-slate-600 mt-2">WAV, MP3 or AAC (Max 10MB)</p>
                  </div>

                  <button className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-4 rounded-xl transition-all shadow-lg shadow-indigo-500/20">
                    Start Neural Training
                  </button>
                  
                  <div className="mt-8 grid grid-cols-2 gap-4 text-left">
                    <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                      <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Target Accuracy</h4>
                      <p className="text-xl font-bold text-indigo-400">98.2%</p>
                    </div>
                    <div className="p-4 bg-slate-950 rounded-xl border border-slate-800">
                      <h4 className="text-xs font-bold text-slate-500 uppercase mb-2">Est. Training Time</h4>
                      <p className="text-xl font-bold text-indigo-400">4m 12s</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {page === 'billing' && (
              <div className="max-w-4xl mx-auto space-y-8">
                <div className="text-center mb-12">
                  <h2 className="text-3xl font-bold mb-4">Enterprise Subscription</h2>
                  <p className="text-slate-400">Choose the scale that fits your production needs.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                  <PricingCard 
                    title="Enterprise Tier" 
                    price="$49" 
                    features={["Unlimited Generations", "11Labs Ultra Engine", "Team Shared Workspaces", "API Keys (5)", "Priority Rendering Queue"]}
                    highlighted={true}
                    onUpgrade={() => {}}
                  />
                  <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 flex flex-col items-center justify-center text-center">
                    <div className="bg-slate-950 p-6 rounded-2xl mb-6">
                       <img 
                        src={`https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa=${CONFIG.upiId}&am=10.00`} 
                        alt="UPI Payment"
                        className="w-48 h-48 rounded-lg"
                       />
                    </div>
                    <h3 className="text-xl font-bold mb-2">Direct UPI Upgrade</h3>
                    <p className="text-sm text-slate-400 mb-6 px-8">Scan to activate Premium instantly via merchant portal.</p>
                    <button className="w-full bg-slate-800 hover:bg-slate-700 text-white py-3 rounded-xl font-bold transition-all">
                      Confirm Transaction ID
                    </button>
                  </div>
                </div>
              </div>
            )}

            {page === 'admin' && (
              <div className="space-y-8 animate-in slide-in-from-right-4">
                 <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden">
                    <div className="px-6 py-4 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                      <h3 className="font-bold flex items-center gap-2">
                        <Users size={18} className="text-indigo-500"/>
                        System User Management
                      </h3>
                      <button className="text-xs bg-indigo-600 hover:bg-indigo-500 px-3 py-1 rounded-md font-medium text-white transition-all">
                        Export CSV
                      </button>
                    </div>
                    <div className="overflow-x-auto">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-slate-950 text-slate-500 border-b border-slate-800">
                          <tr>
                            <th className="px-6 py-4 font-semibold">User</th>
                            <th className="px-6 py-4 font-semibold">Role</th>
                            <th className="px-6 py-4 font-semibold">Plan</th>
                            <th className="px-6 py-4 font-semibold">Usage</th>
                            <th className="px-6 py-4 font-semibold text-right">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800">
                          {users.map(u => (
                            <tr key={u.id} className="hover:bg-slate-800/30 transition-colors group">
                              <td className="px-6 py-4">
                                <div className="flex items-center gap-3">
                                  <div className="w-8 h-8 rounded-full bg-indigo-500/10 flex items-center justify-center text-indigo-400 font-bold text-xs">
                                    {u.username.charAt(0).toUpperCase()}
                                  </div>
                                  <span className="font-medium">{u.username}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4">
                                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${u.role === 'admin' ? 'bg-amber-500/10 text-amber-500' : 'bg-slate-500/10 text-slate-400'}`}>
                                  {u.role}
                                </span>
                              </td>
                              <td className="px-6 py-4 text-slate-400">{u.plan}</td>
                              <td className="px-6 py-4 font-mono text-indigo-400">{u.usage.toLocaleString()}</td>
                              <td className="px-6 py-4 text-right">
                                <button className="text-slate-500 hover:text-white transition-colors p-2 rounded-lg hover:bg-slate-800">
                                  <Settings size={14}/>
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                 </div>

                 <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                      <h3 className="font-bold mb-4 flex items-center gap-2">
                        <ShieldCheck size={18} className="text-emerald-500"/>
                        Security Audit Log
                      </h3>
                      <div className="space-y-3">
                         <AuditItem action="User Login" detail="admin authenticated" time="2m ago" />
                         <AuditItem action="API Access" detail="eleven-labs key ping" time="15m ago" />
                         <AuditItem action="Billing" detail="payment webhook success" time="1h ago" />
                         <AuditItem action="Security" detail="password change request" time="3h ago" />
                      </div>
                    </div>
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
                      <h3 className="font-bold mb-4 flex items-center gap-2">
                        <Settings size={18} className="text-slate-500"/>
                        System Feature Flags
                      </h3>
                      <div className="space-y-4">
                         <FlagToggle label="Neural Voice V2" enabled={true} />
                         <FlagToggle label="Batch Rendering" enabled={true} />
                         <FlagToggle label="Experimental Japanese Engine" enabled={false} />
                         <FlagToggle label="Multi-speaker Pipelines" enabled={false} />
                      </div>
                    </div>
                 </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

// --- Helper Components ---

function SidebarLink({ active, icon, label, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
        active 
          ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' 
          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
      }`}
    >
      {icon}
      <span>{label}</span>
    </button>
  );
}

function StatCard({ label, value, sub }) {
  return (
    <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl shadow-xl">
      <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">{label}</p>
      <div className="flex items-baseline gap-2">
        <p className="text-3xl font-bold text-white">{value}</p>
        <span className="text-[10px] font-medium text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">
          {sub.split(' ')[0]}
        </span>
      </div>
      <p className="text-[10px] text-slate-600 mt-2">{sub.split(' ').slice(1).join(' ')}</p>
    </div>
  );
}

function AuditItem({ action, detail, time }) {
  return (
    <div className="flex justify-between items-center text-xs p-2 rounded-lg bg-slate-950/50 border border-slate-800/50">
      <div>
        <span className="text-slate-200 font-bold mr-2">{action}</span>
        <span className="text-slate-500">{detail}</span>
      </div>
      <span className="text-[10px] text-slate-600">{time}</span>
    </div>
  );
}

function FlagToggle({ label, enabled }) {
  return (
    <div className="flex items-center justify-between p-3 rounded-xl bg-slate-950/30">
      <span className="text-sm text-slate-300">{label}</span>
      <div className={`w-10 h-5 rounded-full relative transition-colors cursor-pointer ${enabled ? 'bg-indigo-600' : 'bg-slate-800'}`}>
        <div className={`absolute top-1 w-3 h-3 rounded-full bg-white transition-all ${enabled ? 'left-6' : 'left-1'}`}></div>
      </div>
    </div>
  );
}

function PricingCard({ title, price, features, highlighted, onUpgrade }) {
  return (
    <div className={`rounded-2xl p-8 border ${highlighted ? 'border-indigo-500 bg-slate-900 shadow-2xl shadow-indigo-500/10 ring-2 ring-indigo-500/20' : 'border-slate-800 bg-slate-900/50'}`}>
      <h3 className="text-lg font-bold mb-2">{title}</h3>
      <div className="flex items-baseline gap-1 mb-6">
        <span className="text-4xl font-bold text-white">{price}</span>
        <span className="text-slate-500 text-sm">/mo</span>
      </div>
      <ul className="space-y-4 mb-8">
        {features.map((f, i) => (
          <li key={i} className="flex items-center gap-3 text-sm text-slate-400">
            <CheckCircle2 size={16} className="text-emerald-500 shrink-0" />
            {f}
          </li>
        ))}
      </ul>
      <button 
        onClick={onUpgrade}
        className={`w-full py-4 rounded-xl font-bold transition-all ${highlighted ? 'bg-indigo-600 hover:bg-indigo-500 text-white' : 'bg-slate-800 hover:bg-slate-700 text-white'}`}
      >
        Choose Plan
      </button>
    </div>
  );
}
