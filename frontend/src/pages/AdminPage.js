import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';
import { Switch } from '../components/ui/switch';
import { toast } from 'sonner';
import axios from 'axios';
import {
  Users,
  Package,
  FileText,
  Settings,
  BarChart3,
  Shield,
  Search,
  ChevronLeft,
  ChevronRight,
  Ban,
  CheckCircle2,
  XCircle,
  Clock,
  Loader2,
  TrendingUp,
  Smartphone,
  FolderKanban,
  AlertTriangle,
  Info,
  Zap,
  RefreshCw
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

export const AdminPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('analytics');
  const [loading, setLoading] = useState(true);
  
  // Analytics state
  const [analytics, setAnalytics] = useState(null);
  
  // Users state
  const [users, setUsers] = useState([]);
  const [usersPage, setUsersPage] = useState(1);
  const [usersTotalPages, setUsersTotalPages] = useState(1);
  const [usersSearch, setUsersSearch] = useState('');
  
  // Builds state
  const [builds, setBuilds] = useState([]);
  const [buildsPage, setBuildsPage] = useState(1);
  const [buildsTotalPages, setBuildsTotalPages] = useState(1);
  const [buildsFilter, setBuildsFilter] = useState('');
  
  // Logs state
  const [logs, setLogs] = useState([]);
  const [logsPage, setLogsPage] = useState(1);
  const [logsTotalPages, setLogsTotalPages] = useState(1);
  const [logsLevel, setLogsLevel] = useState('');
  const [logsCategory, setLogsCategory] = useState('');
  
  // Config state
  const [config, setConfig] = useState(null);

  useEffect(() => {
    if (user?.role !== 'admin') {
      toast.error('Admin access required');
      navigate('/dashboard');
      return;
    }
    fetchAnalytics();
  }, [user, navigate]);

  const fetchAnalytics = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/analytics?admin_id=${user.id}`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Error fetching analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async (page = 1) => {
    try {
      const response = await axios.get(`${API_URL}/admin/users?admin_id=${user.id}&page=${page}&limit=10`);
      setUsers(response.data.users);
      setUsersTotalPages(response.data.pages);
      setUsersPage(page);
    } catch (error) {
      console.error('Error fetching users:', error);
    }
  };

  const fetchBuilds = async (page = 1, status = '') => {
    try {
      let url = `${API_URL}/admin/builds?admin_id=${user.id}&page=${page}&limit=10`;
      if (status) url += `&status=${status}`;
      const response = await axios.get(url);
      setBuilds(response.data.builds);
      setBuildsTotalPages(response.data.pages);
      setBuildsPage(page);
    } catch (error) {
      console.error('Error fetching builds:', error);
    }
  };

  const fetchLogs = async (page = 1, level = '', category = '') => {
    try {
      let url = `${API_URL}/admin/logs?admin_id=${user.id}&page=${page}&limit=20`;
      if (level) url += `&level=${level}`;
      if (category) url += `&category=${category}`;
      const response = await axios.get(url);
      setLogs(response.data.logs);
      setLogsTotalPages(response.data.pages);
      setLogsPage(page);
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API_URL}/admin/config?admin_id=${user.id}`);
      setConfig(response.data);
    } catch (error) {
      console.error('Error fetching config:', error);
    }
  };

  const updateUserStatus = async (userId, status) => {
    try {
      await axios.put(`${API_URL}/admin/users/${userId}?admin_id=${user.id}`, { status });
      toast.success(`User ${status === 'banned' ? 'banned' : 'unbanned'} successfully`);
      fetchUsers(usersPage);
    } catch (error) {
      toast.error('Failed to update user');
    }
  };

  const updateConfig = async (updates) => {
    try {
      await axios.put(`${API_URL}/admin/config?admin_id=${user.id}`, updates);
      toast.success('Configuration updated');
      setConfig(prev => ({ ...prev, ...updates }));
    } catch (error) {
      toast.error('Failed to update configuration');
    }
  };

  const handleTabChange = (value) => {
    setActiveTab(value);
    if (value === 'users' && users.length === 0) fetchUsers();
    if (value === 'builds' && builds.length === 0) fetchBuilds();
    if (value === 'logs' && logs.length === 0) fetchLogs();
    if (value === 'config' && !config) fetchConfig();
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-success/20 text-success border-success/30',
      banned: 'bg-destructive/20 text-destructive border-destructive/30',
      completed: 'bg-success/20 text-success border-success/30',
      processing: 'bg-warning/20 text-warning border-warning/30',
      failed: 'bg-destructive/20 text-destructive border-destructive/30',
      pending: 'bg-muted text-muted-foreground border-muted',
    };
    return styles[status] || styles.pending;
  };

  const getLogIcon = (level) => {
    switch (level) {
      case 'error': return <XCircle className="w-4 h-4 text-destructive" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-warning" />;
      case 'success': return <CheckCircle2 className="w-4 h-4 text-success" />;
      default: return <Info className="w-4 h-4 text-info" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="glass border-b border-white/10 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/dashboard" className="flex items-center gap-2 text-muted-foreground hover:text-white">
              <ChevronLeft className="w-4 h-4" />
              Back
            </Link>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-md bg-destructive/20 border border-destructive/30 flex items-center justify-center">
                <Shield className="w-5 h-5 text-destructive" />
              </div>
              <div>
                <h1 className="font-heading font-bold text-lg">Admin Panel</h1>
                <p className="text-xs text-muted-foreground">NativiWeb Studio</p>
              </div>
            </div>
          </div>
          <Badge className="bg-destructive/20 text-destructive border-destructive/30">
            Admin Access
          </Badge>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="bg-background-paper border border-white/10 mb-8">
            <TabsTrigger value="analytics" className="data-[state=active]:bg-primary data-[state=active]:text-black">
              <BarChart3 className="w-4 h-4 mr-2" />
              Analytics
            </TabsTrigger>
            <TabsTrigger value="users" className="data-[state=active]:bg-primary data-[state=active]:text-black">
              <Users className="w-4 h-4 mr-2" />
              Users
            </TabsTrigger>
            <TabsTrigger value="builds" className="data-[state=active]:bg-primary data-[state=active]:text-black">
              <Package className="w-4 h-4 mr-2" />
              Builds
            </TabsTrigger>
            <TabsTrigger value="logs" className="data-[state=active]:bg-primary data-[state=active]:text-black">
              <FileText className="w-4 h-4 mr-2" />
              Logs
            </TabsTrigger>
            <TabsTrigger value="config" className="data-[state=active]:bg-primary data-[state=active]:text-black">
              <Settings className="w-4 h-4 mr-2" />
              Config
            </TabsTrigger>
          </TabsList>

          {/* Analytics Tab */}
          <TabsContent value="analytics" data-testid="admin-analytics">
            {analytics && (
              <div className="space-y-6">
                {/* Stats Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                  <Card className="bg-background-paper border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Total Users</p>
                          <p className="font-heading font-bold text-3xl">{analytics.users.total}</p>
                          <p className="text-xs text-success mt-1">+{analytics.users.new_this_week} this week</p>
                        </div>
                        <div className="w-12 h-12 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center">
                          <Users className="w-6 h-6 text-primary" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-background-paper border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Total Projects</p>
                          <p className="font-heading font-bold text-3xl">{analytics.projects.total}</p>
                          <p className="text-xs text-success mt-1">+{analytics.projects.new_this_week} this week</p>
                        </div>
                        <div className="w-12 h-12 rounded-md bg-secondary/10 border border-secondary/30 flex items-center justify-center">
                          <FolderKanban className="w-6 h-6 text-secondary" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-background-paper border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Total Builds</p>
                          <p className="font-heading font-bold text-3xl">{analytics.builds.total}</p>
                          <p className="text-xs text-success mt-1">{analytics.builds.success_rate}% success rate</p>
                        </div>
                        <div className="w-12 h-12 rounded-md bg-success/10 border border-success/30 flex items-center justify-center">
                          <Package className="w-6 h-6 text-success" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="bg-background-paper border-white/10">
                    <CardContent className="p-6">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-muted-foreground">Processing</p>
                          <p className="font-heading font-bold text-3xl">{analytics.builds.processing}</p>
                          <p className="text-xs text-muted-foreground mt-1">builds in progress</p>
                        </div>
                        <div className="w-12 h-12 rounded-md bg-warning/10 border border-warning/30 flex items-center justify-center">
                          <Loader2 className="w-6 h-6 text-warning animate-spin" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Charts Row */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Build Status */}
                  <Card className="bg-background-paper border-white/10">
                    <CardHeader>
                      <CardTitle className="font-heading">Build Status Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Successful</span>
                          <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-success rounded-full"
                                style={{ width: `${analytics.builds.total > 0 ? (analytics.builds.successful / analytics.builds.total * 100) : 0}%` }}
                              />
                            </div>
                            <span className="text-sm font-mono">{analytics.builds.successful}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Failed</span>
                          <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-destructive rounded-full"
                                style={{ width: `${analytics.builds.total > 0 ? (analytics.builds.failed / analytics.builds.total * 100) : 0}%` }}
                              />
                            </div>
                            <span className="text-sm font-mono">{analytics.builds.failed}</span>
                          </div>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-sm">Processing</span>
                          <div className="flex items-center gap-2">
                            <div className="w-32 h-2 bg-white/10 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-warning rounded-full"
                                style={{ width: `${analytics.builds.total > 0 ? (analytics.builds.processing / analytics.builds.total * 100) : 0}%` }}
                              />
                            </div>
                            <span className="text-sm font-mono">{analytics.builds.processing}</span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Platform Distribution */}
                  <Card className="bg-background-paper border-white/10">
                    <CardHeader>
                      <CardTitle className="font-heading">Platform Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="flex items-center justify-center gap-12 py-8">
                        <div className="text-center">
                          <div className="w-20 h-20 rounded-full bg-success/10 border-4 border-success flex items-center justify-center mb-3">
                            <Smartphone className="w-8 h-8 text-success" />
                          </div>
                          <p className="font-heading font-bold text-2xl">{analytics.platforms.android}</p>
                          <p className="text-sm text-muted-foreground">Android</p>
                        </div>
                        <div className="text-center">
                          <div className="w-20 h-20 rounded-full bg-info/10 border-4 border-info flex items-center justify-center mb-3">
                            <Smartphone className="w-8 h-8 text-info" />
                          </div>
                          <p className="font-heading font-bold text-2xl">{analytics.platforms.ios}</p>
                          <p className="text-sm text-muted-foreground">iOS</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
              </div>
            )}
          </TabsContent>

          {/* Users Tab */}
          <TabsContent value="users" data-testid="admin-users">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading">User Management</CardTitle>
                  <div className="relative w-64">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                    <Input
                      placeholder="Search users..."
                      value={usersSearch}
                      onChange={(e) => setUsersSearch(e.target.value)}
                      className="pl-10 bg-white/5 border-white/10"
                    />
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {users.filter(u => 
                    u.name.toLowerCase().includes(usersSearch.toLowerCase()) ||
                    u.email.toLowerCase().includes(usersSearch.toLowerCase())
                  ).map((u) => (
                    <div key={u.id} className="p-4 rounded-lg bg-white/5 border border-white/5 flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="w-10 h-10 rounded-full bg-secondary/20 border border-secondary/30 flex items-center justify-center">
                          <span className="font-bold text-secondary">{u.name.charAt(0).toUpperCase()}</span>
                        </div>
                        <div>
                          <p className="font-medium">{u.name}</p>
                          <p className="text-sm text-muted-foreground">{u.email}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <div className="text-right text-sm">
                          <p><span className="text-muted-foreground">Projects:</span> {u.projects_count}</p>
                          <p><span className="text-muted-foreground">Builds:</span> {u.builds_count}</p>
                        </div>
                        <Badge className={`${getStatusBadge(u.status)} capitalize`}>{u.status}</Badge>
                        {u.role === 'admin' ? (
                          <Badge className="bg-destructive/20 text-destructive border-destructive/30">Admin</Badge>
                        ) : (
                          <Button
                            size="sm"
                            variant={u.status === 'banned' ? 'default' : 'destructive'}
                            onClick={() => updateUserStatus(u.id, u.status === 'banned' ? 'active' : 'banned')}
                          >
                            {u.status === 'banned' ? (
                              <>
                                <CheckCircle2 className="w-4 h-4 mr-1" />
                                Unban
                              </>
                            ) : (
                              <>
                                <Ban className="w-4 h-4 mr-1" />
                                Ban
                              </>
                            )}
                          </Button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-muted-foreground">Page {usersPage} of {usersTotalPages}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchUsers(usersPage - 1)}
                      disabled={usersPage <= 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchUsers(usersPage + 1)}
                      disabled={usersPage >= usersTotalPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Builds Tab */}
          <TabsContent value="builds" data-testid="admin-builds">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading">All Builds</CardTitle>
                  <div className="flex gap-2">
                    {['', 'processing', 'completed', 'failed'].map((status) => (
                      <Button
                        key={status}
                        variant={buildsFilter === status ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => { setBuildsFilter(status); fetchBuilds(1, status); }}
                        className={buildsFilter === status ? 'bg-primary text-black' : 'border-white/20'}
                      >
                        {status || 'All'}
                      </Button>
                    ))}
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {builds.map((build) => (
                    <div key={build.id} className="p-4 rounded-lg bg-white/5 border border-white/5">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="w-10 h-10 rounded-md bg-white/5 flex items-center justify-center">
                            <Smartphone className="w-5 h-5 text-muted-foreground" />
                          </div>
                          <div>
                            <p className="font-medium">{build.project_name}</p>
                            <p className="text-sm text-muted-foreground">
                              {build.user_name} ({build.user_email})
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <span className="text-sm text-muted-foreground capitalize">{build.platform}</span>
                          <Badge className={`${getStatusBadge(build.status)} capitalize`}>{build.status}</Badge>
                          <span className="text-xs text-muted-foreground">
                            {new Date(build.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                      {build.status === 'processing' && (
                        <div className="mt-3">
                          <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-primary rounded-full transition-all"
                              style={{ width: `${build.progress}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-muted-foreground">Page {buildsPage} of {buildsTotalPages}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchBuilds(buildsPage - 1, buildsFilter)}
                      disabled={buildsPage <= 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchBuilds(buildsPage + 1, buildsFilter)}
                      disabled={buildsPage >= buildsTotalPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Logs Tab */}
          <TabsContent value="logs" data-testid="admin-logs">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="font-heading">System Logs</CardTitle>
                  <div className="flex gap-2">
                    <select
                      value={logsLevel}
                      onChange={(e) => { setLogsLevel(e.target.value); fetchLogs(1, e.target.value, logsCategory); }}
                      className="bg-white/5 border border-white/10 rounded-md px-3 py-1.5 text-sm"
                    >
                      <option value="">All Levels</option>
                      <option value="info">Info</option>
                      <option value="warning">Warning</option>
                      <option value="error">Error</option>
                      <option value="success">Success</option>
                    </select>
                    <select
                      value={logsCategory}
                      onChange={(e) => { setLogsCategory(e.target.value); fetchLogs(1, logsLevel, e.target.value); }}
                      className="bg-white/5 border border-white/10 rounded-md px-3 py-1.5 text-sm"
                    >
                      <option value="">All Categories</option>
                      <option value="auth">Auth</option>
                      <option value="build">Build</option>
                      <option value="project">Project</option>
                      <option value="admin">Admin</option>
                      <option value="api">API</option>
                    </select>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchLogs(1, logsLevel, logsCategory)}
                      className="border-white/20"
                    >
                      <RefreshCw className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 font-mono text-sm">
                  {logs.map((log) => (
                    <div key={log.id} className="p-3 rounded bg-background border border-white/5 flex items-start gap-3">
                      {getLogIcon(log.level)}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-muted-foreground">
                            {new Date(log.created_at).toLocaleString()}
                          </span>
                          <Badge variant="outline" className="text-xs">{log.category}</Badge>
                        </div>
                        <p className="text-muted-foreground break-all">{log.message}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Pagination */}
                <div className="flex items-center justify-between mt-6">
                  <p className="text-sm text-muted-foreground">Page {logsPage} of {logsTotalPages}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchLogs(logsPage - 1, logsLevel, logsCategory)}
                      disabled={logsPage <= 1}
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => fetchLogs(logsPage + 1, logsLevel, logsCategory)}
                      disabled={logsPage >= logsTotalPages}
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Config Tab */}
          <TabsContent value="config" data-testid="admin-config">
            {config && (
              <div className="space-y-6">
                <Card className="bg-background-paper border-white/10">
                  <CardHeader>
                    <CardTitle className="font-heading">Platform Configuration</CardTitle>
                    <CardDescription>Configure global platform settings</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div className="flex items-center justify-between py-4 border-b border-white/5">
                      <div>
                        <p className="font-medium">Maintenance Mode</p>
                        <p className="text-sm text-muted-foreground">Disable access for non-admin users</p>
                      </div>
                      <Switch
                        checked={config.maintenance_mode}
                        onCheckedChange={(checked) => updateConfig({ maintenance_mode: checked })}
                        className="data-[state=checked]:bg-destructive"
                      />
                    </div>

                    <div className="py-4 border-b border-white/5">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <p className="font-medium">Max Projects per User</p>
                          <p className="text-sm text-muted-foreground">Limit the number of projects</p>
                        </div>
                        <Input
                          type="number"
                          value={config.max_projects_per_user}
                          onChange={(e) => updateConfig({ max_projects_per_user: parseInt(e.target.value) })}
                          className="w-24 bg-white/5 border-white/10 text-center"
                        />
                      </div>
                    </div>

                    <div className="py-4 border-b border-white/5">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <p className="font-medium">Max Builds per User</p>
                          <p className="text-sm text-muted-foreground">Limit the number of builds</p>
                        </div>
                        <Input
                          type="number"
                          value={config.max_builds_per_user}
                          onChange={(e) => updateConfig({ max_builds_per_user: parseInt(e.target.value) })}
                          className="w-24 bg-white/5 border-white/10 text-center"
                        />
                      </div>
                    </div>

                    <div className="py-4">
                      <div className="flex items-center justify-between mb-3">
                        <div>
                          <p className="font-medium">Build Timeout (minutes)</p>
                          <p className="text-sm text-muted-foreground">Maximum build duration before timeout</p>
                        </div>
                        <Input
                          type="number"
                          value={config.build_timeout_minutes}
                          onChange={(e) => updateConfig({ build_timeout_minutes: parseInt(e.target.value) })}
                          className="w-24 bg-white/5 border-white/10 text-center"
                        />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-background-paper border-destructive/30">
                  <CardHeader>
                    <CardTitle className="font-heading text-destructive">Danger Zone</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30">
                      <p className="font-medium mb-2">Clear All Logs</p>
                      <p className="text-sm text-muted-foreground mb-4">
                        This will permanently delete all system logs. This action cannot be undone.
                      </p>
                      <Button variant="destructive" size="sm">
                        Clear Logs
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
};

export default AdminPage;
