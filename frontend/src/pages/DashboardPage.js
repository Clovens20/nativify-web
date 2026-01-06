import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { statsApi, projectsApi, buildsApi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { 
  FolderKanban, 
  Package, 
  Key, 
  CheckCircle2, 
  Plus,
  ArrowRight,
  Clock,
  Smartphone
} from 'lucide-react';

const StatCard = ({ title, value, icon: Icon, color = "primary" }) => (
  <Card className="bg-background-paper border-white/10 hover:border-primary/30 transition-colors">
    <CardContent className="p-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground mb-1">{title}</p>
          <p className="font-heading font-bold text-3xl">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-md bg-${color}/10 border border-${color}/30 flex items-center justify-center`}>
          <Icon className={`w-6 h-6 text-${color}`} />
        </div>
      </div>
    </CardContent>
  </Card>
);

export const DashboardPage = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState({ projects: 0, total_builds: 0, successful_builds: 0, api_keys: 0 });
  const [recentProjects, setRecentProjects] = useState([]);
  const [recentBuilds, setRecentBuilds] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      if (!user?.id) return;
      
      try {
        const [statsData, projectsData, buildsData] = await Promise.all([
          statsApi.get(user.id),
          projectsApi.getAll(user.id),
          buildsApi.getAll(user.id)
        ]);
        
        setStats(statsData);
        setRecentProjects(projectsData.slice(0, 5));
        setRecentBuilds(buildsData.slice(0, 5));
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-success';
      case 'processing': return 'text-warning';
      case 'failed': return 'text-destructive';
      default: return 'text-muted-foreground';
    }
  };

  return (
    <DashboardLayout title="Dashboard" subtitle={`Welcome back, ${user?.name || 'User'}`}>
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8" data-testid="stats-grid">
        <StatCard title="Total Projects" value={stats.projects} icon={FolderKanban} color="primary" />
        <StatCard title="Total Builds" value={stats.total_builds} icon={Package} color="secondary" />
        <StatCard title="Successful Builds" value={stats.successful_builds} icon={CheckCircle2} color="success" />
        <StatCard title="API Keys" value={stats.api_keys} icon={Key} color="warning" />
      </div>

      {/* Quick Actions */}
      <div className="mb-8">
        <h2 className="font-heading font-bold text-xl mb-4">Quick Actions</h2>
        <div className="flex gap-4">
          <Link to="/projects/new">
            <Button className="bg-primary text-black font-bold hover:shadow-neon transition-all" data-testid="new-project-btn">
              <Plus className="w-4 h-4 mr-2" />
              New Project
            </Button>
          </Link>
          <Link to="/docs">
            <Button variant="outline" className="border-white/20 hover:bg-white/5" data-testid="view-docs-btn">
              View Documentation
            </Button>
          </Link>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Recent Projects */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="font-heading text-lg">Recent Projects</CardTitle>
            <Link to="/projects" className="text-sm text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-white/5 rounded animate-pulse"></div>
                ))}
              </div>
            ) : recentProjects.length === 0 ? (
              <div className="text-center py-8">
                <FolderKanban className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No projects yet</p>
                <Link to="/projects/new">
                  <Button variant="link" className="text-primary mt-2">Create your first project</Button>
                </Link>
              </div>
            ) : (
              <div className="space-y-3" data-testid="recent-projects">
                {recentProjects.map((project) => (
                  <Link 
                    key={project.id} 
                    to={`/projects/${project.id}`}
                    className="block p-4 rounded-md bg-white/5 border border-white/5 hover:border-primary/30 transition-colors"
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{project.name}</p>
                        <p className="text-sm text-muted-foreground truncate max-w-xs">{project.web_url}</p>
                      </div>
                      <div className="flex gap-1">
                        {project.platform.map(p => (
                          <span key={p} className="px-2 py-1 text-xs rounded bg-secondary/20 text-secondary border border-secondary/30">
                            {p}
                          </span>
                        ))}
                      </div>
                    </div>
                  </Link>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Builds */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="font-heading text-lg">Recent Builds</CardTitle>
            <Link to="/builds" className="text-sm text-primary hover:underline flex items-center gap-1">
              View all <ArrowRight className="w-4 h-4" />
            </Link>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-white/5 rounded animate-pulse"></div>
                ))}
              </div>
            ) : recentBuilds.length === 0 ? (
              <div className="text-center py-8">
                <Package className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                <p className="text-muted-foreground">No builds yet</p>
                <p className="text-sm text-muted-foreground mt-1">Create a project and start a build</p>
              </div>
            ) : (
              <div className="space-y-3" data-testid="recent-builds">
                {recentBuilds.map((build) => (
                  <div 
                    key={build.id}
                    className="p-4 rounded-md bg-white/5 border border-white/5"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-md bg-white/5 flex items-center justify-center">
                          <Smartphone className="w-5 h-5 text-muted-foreground" />
                        </div>
                        <div>
                          <p className="font-medium capitalize">{build.platform} Build</p>
                          <div className="flex items-center gap-2 text-sm text-muted-foreground">
                            <Clock className="w-3 h-3" />
                            <span>{new Date(build.created_at).toLocaleDateString()}</span>
                          </div>
                        </div>
                      </div>
                      <span className={`text-sm font-medium capitalize ${getStatusColor(build.status)}`}>
                        {build.status}
                      </span>
                    </div>
                    {build.status === 'processing' && (
                      <div className="mt-3">
                        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary rounded-full transition-all duration-500"
                            style={{ width: `${build.progress}%` }}
                          ></div>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default DashboardPage;
