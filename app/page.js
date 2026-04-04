'use client';
import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { createClient } from '@supabase/supabase-js';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import Footer from '@/components/Footer';
import {
  FileSpreadsheet, Upload, Zap, Shield, ArrowRight, Check, X, Loader2,
  Download, Trash2, Eye, History, CreditCard, LogOut, Menu,
  FileText, Image, ChevronRight, LayoutDashboard, Clock, Edit3,
  Plus, Minus, RefreshCw, FileDown, BarChart3, Sparkles, ChevronDown
} from 'lucide-react';

// Lazy initialize Supabase browser client (only at runtime, not during build)
let supabaseInstance = null;
const getSupabase = () => {
  if (supabaseInstance) return supabaseInstance;
  if (typeof window === 'undefined') return null; // SSR/build time safety
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    console.warn('Supabase credentials not configured');
    return null;
  }
  supabaseInstance = createClient(url, key);
  return supabaseInstance;
};

const API_BASE = '/api';

// Helper: API call with Supabase auth token (with token refresh)
const apiFetch = async (url, options = {}) => {
  const supabase = getSupabase();
  const session = supabase ? (await supabase.auth.getSession())?.data?.session : null;
  const token = session?.access_token;
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';
  const response = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (response.status === 401) {
    window.dispatchEvent(new CustomEvent('auth:expired'));
  }
  return response;
};

// ============= REQUIREMENTS FIELD =============
const RequirementsField = ({ value, onChange }) => (
  <div className="space-y-2">
    <Label htmlFor="requirements" className="text-sm font-medium">
      What should we extract? <span className="text-muted-foreground font-normal">(optional)</span>
    </Label>
    <textarea
      id="requirements"
      className="flex w-full rounded-md border border-input bg-transparent px-3 py-2 text-sm shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring resize-none"
      placeholder="e.g. Extract all transactions above ₹1000 with GST breakdown, or get invoice line items grouped by category"
      rows={2}
      value={value}
      onChange={e => onChange(e.target.value)}
      maxLength={500}
    />
    <p className="text-xs text-muted-foreground">{value.length}/500 — Describe what matters to you and the AI will prioritize those fields</p>
  </div>
);

