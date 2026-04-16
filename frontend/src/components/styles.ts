export const styles = {
  page: {
    fontFamily: "Arial, sans-serif",
    padding: "24px",
    maxWidth: "1200px",
    margin: "0 auto",
    color: "#e5e7eb",
  } as const,
  header: {
    marginBottom: "24px",
  } as const,
  title: {
    fontSize: "56px",
    fontWeight: 700,
    marginBottom: "8px",
  } as const,
  subtitle: {
    fontSize: "18px",
    color: "#b8c1cc",
    marginBottom: "16px",
  } as const,
  button: {
    padding: "10px 16px",
    borderRadius: "8px",
    border: "1px solid #374151",
    background: "#111827",
    color: "#f9fafb",
    cursor: "pointer",
  } as const,
  grid: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
    gap: "20px",
  } as const,
  card: {
    background: "#111827",
    border: "1px solid #374151",
    borderRadius: "12px",
    padding: "20px",
  } as const,
  sectionTitle: {
    fontSize: "28px",
    fontWeight: 700,
    marginBottom: "16px",
  } as const,
  list: {
    listStyle: "none",
    padding: 0,
    margin: 0,
  } as const,
  listItem: {
    padding: "10px 0",
    borderBottom: "1px solid #1f2937",
  } as const,
  sourceList: {
    listStyle: "none",
    paddingLeft: "12px",
    marginTop: "8px",
    marginBottom: 0,
  } as const,
  sourceItem: {
    fontSize: "14px",
    color: "#cbd5e1",
    padding: "2px 0",
  } as const,
  error: {
    color: "#f43f5e",
    marginTop: "12px",
  } as const,
  success: {
    color: "#22c55e",
    marginTop: "12px",
  } as const,
  empty: {
    color: "#9ca3af",
  } as const,
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "10px",
  } as const,
  input: {
    padding: "10px 12px",
    borderRadius: "8px",
    border: "1px solid #374151",
    background: "#0b1220",
    color: "#f9fafb",
  } as const,
  select: {
    padding: "10px 12px",
    borderRadius: "8px",
    border: "1px solid #374151",
    background: "#0b1220",
    color: "#f9fafb",
  } as const,
  textarea: {
    padding: "10px 12px",
    borderRadius: "8px",
    border: "1px solid #374151",
    background: "#0b1220",
    color: "#f9fafb",
    minHeight: "90px",
    resize: "vertical",
  } as const,
  formTitle: {
    fontSize: "20px",
    fontWeight: 700,
    marginBottom: "12px",
  } as const,
};