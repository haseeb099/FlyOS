import { redirect } from "next/navigation";

export default function LeaksRedirectPage({
  searchParams,
}: {
  searchParams: { category?: string };
}) {
  const cat = searchParams.category;
  if (cat) {
    redirect(`/?category=${encodeURIComponent(cat)}`);
  }
  redirect("/");
}