// ============= LANDING PAGE =============
const LandingPage = ({ onGetStarted }) => (
  <div className="min-h-screen bg-background">
    <nav className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <FileSpreadsheet className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-foreground">DocXL AI</span>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors hidden sm:inline">Privacy</Link>
            <Link href="/contact" className="text-sm text-muted-foreground hover:text-foreground transition-colors hidden sm:inline">Contact</Link>
            <Button variant="ghost" onClick={() => onGetStarted('login')}>Sign In</Button>
            <Button onClick={() => onGetStarted('register')}>Get Started Free</Button>
          </div>
        </div>
      </div>
    </nav>

    <section className="py-20 lg:py-32">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <Badge variant="secondary" className="mb-6 px-4 py-1.5 text-sm">
          <Sparkles className="w-4 h-4 mr-1" /> AI-Powered Document Processing
        </Badge>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground tracking-tight mb-6">
          Transform Documents to<br />
          <span className="text-primary">Structured Excel</span> in Seconds
        </h1>
        <p className="text-lg sm:text-xl text-muted-foreground max-w-2xl mx-auto mb-10">
          Upload PDFs, invoices, bank statements, or screenshots. Our AI extracts clean,
          structured data you can edit and download as Excel instantly.
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Button size="lg" className="text-lg px-8 py-6" onClick={() => onGetStarted('register')}>
            Start Free <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
          <Button size="lg" variant="outline" className="text-lg px-8 py-6" onClick={() => onGetStarted('login')}>
            Sign In
          </Button>
        </div>
        <p className="mt-4 text-sm text-muted-foreground">5 free extractions. No credit card required.</p>
      </div>
    </section>

    <section id="how-it-works" className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-center mb-4">How It Works</h2>
        <p className="text-muted-foreground text-center mb-12 max-w-xl mx-auto">Three simple steps to convert any document into structured data</p>
        <div className="grid md:grid-cols-3 gap-8">
          {[
            { icon: Upload, title: 'Upload Document', desc: 'Drop your PDF, invoice, bank statement, or image. We support JPG, PNG, and PDF.', step: '01' },
            { icon: Zap, title: 'AI Extracts Data', desc: 'Our AI analyzes the document, identifies tables, and extracts every data point accurately.', step: '02' },
            { icon: FileSpreadsheet, title: 'Download Excel', desc: 'Review, edit the extracted data, then download as a perfectly formatted Excel file.', step: '03' },
          ].map((item, i) => (
            <Card key={i} className="relative overflow-hidden border-0 shadow-lg hover:shadow-xl transition-shadow">
              <div className="absolute top-4 right-4 text-6xl font-bold text-primary/5">{item.step}</div>
              <CardHeader>
                <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center mb-4">
                  <item.icon className="w-6 h-6 text-primary" />
                </div>
                <CardTitle className="text-xl">{item.title}</CardTitle>
              </CardHeader>
              <CardContent><p className="text-muted-foreground">{item.desc}</p></CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>

    <section className="py-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-center mb-12">Built for Financial Documents</h2>
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {[
            { icon: FileText, title: 'PDF Invoices', desc: 'Extract line items, totals, tax details from any invoice format' },
            { icon: CreditCard, title: 'Bank Statements', desc: 'Parse transactions, dates, amounts, and categories automatically' },
            { icon: Image, title: 'Screenshots & Images', desc: 'Capture data from table screenshots and receipts' },
            { icon: Shield, title: 'Secure Processing', desc: 'Files are encrypted and auto-deleted within 48 hours' },
          ].map((item, i) => (
            <Card key={i} className="border shadow-sm hover:shadow-md transition-shadow">
              <CardContent className="pt-6">
                <item.icon className="w-8 h-8 text-primary mb-3" />
                <h3 className="font-semibold mb-2">{item.title}</h3>
                <p className="text-sm text-muted-foreground">{item.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>

    <section className="py-20 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h2 className="text-3xl font-bold text-center mb-4">Simple Pricing</h2>
        <p className="text-muted-foreground text-center mb-12">Start free, upgrade when you need more</p>
        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          <Card className="border-2">
            <CardHeader>
              <CardTitle>Free</CardTitle>
              <CardDescription>For trying out DocXL AI</CardDescription>
              <div className="text-3xl font-bold mt-4">$0<span className="text-lg font-normal text-muted-foreground">/month</span></div>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {['5 file extractions', 'PDF & Image support', 'Excel download', 'Editable results'].map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
                ))}
              </ul>
              <Button className="w-full mt-6" variant="outline" onClick={() => onGetStarted('register')}>Start Free</Button>
            </CardContent>
          </Card>
          <Card className="border-2 border-primary relative">
            <div className="absolute -top-3 left-1/2 -translate-x-1/2"><Badge className="bg-primary">Most Popular</Badge></div>
            <CardHeader>
              <CardTitle>Pro</CardTitle>
              <CardDescription>For teams and businesses</CardDescription>
              <div className="text-3xl font-bold mt-4">$9<span className="text-lg font-normal text-muted-foreground">/month</span></div>
              <p className="text-sm text-muted-foreground">or &#x20B9;699/month for India</p>
            </CardHeader>
            <CardContent>
              <ul className="space-y-3">
                {['300 files/month', 'Priority AI processing', 'Excel & JSON download', 'Editable results', 'Batch processing', '24/7 Support'].map((f, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
                ))}
              </ul>
              <Button className="w-full mt-6" onClick={() => onGetStarted('register')}>Upgrade to Pro</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </section>

    <Footer />
  </div>
);

// ============= AUTH PAGE (Supabase Auth) =============
const AuthPage = ({ mode, onSwitch, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const handleGoogleAuth = async () => {
    setLoading(true);
    setError('');
    try {
      const supabase = getSupabase();
      if (!supabase) {
        setError('Authentication service not available.');
        return;
      }
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
          redirectTo: `${window.location.origin}/auth/callback`,
          queryParams: {
            access_type: 'offline',
            prompt: 'consent',
          },
        },
      });
      if (error) setError(error.message);
    } catch (err) {
      setError('Google sign-in failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    setMessage('');

    const supabase = getSupabase();
    if (!supabase) {
      setError('Authentication service not available. Please try again.');
      setLoading(false);
      return;
    }

    try {
      if (mode === 'register') {
        const res = await fetch(`${API_BASE}/auth/register`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password, name }),
        });
        const data = await res.json();
        if (!res.ok) { setError(data.error || 'Registration failed'); return; }

        const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
          email: email.toLowerCase(),
          password,
        });

        if (signInError) {
          setMessage('Account created! Please sign in.');
          onSwitch();
          return;
        }

        const meRes = await fetch(`${API_BASE}/auth/me`, {
          headers: { 'Authorization': `Bearer ${signInData.session.access_token}` },
        });
        const meData = await meRes.json();
        onSuccess(meData.user || data.user, signInData.session);
      } else {
        const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({
          email: email.toLowerCase(),
          password,
        });

        if (signInError) {
          setError('Invalid credentials');
          return;
        }

        const meRes = await fetch(`${API_BASE}/auth/me`, {
          headers: { 'Authorization': `Bearer ${signInData.session.access_token}` },
        });
        const meData = await meRes.json();
        if (meRes.ok) {
          onSuccess(meData.user, signInData.session);
        } else {
          setError('Failed to load profile');
        }
      }
    } catch (err) {
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
            <FileSpreadsheet className="w-6 h-6 text-white" />
          </div>
          <span className="text-2xl font-bold">DocXL AI</span>
        </div>
        <Card className="shadow-xl border-0">
          <CardHeader className="text-center">
            <CardTitle className="text-2xl">{mode === 'login' ? 'Welcome Back' : 'Create Account'}</CardTitle>
            <CardDescription>{mode === 'login' ? 'Sign in to your account' : 'Start extracting data in seconds'}</CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              type="button"
              variant="outline"
              className="w-full flex items-center gap-3 h-11"
              onClick={handleGoogleAuth}
              disabled={loading}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Continue with Google
            </Button>

            <div className="relative my-4">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">Or continue with email</span>
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              {mode === 'register' && (
                <div>
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" placeholder="Your name" value={name} onChange={e => setName(e.target.value)} className="mt-1" />
                </div>
              )}
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" type="email" placeholder="you@example.com" required value={email} onChange={e => setEmail(e.target.value)} className="mt-1" />
              </div>
              <div>
                <Label htmlFor="password">Password</Label>
                <Input id="password" type="password" placeholder="Min 6 characters" required minLength={6} value={password} onChange={e => setPassword(e.target.value)} className="mt-1" />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              {message && <p className="text-sm text-green-600">{message}</p>}
              <Button type="submit" className="w-full" disabled={loading}>
                {loading ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
                {mode === 'login' ? 'Sign In' : 'Create Account'}
              </Button>
            </form>
            <Separator className="my-6" />
            <p className="text-center text-sm text-muted-foreground">
              {mode === 'login' ? "Don't have an account? " : 'Already have an account? '}
              <button className="text-primary font-medium hover:underline" onClick={onSwitch}>
                {mode === 'login' ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============= SIDEBAR =============
const Sidebar = ({ user, currentView, onNavigate, onLogout, collapsed, onToggle }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'upload', label: 'Upload', icon: Upload },
    { id: 'history', label: 'History', icon: History },
    { id: 'pricing', label: 'Pricing', icon: CreditCard },
  ];

  return (
    <div className={`bg-white border-r h-screen flex flex-col transition-all duration-300 overflow-hidden flex-shrink-0 ${collapsed ? 'w-16' : 'w-64'}`}>
      <div className="p-4 flex items-center gap-2 border-b flex-shrink-0">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
          <FileSpreadsheet className="w-5 h-5 text-white" />
        </div>
        {!collapsed && <span className="font-bold text-lg whitespace-nowrap">DocXL AI</span>}
        <button onClick={onToggle} className="ml-auto p-1 hover:bg-muted rounded flex-shrink-0"><Menu className="w-4 h-4" /></button>
      </div>
      <nav className="flex-1 p-2 space-y-1 overflow-hidden">
        {navItems.map(item => (
          <button key={item.id} onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors overflow-hidden
              ${currentView === item.id ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}>
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span className="whitespace-nowrap">{item.label}</span>}
          </button>
        ))}
      </nav>
      <div className="p-3 border-t flex-shrink-0 overflow-hidden">
        {!collapsed && user && (
          <div className="mb-3 px-3">
            <p className="text-sm font-medium truncate">{user.name || user.email}</p>
            <div className="flex items-center gap-2 mt-1">
              <Badge variant={user.plan === 'pro' ? 'default' : 'secondary'} className="text-xs">
                {user.plan === 'pro' ? 'PRO' : 'FREE'}
              </Badge>
              <span className="text-xs text-muted-foreground">{user.credits_remaining} credits</span>
            </div>
          </div>
        )}
        <button onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors overflow-hidden">
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span className="whitespace-nowrap">Sign Out</span>}
        </button>
      </div>
    </div>
  );
};

// ============= UPLOAD BOX =============
const UploadBox = ({ onUploadComplete, disabled }) => {
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState('');
  const inputRef = useRef(null);

  const handleFile = async (file) => {
    if (!file) return;
    const validExts = ['.pdf', '.jpg', '.jpeg', '.png', '.webp'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();
    if (!validExts.includes(ext)) { setError('Invalid file type. Supported: PDF, JPG, PNG, WEBP'); return; }
    if (file.size > 100 * 1024 * 1024) { setError('File too large. Maximum 100MB.'); return; }
    setError('');
    setUploading(true);
    setUploadProgress(30);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiFetch('/upload', { method: 'POST', body: formData });
      setUploadProgress(80);
      const data = await res.json();
      if (!res.ok) { setError(data.error || 'Upload failed'); return; }
      setUploadProgress(100);
      setTimeout(() => onUploadComplete(data.upload), 500);
    } catch (err) {
      setError('Upload failed. Please try again.');
    } finally {
      setTimeout(() => { setUploading(false); setUploadProgress(0); }, 1000);
    }
  };

  return (
    <Card className="border-2 border-dashed hover:border-primary/50 transition-colors">
      <CardContent className="pt-6">
        <div className={`flex flex-col items-center justify-center py-12 px-6 rounded-xl cursor-pointer transition-colors
            ${dragActive ? 'bg-primary/5 border-primary' : 'hover:bg-muted/50'}
            ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => { e.preventDefault(); setDragActive(false); handleFile(e.dataTransfer.files[0]); }}
          onClick={() => inputRef.current?.click()}>
          <input ref={inputRef} type="file" className="hidden" accept=".pdf,.jpg,.jpeg,.png,.webp" onChange={(e) => handleFile(e.target.files?.[0])} />
          {uploading ? (
            <div className="w-full max-w-xs space-y-4">
              <Loader2 className="w-10 h-10 text-primary animate-spin mx-auto" />
              <p className="text-sm text-center font-medium">Uploading...</p>
              <Progress value={uploadProgress} className="h-2" />
            </div>
          ) : (
            <>
              <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mb-4">
                <Upload className="w-8 h-8 text-primary" />
              </div>
              <p className="text-lg font-medium mb-1">Drop your document here</p>
              <p className="text-sm text-muted-foreground mb-4">or click to browse files</p>
              <div className="flex gap-2">
                {['PDF', 'JPG', 'PNG'].map(t => (<Badge key={t} variant="secondary" className="text-xs">{t}</Badge>))}
              </div>
              <p className="text-xs text-muted-foreground mt-3">Max file size: 100MB</p>
            </>
          )}
        </div>
        {error && <p className="text-sm text-destructive mt-3 text-center">{error}</p>}
      </CardContent>
    </Card>
  );
};

// ============= PROCESSING VIEW =============
const ProcessingView = ({ upload, onComplete, onError }) => {
  const [step, setStep] = useState(0);
  const [error, setError] = useState('');
  const steps = [
    { label: 'Upload Complete', desc: 'File received and stored securely' },
    { label: 'Extracting Data', desc: 'AI is analyzing your document...' },
    { label: 'Structuring Output', desc: 'Organizing data into rows and columns' },
  ];

  useEffect(() => {
    let cancelled = false;
    const process = async () => {
      setStep(0);
      await new Promise(r => setTimeout(r, 800));
      if (cancelled) return;
      setStep(1);
      try {
        const res = await apiFetch('/process', {
          method: 'POST',
          body: JSON.stringify({
            upload_id: upload.id,
            user_requirements: upload.userRequirements || '',
          }),
        });
        const data = await res.json();
        if (!res.ok) { setError(data.error || 'Processing failed'); if (onError) onError(data.error); return; }
        if (cancelled) return;
        setStep(2);
        await new Promise(r => setTimeout(r, 1000));
        if (cancelled) return;
        onComplete(data.result);
      } catch (err) {
        setError('Processing failed. Please try again.');
        if (onError) onError(err.message);
      }
    };
    process();
    return () => { cancelled = true; };
  }, [upload?.id]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Card className="w-full max-w-lg shadow-xl border-0">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-primary animate-pulse" />
          </div>
          <CardTitle className="text-2xl">Processing Document</CardTitle>
          <CardDescription>{upload?.file_name}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {steps.map((s, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 transition-all duration-500
                ${i < step ? 'bg-green-500 text-white' : i === step ? 'bg-primary text-white animate-pulse' : 'bg-muted text-muted-foreground'}`}>
                {i < step ? <Check className="w-4 h-4" /> : i === step ? <Loader2 className="w-4 h-4 animate-spin" /> : <span className="text-xs">{i + 1}</span>}
              </div>
              <div>
                <p className={`font-medium ${i <= step ? 'text-foreground' : 'text-muted-foreground'}`}>{s.label}</p>
                <p className="text-sm text-muted-foreground">{s.desc}</p>
              </div>
            </div>
          ))}
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
              <p className="text-sm text-destructive font-medium">{error}</p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

