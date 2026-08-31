interface Props {
  currentPage: number;
  totalItems: number;
  pageSize: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ currentPage, totalItems, pageSize, onPageChange }: Props) {
  const totalPages = Math.ceil(totalItems / pageSize);

  // ne prikazuj paginaciju ako ima samo jedna strana
  if (totalPages <= 1) return null;

  return (
    <div style={{ display: "flex", gap: "8px", alignItems: "center", marginTop: "16px", justifyContent: "center" }}>
      <button
        className="btn btn-sm"
        style={{ background: currentPage === 1 ? "#bdc3c7" : "#3498db" }}
        disabled={currentPage === 1}
        onClick={() => onPageChange(currentPage - 1)}
      >
        ← Prethodna
      </button>

      <span style={{ fontSize: "14px", color: "#7f8c8d" }}>
        Strana {currentPage} od {totalPages}
      </span>

      <button
        className="btn btn-sm"
        style={{ background: currentPage === totalPages ? "#bdc3c7" : "#3498db" }}
        disabled={currentPage === totalPages}
        onClick={() => onPageChange(currentPage + 1)}
      >
        Sledeća →
      </button>
    </div>
  );
}