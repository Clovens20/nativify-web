import { useState, useEffect } from 'react';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { buildsApi, projectsApi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { 
  Package, 
  Download, 
  Clock,
  Smartphone,
  CheckCircle2,
  XCircle,
  Loader2,
  RefreshCw
} from 'lucide-react';

export const BuildsPage = () => {
  const { user } = useAuth();
  const [builds, setBuilds] = useState([]);
  const [projects, setProjects] = useState({});
  const [loading, setLoading] = useState(true);

  const fetchBuilds = async () => {
    if (!user?.id) return;
    try {
      const [buildsData, projectsData] = await Promise.all([
        buildsApi.getAll(user.id),
        projectsApi.getAll(user.id)
      ]);
      setBuilds(buildsData);
      
      // Create a map of project IDs to names
      const projectMap = {};
      projectsData.forEach(p => {
        projectMap[p.id] = p.name;
      });
      setProjects(projectMap);
    } catch (error) {
      console.error('Error fetching builds:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBuilds();
    
    // Poll for updates every 5 seconds if there are processing builds
    const interval = setInterval(() => {
      const hasProcessing = builds.some(b => b.status === 'processing');
      if (hasProcessing) {
        fetchBuilds();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [user, builds.length]);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <CheckCircle2 className="w-5 h-5 text-success" />;
      case 'processing': return <Loader2 className="w-5 h-5 text-warning animate-spin" />;
      case 'failed': return <XCircle className="w-5 h-5 text-destructive" />;
      default: return <Clock className="w-5 h-5 text-muted-foreground" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-success';
      case 'processing': return 'text-warning';
      case 'failed': return 'text-destructive';
      default: return 'text-muted-foreground';
    }
  };

  return (
    <DashboardLayout title="Builds" subtitle="View and download your native app builds">
      <div className="flex justify-end mb-6">
        <Button 
          variant="outline" 
          onClick={fetchBuilds}
          className="border-white/20"
          data-testid="refresh-builds-btn"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {loading ? (
        <div className="space-y-4">
          {[1, 2, 3].map(i => (
            <Card key={i} className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="h-20 bg-white/5 rounded animate-pulse"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : builds.length === 0 ? (
        <div className="text-center py-16" data-testid="empty-state">
          <Package className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="font-heading font-bold text-xl mb-2">No builds yet</h3>
          <p className="text-muted-foreground">
            Start a build from your project page to generate native apps
          </p>
        </div>
      ) : (
        <div className="space-y-4" data-testid="builds-list">
          {builds.map((build) => (
            <Card key={build.id} className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center">
                      <Smartphone className="w-6 h-6 text-muted-foreground" />
                    </div>
                    <div>
                      <h3 className="font-heading font-bold text-lg">
                        {projects[build.project_id] || 'Unknown Project'}
                      </h3>
                      <div className="flex items-center gap-3 mt-1">
                        <span className="text-sm text-muted-foreground capitalize">
                          {build.platform} • {build.build_type}
                        </span>
                        <div className="flex items-center gap-1">
                          {getStatusIcon(build.status)}
                          <span className={`text-sm font-medium capitalize ${getStatusColor(build.status)}`}>
                            {build.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="flex items-center gap-1 text-sm text-muted-foreground">
                        <Clock className="w-4 h-4" />
                        {new Date(build.created_at).toLocaleString()}
                      </div>
                      {build.completed_at && (
                        <p className="text-xs text-muted-foreground mt-1">
                          Completed: {new Date(build.completed_at).toLocaleString()}
                        </p>
                      )}
                    </div>

                    {build.status === 'completed' && (
                      <a href={buildsApi.download(build.id, user.id)} data-testid={`download-${build.id}`}>
                        <Button className="bg-primary text-black font-bold">
                          <Download className="w-4 h-4 mr-2" />
                          Download
                        </Button>
                      </a>
                    )}
                  </div>
                </div>

                {build.status === 'processing' && (
                  <div className="mt-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-muted-foreground">Building...</span>
                      <span className="text-primary">{build.progress}%</span>
                    </div>
                    <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary rounded-full transition-all duration-500"
                        style={{ width: `${build.progress}%` }}
                      ></div>
                    </div>
                    {build.logs && build.logs.length > 0 && (
                      <p className="text-xs text-muted-foreground mt-2 font-mono">
                        {build.logs[build.logs.length - 1]}
                      </p>
                    )}
                  </div>
                )}

                {build.status === 'completed' && build.logs && (
                  <details className="mt-4">
                    <summary className="text-sm text-muted-foreground cursor-pointer hover:text-white">
                      View build logs
                    </summary>
                    <div className="mt-2 p-3 rounded bg-background border border-white/10 font-mono text-xs space-y-1 max-h-40 overflow-auto">
                      {build.logs.map((log, idx) => (
                        <div key={idx} className="text-muted-foreground">
                          <span className="text-primary mr-2">[{idx + 1}]</span>
                          {log}
                        </div>
                      ))}
                    </div>
                  </details>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
};

export default BuildsPage;
