"use client";

import { useState, type ReactNode } from "react";

interface TooltipHintProps {
  text: string;
  children: ReactNode;
  position?: "top" | "bottom" | "left" | "right";
}

export function TooltipHint({ text, children, position = "top" }: TooltipHintProps) {
  const [show, setShow] = useState(false);

  const positionClasses = {
    top: "bottom-full left-1/2 -translate-x-1/2 mb-2",
    bottom: "top-full left-1/2 -translate-x-1/2 mt-2",
    left: "right-full top-1/2 -translate-y-1/2 mr-2",
    right: "left-full top-1/2 -translate-y-1/2 ml-2",
  };

  return (
    <div
      className="relative inline-flex items-center gap-1"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      <button
        type="button"
        className="inline-flex items-center justify-center w-4 h-4 text-xs text-gray-400 hover:text-gray-600 border border-gray-300 rounded-full focus:outline-none transition-colors"
        onClick={() => setShow(!show)}
        aria-label="راهنما"
      >
        ?
      </button>
      {show && (
        <div className={`absolute ${positionClasses[position]} z-50 w-64 p-3 bg-gray-800 text-white text-sm rounded-lg shadow-lg`}>
          {text}
        </div>
      )}
    </div>
  );
}
