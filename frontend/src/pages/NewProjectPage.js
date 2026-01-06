import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Checkbox } from '../components/ui/checkbox';
import { projectsApi } from '../lib/api';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  ArrowRight,
  Globe,
  Smartphone,
  Zap
} from 'lucide-react';

export const NewProjectPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    web_url: '',
    description: '',
    platform: ['android', 'ios']
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const togglePlatform = (platform) => {
    setFormData(prev => ({
      ...prev,
      platform: prev.platform.includes(platform)
        ? prev.platform.filter(p => p !== platform)
        : [...prev.platform, platform]
    }));
  };

  const handleSubmit = async () => {
    if (!formData.name || !formData.web_url) {
      toast.error('Please fill in all required fields');
      return;
    }

    if (formData.platform.length === 0) {
      toast.error('Please select at least one platform');
      return;
    }

    setLoading(true);
    try {
      const project = await projectsApi.create(formData, user.id);
      toast.success('Project created successfully!');
      navigate(`/projects/${project.id}`);
    } catch (error) {
      console.error('Error creating project:', error);
      toast.error('Failed to create project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <DashboardLayout title="New Project" subtitle="Create a new native app project">
      <div className="max-w-2xl mx-auto">
        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-8">
          {[1, 2].map((s) => (
            <div key={s} className="flex items-center gap-2">
              <div 
                className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm transition-colors ${
                  step >= s 
                    ? 'bg-primary text-black' 
                    : 'bg-white/10 text-muted-foreground'
                }`}
              >
                {s}
              </div>
              <span className={step >= s ? 'text-white' : 'text-muted-foreground'}>
                {s === 1 ? 'Basic Info' : 'Platforms'}
              </span>
              {s < 2 && <div className="w-16 h-px bg-white/20 mx-2"></div>}
            </div>
          ))}
        </div>

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <Card className="bg-background-paper border-white/10" data-testid="step-1">
            <CardHeader>
              <CardTitle className="font-heading flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary" />
                Project Information
              </CardTitle>
              <CardDescription>Enter your web application details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Project Name *</Label>
                <Input
                  id="name"
                  placeholder="My Awesome App"
                  value={formData.name}
                  onChange={(e) => handleChange('name', e.target.value)}
                  className="bg-white/5 border-white/10 focus:border-primary"
                  data-testid="project-name-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="web_url">Web App URL *</Label>
                <Input
                  id="web_url"
                  type="url"
                  placeholder="https://myapp.com"
                  value={formData.web_url}
                  onChange={(e) => handleChange('web_url', e.target.value)}
                  className="bg-white/5 border-white/10 focus:border-primary"
                  data-testid="project-url-input"
                />
                <p className="text-xs text-muted-foreground">
                  Enter the URL of your deployed web application
                </p>
              </div>

              <div className="space-y-2">
                <Label htmlFor="description">Description (optional)</Label>
                <Textarea
                  id="description"
                  placeholder="A brief description of your app..."
                  value={formData.description}
                  onChange={(e) => handleChange('description', e.target.value)}
                  className="bg-white/5 border-white/10 focus:border-primary min-h-24"
                  data-testid="project-description-input"
                />
              </div>

              <div className="flex justify-end">
                <Button 
                  onClick={() => setStep(2)}
                  className="bg-primary text-black font-bold"
                  disabled={!formData.name || !formData.web_url}
                  data-testid="next-step-btn"
                >
                  Next Step
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Step 2: Platforms */}
        {step === 2 && (
          <Card className="bg-background-paper border-white/10" data-testid="step-2">
            <CardHeader>
              <CardTitle className="font-heading flex items-center gap-2">
                <Smartphone className="w-5 h-5 text-primary" />
                Target Platforms
              </CardTitle>
              <CardDescription>Select the platforms you want to target</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div 
                  className={`p-6 rounded-lg border-2 cursor-pointer transition-all ${
                    formData.platform.includes('android')
                      ? 'border-primary bg-primary/10'
                      : 'border-white/10 hover:border-white/30'
                  }`}
                  onClick={() => togglePlatform('android')}
                  data-testid="platform-android"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Checkbox 
                      checked={formData.platform.includes('android')}
                      className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                    />
                    <span className="font-heading font-bold text-lg">Android</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Generate Android project with Kotlin and Gradle
                  </p>
                </div>

                <div 
                  className={`p-6 rounded-lg border-2 cursor-pointer transition-all ${
                    formData.platform.includes('ios')
                      ? 'border-primary bg-primary/10'
                      : 'border-white/10 hover:border-white/30'
                  }`}
                  onClick={() => togglePlatform('ios')}
                  data-testid="platform-ios"
                >
                  <div className="flex items-center gap-3 mb-3">
                    <Checkbox 
                      checked={formData.platform.includes('ios')}
                      className="data-[state=checked]:bg-primary data-[state=checked]:border-primary"
                    />
                    <span className="font-heading font-bold text-lg">iOS</span>
                  </div>
                  <p className="text-sm text-muted-foreground">
                    Generate iOS project with Swift and SwiftUI
                  </p>
                </div>
              </div>

              <div className="p-4 rounded-lg bg-secondary/10 border border-secondary/30">
                <div className="flex items-start gap-3">
                  <Zap className="w-5 h-5 text-secondary mt-0.5" />
                  <div>
                    <p className="font-medium text-sm">Pro Tip</p>
                    <p className="text-sm text-muted-foreground">
                      You can configure native features after creating the project
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex justify-between">
                <Button 
                  variant="outline"
                  onClick={() => setStep(1)}
                  className="border-white/20"
                  data-testid="prev-step-btn"
                >
                  <ArrowLeft className="w-4 h-4 mr-2" />
                  Back
                </Button>
                <Button 
                  onClick={handleSubmit}
                  className="bg-primary text-black font-bold hover:shadow-neon transition-all"
                  disabled={loading || formData.platform.length === 0}
                  data-testid="create-project-btn"
                >
                  {loading ? 'Creating...' : 'Create Project'}
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
};

export default NewProjectPage;