// ============= EDITABLE DATA TABLE =============
const CONFIDENCE_THRESHOLD_LOW = 0.50;
const CONFIDENCE_THRESHOLD_MED = 0.75;

const ConfidenceBadge = ({ score }) => {
  if (score === undefined || score === null) return null;
  if (score < CONFIDENCE_THRESHOLD_LOW) return (
    <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-red-100 text-red-700 font-medium">
      <span className="w-1.5 h-1.5 rounded-full bg-red-500 inline-block"/>Low
    </span>
  );
  if (score < CONFIDENCE_THRESHOLD_MED) return (
    <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700 font-medium">
      <span className="w-1.5 h-1.5 rounded-full bg-yellow-500 inline-block"/>Med
    </span>
  );
  return (
    <span className="inline-flex items-center gap-1 text-xs px-1.5 py-0.5 rounded bg-green-100 text-green-700 font-medium">
      <span className="w-1.5 h-1.5 rounded-full bg-green-500 inline-block"/>OK
    </span>
  );
};

const EditableCell = ({ value, onChange, type = 'text', className = '' }) => {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(String(value ?? ''));
  const inputRef = useRef(null);

  useEffect(() => { setDraft(String(value ?? '')); }, [value]);
  useEffect(() => { if (editing && inputRef.current) inputRef.current.focus(); }, [editing]);

  const commit = () => {
    setEditing(false);
    let finalVal = draft;
    if (type === 'number') {
      const n = parseFloat(draft.replace(/[^\d.]/g, ''));
      finalVal = isNaN(n) ? 0 : n;
    }
    onChange(finalVal);
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') commit();
    if (e.key === 'Escape') { setDraft(String(value ?? '')); setEditing(false); }
    if (e.key === 'Tab') commit();
  };

  if (editing) return (
    <input
      ref={inputRef}
      className={`w-full px-2 py-1 text-sm border border-primary rounded focus:outline-none focus:ring-1 focus:ring-primary bg-background ${className}`}
      value={draft}
      onChange={e => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={handleKey}
      type={type === 'number' ? 'number' : 'text'}
      step={type === 'number' ? '0.01' : undefined}
    />
  );

  return (
    <div
      className={`px-2 py-1 text-sm cursor-pointer rounded hover:bg-primary/5 min-h-[28px] flex items-center group ${className}`}
      onClick={() => setEditing(true)}
      title="Click to edit"
    >
      <span className={`flex-1 ${!value && value !== 0 ? 'text-muted-foreground italic' : ''}`}>
        {type === 'number' ? (parseFloat(value) || 0).toFixed(2) : (value || '\u2014')}
      </span>
      <Edit3 className="w-3 h-3 text-muted-foreground opacity-0 group-hover:opacity-60 ml-1 flex-shrink-0" />
    </div>
  );
};

const TypeSelect = ({ value, onChange }) => {
  const options = ['debit', 'credit', 'expense', 'income'];
  const colors = { debit: 'text-red-600', credit: 'text-green-600', expense: 'text-orange-600', income: 'text-blue-600' };
  return (
    <select
      className={`text-xs px-1 py-1 rounded border border-input bg-background cursor-pointer focus:outline-none focus:ring-1 focus:ring-primary ${colors[value] || ''}`}
      value={value || 'debit'}
      onChange={e => onChange(e.target.value)}
    >
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
};

const DataTable = ({ data, onUpdate }) => {
  const [rows, setRows] = useState([]);
  const [sortConfig, setSortConfig] = useState({ key: null, dir: 'asc' });
  const [filterLowConf, setFilterLowConf] = useState(false);

  useEffect(() => {
    const incoming = (data?.rows || []).map((r, i) => ({ ...r, _id: i + '_' + Date.now() }));
    setRows(incoming);
  }, [data]);

  const updateRow = (index, field, value) => {
    setRows(prev => {
      const updated = [...prev];
      updated[index] = { ...updated[index], [field]: value };
      if (onUpdate) onUpdate(updated.map(({ _id, ...rest }) => rest));
      return updated;
    });
  };

  const addRow = () => {
    const newRow = {
      _id: 'new_' + Date.now(),
      row_number: rows.length + 1,
      date: '',
      description: '',
      amount: 0,
      type: 'debit',
      category: '',
      gst: 0,
      reference: '',
      confidence: 1.0,
    };
    setRows(prev => {
      const updated = [...prev, newRow];
      if (onUpdate) onUpdate(updated.map(({ _id, ...rest }) => rest));
      return updated;
    });
  };

  const deleteRow = (index) => {
    setRows(prev => {
      const updated = prev.filter((_, i) => i !== index);
      if (onUpdate) onUpdate(updated.map(({ _id, ...rest }) => rest));
      return updated;
    });
  };

  const duplicateRow = (index) => {
    setRows(prev => {
      const row = { ...prev[index], _id: 'dup_' + Date.now() };
      const updated = [...prev.slice(0, index + 1), row, ...prev.slice(index + 1)];
      if (onUpdate) onUpdate(updated.map(({ _id, ...rest }) => rest));
      return updated;
    });
  };

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      dir: prev.key === key && prev.dir === 'asc' ? 'desc' : 'asc'
    }));
  };

  const displayRows = [...rows]
    .filter(r => !filterLowConf || (r.confidence ?? 1) < CONFIDENCE_THRESHOLD_MED)
    .sort((a, b) => {
      if (!sortConfig.key) return 0;
      const av = a[sortConfig.key], bv = b[sortConfig.key];
      const cmp = typeof av === 'number' ? av - bv : String(av || '').localeCompare(String(bv || ''));
      return sortConfig.dir === 'asc' ? cmp : -cmp;
    });

  const lowConfCount = rows.filter(r => (r.confidence ?? 1) < CONFIDENCE_THRESHOLD_MED).length;

  const SortHeader = ({ col, label, className = '' }) => (
    <div
      className={`flex items-center gap-1 cursor-pointer select-none hover:text-foreground ${className}`}
      onClick={() => handleSort(col)}
    >
      {label}
      {sortConfig.key === col && <span className="text-xs">{sortConfig.dir === 'asc' ? '\u2191' : '\u2193'}</span>}
    </div>
  );

  return (
    <div className="space-y-3">
      {/* Toolbar */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          {lowConfCount > 0 && (
            <button
              onClick={() => setFilterLowConf(!filterLowConf)}
              className={`text-xs px-3 py-1.5 rounded-md border transition-colors ${filterLowConf ? 'bg-yellow-100 border-yellow-300 text-yellow-800' : 'border-input text-muted-foreground hover:bg-muted'}`}
            >
              {filterLowConf ? `Showing ${lowConfCount} low-confidence rows` : `\u26A0 ${lowConfCount} rows need review`}
            </button>
          )}
          {filterLowConf && (
            <button onClick={() => setFilterLowConf(false)} className="text-xs text-muted-foreground hover:text-foreground">
              Show all
            </button>
          )}
        </div>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-400 inline-block"/>Low confidence</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-yellow-400 inline-block"/>Medium</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-400 inline-block"/>High</span>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-lg border">
        <table className="w-full min-w-[900px] border-collapse">
          <thead>
            <tr className="bg-primary text-primary-foreground text-xs">
              <th className="w-8 px-2 py-3 text-center font-medium">#</th>
              <th className="px-2 py-3 text-left font-medium min-w-[100px]"><SortHeader col="date" label="Date"/></th>
              <th className="px-2 py-3 text-left font-medium min-w-[200px]"><SortHeader col="description" label="Description"/></th>
              <th className="px-2 py-3 text-right font-medium min-w-[100px]"><SortHeader col="amount" label="Amount"/></th>
              <th className="px-2 py-3 text-left font-medium w-24">Type</th>
              <th className="px-2 py-3 text-left font-medium min-w-[100px]">Category</th>
              <th className="px-2 py-3 text-right font-medium w-20"><SortHeader col="gst" label="GST"/></th>
              <th className="px-2 py-3 text-left font-medium w-24">Ref</th>
              <th className="px-2 py-3 text-center font-medium w-16">Score</th>
              <th className="px-2 py-3 w-20"></th>
            </tr>
          </thead>
          <tbody>
            {displayRows.length === 0 ? (
              <tr><td colSpan={10} className="py-12 text-center text-muted-foreground text-sm">No data rows. Click &quot;Add Row&quot; to start.</td></tr>
            ) : displayRows.map((row, visIdx) => {
              const realIndex = rows.findIndex(r => r._id === row._id);
              const conf = row.confidence ?? 1;
              const rowBg = conf < CONFIDENCE_THRESHOLD_LOW
                ? 'bg-red-50/60 hover:bg-red-50'
                : conf < CONFIDENCE_THRESHOLD_MED
                  ? 'bg-yellow-50/40 hover:bg-yellow-50/60'
                  : 'hover:bg-muted/30';
              return (
                <tr key={row._id} className={`border-b transition-colors group ${rowBg}`}>
                  <td className="px-2 py-1 text-xs text-muted-foreground text-center">{visIdx + 1}</td>
                  <td className="px-0 py-1">
                    <EditableCell value={row.date} onChange={v => updateRow(realIndex, 'date', v)} />
                  </td>
                  <td className="px-0 py-1">
                    <EditableCell value={row.description} onChange={v => updateRow(realIndex, 'description', v)} />
                  </td>
                  <td className="px-0 py-1">
                    <EditableCell value={row.amount} type="number" onChange={v => updateRow(realIndex, 'amount', v)} className="text-right" />
                  </td>
                  <td className="px-2 py-1">
                    <TypeSelect value={row.type} onChange={v => updateRow(realIndex, 'type', v)} />
                  </td>
                  <td className="px-0 py-1">
                    <EditableCell value={row.category} onChange={v => updateRow(realIndex, 'category', v)} />
                  </td>
                  <td className="px-0 py-1">
                    <EditableCell value={row.gst} type="number" onChange={v => updateRow(realIndex, 'gst', v)} className="text-right" />
                  </td>
                  <td className="px-0 py-1">
                    <EditableCell value={row.reference} onChange={v => updateRow(realIndex, 'reference', v)} />
                  </td>
                  <td className="px-2 py-1 text-center">
                    <ConfidenceBadge score={conf} />
                  </td>
                  <td className="px-2 py-1">
                    <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <button
                        onClick={() => duplicateRow(realIndex)}
                        className="p-1 hover:bg-blue-100 rounded"
                        title="Duplicate row"
                      >
                        <Plus className="w-3 h-3 text-blue-500" />
                      </button>
                      <button
                        onClick={() => deleteRow(realIndex)}
                        className="p-1 hover:bg-red-100 rounded"
                        title="Delete row"
                      >
                        <Trash2 className="w-3 h-3 text-destructive" />
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
          {displayRows.length > 0 && (
            <tfoot>
              <tr className="border-t bg-muted/50">
                <td colSpan={3} className="px-4 py-2 text-xs font-medium text-right text-muted-foreground">Totals:</td>
                <td className="px-2 py-2 text-xs font-semibold text-right">
                  {displayRows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0).toFixed(2)}
                </td>
                <td/>
                <td/>
                <td className="px-2 py-2 text-xs font-semibold text-right">
                  {displayRows.reduce((s, r) => s + (parseFloat(r.gst) || 0), 0).toFixed(2)}
                </td>
                <td colSpan={3}/>
              </tr>
            </tfoot>
          )}
        </table>
      </div>

      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={addRow}>
          <Plus className="w-4 h-4 mr-1" /> Add Row
        </Button>
        <p className="text-xs text-muted-foreground">
          Click any cell to edit &middot; Tab/Enter to confirm &middot; Esc to cancel
        </p>
      </div>
    </div>
  );
};

// ============= RESULT VIEW =============
const ResultView = ({ result, onBack }) => {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [currentRows, setCurrentRows] = useState(result?.rows || []);

  const handleUpdate = (newRows) => { setCurrentRows(newRows); setSaved(false); };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await apiFetch(`/result/${result.upload_id}`, { method: 'PUT', body: JSON.stringify({ rows: currentRows }) });
      if (res.ok) { setSaved(true); setTimeout(() => setSaved(false), 3000); }
    } catch (err) { console.error('Save failed:', err); }
    finally { setSaving(false); }
  };

  const handleExportExcel = async () => {
    try {
      // Save current edits first
      await handleSave();
      const res = await apiFetch(`/export/excel/${result.upload_id}`);
      if (!res.ok) throw new Error('Export failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `docxl_export_${Date.now()}.xlsx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export error:', err);
    }
  };

  const handleExportJSON = () => {
    const json = JSON.stringify({ rows: currentRows, summary: result.summary }, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob); const a = document.createElement('a'); a.href = url; a.download = `docxl_export_${Date.now()}.json`; a.click(); URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold">Extraction Results</h2>
          <p className="text-muted-foreground mt-1">
            {result?.file_name || 'Document'} &bull; {currentRows.length} rows extracted
            {result?.document_type && <Badge variant="secondary" className="ml-2">{result.document_type}</Badge>}
          </p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={onBack}><ChevronRight className="w-4 h-4 mr-1 rotate-180" /> Back</Button>
          <Button variant="outline" size="sm" onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : saved ? <Check className="w-4 h-4 mr-1 text-green-500" /> : <Edit3 className="w-4 h-4 mr-1" />}
            {saved ? 'Saved!' : 'Save Changes'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportJSON}><FileDown className="w-4 h-4 mr-1" /> JSON</Button>
          <Button size="sm" onClick={handleExportExcel}><Download className="w-4 h-4 mr-1" /> Download Excel</Button>
        </div>
      </div>
      {result?.summary && (
        <div className="grid grid-cols-3 gap-4">
          <Card><CardContent className="pt-4 pb-4"><p className="text-sm text-muted-foreground">Total Rows</p><p className="text-2xl font-bold">{currentRows.length}</p></CardContent></Card>
          <Card><CardContent className="pt-4 pb-4"><p className="text-sm text-muted-foreground">Total Amount</p><p className="text-2xl font-bold">{currentRows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0).toFixed(2)}</p></CardContent></Card>
          <Card><CardContent className="pt-4 pb-4"><p className="text-sm text-muted-foreground">Confidence</p><p className="text-2xl font-bold">{((result.confidence_score || 0.85) * 100).toFixed(0)}%</p></CardContent></Card>
        </div>
      )}
      <Card><CardContent className="pt-6"><DataTable data={{ rows: currentRows }} onUpdate={handleUpdate} /></CardContent></Card>
      <p className="text-xs text-muted-foreground text-center">Click any cell to edit. Changes are saved when you click &quot;Save Changes&quot;.</p>
    </div>
  );
};

