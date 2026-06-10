import type { ReactNode } from "react";
import { createPortal } from "react-dom";
import { useEffect } from "react";

/**
 * 通用模态。
 * - 通过 createPortal 渲染到 document.body，避免被任何祖先 stacking context / overflow 裁切或遮挡。
 * - 内部自带 z-index 与背景遮罩，无需外层包裹 .modal-backdrop。
 * - 点击遮罩或按 Esc 触发 onClose。
 */
export default function Modal({
  open,
  onClose,
  children,
  ariaLabel,
  closeOnBackdrop = true,
}: {
  open: boolean;
  onClose: () => void;
  children: ReactNode;
  ariaLabel?: string;
  closeOnBackdrop?: boolean;
}) {
  // Esc 键关闭
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  // 打开时锁定 body 滚动
  useEffect(() => {
    if (!open) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [open]);

  if (!open) return null;

  return createPortal(
    <div
      className="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-label={ariaLabel}
      onClick={closeOnBackdrop ? onClose : undefined}
      style={{ zIndex: 1000 }}
    >
      <div
        className="modal-panel"
        onClick={(e) => e.stopPropagation()}
      >
        {children}
      </div>
    </div>,
    document.body,
  );
}
