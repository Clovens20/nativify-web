import { Link } from 'react-router-dom';
import { Button } from '../components/ui/button';
import { 
  Zap, 
  Smartphone, 
  Code, 
  Rocket, 
  Shield, 
  Globe,
  ArrowRight,
  CheckCircle2,
  Github
} from 'lucide-react';

const features = [
  {
    icon: Smartphone,
    title: "Native Features",
    description: "Access camera, GPS, push notifications, biometrics and more from your web app."
  },
  {
    icon: Code,
    title: "Simple SDK",
    description: "One JavaScript SDK to bridge your web app with native device capabilities."
  },
  {
    icon: Rocket,
    title: "Fast Generation",
    description: "Generate Android and iOS project templates in seconds, ready for compilation."
  },
  {
    icon: Shield,
    title: "Secure",
    description: "Built-in security best practices and encrypted communication channels."
  },
  {
    icon: Globe,
    title: "Cross-Platform",
    description: "One codebase, two platforms. Support both Android and iOS seamlessly."
  },
  {
    icon: Zap,
    title: "WebView Optimized",
    description: "High-performance WebView with native bridge for smooth user experience."
  }
];

const steps = [
  { num: "01", title: "Submit URL", desc: "Enter your web app URL" },
  { num: "02", title: "Configure", desc: "Select native features" },
  { num: "03", title: "Generate", desc: "Get native project files" },
  { num: "04", title: "Publish", desc: "Deploy to app stores" },
];

