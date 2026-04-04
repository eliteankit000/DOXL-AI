'use client';
import { useEffect } from 'react';
import { createClient } from '@supabase/supabase-js';
import { Loader2, FileSpreadsheet } from 'lucide-react';

const supabase = typeof window !== 'undefined'
  ? createClient(
      process.env.NEXT_PUBLIC_SUPABASE_URL,
      process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
    )
  : null;

export default function AuthCallback() {
  useEffect(() => {
    const handleCallback = async () => {
      try {
        if (!supabase) {
          window.location.href = '/';
          return;
        }
        const { data: { session }, error } = await supabase.auth.getSession();
        if (error) {
          console.error('Auth callback error:', error);
          window.location.href = '/?auth_error=true';
          return;
        }
        if (session) {
          // Profile is auto-created by DB trigger on_auth_user_created
          // Just redirect to app — the main page will pick up the session
          window.location.href = '/';
        } else {
          window.location.href = '/';
        }
      } catch (err) {
        console.error('Auth callback exception:', err);
        window.location.href = '/';
      }
    };
    handleCallback();
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        <div className="w-12 h-12 bg-primary rounded-xl flex items-center justify-center mx-auto">
          <FileSpreadsheet className="w-7 h-7 text-white" />
        </div>
        <Loader2 className="w-6 h-6 animate-spin text-primary mx-auto" />
        <p className="text-muted-foreground text-sm">Completing sign-in...</p>
      </div>
    </div>
  );
}
