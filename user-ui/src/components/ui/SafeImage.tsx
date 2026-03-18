"use client";

import NextImage, { ImageProps } from "next/image";
import { useState } from "react";

interface SafeImageProps extends Omit<ImageProps, "onError"> {
  fallback?: string;
}

/**
 * Wrapper around Next.js Image that falls back to a placeholder SVG
 * when the source image fails to load (e.g. missing media files in dev).
 */
export default function SafeImage({
  src,
  fallback = "/placeholder.svg",
  alt,
  ...props
}: SafeImageProps) {
  const [imgSrc, setImgSrc] = useState(src);

  return (
    <NextImage
      {...props}
      src={imgSrc}
      alt={alt}
      onError={() => setImgSrc(fallback)}
    />
  );
}
