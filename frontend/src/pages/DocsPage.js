import DashboardLayout from '../components/layout/DashboardLayout';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  Book, 
  Code, 
  Smartphone, 
  Rocket,
  Zap,
  Bell,
  Camera,
  MapPin,
  HardDrive
} from 'lucide-react';

export const DocsPage = () => {
  return (
    <DashboardLayout title="Documentation" subtitle="Learn how to use NativiWeb Studio">
      <Tabs defaultValue="getting-started" className="space-y-6">
        <TabsList className="bg-background-paper border border-white/10">
          <TabsTrigger value="getting-started" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Rocket className="w-4 h-4 mr-2" />
            Getting Started
          </TabsTrigger>
          <TabsTrigger value="sdk" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Code className="w-4 h-4 mr-2" />
            SDK Reference
          </TabsTrigger>
          <TabsTrigger value="api" className="data-[state=active]:bg-primary data-[state=active]:text-black">
            <Zap className="w-4 h-4 mr-2" />
            API Reference
          </TabsTrigger>
        </TabsList>

        {/* Getting Started */}
        <TabsContent value="getting-started" data-testid="docs-getting-started">
          <div className="space-y-6">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading flex items-center gap-2">
                  <Book className="w-5 h-5 text-primary" />
                  Introduction
                </CardTitle>
              </CardHeader>
              <CardContent className="prose prose-invert max-w-none">
                <p className="text-muted-foreground">
                  NativiWeb Studio allows you to transform your existing web application into native Android and iOS apps. 
                  Our platform generates native project templates and provides a JavaScript SDK for accessing device features.
                </p>
                
                <h3 className="font-heading font-bold text-lg mt-6 mb-4">How It Works</h3>
                <ol className="space-y-3 text-muted-foreground">
                  <li className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold shrink-0">1</span>
                    <span><strong className="text-white">Create a Project</strong> - Enter your web app URL and select target platforms</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold shrink-0">2</span>
                    <span><strong className="text-white">Configure Features</strong> - Enable the native features your app needs (camera, GPS, notifications, etc.)</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold shrink-0">3</span>
                    <span><strong className="text-white">Generate Build</strong> - Generate native project templates for Android and/or iOS</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold shrink-0">4</span>
                    <span><strong className="text-white">Integrate SDK</strong> - Add our JavaScript SDK to your web app to communicate with native features</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <span className="w-6 h-6 rounded-full bg-primary/20 text-primary flex items-center justify-center text-sm font-bold shrink-0">5</span>
                    <span><strong className="text-white">Compile & Publish</strong> - Use Android Studio / Xcode to compile and publish to app stores</span>
                  </li>
                </ol>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading flex items-center gap-2">
                  <Smartphone className="w-5 h-5 text-primary" />
                  Supported Features
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[
                    { icon: Bell, name: "Push Notifications", desc: "Send and receive push notifications" },
                    { icon: Camera, name: "Camera", desc: "Access device camera for photos and video" },
                    { icon: MapPin, name: "Geolocation", desc: "Get user's current location via GPS" },
                    { icon: HardDrive, name: "Local Storage", desc: "Persistent native storage for app data" },
                  ].map((feature) => (
                    <div key={feature.name} className="p-4 rounded-lg bg-white/5 border border-white/5">
                      <div className="flex items-center gap-3 mb-2">
                        <feature.icon className="w-5 h-5 text-primary" />
                        <span className="font-medium">{feature.name}</span>
                      </div>
                      <p className="text-sm text-muted-foreground">{feature.desc}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* SDK Reference */}
        <TabsContent value="sdk" data-testid="docs-sdk">
          <div className="space-y-6">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading">Installation</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-muted-foreground">
                  Download the SDK from your project page and include it in your web app:
                </p>
                <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
                  <code className="text-primary">&lt;script</code>
                  <code className="text-muted-foreground"> src=</code>
                  <code className="text-success">"nativiweb-sdk.js"</code>
                  <code className="text-primary">&gt;&lt;/script&gt;</code>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading">Core Methods</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* getDeviceInfo */}
                <div>
                  <h4 className="font-mono text-primary mb-2">NativiWeb.getDeviceInfo()</h4>
                  <p className="text-sm text-muted-foreground mb-3">Returns information about the device.</p>
                  <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
                    <div><span className="text-secondary">const</span> info = <span className="text-secondary">await</span> NativiWeb.<span className="text-primary">getDeviceInfo</span>();</div>
                    <div className="text-muted-foreground">// {"{"} platform: "android", version: "14", ... {"}"}</div>
                  </div>
                </div>

                {/* getCurrentPosition */}
                <div>
                  <h4 className="font-mono text-primary mb-2">NativiWeb.getCurrentPosition(options?)</h4>
                  <p className="text-sm text-muted-foreground mb-3">Gets the user's current GPS location.</p>
                  <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
                    <div><span className="text-secondary">const</span> position = <span className="text-secondary">await</span> NativiWeb.<span className="text-primary">getCurrentPosition</span>();</div>
                    <div className="text-muted-foreground">// {"{"} coords: {"{"} latitude: 40.7128, longitude: -74.0060 {"}"} {"}"}</div>
                  </div>
                </div>

                {/* showNotification */}
                <div>
                  <h4 className="font-mono text-primary mb-2">NativiWeb.showNotification(title, options)</h4>
                  <p className="text-sm text-muted-foreground mb-3">Displays a native push notification.</p>
                  <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
                    <div><span className="text-secondary">await</span> NativiWeb.<span className="text-primary">showNotification</span>(</div>
                    <div className="pl-4"><span className="text-success">"New Message"</span>,</div>
                    <div className="pl-4">{"{"} <span className="text-primary">body</span>: <span className="text-success">"You have a new message"</span> {"}"}</div>
                    <div>);</div>
                  </div>
                </div>

                {/* vibrate */}
                <div>
                  <h4 className="font-mono text-primary mb-2">NativiWeb.vibrate(pattern)</h4>
                  <p className="text-sm text-muted-foreground mb-3">Triggers haptic feedback on the device.</p>
                  <div className="p-4 rounded-lg bg-background border border-white/10 font-mono text-sm">
                    <div><span className="text-secondary">await</span> NativiWeb.<span className="text-primary">vibrate</span>(<span className="text-warning">100</span>); <span className="text-muted-foreground">// vibrate for 100ms</span></div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading">Properties</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="p-4 rounded-lg bg-white/5 border border-white/5">
                    <code className="text-primary">NativiWeb.isNative</code>
                    <p className="text-sm text-muted-foreground mt-1">Boolean indicating if the app is running in a native WebView</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 border border-white/5">
                    <code className="text-primary">NativiWeb.platform</code>
                    <p className="text-sm text-muted-foreground mt-1">String: "android", "ios", or "web"</p>
                  </div>
                  <div className="p-4 rounded-lg bg-white/5 border border-white/5">
                    <code className="text-primary">NativiWeb.version</code>
                    <p className="text-sm text-muted-foreground mt-1">SDK version string (e.g., "1.0.0")</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* API Reference */}
        <TabsContent value="api" data-testid="docs-api">
          <div className="space-y-6">
            <Card className="bg-background-paper border-white/10">
              <CardHeader>
                <CardTitle className="font-heading">REST API</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                <p className="text-muted-foreground">
                  NativiWeb Studio provides a REST API for managing your projects and builds programmatically.
                </p>

                {/* Projects */}
                <div>
                  <h4 className="font-heading font-bold mb-3">Projects</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-success/20 text-success text-xs font-mono">GET</span>
                      <code className="text-sm">/api/projects</code>
                      <span className="text-sm text-muted-foreground">List all projects</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-primary/20 text-primary text-xs font-mono">POST</span>
                      <code className="text-sm">/api/projects</code>
                      <span className="text-sm text-muted-foreground">Create a new project</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-success/20 text-success text-xs font-mono">GET</span>
                      <code className="text-sm">/api/projects/:id</code>
                      <span className="text-sm text-muted-foreground">Get project details</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-warning/20 text-warning text-xs font-mono">PUT</span>
                      <code className="text-sm">/api/projects/:id</code>
                      <span className="text-sm text-muted-foreground">Update project</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-destructive/20 text-destructive text-xs font-mono">DELETE</span>
                      <code className="text-sm">/api/projects/:id</code>
                      <span className="text-sm text-muted-foreground">Delete project</span>
                    </div>
                  </div>
                </div>

                {/* Builds */}
                <div>
                  <h4 className="font-heading font-bold mb-3">Builds</h4>
                  <div className="space-y-2">
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-success/20 text-success text-xs font-mono">GET</span>
                      <code className="text-sm">/api/builds</code>
                      <span className="text-sm text-muted-foreground">List all builds</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-primary/20 text-primary text-xs font-mono">POST</span>
                      <code className="text-sm">/api/builds</code>
                      <span className="text-sm text-muted-foreground">Start a new build</span>
                    </div>
                    <div className="flex items-center gap-3 p-3 rounded bg-white/5">
                      <span className="px-2 py-0.5 rounded bg-success/20 text-success text-xs font-mono">GET</span>
                      <code className="text-sm">/api/builds/:id/download</code>
                      <span className="text-sm text-muted-foreground">Download build artifacts</span>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>
    </DashboardLayout>
  );
};

export default DocsPage;
