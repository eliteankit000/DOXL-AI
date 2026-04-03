import { createClient } from '@supabase/supabase-js';

let supabase = null;

export function getSupabaseBrowser() {
  if (supabase) return supabase;
  // Prevent initialization during SSR/build time
  if (typeof window === 'undefined') return null;
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!url || !key) {
    console.warn('Supabase credentials not available');
    return null;
  }
  supabase = createClient(url, key, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  });
  return supabase;
}
