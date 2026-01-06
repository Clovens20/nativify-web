import { useState } from 'react';
import DashboardLayout from '../components/layout/DashboardLayout';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { User, Mail, Shield, Bell } from 'lucide-react';
import { Switch } from '../components/ui/switch';

export const SettingsPage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
  });
  const [notifications, setNotifications] = useState({
    buildComplete: true,
    buildFailed: true,
    weeklyReport: false,
  });

  const handleChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      toast.success('Settings saved successfully');
      setLoading(false);
    }, 1000);
  };

  return (
    <DashboardLayout title="Settings" subtitle="Manage your account settings">
      <div className="max-w-2xl space-y-6">
        {/* Profile Settings */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <User className="w-5 h-5 text-primary" />
              Profile
            </CardTitle>
            <CardDescription>Update your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="name">Full Name</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => handleChange('name', e.target.value)}
                className="bg-white/5 border-white/10 focus:border-primary"
                data-testid="name-input"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => handleChange('email', e.target.value)}
                className="bg-white/5 border-white/10 focus:border-primary"
                data-testid="email-input"
              />
            </div>
            <Button 
              onClick={handleSave}
              disabled={loading}
              className="bg-primary text-black font-bold"
              data-testid="save-profile-btn"
            >
              {loading ? 'Saving...' : 'Save Changes'}
            </Button>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <Bell className="w-5 h-5 text-primary" />
              Notifications
            </CardTitle>
            <CardDescription>Configure your notification preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <div>
                <p className="font-medium">Build Completed</p>
                <p className="text-sm text-muted-foreground">Get notified when a build finishes successfully</p>
              </div>
              <Switch
                checked={notifications.buildComplete}
                onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, buildComplete: checked }))}
                className="data-[state=checked]:bg-primary"
                data-testid="notif-build-complete"
              />
            </div>
            <div className="flex items-center justify-between py-3 border-b border-white/5">
              <div>
                <p className="font-medium">Build Failed</p>
                <p className="text-sm text-muted-foreground">Get notified when a build fails</p>
              </div>
              <Switch
                checked={notifications.buildFailed}
                onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, buildFailed: checked }))}
                className="data-[state=checked]:bg-primary"
                data-testid="notif-build-failed"
              />
            </div>
            <div className="flex items-center justify-between py-3">
              <div>
                <p className="font-medium">Weekly Report</p>
                <p className="text-sm text-muted-foreground">Receive a weekly summary of your projects</p>
              </div>
              <Switch
                checked={notifications.weeklyReport}
                onCheckedChange={(checked) => setNotifications(prev => ({ ...prev, weeklyReport: checked }))}
                className="data-[state=checked]:bg-primary"
                data-testid="notif-weekly-report"
              />
            </div>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card className="bg-background-paper border-white/10">
          <CardHeader>
            <CardTitle className="font-heading flex items-center gap-2">
              <Shield className="w-5 h-5 text-primary" />
              Security
            </CardTitle>
            <CardDescription>Manage your account security</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="p-4 rounded-lg bg-white/5 border border-white/5">
              <h4 className="font-medium mb-1">Change Password</h4>
              <p className="text-sm text-muted-foreground mb-3">Update your password to keep your account secure</p>
              <Button variant="outline" className="border-white/20" data-testid="change-password-btn">
                Change Password
              </Button>
            </div>
            <div className="p-4 rounded-lg bg-white/5 border border-white/5">
              <h4 className="font-medium mb-1">Two-Factor Authentication</h4>
              <p className="text-sm text-muted-foreground mb-3">Add an extra layer of security to your account</p>
              <Button variant="outline" className="border-white/20" data-testid="enable-2fa-btn">
                Enable 2FA
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Danger Zone */}
        <Card className="bg-background-paper border-destructive/30">
          <CardHeader>
            <CardTitle className="font-heading text-destructive">Danger Zone</CardTitle>
            <CardDescription>Irreversible actions</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30">
              <h4 className="font-medium text-destructive mb-1">Delete Account</h4>
              <p className="text-sm text-muted-foreground mb-3">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <Button variant="destructive" data-testid="delete-account-btn">
                Delete Account
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default SettingsPage;
