'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import { DashboardLayout } from '@/components/layout/DashboardLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Badge } from '@/components/ui/badge'
import { Loader2 } from 'lucide-react'

export default function DocsPage() {
  const { user, loading: authLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [user, authLoading, router])

  if (authLoading || !user) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    )
  }

  return (
    <DashboardLayout title="Documentation" subtitle="Learn how to use NativiWeb SDK">
      <Tabs defaultValue="quickstart" className="space-y-6">
        <TabsList className="bg-background-subtle">
          <TabsTrigger value="quickstart">Quick Start</TabsTrigger>
          <TabsTrigger value="sdk">SDK Reference</TabsTrigger>
          <TabsTrigger value="api">API Reference</TabsTrigger>
        </TabsList>

        <TabsContent value="quickstart">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>Getting Started with NativiWeb</CardTitle>
              <CardDescription>Follow these steps to convert your web app to native</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-8">
                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4 flex items-center gap-2">
                      <Badge>Step 1</Badge> Create a Project
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Create a new project in the dashboard and enter your web app URL.
                    </p>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`1. Go to Projects → New Project
2. Enter your web app URL (e.g., https://myapp.com)
3. Select target platforms (Android, iOS, or both)
4. Click "Create Project"`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4 flex items-center gap-2">
                      <Badge>Step 2</Badge> Configure Native Features
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Enable the native features your app needs.
                    </p>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`Available features:
• Push Notifications - Send push notifications to users
• Camera - Access device camera
• Geolocation - Get user's GPS location
• Biometrics - Fingerprint/Face ID authentication
• Local Storage - Store data locally
• Contacts - Access user contacts
• And more...`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4 flex items-center gap-2">
                      <Badge>Step 3</Badge> Integrate the SDK
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Add the NativiWeb SDK to your web application.
                    </p>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`<script src="https://sdk.nativiweb.com/v1/nativiweb.js"></script>
<script>
  const nw = NativiWeb.init({
    apiKey: 'your-api-key',
    projectId: 'your-project-id'
  });
</script>`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4 flex items-center gap-2">
                      <Badge>Step 4</Badge> Build & Download
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Start a build and download your native project files.
                    </p>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`1. Go to your project page
2. Click "Build for Android" or "Build for iOS"
3. Wait for the build to complete
4. Download the generated project files
5. Open in Android Studio or Xcode
6. Build and publish to app stores`}
                      </code>
                    </pre>
                  </section>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="sdk">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>SDK Reference</CardTitle>
              <CardDescription>Complete SDK method documentation</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-8">
                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Initialization</h3>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`const nw = NativiWeb.init({
  apiKey: 'your-api-key',
  projectId: 'your-project-id',
  debug: false
});`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Geolocation</h3>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`// Get current position
const position = await nw.getCurrentPosition();
console.log(position.latitude, position.longitude);

// Watch position
nw.watchPosition((position) => {
  console.log('Position updated:', position);
});`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Push Notifications</h3>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`// Request permission
await nw.requestNotificationPermission();

// Show local notification
await nw.showNotification('Title', {
  body: 'Notification body',
  icon: '/icon.png'
});

// Listen for notifications
nw.onNotification((notification) => {
  console.log('Received:', notification);
});`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Camera</h3>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`// Take photo
const photo = await nw.takePhoto({
  quality: 0.8,
  width: 1024,
  height: 1024
});

// Access camera stream
const stream = await nw.getCameraStream();`}
                      </code>
                    </pre>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Biometric Authentication</h3>
                    <pre className="bg-background p-4 rounded-lg border border-white/10 overflow-x-auto">
                      <code className="text-sm font-mono">
{`// Check if available
const available = await nw.isBiometricAvailable();

// Authenticate
const result = await nw.authenticateBiometric({
  title: 'Verify your identity',
  subtitle: 'Use fingerprint to continue'
});`}
                      </code>
                    </pre>
                  </section>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="api">
          <Card className="bg-background-paper border-white/10">
            <CardHeader>
              <CardTitle>API Reference</CardTitle>
              <CardDescription>REST API endpoints for backend integration</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-8">
                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Authentication</h3>
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-success/20 text-success">POST</Badge>
                          <code className="text-sm">/api/auth/register</code>
                        </div>
                        <p className="text-sm text-muted-foreground">Register a new user account</p>
                      </div>
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-success/20 text-success">POST</Badge>
                          <code className="text-sm">/api/auth/login</code>
                        </div>
                        <p className="text-sm text-muted-foreground">Login with email and password</p>
                      </div>
                    </div>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Projects</h3>
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-info/20 text-info">GET</Badge>
                          <code className="text-sm">/api/projects</code>
                        </div>
                        <p className="text-sm text-muted-foreground">List all projects for the authenticated user</p>
                      </div>
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-success/20 text-success">POST</Badge>
                          <code className="text-sm">/api/projects</code>
                        </div>
                        <p className="text-sm text-muted-foreground">Create a new project</p>
                      </div>
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-warning/20 text-warning">PUT</Badge>
                          <code className="text-sm">/api/projects/:id</code>
                        </div>
                        <p className="text-sm text-muted-foreground">Update a project</p>
                      </div>
                    </div>
                  </section>

                  <section>
                    <h3 className="text-lg font-heading font-bold mb-4">Builds</h3>
                    <div className="space-y-4">
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-info/20 text-info">GET</Badge>
                          <code className="text-sm">/api/builds</code>
                        </div>
                        <p className="text-sm text-muted-foreground">List all builds</p>
                      </div>
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-success/20 text-success">POST</Badge>
                          <code className="text-sm">/api/builds</code>
                        </div>
                        <p className="text-sm text-muted-foreground">Start a new build</p>
                      </div>
                      <div className="p-4 rounded-lg border border-white/10">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className="bg-info/20 text-info">GET</Badge>
                          <code className="text-sm">/api/builds/:id/download</code>
                        </div>
                        <p className="text-sm text-muted-foreground">Download build artifacts</p>
                      </div>
                    </div>
                  </section>
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  )
}
