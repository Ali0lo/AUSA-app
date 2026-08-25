import type { Metadata } from "next";
import { RegisterForm } from "@/components/RegisterForm";

export const metadata: Metadata = {
  title: "Create account",
  description: "Create an AUSA student profile using the existing backend registration flow."
};

export default function RegisterPage() {
  return <RegisterForm />;
}
