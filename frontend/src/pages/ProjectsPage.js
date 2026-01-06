import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Button } from '../components/ui/button';
import { Card, CardContent } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { projectsApi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { 
  Plus, 
  Search, 
  FolderKanban,
  Globe,
  Calendar,
  MoreVertical,
  Trash2
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '../components/ui/dropdown-menu';
import { toast } from 'sonner';

export const ProjectsPage = () => {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const fetchProjects = async () => {
    if (!user?.id) return;
    try {
      const data = await projectsApi.getAll(user.id);
      setProjects(data);
    } catch (error) {
      console.error('Error fetching projects:', error);
      toast.error('Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, [user]);

  const handleDelete = async (projectId) => {
    if (!window.confirm('Are you sure you want to delete this project?')) return;
    
    try {
      await projectsApi.delete(projectId, user.id);
      toast.success('Project deleted');
      fetchProjects();
    } catch (error) {
      toast.error('Failed to delete project');
    }
  };

  const filteredProjects = projects.filter(p => 
    p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.web_url.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const enabledFeaturesCount = (features) => features?.filter(f => f.enabled).length || 0;

  return (
    <DashboardLayout title="Projects" subtitle="Manage your native app projects">
      {/* Header Actions */}
      <div className="flex items-center justify-between mb-8">
        <div className="relative w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search projects..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-white/5 border-white/10"
            data-testid="search-projects"
          />
        </div>
        <Link to="/projects/new">
          <Button className="bg-primary text-black font-bold hover:shadow-neon transition-all" data-testid="new-project-btn">
            <Plus className="w-4 h-4 mr-2" />
            New Project
          </Button>
        </Link>
      </div>

      {/* Projects Grid */}
      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <Card key={i} className="bg-background-paper border-white/10">
              <CardContent className="p-6">
                <div className="h-32 bg-white/5 rounded animate-pulse"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : filteredProjects.length === 0 ? (
        <div className="text-center py-16" data-testid="empty-state">
          <FolderKanban className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h3 className="font-heading font-bold text-xl mb-2">No projects found</h3>
          <p className="text-muted-foreground mb-6">
            {searchQuery ? 'Try a different search term' : 'Create your first project to get started'}
          </p>
          {!searchQuery && (
            <Link to="/projects/new">
              <Button className="bg-primary text-black font-bold">
                <Plus className="w-4 h-4 mr-2" />
                Create Project
              </Button>
            </Link>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="projects-grid">
          {filteredProjects.map((project) => (
            <Card 
              key={project.id} 
              className="bg-background-paper border-white/10 hover:border-primary/30 transition-all group"
            >
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="w-12 h-12 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center">
                    <FolderKanban className="w-6 h-6 text-primary" />
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-background-paper border-white/10">
                      <DropdownMenuItem 
                        className="text-destructive focus:text-destructive"
                        onClick={() => handleDelete(project.id)}
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <Link to={`/projects/${project.id}`}>
                  <h3 className="font-heading font-bold text-lg mb-2 hover:text-primary transition-colors">
                    {project.name}
                  </h3>
                </Link>
                
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-4">
                  <Globe className="w-4 h-4" />
                  <span className="truncate">{project.web_url}</span>
                </div>

                <div className="flex items-center justify-between text-sm">
                  <div className="flex gap-1">
                    {project.platform.map(p => (
                      <span key={p} className="px-2 py-1 rounded bg-secondary/20 text-secondary border border-secondary/30 text-xs">
                        {p}
                      </span>
                    ))}
                  </div>
                  <span className="text-muted-foreground">
                    {enabledFeaturesCount(project.features)} features
                  </span>
                </div>

                <div className="flex items-center gap-2 mt-4 pt-4 border-t border-white/5 text-xs text-muted-foreground">
                  <Calendar className="w-3 h-3" />
                  <span>Created {new Date(project.created_at).toLocaleDateString()}</span>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </DashboardLayout>
  );
};

export default ProjectsPage;
