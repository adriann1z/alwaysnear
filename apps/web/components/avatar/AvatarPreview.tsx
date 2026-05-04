"use client";

export function AvatarPreview({ imageUrl }: { imageUrl?: string | null }) {
  return (
    <div className="aspect-square w-full overflow-hidden rounded-[2rem] bg-lavender">
      {imageUrl ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={imageUrl} alt="Avatar preview" className="h-full w-full object-cover" />
      ) : (
        <div className="flex h-full items-center justify-center text-sm text-ink/60">
          Avatar preview
        </div>
      )}
    </div>
  );
}

export default AvatarPreview;
