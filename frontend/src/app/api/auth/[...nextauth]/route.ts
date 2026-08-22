import NextAuth, { AuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const authOptions: AuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Credentials",
      credentials: {
        email: { label: "Email", type: "email", placeholder: "student@ausa.edu.az" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error("Missing email or password credentials.");
        }

        // 1. Post to backend FastAPI /auth/login
        const loginRes = await fetch(`${API_BASE_URL}/auth/login`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
          }),
        });

        if (!loginRes.ok) {
          const errData = await loginRes.json().catch(() => ({}));
          throw new Error(errData.detail || "Invalid login credentials.");
        }

        const tokenData = await loginRes.json();
        const accessToken = tokenData.access_token;

        // 2. Fetch authenticated student profile from /auth/me
        const profileRes = await fetch(`${API_BASE_URL}/auth/me`, {
          headers: {
            Authorization: `Bearer ${accessToken}`,
          },
        });

        if (!profileRes.ok) {
          throw new Error("Failed to fetch authenticated student profile.");
        }

        const profileData = await profileRes.json();

        return {
          id: String(profileData.id),
          email: profileData.email,
          name: profileData.email.split("@")[0],
          accessToken: accessToken,
          profile: profileData,
        };
      },
    }),
  ],
  session: {
    strategy: "jwt",
    maxAge: 7 * 24 * 60 * 60, // 7 days
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.accessToken = (user as any).accessToken;
        token.profile = (user as any).profile;
      }
      return token;
    },
    async session({ session, token }) {
      if (session.user) {
        (session.user as any).accessToken = token.accessToken;
        (session.user as any).profile = token.profile;
      }
      return session;
    },
  },
  secret: process.env.NEXTAUTH_SECRET || "ausa_nextauth_secret_key_12345",
  pages: {
    signIn: "/",
  },
};

const handler = NextAuth(authOptions);

export { handler as GET, handler as POST };