export const LandingPage = () => {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-hidden">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-3" data-testid="nav-logo">
            <div className="w-10 h-10 rounded-md bg-primary/20 border border-primary flex items-center justify-center">
              <Zap className="w-5 h-5 text-primary" />
            </div>
            <span className="font-heading font-bold text-xl">NativiWeb</span>
          </Link>
          
          <div className="flex items-center gap-4">
            <Link to="/login">
              <Button variant="ghost" className="text-muted-foreground hover:text-white" data-testid="nav-login">
                Login
              </Button>
            </Link>
            <Link to="/register">
              <Button className="bg-primary text-black font-bold hover:bg-primary-hover" data-testid="nav-register">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-20 px-6">
        {/* Grid background */}
        <div className="absolute inset-0 grid-texture opacity-30"></div>
        
        {/* Glow effects */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/20 rounded-full blur-[128px]"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-secondary/20 rounded-full blur-[128px]"></div>
        
        <div className="max-w-7xl mx-auto relative">
          <div className="text-center max-w-4xl mx-auto">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-primary/30 bg-primary/5 mb-8">
              <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
              <span className="text-sm text-primary font-medium">Transform Web to Native</span>
            </div>
            
            <h1 className="font-heading font-black text-5xl sm:text-6xl lg:text-7xl leading-tight mb-6" data-testid="hero-title">
              Turn Your <span className="text-primary">Web App</span> Into a
              <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">
                Native Experience
              </span>
            </h1>
            
            <p className="text-lg text-muted-foreground max-w-2xl mx-auto mb-10">
              NativiWeb Studio generates native Android and iOS projects from your existing web application. 
              Access device features through our JavaScript SDK without writing native code.
            </p>
            
            <div className="flex items-center justify-center gap-4">
              <Link to="/register">
                <Button 
                  size="lg" 
                  className="bg-primary text-black font-bold px-8 py-6 text-lg hover:shadow-neon transition-all"
                  data-testid="hero-cta"
                >
                  Start Building Free
                  <ArrowRight className="ml-2 w-5 h-5" />
                </Button>
              </Link>
              <Link to="/docs">
                <Button 
                  size="lg" 
                  variant="outline" 
                  className="border-white/20 px-8 py-6 text-lg hover:bg-white/5"
                  data-testid="hero-docs"
                >
                  <Github className="mr-2 w-5 h-5" />
                  View Docs
                </Button>
              </Link>
            </div>
          </div>
          
          {/* Hero image/preview */}
          <div className="mt-20 relative">
            <div className="absolute -inset-4 bg-gradient-to-r from-primary/20 to-secondary/20 rounded-lg blur-xl"></div>
            <div className="relative bg-background-paper border border-white/10 rounded-lg overflow-hidden">
              <div className="h-8 bg-background-subtle border-b border-white/10 flex items-center gap-2 px-4">
                <div className="w-3 h-3 rounded-full bg-destructive/80"></div>
                <div className="w-3 h-3 rounded-full bg-warning/80"></div>
                <div className="w-3 h-3 rounded-full bg-success/80"></div>
                <span className="text-xs text-muted-foreground ml-4">NativiWeb Studio Dashboard</span>
              </div>
              <div className="p-8 grid grid-cols-3 gap-4">
                <div className="col-span-2 bg-background-subtle rounded-md p-6 border border-white/5">
                  <div className="h-4 w-32 bg-white/10 rounded mb-4"></div>
                  <div className="space-y-2">
                    <div className="h-3 w-full bg-white/5 rounded"></div>
                    <div className="h-3 w-3/4 bg-white/5 rounded"></div>
                  </div>
                </div>
                <div className="space-y-4">
                  <div className="bg-primary/10 border border-primary/30 rounded-md p-4">
                    <div className="h-3 w-16 bg-primary/30 rounded mb-2"></div>
                    <div className="h-6 w-12 bg-primary/50 rounded"></div>
                  </div>
                  <div className="bg-secondary/10 border border-secondary/30 rounded-md p-4">
                    <div className="h-3 w-16 bg-secondary/30 rounded mb-2"></div>
                    <div className="h-6 w-12 bg-secondary/50 rounded"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading font-bold text-3xl sm:text-4xl mb-4">How It Works</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Four simple steps to transform your web app into a native mobile application.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {steps.map((step, idx) => (
              <div key={step.num} className="relative group" data-testid={`step-${idx + 1}`}>
                {idx < steps.length - 1 && (
                  <div className="hidden md:block absolute top-8 left-1/2 w-full h-px bg-gradient-to-r from-primary/50 to-transparent"></div>
                )}
                <div className="relative bg-background-paper border border-white/10 rounded-lg p-6 hover:border-primary/30 transition-colors">
                  <span className="font-mono text-4xl font-bold text-primary/30 group-hover:text-primary/50 transition-colors">
                    {step.num}
                  </span>
                  <h3 className="font-heading font-bold text-xl mt-4 mb-2">{step.title}</h3>
                  <p className="text-sm text-muted-foreground">{step.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-6 bg-background-paper border-t border-b border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="font-heading font-bold text-3xl sm:text-4xl mb-4">Powerful Features</h2>
            <p className="text-muted-foreground max-w-xl mx-auto">
              Everything you need to bridge your web app with native device capabilities.
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, idx) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={feature.title}
                  className="group bg-background border border-white/10 rounded-lg p-6 hover:border-primary/30 transition-all duration-300"
                  data-testid={`feature-${idx}`}
                >
                  <div className="w-12 h-12 rounded-md bg-primary/10 border border-primary/30 flex items-center justify-center mb-4 group-hover:shadow-neon transition-shadow">
                    <Icon className="w-6 h-6 text-primary" />
                  </div>
                  <h3 className="font-heading font-bold text-lg mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Native Features List */}
      <section className="py-20 px-6">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 className="font-heading font-bold text-3xl sm:text-4xl mb-6">
                Access All <span className="text-primary">Native Features</span>
              </h2>
              <p className="text-muted-foreground mb-8">
                Our SDK provides seamless access to device capabilities that are typically only available to native applications.
              </p>
              
              <div className="grid grid-cols-2 gap-4">
                {[
                  "Push Notifications",
                  "Camera Access",
                  "GPS Location",
                  "Biometric Auth",
                  "Local Storage",
                  "File System",
                  "Contacts",
                  "Haptic Feedback",
                  "Deep Links",
                  "App Badge",
                  "Native Share",
                  "Clipboard"
                ].map((feature) => (
                  <div key={feature} className="flex items-center gap-2">
                    <CheckCircle2 className="w-5 h-5 text-success" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="relative">
              <div className="absolute -inset-4 bg-gradient-to-br from-primary/10 to-secondary/10 rounded-xl blur-2xl"></div>
              <div className="relative bg-background-paper border border-white/10 rounded-lg p-6 font-mono text-sm">
                <div className="text-muted-foreground mb-4">// Initialize NativiWeb SDK</div>
                <div><span className="text-secondary">const</span> nw = <span className="text-primary">NativiWeb</span>;</div>
                <br />
                <div className="text-muted-foreground">// Get user location</div>
                <div><span className="text-secondary">const</span> position = <span className="text-secondary">await</span> nw.<span className="text-primary">getCurrentPosition</span>();</div>
                <br />
                <div className="text-muted-foreground">// Show notification</div>
                <div><span className="text-secondary">await</span> nw.<span className="text-primary">showNotification</span>(</div>
                <div className="pl-4"><span className="text-success">"Hello!"</span>,</div>
                <div className="pl-4">{"{ "}<span className="text-primary">body</span>: <span className="text-success">"Welcome to NativiWeb"</span>{" }"}</div>
                <div>);</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="font-heading font-bold text-3xl sm:text-4xl mb-6">
            Ready to Go Native?
          </h2>
          <p className="text-muted-foreground mb-8 max-w-xl mx-auto">
            Start transforming your web application into native Android and iOS apps today.
            No credit card required.
          </p>
          <Link to="/register">
            <Button 
              size="lg" 
              className="bg-primary text-black font-bold px-8 py-6 text-lg hover:shadow-neon transition-all"
              data-testid="cta-btn"
            >
              Get Started Free
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/10">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-primary" />
            <span className="font-heading font-bold">NativiWeb Studio</span>
          </div>
          <p className="text-sm text-muted-foreground">
            © 2024 NativiWeb. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
