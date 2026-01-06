import { useState, useEffect } from 'react';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { apiKeysApi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
  DialogFooter,
} from '../components/ui/dialog';
import { 
  Key, 
  Plus, 
  Copy, 
  Trash2,
  Eye,
  EyeOff,
  Clock,
  Shield
} from 'lucide-react';

export const ApiKeysPage = () => {
  const { user } = useAuth();
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState('');
  const [creating, setCreating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [visibleKeys, setVisibleKeys] = useState({});

  const fetchApiKeys = async () => {
    if (!user?.id) return;
    try {
      const data = await apiKeysApi.getAll(user.id);
      setApiKeys(data);
    } catch (error) {
      console.error('Error fetching API keys:', error);
      toast.error('Failed to load API keys');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApiKeys();
  }, [user]);

  const handleCreateKey = async () => {
    if (!newKeyName.trim()) {
      toast.error('Please enter a key name');
      return;
    }

    setCreating(true);
    try {
      const newKey = await apiKeysApi.create({ name: newKeyName, permissions: ['read', 'write'] }, user.id);
      setApiKeys(prev => [newKey, ...prev]);
      setNewKeyName('');
      setDialogOpen(false);
      toast.success('API key created successfully');
      
      // Show the new key by default
      setVisibleKeys(prev => ({ ...prev, [newKey.id]: true }));
    } catch (error) {
      toast.error('Failed to create API key');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteKey = async (keyId) => {
    if (!window.confirm('Are you sure you want to delete this API key? This action cannot be undone.')) return;
    
    try {
      await apiKeysApi.delete(keyId, user.id);
      setApiKeys(prev => prev.filter(k => k.id !== keyId));
      toast.success('API key deleted');
    } catch (error) {
      toast.error('Failed to delete API key');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard');
  };

  const toggleKeyVisibility = (keyId) => {
    setVisibleKeys(prev => ({ ...prev, [keyId]: !prev[keyId] }));
  };

  const maskKey = (key) => {
    return key.substring(0, 8) + '•'.repeat(32) + key.substring(key.length - 4);
  };

  return (
    <DashboardLayout title="API Keys" subtitle="Manage your API keys for SDK authentication">
      {/* Header Actions */}
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Shield className="w-4 h-4" />
          <span>Keep your API keys secure and never share them publicly</span>
        </div>
        
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-primary text-black font-bold hover:shadow-neon transition-all" data-testid="new-key-btn">
              <Plus className="w-4 h-4 mr-2" />
              New API Key
            </Button>
          </DialogTrigger>
          <DialogContent className="bg-background-paper border-white/10">
            <DialogHeader>
              <DialogTitle className="font-heading">Create API Key</DialogTitle>
              <DialogDescription>
                Create a new API key for authenticating your SDK requests
              </DialogDescription>
            </DialogHeader>
            <div className="py-4">
              <Label htmlFor="keyName">Key Name</Label>
              <Input
                id="keyName"
                placeholder="e.g., Production Key"
                value={newKeyName}
                onChange={(e) => setNewKeyName(e.target.value)}
                className="mt-2 bg-white/5 border-white/10 focus:border-primary"
                data-testid="key-name-input"
              />
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setDialogOpen(false)} className="border-white/20">
                Cancel
              </Button>
              <Button 
                onClick={handleCreateKey}
                disabled={creating || !newKeyName.trim()}
                className="bg-primary text-black font-bold"
                data-testid="create-key-btn"
              >
                {creating ? 'Creating...' : 'Create Key'}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      {/* API Keys List */}
      {loading ? (
        <div className="space-y-4">
          {[1, 2].map(i => (
            <Card key={i} className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="h-16 bg-white/5 rounded animate-pulse"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : apiKeys.length === 0 ? (
        <Card className="bg-background-paper border-white/10">
          <CardContent className="py-16 text-center">
            <Key className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
            <h3 className="font-heading font-bold text-xl mb-2">No API keys yet</h3>
            <p className="text-muted-foreground mb-6">
              Create an API key to authenticate your SDK requests
            </p>
            <Button 
              onClick={() => setDialogOpen(true)}
              className="bg-primary text-black font-bold"
            >
              <Plus className="w-4 h-4 mr-2" />
              Create Your First Key
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-4" data-testid="api-keys-list">
          {apiKeys.map((apiKey) => (
            <Card key={apiKey.id} className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center">
                      <Key className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                      <h3 className="font-heading font-bold text-lg">{apiKey.name}</h3>
                      <div className="flex items-center gap-2 mt-2">
                        <code className="px-3 py-1.5 rounded bg-background border border-white/10 font-mono text-sm">
                          {visibleKeys[apiKey.id] ? apiKey.key : maskKey(apiKey.key)}
                        </code>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => toggleKeyVisibility(apiKey.id)}
                          className="h-8 w-8"
                        >
                          {visibleKeys[apiKey.id] ? (
                            <EyeOff className="w-4 h-4" />
                          ) : (
                            <Eye className="w-4 h-4" />
                          )}
                        </Button>
                        <Button 
                          variant="ghost" 
                          size="icon"
                          onClick={() => copyToClipboard(apiKey.key)}
                          className="h-8 w-8"
                          data-testid={`copy-${apiKey.id}`}
                        >
                          <Copy className="w-4 h-4" />
                        </Button>
                      </div>
                      <div className="flex items-center gap-4 mt-3 text-sm text-muted-foreground">
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4" />
                          Created {new Date(apiKey.created_at).toLocaleDateString()}
                        </div>
                        <div className="flex gap-1">
                          {apiKey.permissions.map(p => (
                            <span key={p} className="px-2 py-0.5 rounded bg-secondary/20 text-secondary text-xs border border-secondary/30">
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <Button 
                    variant="ghost" 
                    size="icon"
                    onClick={() => handleDeleteKey(apiKey.id)}
                    className="text-muted-foreground hover:text-destructive hover:bg-destructive/10"
                    data-testid={`delete-${apiKey.id}`}
                  >
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Usage Info */}
      <Card className="bg-background-paper border-white/10 mt-8">
        <CardHeader>
          <CardTitle className="font-heading">Using Your API Key</CardTitle>
          <CardDescription>Include your API key in SDK initialization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
            <div><span className="text-muted-foreground">// Initialize NativiWeb SDK with your API key</span></div>
            <div><span className="text-secondary">const</span> config = {"{"}</div>
            <div className="pl-4"><span className="text-primary">apiKey</span>: <span className="text-success">"nw_your_api_key_here"</span>,</div>
            <div className="pl-4"><span className="text-primary">projectId</span>: <span className="text-success">"your_project_id"</span></div>
            <div>{"};"}</div>
          </div>
        </CardContent>
      </Card>
    </DashboardLayout>
  );
};

export default ApiKeysPage;
