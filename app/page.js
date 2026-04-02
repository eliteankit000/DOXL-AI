'use client';
import { useState, useEffect, useCallback, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  FileSpreadsheet, Upload, Zap, Shield, ArrowRight, Check, X, Loader2,
  Download, Trash2, Eye, History, CreditCard, LogOut, Menu,
  FileText, Image, ChevronRight, LayoutDashboard, Clock, Edit3,
  Plus, Minus, RefreshCw, FileDown, BarChart3, Sparkles, ChevronDown
} from 'lucide-react';

const API_BASE = '/api';

// Helper: API call with auth
const apiFetch = async (url, options = {}) => {
  const token = localStorage.getItem('docxl_token');
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }
  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  return res;
};

// ============= LANDING PAGE =============
const LandingPage = ({ onGetStarted }) => {
  return (
    <div className="min-h-screen bg-background">
      {/* Navbar */}
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
              <Button variant="ghost" onClick={() => onGetStarted('login')}>Sign In</Button>
              <Button onClick={() => onGetStarted('register')}>Get Started Free</Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero */}
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

      {/* How it works */}
      <section className="py-20 bg-white">
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
                <CardContent>
                  <p className="text-muted-foreground">{item.desc}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center mb-12">Built for Financial Documents</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: FileText, title: 'PDF Invoices', desc: 'Extract line items, totals, tax details from any invoice format' },
              { icon: CreditCard, title: 'Bank Statements', desc: 'Parse transactions, dates, amounts, and categories automatically' },
              { icon: Image, title: 'Screenshots & Images', desc: 'Capture data from table screenshots and receipts' },
              { icon: Shield, title: 'Secure Processing', desc: 'Files are encrypted and auto-deleted within 24 hours' },
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

      {/* Pricing */}
      <section className="py-20 bg-white" id="pricing">
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
              <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                <Badge className="bg-primary">Most Popular</Badge>
              </div>
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

      {/* Footer */}
      <footer className="py-12 border-t">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <div className="w-6 h-6 bg-primary rounded flex items-center justify-center">
              <FileSpreadsheet className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold">DocXL AI</span>
          </div>
          <p className="text-sm text-muted-foreground">Transform documents into structured data with AI. Fast, secure, accurate.</p>
        </div>
      </footer>
    </div>
  );
};

