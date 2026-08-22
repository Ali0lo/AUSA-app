"use client";

import React from "react";
import { signOut, useSession } from "next-auth/react";

export const NavAuthButton: React.FC = () => {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <span className="text-xs text-blue-200">Loading session...</span>;
  }

  if (!session) {
    return null;
  }

  return (
    <div className="flex items-center gap-3 border-l border-blue-800/80 pl-4">
      <div className="text-right">
        <div className="text-xs font-bold text-white leading-tight">
          {session.user?.name || "Student User"}
        </div>
        <div className="text-[10px] text-blue-200">{session.user?.email}</div>
      </div>

      <button
        onClick={() => signOut({ callbackUrl: "/" })}
        className="px-3 py-1.5 rounded-lg bg-blue-800 hover:bg-rose-600 text-white text-xs font-semibold border border-blue-700 hover:border-rose-500 transition-all shadow-sm"
      >
        Sign Out
      </button>
    </div>
  );
};
