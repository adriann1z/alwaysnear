import type { ReactNode } from "react";

import { Providers } from "./providers";
import "../styles/globals.css";

export const metadata = {
  title: "Always Near",
  description: "Always Near MVP"
};

export default function RootLayout({
  children
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
