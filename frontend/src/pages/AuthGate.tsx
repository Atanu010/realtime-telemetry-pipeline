import { useState } from "react";
import { Activity, KeyRound, Lock, ShieldCheck, Terminal, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { loginOperator } from "@/lib/api";
import { toast } from "sonner";

interface AuthGateProps {
  onAuthenticated: () => void;
}

export default function AuthGate({ onAuthenticated }: AuthGateProps) {
  const [passkey, setPasskey] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!passkey.trim()) {
      setError("Please enter the operator passkey.");
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const res = await loginOperator(passkey.trim());
      toast.success(`Access granted. Welcome, Operator ${res.operator.name}`);
      onAuthenticated();
    } catch {
      setError("Access denied: Invalid operator passkey.");
      toast.error("Authentication failed: Invalid passkey");
    } finally {
      setIsLoading(false);
    }
  };

  const handleUseDefaultKey = () => {
    setPasskey("atanu-telemetry-2026");
    setError(null);
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#070a0f] p-4 text-slate-100">
      <div className="w-full max-w-md">
        {/* Glow & Card container */}
        <div className="relative overflow-hidden rounded-lg border border-[#30363d] bg-[#0d1117] p-6 shadow-2xl sm:p-8">
          <div className="absolute -right-16 -top-16 h-36 w-36 rounded-full bg-cyan-500/10 blur-3xl pointer-events-none" />
          <div className="absolute -left-16 -bottom-16 h-36 w-36 rounded-full bg-emerald-500/10 blur-3xl pointer-events-none" />

          {/* Header */}
          <div className="mb-6 text-center">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-lg border border-cyan-400/30 bg-cyan-400/10 text-cyan-300">
              <Lock className="h-7 w-7" />
            </div>
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/5 px-3 py-1 text-[10px] font-mono uppercase tracking-widest text-cyan-300">
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-cyan-400" />
              RESTRICTED OPERATOR CONSOLE
            </div>
            <h1 className="mt-3 font-mono text-xl font-bold tracking-tight text-white sm:text-2xl">
              STREAMPULSE PIPELINE
            </h1>
            <p className="mt-1.5 text-xs text-slate-400">
              Authorized access only. Enter the operator passkey to unlock telemetry command center.
            </p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-mono uppercase tracking-wider text-slate-400">
                Operator Passkey
              </label>
              <div className="relative mt-2">
                <KeyRound className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                <Input
                  type="password"
                  value={passkey}
                  onChange={(e) => {
                    setPasskey(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Enter operator passkey..."
                  className="h-10 border-[#30363d] bg-[#11161d] pl-9 text-sm text-slate-100 placeholder:text-slate-600 focus:border-cyan-400"
                  autoFocus
                />
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 rounded-sm border border-red-500/30 bg-red-500/10 p-2.5 text-xs text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <Button
              type="submit"
              disabled={isLoading}
              className="w-full bg-cyan-500 font-mono text-xs uppercase tracking-wider text-black hover:bg-cyan-400"
            >
              {isLoading ? (
                <span className="flex items-center gap-2">
                  <Activity className="h-4 w-4 animate-spin" /> Verifying...
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <ShieldCheck className="h-4 w-4" /> Unlock Console
                </span>
              )}
            </Button>
          </form>

          {/* Default Key Fast Unlock Helper */}
          <div className="mt-6 border-t border-[#21262d] pt-4">
            <div className="flex items-center justify-between text-[11px] text-slate-400">
              <span className="flex items-center gap-1.5 text-slate-500">
                <Terminal className="h-3.5 w-3.5" /> Pipeline Owner: Atanu
              </span>
              <button
                type="button"
                onClick={handleUseDefaultKey}
                className="font-mono text-xs text-cyan-400 hover:text-cyan-300 hover:underline"
              >
                Autofill Owner Key
              </button>
            </div>
          </div>
        </div>

        {/* Security badge footer */}
        <p className="mt-4 text-center font-mono text-[10px] text-slate-600">
          TLS ENCRYPTED · ZERO-TRUST OPERATOR PERIMETER · AUDITED ACCESS
        </p>
      </div>
    </div>
  );
}
