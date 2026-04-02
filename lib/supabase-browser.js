import { createClient } from '@supabase/supabase-js';

let supabase = null;

export function getSupabaseBrowser() {
  if (supabase) return supabase;
  supabase = createClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
      },
    }
  );
  return supabase;
}
