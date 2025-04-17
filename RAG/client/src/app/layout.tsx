import "./globals.css";
import { Toaster } from "sonner";

export const metadata = {
  title: "Shadcn Tailwind Learn",
  description: "Learning project with Shadcn UI and Tailwind CSS",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>
        {children}
        <Toaster />
      </body>
    </html>
  );
}
