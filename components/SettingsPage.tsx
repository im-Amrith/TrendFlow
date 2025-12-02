import React, { useState, useEffect } from 'react';
import { Save, Shield, Globe, Bell, Moon, Smartphone, Key, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '../services/api';

export const SettingsPage: React.FC = () => {
  const [apiKeyDevTo, setApiKeyDevTo] = useState('');
  const [apiKeyHashnode, setApiKeyHashnode] = useState('');
  const [hashnodePubId, setHashnodePubId] = useState('');
  
  const [devtoConfigured, setDevtoConfigured] = useState(false);
  const [hashnodeConfigured, setHashnodeConfigured] = useState(false);
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{type: 'success' | 'error', text: string} | null>(null);

  const [notifications, setNotifications] = useState(true);
  const [autoPublish, setAutoPublish] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const settings = await api.getSettings();
      setDevtoConfigured(settings.devto_configured);
      setHashnodeConfigured(settings.hashnode_configured);
      
      // Pre-fill if available (or leave empty if masked/not returned)
      if (settings.devto_api_key) setApiKeyDevTo(settings.devto_api_key);
      if (settings.hashnode_token) setApiKeyHashnode(settings.hashnode_token);
      if (settings.hashnode_pub_id) setHashnodePubId(settings.hashnode_pub_id);
      
    } catch (err) {
      console.error("Failed to load settings", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveDevTo = async () => {
    try {
      setSaving(true);
      await api.updateSettings({ devto_api_key: apiKeyDevTo });
      setDevtoConfigured(true);
      setMessage({ type: 'success', text: 'Dev.to settings saved!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save Dev.to settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleSaveHashnode = async () => {
    try {
      setSaving(true);
      await api.updateSettings({ 
        hashnode_token: apiKeyHashnode,
        hashnode_pub_id: hashnodePubId
      });
      setHashnodeConfigured(true);
      setMessage({ type: 'success', text: 'Hashnode settings saved!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save Hashnode settings' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <div className="flex justify-center p-20"><Loader2 className="animate-spin text-purple-500" size={40} /></div>;
  }

  return (
    <div className="animate-fade-in pb-20 max-w-4xl mx-auto">
      
      <div className="mb-10">
        <h1 className="text-4xl font-extrabold text-white mb-2 tracking-tight">Settings</h1>
        <p className="text-gray-400 text-lg">Manage your API keys, preferences, and system configuration.</p>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-xl flex items-center gap-3 ${message.type === 'success' ? 'bg-green-500/10 text-green-400 border border-green-500/20' : 'bg-red-500/10 text-red-400 border border-red-500/20'}`}>
          {message.type === 'success' ? <CheckCircle size={20} /> : <AlertCircle size={20} />}
          {message.text}
        </div>
      )}

      <div className="space-y-8">
        
        {/* API Configuration Section */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-3xl overflow-hidden">
            <div className="p-6 border-b border-gray-800 flex items-center gap-3">
                <div className="p-2 bg-purple-500/10 rounded-lg text-purple-400">
                    <Key size={20} />
                </div>
                <h2 className="text-xl font-bold text-white">Platform Connections</h2>
            </div>
            
            <div className="p-8 space-y-6">
                <div className="grid gap-6">
                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 flex items-center justify-between">
                            <span className="flex items-center gap-2"><img src="https://dev.to/favicon.ico" className="w-4 h-4 rounded" /> Dev.to API Key</span>
                            {devtoConfigured ? (
                                <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle size={12} /> Connected</span>
                            ) : (
                                <span className="text-xs text-gray-500 flex items-center gap-1"><AlertCircle size={12} /> Not Configured</span>
                            )}
                        </label>
                        <div className="flex gap-3">
                            <input 
                                type="password" 
                                value={apiKeyDevTo}
                                onChange={(e) => setApiKeyDevTo(e.target.value)}
                                placeholder={devtoConfigured ? "••••••••••••••••" : "Enter API Key"}
                                className="flex-1 bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
                            />
                            <button 
                                onClick={handleSaveDevTo}
                                disabled={saving}
                                className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                            >
                                {saving ? <Loader2 className="animate-spin" size={18} /> : 'Update'}
                            </button>
                        </div>
                        <p className="text-xs text-gray-500">Used for publishing articles and fetching analytics.</p>
                    </div>

                    <div className="h-px bg-gray-800/50"></div>

                    <div className="space-y-2">
                        <label className="text-sm font-medium text-gray-300 flex items-center justify-between">
                            <span className="flex items-center gap-2"><img src="https://hashnode.com/favicon.ico" className="w-4 h-4 rounded" /> Hashnode Configuration</span>
                            {hashnodeConfigured ? (
                                <span className="text-xs text-green-400 flex items-center gap-1"><CheckCircle size={12} /> Connected</span>
                            ) : (
                                <span className="text-xs text-gray-500 flex items-center gap-1"><AlertCircle size={12} /> Not Configured</span>
                            )}
                        </label>
                        <div className="grid gap-3">
                            <div className="flex gap-3">
                                <input 
                                    type="password" 
                                    value={apiKeyHashnode}
                                    onChange={(e) => setApiKeyHashnode(e.target.value)}
                                    placeholder={hashnodeConfigured ? "Access Token (••••••••)" : "Enter Access Token"}
                                    className="flex-1 bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
                                />
                            </div>
                            <div className="flex gap-3">
                                <input 
                                    type="text" 
                                    value={hashnodePubId}
                                    onChange={(e) => setHashnodePubId(e.target.value)}
                                    placeholder={hashnodeConfigured ? "Publication ID (••••••••)" : "Enter Publication ID"}
                                    className="flex-1 bg-black/50 border border-gray-700 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent outline-none transition-all"
                                />
                                <button 
                                    onClick={handleSaveHashnode}
                                    disabled={saving}
                                    className="px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-xl font-medium transition-colors disabled:opacity-50"
                                >
                                    {saving ? <Loader2 className="animate-spin" size={18} /> : 'Update'}
                                </button>
                            </div>
                        </div>
                        <p className="text-xs text-gray-500">Required for GraphQL API access and publishing.</p>
                    </div>
                </div>
            </div>
        </div>

        {/* Preferences Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-3xl overflow-hidden">
                <div className="p-6 border-b border-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-blue-500/10 rounded-lg text-blue-400">
                        <Globe size={20} />
                    </div>
                    <h2 className="text-xl font-bold text-white">Publishing Defaults</h2>
                </div>
                <div className="p-6 space-y-4">
                    <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors cursor-pointer" onClick={() => setAutoPublish(!autoPublish)}>
                        <div>
                            <h3 className="text-white font-medium">Auto-Publish</h3>
                            <p className="text-sm text-gray-500">Automatically publish approved drafts</p>
                        </div>
                        <div className={`w-12 h-6 rounded-full p-1 transition-colors ${autoPublish ? 'bg-purple-600' : 'bg-gray-700'}`}>
                            <div className={`w-4 h-4 bg-white rounded-full shadow-sm transform transition-transform ${autoPublish ? 'translate-x-6' : 'translate-x-0'}`}></div>
                        </div>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors">
                        <div>
                            <h3 className="text-white font-medium">Default Category</h3>
                            <p className="text-sm text-gray-500">Primary tag for new posts</p>
                        </div>
                        <select className="bg-black/50 border border-gray-700 text-white text-sm rounded-lg p-2 outline-none">
                            <option>Technology</option>
                            <option>Finance</option>
                            <option>Lifestyle</option>
                        </select>
                    </div>
                </div>
            </div>

            <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-3xl overflow-hidden">
                <div className="p-6 border-b border-gray-800 flex items-center gap-3">
                    <div className="p-2 bg-pink-500/10 rounded-lg text-pink-400">
                        <Bell size={20} />
                    </div>
                    <h2 className="text-xl font-bold text-white">Notifications</h2>
                </div>
                <div className="p-6 space-y-4">
                    <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors cursor-pointer" onClick={() => setNotifications(!notifications)}>
                        <div>
                            <h3 className="text-white font-medium">Email Alerts</h3>
                            <p className="text-sm text-gray-500">Get notified when drafts are ready</p>
                        </div>
                        <div className={`w-12 h-6 rounded-full p-1 transition-colors ${notifications ? 'bg-purple-600' : 'bg-gray-700'}`}>
                            <div className={`w-4 h-4 bg-white rounded-full shadow-sm transform transition-transform ${notifications ? 'translate-x-6' : 'translate-x-0'}`}></div>
                        </div>
                    </div>
                    <div className="flex items-center justify-between p-3 rounded-xl hover:bg-white/5 transition-colors">
                        <div>
                            <h3 className="text-white font-medium">Digest Frequency</h3>
                            <p className="text-sm text-gray-500">How often to receive summaries</p>
                        </div>
                        <select className="bg-black/50 border border-gray-700 text-white text-sm rounded-lg p-2 outline-none">
                            <option>Daily</option>
                            <option>Weekly</option>
                            <option>Never</option>
                        </select>
                    </div>
                </div>
            </div>
        </div>

        {/* System Info */}
        <div className="bg-gray-900/50 backdrop-blur-sm border border-gray-800 rounded-3xl p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <div className="p-3 bg-green-500/10 rounded-full text-green-400">
                    <Shield size={24} />
                </div>
                <div>
                    <h3 className="text-white font-bold">System Status</h3>
                    <p className="text-green-400 text-sm flex items-center gap-1">
                        <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                        All systems operational
                    </p>
                </div>
            </div>
            <div className="text-right">
                <p className="text-gray-500 text-xs uppercase tracking-wider font-semibold">Version</p>
                <p className="text-white font-mono">v2.4.0-beta</p>
            </div>
        </div>

        <div className="flex justify-end pt-4">
            <button className="flex items-center gap-2 px-8 py-4 bg-white text-black rounded-full font-bold hover:bg-gray-200 transition-colors shadow-lg shadow-white/10">
                <Save size={20} />
                Save Changes
            </button>
        </div>

      </div>
    </div>
  );
};
