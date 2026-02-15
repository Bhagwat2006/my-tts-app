import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, BarChart3, Users, CreditCard, ShieldCheck, Settings, 
  LogOut, Play, Upload, CheckCircle2, AlertCircle, Menu, 
  X, Zap, History, Volume2, Command, MessageSquare, Save
} from 'lucide-react';
import { 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, BarChart, Bar 
} from 'recharts';

// --- Configuration & Constants ---
const CONFIG = {
  freeDailyLimit: 5,
  maxAudioChars: 5000,
  upiId: "8452095418@ybl"
};

const INITIAL_USERS = [
  { id: '1', username: 'admin', role: 'admin', plan: 'Enterprise', usage: 145 },
  { id: '2', username: 'guest', role: 'user', plan: 'Basic', usage: 12 }
];

const ANALYTICS_DATA = [
  { date: '2023-10-01', count: 45 },
  { date: '2023-10-02', count: 52 },
  { date: '2023-10-03', count: 38 },
  { date: '2023-10-04', count: 65 },
  { date: '2023-10-05', count: 48 },
  { date: '2023-10-06', count: 70 },
  { date: '2023-10-07', count: 55 },
];

export default function App() {
  // Authentication State
  const [user, setUser] = useState(null);
  const [authMode, setAuthMode] = useState('login');
  const [formData, setFormData] = useState({ username: '', password: '' });
  const [error, setError] = useState('');

  // Navigation State
  const [page, setPage] = useState('studio');
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Studio & Voice State
  const [script, setScript] = useState('');
  const [engine, setEngine] = useState('eleven');
  const [isProcessing, setIsProcessing] = useState(false);
  const [history, setHistory] = useState([]);
  
  // Voice-to-Voice / Command State
  const [isListening, setIsListening] = useState(false);
  const [voiceCommand, setVoiceCommand] = useState('');

  // --- Auth Handlers ---
  const handleAuth = (e) => {
    e.preventDefault();
    const found = INITIAL_USERS.find(u => u.username === formData.username);
    if (found) {
      setUser(found);
      setError('');
    } else {
      setError('Invalid credentials for this preview.');
    }
  };

  // --- Voice-to-Voice Command Loader ---
  const toggleListening = () => {
    if (!isListening) {
      setIsListening(true);
      // Simulate Voice-to-Text Command Loader
      setTimeout(() => {
        const mockCommands = ["Generate a welcome message", "Switch to admin dashboard", "Start voice cloning"];
        const randomCmd = mockCommands[Math.floor(Math.random() * mockCommands.length)];
        setVoiceCommand(randomCmd);
        setIsListening(false);
        if (randomCmd.includes("Generate")) setScript("Welcome to the Global AI Voice Studio Enterprise Edition.");
      }, 2000);
    }
  };

  // --- Production Rendering Pipeline ---
  const handleGenerate = () => {
    if (!script.trim()) return;
    setIsProcessing(true);
    
    setTimeout(() => {
      const newEntry = {
        id: Date.now(),
        text: script.slice(0, 40) + "...",
        engine: engine.toUpperCase(),
        time: new Date().toLocaleTimeString(),
      };
      setHistory([newEntry, ...history]);
      setIsProcessing(false);
    }, 1500);
  };

  if (!user) {
    return (
      <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
        <div className="w-full max-w-md bg-[#0f0f0f] border border-white/10 rounded-2xl p-8 shadow-2xl">
          <div className="text-center mb-8">
            <div className="bg-indigo-600 w-12 h-12 rounded-xl flex items-center justify-center mx-auto mb-4">
              <Mic className="text-white" />
            </div>
            <h1 className="text-2xl font-bold text-white">Voice Studio AI</h1>
            <p className="text-gray-500 text-sm">Enterprise Management Suite</p>
          </div>
          
          <form onSubmit={handleAuth} className="space-y-4">
            <input 
              type="text" placeholder="Username" required
              className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-white focus:border-indigo-500 outline-none"
              onChange={e => setFormData({...formData, username: e.target.value})}
            />
            <input 
              type="password" placeholder="Password" required
              className="w-full bg-black border border-white/10 rounded-lg px-4 py-3 text-white focus:border-indigo-500 outline-none"
              onChange={e => setFormData({...formData, password: e.target.value})}
            />
            {error && <p className="text-red-500 text-xs">{error}</p>}
            <button className="w-full bg-indigo-600 hover:bg-indigo-500 text-white font-bold py-3 rounded-lg transition-all">
              Login to Studio
            </button>
          </form>
          <p className="text-center text-gray-600 text-xs mt-6">Use 'admin' or 'guest' to preview</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-gray-200 flex">
      {/* Sidebar Navigation */}
      <aside className={`fixed lg:static inset-y-0 left-0 z-50 w-64 bg-[#0a0a0a] border-r border-white/5 transition-transform ${isSidebarOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="p-6 flex items-center gap-3 border-b border-white/5">
          <Zap className="text-indigo-500" fill="currentColor" size={20}/>
          <span className="font-bold tracking-tight">VOICE STUDIO</span>
        </div>
        <nav className="p-4 space-y-2">
          <NavItem active={page==='studio'} icon={<Mic size={18}/>} label="Studio" onClick={()=>setPage('studio')} />
          <NavItem active={page==='analytics'} icon={<BarChart3 size={18}/>} label="Analytics" onClick={()=>setPage('analytics')} />
          <NavItem active={page==='clone'} icon={<Volume2 size={18}/>} label="Voice Cloning" onClick={()=>setPage('clone')} />
          <NavItem active={page==='billing'} icon={<CreditCard size={18}/>} label="Billing" onClick={()=>setPage('billing')} />
          {user.role === 'admin' && (
            <NavItem active={page==='admin'} icon={<ShieldCheck size={18}/>} label="Admin" onClick={()=>setPage('admin')} />
          )}
        </nav>
        <div className="absolute bottom-0 w-full p-4 border-t border-white/5">
          <button onClick={() => setUser(null)} className="flex items-center gap-3 w-full p-2 text-gray-500 hover:text-white transition-colors">
            <LogOut size={18}/> <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Panel */}
      <main className="flex-1 flex flex-col h-screen overflow-hidden">
        <header className="h-16 border-b border-white/5 bg-[#0a0a0a]/50 backdrop-blur-xl px-6 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button className="lg:hidden" onClick={()=>setIsSidebarOpen(!isSidebarOpen)}><Menu/></button>
            <h2 className="text-sm font-semibold uppercase tracking-widest text-gray-400">{page}</h2>
          </div>
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-xs font-bold">{user.username}</p>
              <p className="text-[10px] text-indigo-400">{user.plan} Plan</p>
            </div>
            <div className="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center font-bold text-xs">
              {user.username[0].toUpperCase()}
            </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-6 lg:p-10">
          <div className="max-w-5xl mx-auto">
            {page === 'studio' && (
              <div className="grid lg:grid-cols-3 gap-8">
                <div className="lg:col-span-2 space-y-6">
                  {/* Voice Command Section */}
                  <div className="bg-[#0f0f0f] border border-white/10 rounded-2xl p-6">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="flex items-center gap-2 font-bold"><Command size={18}/> Voice Command</h3>
                      <button 
                        onClick={toggleListening}
                        className={`p-3 rounded-full transition-all ${isListening ? 'bg-red-500 animate-pulse' : 'bg-indigo-600 hover:bg-indigo-500'}`}
                      >
                        <Mic size={20} className="text-white"/>
                      </button>
                    </div>
                    <div className="bg-black/40 rounded-lg p-3 text-sm border border-white/5 min-h-[40px]">
                      {isListening ? "Listening..." : voiceCommand || "Click mic to speak command..."}
                    </div>
                  </div>

                  {/* Text to Speech Section */}
                  <div className="bg-[#0f0f0f] border border-white/10 rounded-2xl p-6 shadow-xl">
                    <div className="flex gap-4 mb-6">
                      <select 
                        className="flex-1 bg-black border border-white/10 rounded-lg px-4 py-2 text-sm outline-none"
                        value={engine} onChange={e => setEngine(e.target.value)}
                      >
                        <option value="eleven">ElevenLabs HD</option>
                        <option value="edge">Edge Neural</option>
                        <option value="gtts">Google Lite</option>
                      </select>
                      <input className="flex-1 bg-black border border-white/10 rounded-lg px-4 py-2 text-sm" placeholder="Voice ID: MadhurNeural"/>
                    </div>
                    <textarea 
                      className="w-full bg-black border border-white/10 rounded-xl p-5 h-64 outline-none focus:border-indigo-500 transition-colors resize-none"
                      placeholder="Enter production script..."
                      value={script}
                      onChange={e => setScript(e.target.value)}
                    />
                    <button 
                      onClick={handleGenerate}
                      disabled={isProcessing}
                      className="w-full bg-indigo-600 hover:bg-indigo-500 py-4 rounded-xl mt-6 font-bold flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isProcessing ? <div className="animate-spin rounded-full h-5 w-5 border-2 border-white/20 border-t-white" /> : <><Play size={18}/> Generate Audio</>}
                    </button>
                  </div>
                </div>

                {/* History Sidebar */}
                <div className="bg-[#0f0f0f] border border-white/10 rounded-2xl p-6 h-fit">
                  <h3 className="font-bold mb-4 flex items-center gap-2"><History size={18}/> History</h3>
                  <div className="space-y-4">
                    {history.length === 0 && <p className="text-gray-600 text-sm italic">No recent jobs</p>}
                    {history.map(item => (
                      <div key={item.id} className="p-3 bg-black/50 border border-white/5 rounded-lg group">
                        <div className="flex justify-between text-[10px] text-indigo-400 font-bold mb-1 uppercase tracking-tighter">
                          <span>{item.engine}</span>
                          <span>{item.time}</span>
                        </div>
                        <p className="text-xs text-gray-400 truncate">{item.text}</p>
                        <button className="mt-2 text-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity"><Volume2 size={14}/></button>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {page === 'analytics' && (
              <div className="space-y-8 animate-in fade-in duration-500">
                <div className="grid sm:grid-cols-3 gap-6">
                  <div className="bg-[#0f0f0f] border border-white/10 p-6 rounded-2xl">
                    <p className="text-xs text-gray-500 font-bold uppercase mb-2">Total Output</p>
                    <p className="text-3xl font-bold">12,402</p>
                  </div>
                  <div className="bg-[#0f0f0f] border border-white/10 p-6 rounded-2xl">
                    <p className="text-xs text-gray-500 font-bold uppercase mb-2">Characters</p>
                    <p className="text-3xl font-bold">2.4M</p>
                  </div>
                  <div className="bg-[#0f0f0f] border border-white/10 p-6 rounded-2xl">
                    <p className="text-xs text-gray-500 font-bold uppercase mb-2">Avg. Clarity</p>
                    <p className="text-3xl font-bold">98.2%</p>
                  </div>
                </div>
                <div className="bg-[#0f0f0f] border border-white/10 p-8 rounded-2xl h-80">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={ANALYTICS_DATA}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#222" />
                      <XAxis dataKey="date" stroke="#555" fontSize={10}/>
                      <YAxis stroke="#555" fontSize={10}/>
                      <Tooltip contentStyle={{backgroundColor: '#000', border: '1px solid #333'}}/>
                      <Line type="monotone" dataKey="count" stroke="#6366f1" strokeWidth={3} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>
            )}

            {page === 'clone' && (
              <div className="max-w-xl mx-auto text-center space-y-6">
                <div className="w-20 h-20 bg-indigo-500/10 rounded-full flex items-center justify-center mx-auto">
                  <Volume2 size={40} className="text-indigo-500"/>
                </div>
                <h2 className="text-2xl font-bold">Neural Voice Cloning</h2>
                <p className="text-gray-400 text-sm">Upload a 1-minute sample of clear audio to create a digital twin.</p>
                <div className="border-2 border-dashed border-white/10 rounded-2xl p-12 hover:border-indigo-500/50 transition-colors cursor-pointer bg-[#0f0f0f]">
                  <Upload className="mx-auto mb-4 text-gray-600" size={32}/>
                  <p className="text-xs text-gray-500">Drop audio files (WAV, MP3) here</p>
                </div>
                <button className="w-full bg-indigo-600 py-3 rounded-xl font-bold">Initialize Clone Engine</button>
              </div>
            )}

            {page === 'billing' && (
              <div className="grid md:grid-cols-2 gap-8">
                <div className="bg-[#0f0f0f] border-2 border-indigo-600 p-8 rounded-2xl relative overflow-hidden">
                  <div className="absolute top-0 right-0 bg-indigo-600 text-white text-[10px] font-bold px-3 py-1 rounded-bl-lg uppercase">Best Value</div>
                  <h3 className="text-xl font-bold mb-2">Enterprise Plan</h3>
                  <p className="text-4xl font-bold mb-6">$49<span className="text-sm text-gray-500 font-normal">/mo</span></p>
                  <ul className="space-y-3 mb-8 text-sm text-gray-400">
                    <li className="flex items-center gap-2"><CheckCircle2 size={16} className="text-indigo-500"/> Unlimited Characters</li>
                    <li className="flex items-center gap-2"><CheckCircle2 size={16} className="text-indigo-500"/> Custom Neural Cloning</li>
                    <li className="flex items-center gap-2"><CheckCircle2 size={16} className="text-indigo-500"/> API Access & Webhooks</li>
                  </ul>
                  <button className="w-full bg-indigo-600 py-3 rounded-xl font-bold">Get Started</button>
                </div>
                <div className="bg-[#0f0f0f] border border-white/10 p-8 rounded-2xl flex flex-col items-center justify-center">
                  <div className="bg-white p-2 rounded-lg mb-4">
                    <img src={`https://api.qrserver.com/v1/create-qr-code/?data=upi://pay?pa=${CONFIG.upiId}&am=10.00`} alt="QR" className="w-32 h-32"/>
                  </div>
                  <p className="font-bold mb-1">Direct UPI Upgrade</p>
                  <p className="text-xs text-gray-500 mb-6 text-center">Scan to upgrade via secure payment gateway.</p>
                  <button className="w-full bg-white/5 py-3 rounded-xl font-bold text-sm">Verify Transaction</button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function NavItem({ active, icon, label, onClick }) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${active ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-600/20' : 'text-gray-500 hover:text-gray-200 hover:bg-white/5'}`}
    >
      {icon}
      <span className="text-sm font-medium">{label}</span>
    </button>
  );
}
