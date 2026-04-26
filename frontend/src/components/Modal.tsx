import { useEffect, type ReactNode } from "react";
import { styles } from "./styles";

type Props = {
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function Modal({ title, onClose, children }: Props) {
  useEffect(() => {
    const previousBodyOverflow = document.body.style.overflow;
    const previousHtmlOverflow = document.documentElement.style.overflow;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        onClose();
      }
    };

    document.body.style.overflow = "hidden";
    document.documentElement.style.overflow = "hidden";
    window.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousBodyOverflow;
      document.documentElement.style.overflow = previousHtmlOverflow;
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [onClose]);

  return (
    <div className="nf-modal-shell" onClick={onClose}>
      <div
        className="nf-modal-card"
        style={styles.modal}
        onClick={(event) => event.stopPropagation()}
      >
        <div className="nf-modal-header">
          <div className="nf-modal-title-wrap">
            <h2 style={styles.modalTitle}>{title}</h2>
          </div>

          <button
            type="button"
            className="nf-modal-close"
            style={styles.closeButton}
            onClick={onClose}
          >
            Fechar
          </button>
        </div>

        <div className="nf-modal-content">{children}</div>
      </div>
    </div>
  );
}