// ============= DASHBOARD VIEW =============
const DashboardView = ({ user, onUploadComplete, uploads, onViewResult, onRefresh, userRequirements, onRequirementsChange }) => (
  <div className="space-y-8 animate-fade-in">
    <div>
      <h1 className="text-3xl font-bold">Welcome, {user?.name || 'there'}!</h1>
      <p className="text-muted-foreground mt-1">Upload a document to get started</p>
    </div>
    <div className="grid grid-cols-3 gap-4">
      <Card><CardContent className="pt-4 pb-4"><div className="flex items-center gap-3"><div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center"><BarChart3 className="w-5 h-5 text-primary" /></div><div><p className="text-sm text-muted-foreground">Credits Left</p><p className="text-xl font-bold">{user?.credits_remaining ?? 0}</p></div></div></CardContent></Card>
      <Card><CardContent className="pt-4 pb-4"><div className="flex items-center gap-3"><div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center"><FileSpreadsheet className="w-5 h-5 text-green-500" /></div><div><p className="text-sm text-muted-foreground">Files Processed</p><p className="text-xl font-bold">{uploads?.filter(u => u.status === 'completed').length || 0}</p></div></div></CardContent></Card>
      <Card><CardContent className="pt-4 pb-4"><div className="flex items-center gap-3"><div className="w-10 h-10 bg-orange-500/10 rounded-lg flex items-center justify-center"><Zap className="w-5 h-5 text-orange-500" /></div><div><p className="text-sm text-muted-foreground">Plan</p><p className="text-xl font-bold capitalize">{user?.plan || 'free'}</p></div></div></CardContent></Card>
    </div>
    <RequirementsField value={userRequirements} onChange={onRequirementsChange} />
    <UploadBox onUploadComplete={onUploadComplete} disabled={(user?.credits_remaining ?? 0) <= 0} />
    {(user?.credits_remaining ?? 0) <= 0 && (
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
        <p className="text-orange-700 font-medium">No credits remaining. Upgrade to Pro for 300 files/month.</p>
      </div>
    )}
    {uploads && uploads.length > 0 && (
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Recent Uploads</h3>
          <Button variant="ghost" size="sm" onClick={onRefresh}><RefreshCw className="w-4 h-4 mr-1" /> Refresh</Button>
        </div>
        <div className="space-y-2">
          {uploads.slice(0, 5).map(upload => (
            <Card key={upload.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => upload.status === 'completed' && onViewResult(upload.id)}>
              <CardContent className="py-3 px-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-muted rounded flex items-center justify-center">
                      {upload.file_type === 'invoice' || upload.file_type === 'bank' ? <FileText className="w-4 h-4" /> : <Image className="w-4 h-4" />}
                    </div>
                    <div>
                      <p className="text-sm font-medium">{upload.file_name}</p>
                      <p className="text-xs text-muted-foreground">{new Date(upload.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge variant={upload.status === 'completed' ? 'default' : upload.status === 'processing' ? 'secondary' : upload.status === 'failed' ? 'destructive' : 'outline'}>{upload.status}</Badge>
                    {upload.status === 'completed' && <ChevronRight className="w-4 h-4 text-muted-foreground" />}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    )}
  </div>
);

// ============= HISTORY VIEW =============
const HistoryView = ({ uploads, onViewResult, onDelete, onRefresh }) => (
  <div className="space-y-6 animate-fade-in">
    <div className="flex items-center justify-between">
      <div><h2 className="text-2xl font-bold">Upload History</h2><p className="text-muted-foreground mt-1">{uploads?.length || 0} total uploads</p></div>
      <Button variant="outline" size="sm" onClick={onRefresh}><RefreshCw className="w-4 h-4 mr-1" /> Refresh</Button>
    </div>
    {(!uploads || uploads.length === 0) ? (
      <Card className="py-16 text-center"><CardContent><History className="w-12 h-12 text-muted-foreground mx-auto mb-4" /><p className="text-muted-foreground">No uploads yet. Upload your first document!</p></CardContent></Card>
    ) : (
      <div className="space-y-2">
        {uploads.map(upload => (
          <Card key={upload.id} className="hover:shadow-md transition-shadow">
            <CardContent className="py-3 px-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-muted rounded-lg flex items-center justify-center">
                    {upload.file_type === 'invoice' || upload.file_type === 'bank' ? <FileText className="w-5 h-5" /> : <Image className="w-5 h-5" />}
                  </div>
                  <div>
                    <p className="font-medium">{upload.file_name}</p>
                    <p className="text-sm text-muted-foreground">{new Date(upload.created_at).toLocaleString()}</p>
                    {upload.error_message && <p className="text-xs text-destructive mt-1">{upload.error_message}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Badge variant={upload.status === 'completed' ? 'default' : upload.status === 'processing' ? 'secondary' : upload.status === 'failed' ? 'destructive' : 'outline'}>{upload.status}</Badge>
                  {upload.status === 'completed' && <Button size="sm" variant="outline" onClick={() => onViewResult(upload.id)}><Eye className="w-4 h-4 mr-1" /> View</Button>}
                  <Button size="sm" variant="ghost" onClick={() => onDelete(upload.id)}><Trash2 className="w-4 h-4 text-muted-foreground" /></Button>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    )}
  </div>
);

// ============= PRICING VIEW =============
const PricingView = ({ user, onUpgrade }) => (
  <div className="space-y-8 animate-fade-in">
    <div className="text-center"><h2 className="text-3xl font-bold">Upgrade Your Plan</h2><p className="text-muted-foreground mt-2">Get more extractions with DocXL Pro</p></div>
    <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
      <Card className={`border-2 ${user?.plan === 'free' ? 'border-primary/30' : ''}`}>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">Free {user?.plan === 'free' && <Badge variant="secondary">Current</Badge>}</CardTitle>
          <div className="text-3xl font-bold mt-4">$0<span className="text-lg font-normal text-muted-foreground">/month</span></div>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {['5 file extractions', 'PDF & Image support', 'Excel & JSON export', 'Editable results'].map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
            ))}
          </ul>
        </CardContent>
      </Card>
      <Card className={`border-2 ${user?.plan === 'pro' ? 'border-primary' : 'border-primary/50'} relative`}>
        <div className="absolute -top-3 left-1/2 -translate-x-1/2"><Badge className="bg-primary">Recommended</Badge></div>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">Pro {user?.plan === 'pro' && <Badge>Active</Badge>}</CardTitle>
          <div className="text-3xl font-bold mt-4">&#x20B9;699<span className="text-lg font-normal text-muted-foreground">/month</span></div>
          <p className="text-sm text-muted-foreground">~$9/month</p>
        </CardHeader>
        <CardContent>
          <ul className="space-y-3">
            {['300 files/month', 'Priority processing', 'All export formats', 'Editable results', 'Batch processing', 'Priority support'].map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
            ))}
          </ul>
          {user?.plan !== 'pro' && (
            <Button className="w-full mt-6" onClick={onUpgrade}>
              Upgrade to Pro — &#x20B9;699/month
            </Button>
          )}
        </CardContent>
      </Card>
    </div>
  </div>
);

// ============= MAIN APP =============
const App = () => {
  const [view, setView] = useState('landing');
  const [authMode, setAuthMode] = useState('login');
  const [user, setUser] = useState(null);
  const [session, setSession] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [currentUpload, setCurrentUpload] = useState(null);
  const [currentResult, setCurrentResult] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);
  const [userRequirements, setUserRequirements] = useState('');

  // Check Supabase auth on mount + load Razorpay
  useEffect(() => {
    // Load Razorpay script
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    document.body.appendChild(script);

    const supabase = getSupabase();
    if (!supabase) {
      setLoading(false);
      return;
    }

    const checkSession = async () => {
      try {
        const { data: { session: existingSession } } = await supabase.auth.getSession();
        if (existingSession) {
          setSession(existingSession);
          const res = await fetch(`${API_BASE}/auth/me`, {
            headers: { 'Authorization': `Bearer ${existingSession.access_token}` },
          });
          if (res.ok) {
            const data = await res.json();
            setUser(data.user);
            setView('dashboard');
            fetchUploads(existingSession.access_token);
          } else {
            await supabase.auth.signOut();
          }
        }
      } catch (err) {
        console.error('Session check error:', err);
      } finally {
        setLoading(false);
      }
    };

    checkSession();

    // Listen for auth state changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(async (event, newSession) => {
      if (event === 'SIGNED_OUT') {
        setUser(null);
        setSession(null);
        setUploads([]);
        setView('landing');
      } else if (event === 'TOKEN_REFRESHED' && newSession) {
        setSession(newSession);
      } else if (event === 'SIGNED_IN' && newSession) {
        setSession(newSession);
        if (!user) {
          try {
            const res = await fetch(`${API_BASE}/auth/me`, {
              headers: { 'Authorization': `Bearer ${newSession.access_token}` },
            });
            if (res.ok) {
              const data = await res.json();
              setUser(data.user);
              setView('dashboard');
              fetchUploads(newSession.access_token);
            }
          } catch (err) {
            console.error('SIGNED_IN handler error:', err);
          }
        }
      }
    });

    // Listen for auth expired events
    const handleAuthExpired = () => {
      setUser(null);
      setSession(null);
      setUploads([]);
      setView('landing');
    };
    window.addEventListener('auth:expired', handleAuthExpired);

    return () => {
      subscription.unsubscribe();
      window.removeEventListener('auth:expired', handleAuthExpired);
    };
  }, []);

  const fetchUploads = async (token) => {
    try {
      const supabase = getSupabase();
      const freshSession = supabase ? (await supabase.auth.getSession())?.data?.session : null;
      const accessToken = token || freshSession?.access_token;
      if (!accessToken) return;
      const res = await fetch(`${API_BASE}/uploads`, {
        headers: { 'Authorization': `Bearer ${accessToken}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUploads(data.uploads || []);
      }
    } catch (err) { console.error('Fetch uploads error:', err); }
  };

  const refreshUser = async () => {
    try {
      const supabase = getSupabase();
      if (!supabase) return;
      const { data: { session: s } } = await supabase.auth.getSession();
      if (!s) return;
      const res = await fetch(`${API_BASE}/auth/me`, {
        headers: { 'Authorization': `Bearer ${s.access_token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setUser(data.user);
      }
    } catch (err) { console.error('Refresh user error:', err); }
  };

  const handleAuthSuccess = (userData, newSession) => {
    setUser(userData);
    setSession(newSession);
    setView('dashboard');
    if (newSession) fetchUploads(newSession.access_token);
  };

  const handleLogout = async () => {
    const supabase = getSupabase();
    if (supabase) await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setUploads([]);
    setCurrentUpload(null);
    setCurrentResult(null);
    setView('landing');
  };

  const handleUploadComplete = (upload) => {
    setCurrentUpload({ ...upload, userRequirements });
    setView('processing');
  };

  const handleProcessComplete = (result) => {
    setCurrentResult(result);
    setView('result');
    fetchUploads();
    refreshUser();
  };

  const handleViewResult = async (uploadId) => {
    try {
      const res = await apiFetch(`/result/${uploadId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentResult(data.result);
        setView('result');
      }
    } catch (err) { console.error('View result error:', err); }
  };

  const handleDeleteUpload = async (id) => {
    try {
      await apiFetch(`/file/${id}`, { method: 'DELETE' });
      fetchUploads();
    } catch (err) { console.error('Delete error:', err); }
  };

  const handleUpgrade = async () => {
    try {
      const res = await apiFetch('/payment/create-order', { method: 'POST' });
      if (!res.ok) { alert('Could not start payment. Please try again.'); return; }
      const { orderId, amount, currency, keyId } = await res.json();
      if (!window.Razorpay) { alert('Payment system loading, please try again in a moment.'); return; }
      const rzp = new window.Razorpay({
        key: keyId,
        amount,
        currency,
        order_id: orderId,
        name: 'DocXL AI',
        description: 'Pro Plan — 300 extractions/month',
        prefill: { email: user?.email || '' },
        theme: { color: '#1D4ED8' },
        handler: async (response) => {
          const verifyRes = await apiFetch('/payment/verify', {
            method: 'POST',
            body: JSON.stringify({ ...response, user_id: user.id }),
          });
          if (verifyRes.ok) {
            await refreshUser();
            alert('You are now on Pro! 300 credits have been added.');
          } else {
            alert('Payment received but activation failed. Please contact support.');
          }
        },
      });
      rzp.open();
    } catch (err) {
      console.error('Upgrade error:', err);
      alert('Something went wrong. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-center">
          <Loader2 className="w-8 h-8 animate-spin text-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Loading DocXL AI...</p>
        </div>
      </div>
    );
  }

  if (view === 'landing') return <LandingPage onGetStarted={(mode) => { setAuthMode(mode); setView('auth'); }} />;
  if (view === 'auth') return <AuthPage mode={authMode} onSwitch={() => setAuthMode(authMode === 'login' ? 'register' : 'login')} onSuccess={handleAuthSuccess} />;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar user={user} currentView={view} onNavigate={setView} onLogout={handleLogout} collapsed={sidebarCollapsed} onToggle={() => setSidebarCollapsed(!sidebarCollapsed)} />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto p-6 lg:p-8">
          {view === 'dashboard' && (
            <DashboardView
              user={user}
              uploads={uploads}
              onUploadComplete={handleUploadComplete}
              onViewResult={handleViewResult}
              onRefresh={() => fetchUploads()}
              userRequirements={userRequirements}
              onRequirementsChange={setUserRequirements}
            />
          )}
          {view === 'upload' && (
            <div className="space-y-6 animate-fade-in">
              <h2 className="text-2xl font-bold">Upload Document</h2>
              <RequirementsField value={userRequirements} onChange={setUserRequirements} />
              <UploadBox onUploadComplete={handleUploadComplete} disabled={(user?.credits_remaining ?? 0) <= 0} />
            </div>
          )}
          {view === 'processing' && <ProcessingView upload={currentUpload} onComplete={handleProcessComplete} onError={() => fetchUploads()} />}
          {view === 'result' && currentResult && <ResultView result={currentResult} onBack={() => { setView('dashboard'); fetchUploads(); }} />}
          {view === 'history' && <HistoryView uploads={uploads} onViewResult={handleViewResult} onDelete={handleDeleteUpload} onRefresh={() => fetchUploads()} />}
          {view === 'pricing' && <PricingView user={user} onUpgrade={handleUpgrade} />}
        </div>
      </main>
    </div>
  );
};

export default App;
