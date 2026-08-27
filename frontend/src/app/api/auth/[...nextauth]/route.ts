import NextAuth, { AuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";
import GoogleProvider from "next-auth/providers/google";
import { StudentAccountProfile } from "@/types";

const API_BASE_URL =
  process.env.AUSA_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:8000/api/v1";

async function readDetail(response: Response, fallback: string): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: unknown };
    return typeof data.detail === "string" ? data.detail : fallback;
  } catch {
    return fallback;
  }
}

const providers = [];

if (process.env.GOOGLE_CLIENT_ID?.trim() && process.env.GOOGLE_CLIENT_SECRET?.trim()) {
  providers.push(
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID.trim(),
      clientSecret: process.env.GOOGLE_CLIENT_SECRET.trim()
    })
  );
}

providers.push(
  CredentialsProvider({
    name: "Email and password",
    credentials: {
      email: { label: "Email", type: "email" },
      password: { label: "Password", type: "password" }
    },
    async authorize(credentials) {
      const email = credentials?.email?.trim();
      const password = credentials?.password;

      if (!email || !password) {
        throw new Error("Enter both your email address and password.");
      }

      let loginResponse: Response;

      try {
        loginResponse = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json"
          },
          body: JSON.stringify({ email, password }),
          signal: AbortSignal.timeout(12000)
        });
      } catch {
        throw new Error("The AUSA backend could not be reached. Start it and try again.");
      }

      if (!loginResponse.ok) {
        throw new Error(await readDetail(loginResponse, "The email address or password was not accepted."));
      }

      const tokenData = (await loginResponse.json()) as { access_token?: string };

      if (!tokenData.access_token) {
        throw new Error("The backend did not return an access token.");
      }

      let profileResponse: Response;

      try {
        profileResponse = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            Accept: "application/json",
            Authorization: `Bearer ${tokenData.access_token}`
          },
          signal: AbortSignal.timeout(12000)
        });
      } catch {
        throw new Error("Login succeeded, but the student profile could not be loaded.");
      }

      if (!profileResponse.ok) {
        throw new Error(await readDetail(profileResponse, "Login succeeded, but the student profile was rejected."));
      }

      const profile = (await profileResponse.json()) as StudentAccountProfile;

      if (!profile.id || !profile.email) {
        throw new Error("The backend returned an incomplete student profile.");
      }

      return {
        id: String(profile.id),
        email: profile.email,
        name: profile.email.split("@")[0],
        accessToken: tokenData.access_token,
        profile
      };
    }
  })
);

const authOptions: AuthOptions = {
  providers,
  session: {
    strategy: "jwt",
    maxAge: 7 * 24 * 60 * 60
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = user.accessToken;
        token.profile = user.profile;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.accessToken = token.accessToken;
        session.user.profile = token.profile;
      }
      return session;
    }
  },
  secret: process.env.NEXTAUTH_SECRET || "ausa_development_secret_key_change_in_prod_2026",
  pages: {
    signIn: "/sign-in"
  }
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
