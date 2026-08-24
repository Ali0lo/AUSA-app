import "next-auth";
import "next-auth/jwt";
import { StudentAccountProfile } from "@/types";

declare module "next-auth" {
  interface Session {
    user?: {
      name?: string | null;
      email?: string | null;
      image?: string | null;
      accessToken?: string;
      profile?: StudentAccountProfile;
    };
  }

  interface User {
    accessToken?: string;
    profile?: StudentAccountProfile;
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    accessToken?: string;
    profile?: StudentAccountProfile;
  }
}