// ============= AUTH PAGE =============
const AuthPage = ({ mode, onSwitch, onSuccess }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const endpoint = mode === 'login' ? '/auth/login' : '/auth/register';
      const body = mode === 'login' ? { email, password } : { email, password, name };
      const res = await apiFetch(endpoint, { method: 'POST', body: JSON.stringify(body) });
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Something went wrong');
        return;
      }
      localStorage.setItem('docxl_token', data.token);
      onSuccess(data.user);
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
                <Input id="password" type="password" placeholder="Min 6 characters" required value={password} onChange={e => setPassword(e.target.value)} className="mt-1" />
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
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
    <div className={`bg-white border-r h-screen flex flex-col transition-all duration-300 ${collapsed ? 'w-16' : 'w-64'}`}>
      <div className="p-4 flex items-center gap-2 border-b">
        <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center flex-shrink-0">
          <FileSpreadsheet className="w-5 h-5 text-white" />
        </div>
        {!collapsed && <span className="font-bold text-lg">DocXL AI</span>}
        <button onClick={onToggle} className="ml-auto p-1 hover:bg-muted rounded">
          <Menu className="w-4 h-4" />
        </button>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {navItems.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
              ${currentView === item.id ? 'bg-primary/10 text-primary' : 'text-muted-foreground hover:bg-muted hover:text-foreground'}`}
          >
            <item.icon className="w-5 h-5 flex-shrink-0" />
            {!collapsed && <span>{item.label}</span>}
          </button>
        ))}
      </nav>
      <div className="p-3 border-t">
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
        <button
          onClick={onLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
        >
          <LogOut className="w-5 h-5 flex-shrink-0" />
          {!collapsed && <span>Sign Out</span>}
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
    if (!validExts.includes(ext)) {
      setError('Invalid file type. Supported: PDF, JPG, PNG, WEBP');
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError('File too large. Maximum 10MB.');
      return;
    }
    setError('');
    setUploading(true);
    setUploadProgress(30);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await apiFetch('/upload', { method: 'POST', body: formData });
      setUploadProgress(80);
      const data = await res.json();
      if (!res.ok) {
        setError(data.error || 'Upload failed');
        return;
      }
      setUploadProgress(100);
      setTimeout(() => onUploadComplete(data.upload), 500);
    } catch (err) {
      setError('Upload failed: ' + err.message);
    } finally {
      setTimeout(() => {
        setUploading(false);
        setUploadProgress(0);
      }, 1000);
    }
  };

  return (
    <Card className="border-2 border-dashed hover:border-primary/50 transition-colors">
      <CardContent className="pt-6">
        <div
          className={`flex flex-col items-center justify-center py-12 px-6 rounded-xl cursor-pointer transition-colors
            ${dragActive ? 'bg-primary/5 border-primary' : 'hover:bg-muted/50'}
            ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={(e) => { e.preventDefault(); setDragActive(false); handleFile(e.dataTransfer.files[0]); }}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            className="hidden"
            accept=".pdf,.jpg,.jpeg,.png,.webp"
            onChange={(e) => handleFile(e.target.files?.[0])}
          />
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
                {['PDF', 'JPG', 'PNG'].map(t => (
                  <Badge key={t} variant="secondary" className="text-xs">{t}</Badge>
                ))}
              </div>
              <p className="text-xs text-muted-foreground mt-3">Max file size: 10MB</p>
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
    { label: 'Upload Complete', desc: 'File received successfully' },
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
          body: JSON.stringify({ upload_id: upload.id }),
        });
        const data = await res.json();
        if (!res.ok) {
          setError(data.error || 'Processing failed');
          if (onError) onError(data.error);
          return;
        }
        if (cancelled) return;
        setStep(2);
        await new Promise(r => setTimeout(r, 1000));
        if (cancelled) return;
        onComplete(data.result);
      } catch (err) {
        setError('Processing failed: ' + err.message);
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
const DataTable = ({ data, onUpdate }) => {
  const [rows, setRows] = useState(data?.rows || []);
  const [editingCell, setEditingCell] = useState(null);
  const [editValue, setEditValue] = useState('');

  useEffect(() => {
    setRows(data?.rows || []);
  }, [data]);

  const startEdit = (rowIndex, field) => {
    setEditingCell({ rowIndex, field });
    setEditValue(String(rows[rowIndex][field] || ''));
  };

  const saveEdit = () => {
    if (!editingCell) return;
    const { rowIndex, field } = editingCell;
    const newRows = [...rows];
    let value = editValue;
    if (field === 'amount' || field === 'gst') {
      value = parseFloat(editValue) || 0;
    }
    newRows[rowIndex] = { ...newRows[rowIndex], [field]: value };
    setRows(newRows);
    setEditingCell(null);
    if (onUpdate) onUpdate(newRows);
  };

  const addRow = () => {
    const newRow = { id: crypto.randomUUID(), row_number: rows.length + 1, date: '', description: '', amount: 0, type: 'debit', category: '', gst: 0, reference: '' };
    const newRows = [...rows, newRow];
    setRows(newRows);
    if (onUpdate) onUpdate(newRows);
  };

  const deleteRow = (index) => {
    const newRows = rows.filter((_, i) => i !== index);
    setRows(newRows);
    if (onUpdate) onUpdate(newRows);
  };

  const columns = [
    { key: 'date', label: 'Date', width: 'w-28' },
    { key: 'description', label: 'Description', width: 'w-64' },
    { key: 'amount', label: 'Amount', width: 'w-28', align: 'right' },
    { key: 'type', label: 'Type', width: 'w-24' },
    { key: 'category', label: 'Category', width: 'w-32' },
    { key: 'gst', label: 'GST', width: 'w-24', align: 'right' },
    { key: 'reference', label: 'Ref', width: 'w-28' },
  ];

  return (
    <div className="space-y-4">
      <ScrollArea className="w-full">
        <div className="min-w-[800px]">
          <div className="bg-primary text-primary-foreground rounded-t-lg">
            <div className="flex items-center text-sm font-medium">
              <div className="w-10 px-3 py-3">#</div>
              {columns.map(col => (
                <div key={col.key} className={`${col.width} px-3 py-3 ${col.align === 'right' ? 'text-right' : ''}`}>{col.label}</div>
              ))}
              <div className="w-16 px-3 py-3"></div>
            </div>
          </div>
          <div className="border border-t-0 rounded-b-lg divide-y">
            {rows.length === 0 ? (
              <div className="py-8 text-center text-muted-foreground">No data extracted. Try reprocessing.</div>
            ) : (
              rows.map((row, rowIndex) => (
                <div key={row.id || rowIndex} className="flex items-center hover:bg-muted/30 transition-colors group">
                  <div className="w-10 px-3 py-2 text-xs text-muted-foreground">{rowIndex + 1}</div>
                  {columns.map(col => (
                    <div
                      key={col.key}
                      className={`${col.width} px-3 py-2 text-sm cursor-pointer ${col.align === 'right' ? 'text-right' : ''}
                        ${editingCell?.rowIndex === rowIndex && editingCell?.field === col.key ? '' : 'hover:bg-primary/5 rounded'}`}
                      onClick={() => startEdit(rowIndex, col.key)}
                    >
                      {editingCell?.rowIndex === rowIndex && editingCell?.field === col.key ? (
                        <Input
                          className="h-7 text-sm"
                          value={editValue}
                          onChange={e => setEditValue(e.target.value)}
                          onBlur={saveEdit}
                          onKeyDown={e => { if (e.key === 'Enter') saveEdit(); if (e.key === 'Escape') setEditingCell(null); }}
                          autoFocus
                        />
                      ) : (
                        <span className={`${!row[col.key] && row[col.key] !== 0 ? 'text-muted-foreground italic' : ''}`}>
                          {col.key === 'amount' || col.key === 'gst' ? (typeof row[col.key] === 'number' ? row[col.key].toFixed(2) : row[col.key] || '0.00') : (row[col.key] || '-')}
                        </span>
                      )}
                    </div>
                  ))}
                  <div className="w-16 px-3 py-2">
                    <button onClick={() => deleteRow(rowIndex)} className="opacity-0 group-hover:opacity-100 transition-opacity p-1 hover:bg-destructive/10 rounded">
                      <Trash2 className="w-3.5 h-3.5 text-destructive" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </ScrollArea>
      <Button variant="outline" size="sm" onClick={addRow}>
        <Plus className="w-4 h-4 mr-1" /> Add Row
      </Button>
    </div>
  );
};

// ============= RESULT VIEW =============
const ResultView = ({ result, onBack, onSave, token }) => {
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [currentRows, setCurrentRows] = useState(result?.rows || []);

  const handleUpdate = (newRows) => {
    setCurrentRows(newRows);
    setSaved(false);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const res = await apiFetch(`/result/${result.upload_id}`, {
        method: 'PUT',
        body: JSON.stringify({ rows: currentRows }),
      });
      if (res.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (err) {
      console.error('Save failed:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleExportExcel = async () => {
    try {
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
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `docxl_export_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Extraction Results</h2>
          <p className="text-muted-foreground mt-1">
            {result?.file_name || 'Document'} &bull; {currentRows.length} rows extracted
            {result?.document_type && <Badge variant="secondary" className="ml-2">{result.document_type}</Badge>}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={onBack}>
            <ChevronRight className="w-4 h-4 mr-1 rotate-180" /> Back
          </Button>
          <Button variant="outline" size="sm" onClick={handleSave} disabled={saving}>
            {saving ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : saved ? <Check className="w-4 h-4 mr-1 text-green-500" /> : <Edit3 className="w-4 h-4 mr-1" />}
            {saved ? 'Saved!' : 'Save Changes'}
          </Button>
          <Button variant="outline" size="sm" onClick={handleExportJSON}>
            <FileDown className="w-4 h-4 mr-1" /> JSON
          </Button>
          <Button size="sm" onClick={handleExportExcel}>
            <Download className="w-4 h-4 mr-1" /> Download Excel
          </Button>
        </div>
      </div>

      {/* Summary cards */}
      {result?.summary && (
        <div className="grid grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Total Rows</p>
              <p className="text-2xl font-bold">{currentRows.length}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Total Amount</p>
              <p className="text-2xl font-bold">{(currentRows.reduce((s, r) => s + (parseFloat(r.amount) || 0), 0)).toFixed(2)}</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-4 pb-4">
              <p className="text-sm text-muted-foreground">Confidence</p>
              <p className="text-2xl font-bold">{((result.confidence_score || 0.85) * 100).toFixed(0)}%</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Editable Table */}
      <Card>
        <CardContent className="pt-6">
          <DataTable data={{ rows: currentRows }} onUpdate={handleUpdate} />
        </CardContent>
      </Card>

      <p className="text-xs text-muted-foreground text-center">Click any cell to edit. Changes are saved when you click &quot;Save Changes&quot;.</p>
    </div>
  );
};

// ============= DASHBOARD VIEW =============
const DashboardView = ({ user, onUploadComplete, uploads, onViewResult, onRefresh }) => {
  return (
    <div className="space-y-8 animate-fade-in">
      <div>
        <h1 className="text-3xl font-bold">Welcome, {user?.name || 'there'}!</h1>
        <p className="text-muted-foreground mt-1">Upload a document to get started</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                <BarChart3 className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Credits Left</p>
                <p className="text-xl font-bold">{user?.credits_remaining || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-green-500/10 rounded-lg flex items-center justify-center">
                <FileSpreadsheet className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Files Processed</p>
                <p className="text-xl font-bold">{uploads?.filter(u => u.status === 'completed').length || 0}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-orange-500/10 rounded-lg flex items-center justify-center">
                <Zap className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p className="text-sm text-muted-foreground">Plan</p>
                <p className="text-xl font-bold capitalize">{user?.plan || 'free'}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Upload Box */}
      <UploadBox onUploadComplete={onUploadComplete} disabled={user?.credits_remaining <= 0} />
      {user?.credits_remaining <= 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 text-center">
          <p className="text-orange-700 font-medium">No credits remaining. Upgrade to Pro for 300 files/month.</p>
        </div>
      )}

      {/* Recent Uploads */}
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
                      <Badge variant={
                        upload.status === 'completed' ? 'default' :
                        upload.status === 'processing' ? 'secondary' :
                        upload.status === 'failed' ? 'destructive' : 'outline'
                      }>
                        {upload.status}
                      </Badge>
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
};

// ============= HISTORY VIEW =============
const HistoryView = ({ uploads, onViewResult, onDelete, onRefresh }) => {
  return (
    <div className="space-y-6 animate-fade-in">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Upload History</h2>
          <p className="text-muted-foreground mt-1">{uploads?.length || 0} total uploads</p>
        </div>
        <Button variant="outline" size="sm" onClick={onRefresh}><RefreshCw className="w-4 h-4 mr-1" /> Refresh</Button>
      </div>
      {(!uploads || uploads.length === 0) ? (
        <Card className="py-16 text-center">
          <CardContent>
            <History className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">No uploads yet. Upload your first document!</p>
          </CardContent>
        </Card>
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
                    <Badge variant={
                      upload.status === 'completed' ? 'default' :
                      upload.status === 'processing' ? 'secondary' :
                      upload.status === 'failed' ? 'destructive' : 'outline'
                    }>
                      {upload.status}
                    </Badge>
                    {upload.status === 'completed' && (
                      <Button size="sm" variant="outline" onClick={() => onViewResult(upload.id)}>
                        <Eye className="w-4 h-4 mr-1" /> View
                      </Button>
                    )}
                    <Button size="sm" variant="ghost" onClick={() => onDelete(upload.id)}>
                      <Trash2 className="w-4 h-4 text-muted-foreground" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// ============= PRICING VIEW =============
const PricingView = ({ user, onNavigate }) => {
  return (
    <div className="space-y-8 animate-fade-in">
      <div className="text-center">
        <h2 className="text-3xl font-bold">Upgrade Your Plan</h2>
        <p className="text-muted-foreground mt-2">Get more extractions with DocXL Pro</p>
      </div>
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
            <div className="text-3xl font-bold mt-4">$9<span className="text-lg font-normal text-muted-foreground">/month</span></div>
            <p className="text-sm text-muted-foreground">or &#x20B9;699/month for India</p>
          </CardHeader>
          <CardContent>
            <ul className="space-y-3">
              {['300 files/month', 'Priority processing', 'All export formats', 'Editable results', 'Batch processing', 'Priority support'].map((f, i) => (
                <li key={i} className="flex items-center gap-2 text-sm"><Check className="w-4 h-4 text-green-500" />{f}</li>
              ))}
            </ul>
            {user?.plan !== 'pro' && (
              <Button className="w-full mt-6">Upgrade to Pro</Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// ============= MAIN APP =============
const App = () => {
  const [view, setView] = useState('landing');
  const [authMode, setAuthMode] = useState('login');
  const [user, setUser] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [currentUpload, setCurrentUpload] = useState(null);
  const [currentResult, setCurrentResult] = useState(null);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [loading, setLoading] = useState(true);

  // Check auth on mount
  useEffect(() => {
    const checkAuth = async () => {
      const token = localStorage.getItem('docxl_token');
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const res = await apiFetch('/auth/me');
        if (res.ok) {
          const data = await res.json();
          setUser(data.user);
          setView('dashboard');
          fetchUploads();
        } else {
          localStorage.removeItem('docxl_token');
        }
      } catch (err) {
        localStorage.removeItem('docxl_token');
      } finally {
        setLoading(false);
      }
    };
    checkAuth();
  }, []);

  const fetchUploads = async () => {
    try {
      const res = await apiFetch('/uploads');
      if (res.ok) {
        const data = await res.json();
        setUploads(data.uploads || []);
      }
    } catch (err) {
      console.error('Fetch uploads error:', err);
    }
  };

  const handleAuthSuccess = (userData) => {
    setUser(userData);
    setView('dashboard');
    fetchUploads();
  };

  const handleLogout = () => {
    localStorage.removeItem('docxl_token');
    setUser(null);
    setUploads([]);
    setCurrentUpload(null);
    setCurrentResult(null);
    setView('landing');
  };

  const handleUploadComplete = (upload) => {
    setCurrentUpload(upload);
    setView('processing');
  };

  const handleProcessComplete = (result) => {
    setCurrentResult(result);
    setView('result');
    fetchUploads();
    // Refresh user to get updated credits
    apiFetch('/auth/me').then(r => r.json()).then(d => { if (d.user) setUser(d.user); }).catch(() => {});
  };

  const handleViewResult = async (uploadId) => {
    try {
      const res = await apiFetch(`/result/${uploadId}`);
      if (res.ok) {
        const data = await res.json();
        setCurrentResult(data.result);
        setView('result');
      }
    } catch (err) {
      console.error('View result error:', err);
    }
  };

  const handleDeleteUpload = async (id) => {
    try {
      await apiFetch(`/file/${id}`, { method: 'DELETE' });
      fetchUploads();
    } catch (err) {
      console.error('Delete error:', err);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  // Landing / Auth views
  if (view === 'landing') {
    return <LandingPage onGetStarted={(mode) => { setAuthMode(mode); setView('auth'); }} />;
  }
  if (view === 'auth') {
    return (
      <AuthPage
        mode={authMode}
        onSwitch={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
        onSuccess={handleAuthSuccess}
      />
    );
  }

  // Authenticated views with sidebar
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar
        user={user}
        currentView={view}
        onNavigate={(v) => setView(v)}
        onLogout={handleLogout}
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
      />
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-6xl mx-auto p-6 lg:p-8">
          {view === 'dashboard' && (
            <DashboardView
              user={user}
              uploads={uploads}
              onUploadComplete={handleUploadComplete}
              onViewResult={handleViewResult}
              onRefresh={fetchUploads}
            />
          )}
          {view === 'upload' && (
            <div className="space-y-6 animate-fade-in">
              <h2 className="text-2xl font-bold">Upload Document</h2>
              <UploadBox onUploadComplete={handleUploadComplete} disabled={user?.credits_remaining <= 0} />
            </div>
          )}
          {view === 'processing' && (
            <ProcessingView
              upload={currentUpload}
              onComplete={handleProcessComplete}
              onError={() => { fetchUploads(); }}
            />
          )}
          {view === 'result' && currentResult && (
            <ResultView
              result={currentResult}
              onBack={() => { setView('dashboard'); fetchUploads(); }}
              token={localStorage.getItem('docxl_token')}
            />
          )}
          {view === 'history' && (
            <HistoryView
              uploads={uploads}
              onViewResult={handleViewResult}
              onDelete={handleDeleteUpload}
              onRefresh={fetchUploads}
            />
          )}
          {view === 'pricing' && (
            <PricingView user={user} onNavigate={setView} />
          )}
        </div>
      </main>
    </div>
  );
};

export default App;
