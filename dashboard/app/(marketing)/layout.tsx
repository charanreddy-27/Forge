import SiteNav from "@/components/site/SiteNav";
import Footer from "@/components/site/Footer";

// Shell for the public-facing site: floating nav + shared footer. The dashboard
// lives under /dashboard with its own shell, so it doesn't inherit this chrome.
export default function MarketingLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <SiteNav />
      <main className="overflow-x-clip">{children}</main>
      <Footer />
    </>
  );
}
