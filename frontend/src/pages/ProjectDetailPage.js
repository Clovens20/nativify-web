import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Switch } from '../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { projectsApi, buildsApi, generatorApi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  ArrowLeft,
  Globe,
  Smartphone,
  Play,
  Download,
  Code,
  Settings,
  Bell,
  Camera,
  MapPin,
  HardDrive,
  Fingerprint,
  Users,
  FolderOpen,
  Share2,
  Vibrate,
  Link2,
  Badge,
  Clipboard,
  FileCode,
  Package
} from 'lucide-react';

const featureIcons = {
  push_notifications: Bell,
  camera: Camera,
  geolocation: MapPin,
  local_storage: HardDrive,
  biometrics: Fingerprint,
  contacts: Users,
  file_system: FolderOpen,
  share: Share2,
  haptics: Vibrate,
  deep_links: Link2,
  app_badge: Badge,
  clipboard: Clipboard,
};

export const ProjectDetailPage = () => {
  const { id } = useParams();
  const { user } = useAuth();
  const [project, setProject] = useState(null);
  const [builds, setBuilds] = useState([]);
  const [loading, setLoading] = useState(true);
  const [buildingPlatform, setBuildingPlatform] = useState(null);

  const fetchProject = async () => {
    try {
      const [projectData, buildsData] = await Promise.all([
        projectsApi.getOne(id, user.id),
        buildsApi.getAll(user.id, id)
      ]);
      setProject(projectData);
      setBuilds(buildsData);
    } catch (error) {
      console.error('Error fetching project:', error);
      toast.error('Failed to load project');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (user?.id) {
      fetchProject();
    }
  }, [id, user]);

  const toggleFeature = async (featureId) => {
    if (!project) return;

    const updatedFeatures = project.features.map(f => 
      f.id === featureId ? { ...f, enabled: !f.enabled } : f
    );

    try {
      await projectsApi.update(id, { features: updatedFeatures }, user.id);
      setProject(prev => ({ ...prev, features: updatedFeatures }));
      toast.success('Feature updated');
    } catch (error) {
      toast.error('Failed to update feature');
    }
  };

  const startBuild = async (platform) => {
    setBuildingPlatform(platform);
    try {
      await buildsApi.create({
        project_id: id,
        platform: platform,
        build_type: 'debug'
      }, user.id);
      toast.success(`${platform} build started!`);
      fetchProject();
    } catch (error) {
      toast.error('Failed to start build');
    } finally {
      setBuildingPlatform(null);
    }
  };

  const downloadSdk = () => {
    window.open(generatorApi.getSdk(id, user.id), '_blank');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'text-success bg-success/10 border-success/30';
      case 'processing': return 'text-warning bg-warning/10 border-warning/30';
      case 'failed': return 'text-destructive bg-destructive/10 border-destructive/30';
      default: return 'text-muted-foreground bg-white/5 border-white/10';
    }
  };

  if (loading) {
    return (
      <DashboardLayout title="Loading...">
        <div className="animate-pulse space-y-6">
          <div className="h-32 bg-white/5 rounded-lg"></div>
          <div className="h-64 bg-white/5 rounded-lg"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout title="Project Not Found">
        <div className="text-center py-16">
          <p className="text-muted-foreground mb-4">The project you're looking for doesn't exist.</p>
          <Link to="/projects">
            <Button variant="outline">Back to Projects</Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout title={project.name} subtitle={project.description || 'Native app project'}>
      {/* Back Link */}
      <Link 
        to="/projects" 
        className="inline-flex items-center gap-2 text-muted-foreground hover:text-white mb-6 transition-colors"
        data-testid="back-link"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Projects
      </Link>

      {/* Project Header Card */}
      <Card className="bg-background-paper border-white/10 mb-8">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-4">
              <div className="w-16 h-16 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center">
                <Globe className="w-8 h-8 text-primary" />
              </div>
              <div>
                <h2 className="font-heading font-bold text-2xl mb-1">{project.name}</h2>
                <a 
                  href={project.web_url} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-primary hover:underline flex items-center gap-1"
                >
                  {project.web_url}
                  <Globe className="w-3 h-3" />
                </a>
                <div className="flex gap-2 mt-3">
                  {project.platform.map(p => (
                    <span key={p} className="px-3 py-1 rounded bg-secondary/20 text-secondary border border-secondary/30 text-sm font-medium">
                      {p}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            <div className="flex gap-2">
              <Button 
                variant="outline" 
                onClick={downloadSdk}
                className="border-white/20"
                data-testid="download-sdk-btn"
              >
                <Code className="w-4 h-4 mr-2" />
                Download SDK
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs */}
      <Tabs defaultValue="features" className="space-y-6">
        <TabsList className="bg-background-paper border border-white/10">
          <TabsTrigger value="features" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Settings className="w-4 h-4 mr-2" />
            Features
          </TabsTrigger>
          <TabsTrigger value="builds" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Package className="w-4 h-4 mr-2" />
            Builds
          </TabsTrigger>
          <TabsTrigger value="sdk" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <FileCode className="w-4 h-4 mr-2" />
            SDK
          </TabsTrigger>
        </TabsList>

        {/* Features Tab */}
        <TabsContent value="features" data-testid="features-tab">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle className="font-heading">Native Features</CardTitle>
              <CardDescription>Enable the native features you want to access from your web app</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {project.features.map((feature) => {
                  const Icon = featureIcons[feature.id] || Settings;
                  return (
                    <div 
                      key={feature.id}
                      className={`p-4 rounded-lg border transition-all ${
                        feature.enabled 
                          ? 'border-primary/30 bg-primary/5' 
                          : 'border-white/10 bg-white/5'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-md flex items-center justify-center ${
                            feature.enabled ? 'bg-primary/20' : 'bg-white/10'
                          }`}>
                            <Icon className={`w-5 h-5 ${feature.enabled ? 'text-primary' : 'text-muted-foreground'}`} />
                          </div>
                          <span className="font-medium">{feature.name}</span>
                        </div>
                        <Switch
                          checked={feature.enabled}
                          onCheckedChange={() => toggleFeature(feature.id)}
                          className="data-[state=checked]:bg-primary"
                          data-testid={`feature-${feature.id}`}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Builds Tab */}
        <TabsContent value="builds" data-testid="builds-tab">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Start Build Cards */}
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading flex items-center gap-2">
                  <Smartphone className="w-5 h-5 text-primary" />
                  Start Build
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {project.platform.map(platform => (
                  <Button
                    key={platform}
                    onClick={() => startBuild(platform)}
                    disabled={buildingPlatform === platform}
                    className="w-full bg-primary/10 border border-primary/30 text-primary hover:bg-primary hover:text-black transition-all"
                    data-testid={`build-${platform}-btn`}
                  >
                    <Play className="w-4 h-4 mr-2" />
                    {buildingPlatform === platform ? 'Starting...' : `Build ${platform}`}
                  </Button>
                ))}
              </CardContent>
            </Card>

            {/* Build History */}
            <Card className="bg-background-paper border-white/10 lg:col-span-2">
              <CardHeader>
                <CardTitle className="font-heading">Build History</CardTitle>
              </CardHeader>
              <CardContent>
                {builds.length === 0 ? (
                  <div className="text-center py-8">
                    <Package className="w-12 h-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground">No builds yet</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {builds.map((build) => (
                      <div 
                        key={build.id}
                        className="p-4 rounded-lg bg-white/5 border border-white/5"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-3">
                            <Smartphone className="w-5 h-5 text-muted-foreground" />
                            <span className="font-medium capitalize">{build.platform}</span>
                            <span className={`px-2 py-0.5 rounded text-xs border ${getStatusColor(build.status)}`}>
                              {build.status}
                            </span>
                          </div>
                          {build.status === 'completed' && (
                            <a href={buildsApi.download(build.id, user.id)} data-testid={`download-${build.id}`}>
                              <Button size="sm" variant="outline" className="border-white/20">
                                <Download className="w-4 h-4 mr-1" />
                                Download
                              </Button>
                            </a>
                          )}
                        </div>
                        {build.status === 'processing' && (
                          <div className="mt-2">
                            <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-primary rounded-full transition-all"
                                style={{ width: `${build.progress}%` }}
                              ></div>
                            </div>
                            <p className="text-xs text-muted-foreground mt-1">{build.progress}%</p>
                          </div>
                        )}
                        <p className="text-xs text-muted-foreground mt-2">
                          {new Date(build.created_at).toLocaleString()}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* SDK Tab */}
        <TabsContent value="sdk" data-testid="sdk-tab">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle className="font-heading">JavaScript SDK</CardTitle>
              <CardDescription>Include this SDK in your web app to access native features</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <h4 className="font-medium mb-2">Installation</h4>
                <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
                  <code className="text-primary">&lt;script</code>
                  <code className="text-muted-foreground"> src=</code>
                  <code className="text-success">"nativiweb-sdk.js"</code>
                  <code className="text-primary">&gt;&lt;/script&gt;</code>
                </div>
              </div>

              <div>
                <h4 className="font-medium mb-2">Usage Example</h4>
                <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm space-y-1">
                  <div><span className="text-muted-foreground">// Check if running in native app</span></div>
                  <div><span className="text-secondary">if</span> (NativiWeb.isNative) {"{"}</div>
                  <div className="pl-4"><span className="text-muted-foreground">// Get user location</span></div>
                  <div className="pl-4"><span className="text-secondary">const</span> pos = <span className="text-secondary">await</span> NativiWeb.<span className="text-primary">getCurrentPosition</span>();</div>
                  <div className="pl-4">console.log(pos.coords);</div>
                  <div>{"}"}</div>
                </div>
              </div>

              <Button onClick={downloadSdk} className="bg-primary text-black font-bold">
                <Download className="w-4 h-4 mr-2" />
                Download SDK
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
};

export default ProjectDetailPage;
